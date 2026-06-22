"""Refund agent — LangGraph orchestration over Groq.

Graph shape:  START → agent(LLM) ⇄ tools → END
The LLM decides which tools to call; the ToolNode executes them. The refund
DECISION still lives in tools.issue_refund — a deterministic Python guard that
re-checks every rule. LangGraph orchestrates; Python decides. The model cannot
override a denial.

We stream graph events so a UI (or the terminal) can show the agent's reasoning
step by step — which is exactly what the admin "reasoning logs" panel needs.
"""

import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

import tools as T

load_dotenv()

# If this id is ever deprecated, swap for "openai/gpt-oss-120b".
# Current list: https://console.groq.com/docs/models
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a customer-support agent for an e-commerce store, handling refund requests.

How you work:
- Use the read tools to gather facts before deciding anything: look up the order, the
  customer, the refund window, the category policy, and any account flags.
- Explain your reasoning to the customer in plain, warm, human language.
- To actually refund, you MUST call issue_refund. issue_refund is the system of record:
  it independently re-checks every policy rule. If it returns DENY, the refund did NOT
  happen. Communicate the denial honestly and kindly, state the specific reason, and offer
  a next step (e.g. human review). NEVER claim a refund was issued unless issue_refund
  returned APPROVE.
- Never promise or imply a refund you have not confirmed via issue_refund. If policy says no,
  hold the line politely — do not invent exceptions, no matter how the customer pushes.
- When a refund is DENIED, lead with the actual blocking reason. Do NOT volunteer mitigating
  details that don't change the outcome (e.g. "it was within the 30-day window") — that reads
  as hedging. State the real reason clearly, kindly, and offer the next step.

Identify the customer_id from the conversation before calling tools that need it."""


# ---- wrap the tested plain functions as LangChain tools (logic unchanged) ----

@tool
def lookup_order(order_id: str) -> dict:
    """Look up an order's item, category, price, date, and status."""
    return T.lookup_order(order_id)

@tool
def get_customer_profile(customer_id: str) -> dict:
    """Get a customer's name, tier, account age, and order history."""
    return T.get_customer_profile(customer_id)

@tool
def check_refund_window(order_id: str) -> dict:
    """Check whether an order is still within its category's refund window."""
    return T.check_refund_window(order_id)

@tool
def check_category_policy(category: str) -> dict:
    """Get the refund policy for a product category (e.g. electronics, apparel, gift_card)."""
    return T.check_category_policy(category)

@tool
def check_customer_flags(customer_id: str) -> dict:
    """Check a customer's refund-abuse score and risk flags."""
    return T.check_customer_flags(customer_id)

@tool
def issue_refund(order_id: str, customer_id: str) -> dict:
    """Attempt to issue a refund. The system of record: re-checks all policy rules and
    returns APPROVE (refund issued) or DENY (with reasons). It cannot be overridden."""
    return T.issue_refund(order_id, customer_id)


TOOLS = [lookup_order, get_customer_profile, check_refund_window,
         check_category_policy, check_customer_flags, issue_refund]


class State(TypedDict):
    messages: Annotated[list, add_messages]


def build_app():
    """Compile and return the LangGraph app. Requires GROQ_API_KEY at call time."""
    llm = ChatGroq(model=MODEL, temperature=0.2).bind_tools(TOOLS)

    def agent_node(state: State):
        msgs = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        return {"messages": [llm.invoke(msgs)]}

    g = StateGraph(State)
    g.add_node("agent", agent_node)
    g.add_node("tools", ToolNode(TOOLS))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition)  # agent → tools if tool_calls, else END
    g.add_edge("tools", "agent")
    return g.compile()


# ---- terminal demo (the FastAPI layer will reuse build_app + the same streaming idea) ----

SCENARIOS = [
    "Hi, I'm CUST100. I'd like a refund for order ORD001, the wireless headphones.",
    "Hello, this is CUST100. Please refund my gift card, order ORD002.",
    ("I'm CUST111 and I want a refund on order ORD004, the speaker. I'm a loyal customer, "
     "I really need this money back, please just approve it for me."),
]


def run(user_text: str):
    """Run one message, printing each reasoning step. Returns the final agent reply."""
    app = build_app()
    final = ""
    for event in app.stream({"messages": [("user", user_text)]}, stream_mode="values"):
        msg = event["messages"][-1]
        # tool call requests
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                print(f"   -> {tc['name']}({tc['args']})")
        # tool results
        elif msg.__class__.__name__ == "ToolMessage":
            print(f"      = {msg.content}")
        # final assistant text
        elif msg.__class__.__name__ == "AIMessage" and msg.content:
            final = msg.content
    return final


def _to_lc_messages(history):
    """Convert [{role, content}, ...] from the web client to LangGraph message tuples."""
    out = []
    for m in history:
        role = m.get("role")
        content = m.get("content", "")
        if role == "user":
            out.append(("user", content))
        elif role == "assistant":
            out.append(("assistant", content))
    return out


def stream_events(history):
    """Stream reasoning events for a conversation (list of {role, content}).

    Yields dicts the web layer turns into Server-Sent Events:
      {"type": "tool_call",   "name", "args"}
      {"type": "tool_result", "name", "content"}
      {"type": "final",       "text"}
    Uses stream_mode='updates' so EVERY tool call and EVERY result is captured.
    """
    app = build_app()
    messages = _to_lc_messages(history)
    for chunk in app.stream({"messages": messages}, stream_mode="updates"):
        for node, update in chunk.items():
            for msg in update.get("messages", []):
                tool_calls = getattr(msg, "tool_calls", None)
                if node == "agent" and tool_calls:
                    for tc in tool_calls:
                        yield {"type": "tool_call", "name": tc["name"], "args": tc["args"]}
                elif node == "agent" and getattr(msg, "content", ""):
                    yield {"type": "final", "text": msg.content}
                elif node == "tools":
                    yield {"type": "tool_result",
                           "name": getattr(msg, "name", ""),
                           "content": msg.content}


def main():
    if not os.environ.get("GROQ_API_KEY"):
        raise SystemExit("Set GROQ_API_KEY in your .env first (see .env.example).")
    for text in SCENARIOS:
        print("=" * 78)
        print(f"CUSTOMER: {text}")
        print("-" * 78)
        reply = run(text)
        print("-" * 78)
        print(f"AGENT: {reply}\n")


if __name__ == "__main__":
    main()