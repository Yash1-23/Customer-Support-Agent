# AI Customer-Support-Agent

## AI Customer Support Agent : E-Commerce Refunds

An AI customer support agent that processes or denies e-commerce refund requests by reasoning over a mock CRM and a strict refund policy. The agent dynamically orchestrates a set of granular tools to gather facts, but the final grant/deny decision is enforced by deterministic Python, not LLM discretion — so the agent can be persuasive and conversational while remaining impossible to talk into a policy violation.

## The Problem

Refund automation is easy to get wrong in one specific way: if you let the LLM decide whether a refund is valid, a frustrated or clever customer can argue it into approving something the policy forbids. The interesting engineering challenge isn't the happy path — it's holding the line on the edge case.

This project solves that by splitting responsibilities cleanly:


-The LLM gathers and explains — it decides which tools to call, in what order, and narrates its reasoning.

-Python enforces the policy — the actual approve/deny decision lives in a deterministic guard that the model cannot override.


This is the same architectural principle used in production financial systems: the model extracts facts, code makes the decision.

<img width="1043" height="1268" alt="Screenshot 2026-06-23 184831" src="https://github.com/user-attachments/assets/06312f06-8bc6-45e8-94d9-ab2422a9357f" />


Even if the LLM is convinced a refund should be issued, the guard independently verifies the refund window, category policy, and customer flags. If any rule fails, the refund is denied — regardless of what the conversation looked like.

## How the Agent Works (Tool Orchestration)

The agent runs a function-calling loop powered by Groq. On each turn it can call one or more tools, observe the results, reason about them, and decide its next step. Every step is logged to a visible reasoning trace shown in the admin dashboard.


Read tools (gather facts)

  Tool                      Purpose
  
lookup_order           Fetch an order by ID — items, price, purchase date, status

get_customer_profile   Pull the customer's CRM record and history

check_refund_window    Determine whether the order is still within the allowed return window

check_category_policy  Apply category-specific rules (e.g. final-sale, perishable, electronics)

check_customer_flags   Surface risk flags (refund abuse history, blacklist, chargebacks)



Action tool (make the change)

Tool                  Purpose

issue_refund        Attempts to issue a refund — gated by a deterministic policy guard that re-validates every rule before approving



A typical run: the agent calls lookup_order → check_refund_window → check_category_policy → check_customer_flags, reasons over the combined result, and only then calls issue_refund. The guard inside issue_refund is the final authority.


## Tech Stack
 
Layer                     Choice                                                         Why

LLM/Agent Loop          Groq function calling (llama-3.3-70b-versatile)                 Fast inference, native tool-calling, transparent per-step orchestration.
             
Frontend                  Streamlit                                                     Quick to build a clean chat UI + admin dashboard in one app
 
Backend logic            Plain Python (dicts + functions)                                Flat, readable, no unnecessary framework overhead

Mock CRM                  In-code Python data store                                      15 customer profiles, 21 orders covering every policy branch

Policy                    Strict refund policy document + deterministic rule checks       Decisions are auditable and tamper-proof



## Setup

1. Clone and enter the repo

 git clone https://github.com/Yash1-23/Customer-Support-Agent.git
 
cd Customer-Support-Agent

2. Create a virtual environment and install dependencies

python -m venv venv

source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt

3. Add your Groq API key

Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key_here

## Running the App

bashstreamlit run app.py

This launches:

Customer chat interface — where a customer submits a refund request and converses with the agent.

Admin dashboard (pages/) — a real-time view of the agent's reasoning: which tools were called, what they returned, and how the final decision was reached.


Demo Scenarios

The agent is built to handle two cases the evaluator cares about:

1. Standard refund (happy path)
A customer requests a refund for an order that's within the return window, in an eligible category, with no risk flags. The agent gathers the facts, confirms eligibility, and issues the refund.

2. Holding the line (edge case / policy violation)
A customer requests a refund that violates policy — e.g. outside the return window, a final-sale item, or an account flagged for refund abuse. Even when the customer pushes back, the agent stays firm: the deterministic guard inside issue_refund denies the request and the agent clearly explains why.



## Testing

bash :  test_guard.py

test_guard.py asserts that policy-violating refund requests are denied by the deterministic guard — the single most important behavior of the system. This proves the deny path is enforced in code, not left to LLM judgment.


## What Makes This Robust

- Tamper-proof decisions — the LLM can't be argued into a policy violation; the Python guard has the final say.

- Visible orchestration — every tool call and reasoning step is logged and surfaced in the admin panel, so decisions are fully auditable.

- Granular tools — splitting investigation into five focused tools (rather than one monolithic checker) lets the agent orchestrate dynamically and makes the reasoning trace genuinely informative.

- Complete test data — 15 profiles and 21 orders cover every policy branch, so each rule can be demonstrated live.


                                      
