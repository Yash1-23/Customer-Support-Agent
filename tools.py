"""Tools the agent can call: five read-only lookups + one guarded action.
 
THE KEY DESIGN DECISION

The LLM gathers facts with the read tools and talks to the customer, but it does
NOT decide refunds. issue_refund() is a deterministic Python guard: it re-checks
EVERY policy rule itself, so no amount of customer persuasion (or LLM mistake)
can force a refund the policy forbids. The LLM orchestrates; Python decides.
 
This is deterministic control over the money decision, for auditability:
an LLM can be talked into things; a guard can't.
"""
 
from datetime import date
import data
 
 
def _days_between(d1: str, d2: str) -> int:
    y1, m1, dd1 = map(int, d1.split("-"))
    y2, m2, dd2 = map(int, d2.split("-"))
    return (date(y2, m2, dd2) - date(y1, m1, dd1)).days
 
 

# 5 read-only tools — the agent calls these to gather facts (visible in the loop)

 
def lookup_order(order_id: str) -> dict:
    order = data.ORDERS.get(order_id)
    if not order:
        return {"found": False, "error": f"No order with id {order_id}."}
    return {"found": True, **order}
 
 
def get_customer_profile(customer_id: str) -> dict:
    c = data.CUSTOMERS.get(customer_id)
    if not c:
        return {"found": False, "error": f"No customer with id {customer_id}."}
    return {"found": True, **c}
 
 
def check_refund_window(order_id: str) -> dict:
    order = data.ORDERS.get(order_id)
    if not order:
        return {"found": False, "error": f"No order with id {order_id}."}
    policy = data.CATEGORY_POLICY.get(order["category"], {})
    window = policy.get("window_days")
    days_since = _days_between(order["order_date"], data.TODAY)
    if window is None:
        return {"found": True, "days_since_order": days_since, "window_days": None,
                "within_window": False, "note": "Category has no refund window (final sale)."}
    return {"found": True, "days_since_order": days_since, "window_days": window,
            "within_window": days_since <= window}
 
 
def check_category_policy(category: str) -> dict:
    policy = data.CATEGORY_POLICY.get(category)
    if not policy:
        return {"found": False, "error": f"No policy on record for category '{category}'."}
    return {"found": True, "category": category, **policy}
 
 
def check_customer_flags(customer_id: str) -> dict:
    flags = data.CUSTOMER_FLAGS.get(customer_id)
    if not flags:
        return {"found": True, "customer_id": customer_id, "refund_abuse_score": 0,
                "refunds_last_90d": 0, "blocked": False, "note": "No risk flags on record."}
    return {"found": True, **flags}
 
 

# The guarded action — deterministic. Re-checks everything. LLM cannot override.
 
def issue_refund(order_id: str, customer_id: str) -> dict:
 
    """  Deterministic refund guard. Returns APPROVE (+ refund issued) or DENY (+ reasons).
    Every rule is re-checked here regardless of what the conversation claimed."""
    reasons = []
 
    order = data.ORDERS.get(order_id)
    if not order:
        return {"action": "issue_refund", "decision": "DENY", "order_id": order_id,
                "reasons": [f"Order {order_id} does not exist."]}
 
    # Rule 1 — order must belong to the requesting customer
    if order["customer_id"] != customer_id:
        reasons.append("Order does not belong to this customer.")
 
    # Rule 2 — only delivered orders can be refunded
    if order["status"] != "delivered":
        reasons.append(f"Order status is '{order['status']}', not 'delivered'. "
                       "Refunds apply only to delivered orders.")
 
    # Rule 3 — category must be refundable
    policy = data.CATEGORY_POLICY.get(order["category"], {})
    if not policy.get("refundable", False):
        reasons.append(f"Category '{order['category']}' is non-refundable. "
                       f"{policy.get('note', 'Final sale.')}")
 
    # Rule 4 — must be inside the refund window (only if category has one)
    window = policy.get("window_days")
    if window is not None:
        days_since = _days_between(order["order_date"], data.TODAY)
        if days_since > window:
            reasons.append(f"Refund window passed: {days_since} days since order, "
                           f"limit is {window} days for {order['category']}.")
 
    # Rule 5 — customer must not be flagged for refund abuse
    flags = data.CUSTOMER_FLAGS.get(customer_id, {})
    if flags.get("blocked"):
        reasons.append("Customer account is blocked from automated refunds.")
    if flags.get("refund_abuse_score", 0) >= data.REFUND_ABUSE_THRESHOLD:
        reasons.append(f"Refund-abuse score {flags.get('refund_abuse_score')} is at/above the "
                       f"threshold of {data.REFUND_ABUSE_THRESHOLD}; routing to human review.")
 
    if reasons:
        return {"action": "issue_refund", "decision": "DENY", "order_id": order_id, "reasons": reasons}
 
    return {"action": "issue_refund", "decision": "APPROVE", "order_id": order_id,
            "amount": order["price"], "status": "refund_issued",
            "message": f"Refund of Rs {order['price']:.2f} issued for {order['item']}."}
 
 
# Dispatch table + JSON schemas the LLM sees
 
TOOL_FUNCTIONS = {
    "lookup_order": lookup_order,
    "get_customer_profile": get_customer_profile,
    "check_refund_window": check_refund_window,
    "check_category_policy": check_category_policy,
    "check_customer_flags": check_customer_flags,
    "issue_refund": issue_refund,
}
 
def _fn(name, desc, props, required):
    return {"type": "function", "function": {
        "name": name, "description": desc,
        "parameters": {"type": "object", "properties": props, "required": required}}}
 
TOOL_SCHEMAS = [
    _fn("lookup_order", "Look up an order's item, category, price, date, and status.",
        {"order_id": {"type": "string", "description": "Order id, e.g. ORD001"}}, ["order_id"]),
    _fn("get_customer_profile", "Get a customer's name, tier, account age, and order history.",
        {"customer_id": {"type": "string", "description": "Customer id, e.g. CUST100"}}, ["customer_id"]),
    _fn("check_refund_window", "Check whether an order is still within its category's refund window.",
        {"order_id": {"type": "string"}}, ["order_id"]),
    _fn("check_category_policy", "Get the refund policy for a product category.",
        {"category": {"type": "string", "description": "e.g. electronics, apparel, gift_card"}}, ["category"]),
    _fn("check_customer_flags", "Check a customer's refund-abuse score and risk flags.",
        {"customer_id": {"type": "string"}}, ["customer_id"]),
    _fn("issue_refund",
        "Attempt to issue a refund. This is the system of record and re-checks all policy "
        "rules. Returns APPROVE (refund issued) or DENY (with reasons). It cannot be overridden.",
        {"order_id": {"type": "string"}, "customer_id": {"type": "string"}}, ["order_id", "customer_id"]),
]
