"""Offline  test of the deterministic guard — no API key needed.
 
Proves the guard returns the right decision for every path, including deny cases.
Run:  python test_guard.py
"""
import tools
 
CASES = [
    ("ORD001", "CUST100", "APPROVE", "delivered electronics, in window, clean customer"),
    ("ORD002", "CUST100", "DENY",    "gift card is final sale (non-refundable category)"),
    ("ORD003", "CUST100", "DENY",    "apparel ordered ~82 days ago, 15-day window passed"),
    ("ORD004", "CUST111", "DENY",    "valid order BUT customer flagged for refund abuse (score 8)"),
    ("ORD005", "CUST100", "DENY",    "order still in transit, not delivered"),
    ("ORD013", "CUST113", "DENY",    "perishable + blocked account"),
    ("ORD001", "CUST111", "DENY",    "order does not belong to this customer"),
    ("ORD006", "CUST102", "APPROVE", "delivered electronics, in window, clean gold customer"),
    ("ORD999", "CUST100", "DENY",    "order does not exist"),
]
 
def main():
    passed = 0
    for oid, cid, expected, why in CASES:
        r = tools.issue_refund(oid, cid)
        ok = r["decision"] == expected
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {oid} / {cid} -> {r['decision']}  ({why})")
        if r["decision"] == "DENY":
            for reason in r["reasons"]:
                print(f"         reason: {reason}")
    print(f"\n{passed}/{len(CASES)} cases passed.")
 
if __name__ == "__main__":
    main()