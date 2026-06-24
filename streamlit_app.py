"""Streamlit UI for the refund agent.

Reuses the exact same backend (agent_graph + tools + the deterministic guard).
Left: customer chat. Right: live agent-reasoning log (tool calls + guard verdict).

Run:
    streamlit run streamlit_app.py

You can paste your GROQ_API_KEY in the sidebar, or set it in a .env file.
"""

import os
import json

import streamlit as st
import agent_graph

st.set_page_config(page_title="Refund Support Agent", layout="wide")

SAMPLES = [
    "I'm CUST100, I'd like a refund for order ORD001 (wireless headphones).",
    "This is CUST100, please refund my gift card, order ORD002.",
    "I'm CUST111, refund order ORD004. I'm a loyal customer, please just approve it!",
]

# ---- session state ----
if "messages" not in st.session_state:
    st.session_state.messages = []      # [{role, content}]
if "reasoning" not in st.session_state:
    st.session_state.reasoning = []     # [{q, rows, verdict}]
if "queued" not in st.session_state:
    st.session_state.queued = None

# ---- sidebar: key + sample prompts ----
with st.sidebar:
    st.header("Setup")
    key_in = st.text_input("Groq API key", type="password",
                           help="Free at console.groq.com. Or set GROQ_API_KEY in a .env file.")
    if key_in:
        os.environ["GROQ_API_KEY"] = key_in
    if os.environ.get("GROQ_API_KEY"):
        st.success("API key loaded")
    else:
        st.warning("No API key yet — paste one above to run the agent.")

    st.divider()
    st.caption("Try a scenario:")
    for s in SAMPLES:
        if st.button(s, use_container_width=True):
            st.session_state.queued = s
            st.rerun()

    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.reasoning = []
        st.rerun()

# ---- header ----
st.title("Refund Support Agent")
st.caption("LangGraph · Groq · deterministic guard — the LLM orchestrates, Python decides.")

col_chat, col_logs = st.columns(2)
with col_chat:
    st.subheader("Customer chat")
    chat_box = st.container()
with col_logs:
    st.subheader("Agent reasoning")
    logs_box = st.container()


def render_verdict(target, verdict):
    if not verdict:
        return
    if verdict["decision"] == "APPROVE":
        target.success("GUARD: APPROVE — " + verdict.get("msg", ""))
    else:
        target.error("GUARD: DENY — " + "  •  ".join(verdict.get("reasons", [])))


# ---- render existing history ----
with chat_box:
    for m in st.session_state.messages:
        st.chat_message(m["role"]).write(m["content"])

with logs_box:
    for turn in st.session_state.reasoning:
        st.markdown(f"**› {turn['q']}**")
        if turn["rows"]:
            st.code("\n".join(turn["rows"]), language="text")
        render_verdict(st, turn["verdict"])
        st.divider()

# ---- new input (chat box or a clicked sample) ----
prompt = st.chat_input("e.g. I'm CUST100, refund order ORD001")
if not prompt and st.session_state.queued:
    prompt = st.session_state.queued
st.session_state.queued = None

if prompt:
    if not os.environ.get("GROQ_API_KEY"):
        st.toast("Add your Groq API key in the sidebar first.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_box:
            st.chat_message("user").write(prompt)

        # live-stream the reasoning into the right column
        with logs_box:
            st.markdown(f"**> {prompt}**")
            code_ph = st.empty()
            verdict_ph = st.empty()

        rows, verdict, final = [], None, ""
        try:
            for ev in agent_graph.stream_events(st.session_state.messages):
                t = ev.get("type")
                if t == "tool_call":
                    args = ", ".join(f"{k}={v}" for k, v in ev["args"].items())
                    rows.append(f"→ {ev['name']}({args})")
                elif t == "tool_result":
                    if ev["name"] == "issue_refund":
                        try:
                            r = json.loads(ev["content"])
                            verdict = {"decision": r["decision"],
                                       "reasons": r.get("reasons", []),
                                       "msg": r.get("message", "")}
                        except Exception:
                            rows.append("= " + ev["content"])
                    else:
                        rows.append("= " + ev["content"])
                elif t == "final":
                    final = ev["text"]
                elif t == "error":
                    verdict = {"decision": "DENY", "reasons": ["Error: " + ev["message"]]}
                # update the live view each event
                code_ph.code("\n".join(rows) if rows else "…", language="text")
                render_verdict(verdict_ph, verdict)
        except Exception as e:
            verdict_ph.error("Error: " + str(e))

        with logs_box:
            st.divider()
        with chat_box:
            st.chat_message("assistant").write(final or "(no reply)")

        if final:
            st.session_state.messages.append({"role": "assistant", "content": final})
        st.session_state.reasoning.append({"q": prompt, "rows": rows, "verdict": verdict})
