"""Mock data store: 15-profile CRM + category refund policy. Plain dicts, no DB.
"""
 
TODAY = "2026-06-22"
REFUND_ABUSE_THRESHOLD = 5  # abuse score at/above this blocks an automated refund
 
# 15 customer profiles (CRM) 
CUSTOMERS = {
    "CUST100": {"customer_id": "CUST100", "name": "Asha Rao",        "tier": "gold",     "account_age_days": 540, "lifetime_orders": 42},
    "CUST101": {"customer_id": "CUST101", "name": "Rahul Mehta",     "tier": "standard", "account_age_days": 210, "lifetime_orders": 11},
    "CUST102": {"customer_id": "CUST102", "name": "Priya Nair",      "tier": "gold",     "account_age_days": 800, "lifetime_orders": 67},
    "CUST103": {"customer_id": "CUST103", "name": "Imran Sheikh",    "tier": "standard", "account_age_days": 95,  "lifetime_orders": 7},
    "CUST104": {"customer_id": "CUST104", "name": "Neha Gupta",      "tier": "silver",   "account_age_days": 300, "lifetime_orders": 19},
    "CUST105": {"customer_id": "CUST105", "name": "Arjun Reddy",     "tier": "standard", "account_age_days": 45,  "lifetime_orders": 4},
    "CUST106": {"customer_id": "CUST106", "name": "Sara Thomas",     "tier": "gold",     "account_age_days": 610, "lifetime_orders": 51},
    "CUST107": {"customer_id": "CUST107", "name": "Kabir Singh",     "tier": "silver",   "account_age_days": 260, "lifetime_orders": 15},
    "CUST108": {"customer_id": "CUST108", "name": "Divya Iyer",      "tier": "standard", "account_age_days": 130, "lifetime_orders": 9},
    "CUST109": {"customer_id": "CUST109", "name": "Manish Verma",    "tier": "silver",   "account_age_days": 410, "lifetime_orders": 23},
    "CUST110": {"customer_id": "CUST110", "name": "Fatima Khan",     "tier": "gold",     "account_age_days": 720, "lifetime_orders": 58},
    "CUST111": {"customer_id": "CUST111", "name": "Vikram Shah",     "tier": "standard", "account_age_days": 25,  "lifetime_orders": 9},
    "CUST112": {"customer_id": "CUST112", "name": "Ananya Bose",     "tier": "silver",   "account_age_days": 340, "lifetime_orders": 21},
    "CUST113": {"customer_id": "CUST113", "name": "Rohit Pillai",    "tier": "standard", "account_age_days": 60,  "lifetime_orders": 6},
    "CUST114": {"customer_id": "CUST114", "name": "Meera Joshi",     "tier": "gold",     "account_age_days": 905, "lifetime_orders": 80},
}
 
# orders 
ORDERS = {
    "ORD001": {"order_id": "ORD001", "customer_id": "CUST100", "item": "Wireless Headphones", "category": "electronics", "price": 2999.0, "order_date": "2026-06-10", "status": "delivered"},
    "ORD002": {"order_id": "ORD002", "customer_id": "CUST100", "item": "Amazon Gift Card",    "category": "gift_card",   "price": 1000.0, "order_date": "2026-06-18", "status": "delivered"},
    "ORD003": {"order_id": "ORD003", "customer_id": "CUST100", "item": "Cotton T-Shirt",      "category": "apparel",     "price": 799.0,  "order_date": "2026-04-01", "status": "delivered"},
    "ORD004": {"order_id": "ORD004", "customer_id": "CUST111", "item": "Bluetooth Speaker",   "category": "electronics", "price": 3499.0, "order_date": "2026-06-15", "status": "delivered"},
    "ORD005": {"order_id": "ORD005", "customer_id": "CUST100", "item": "Running Shoes",       "category": "apparel",     "price": 4999.0, "order_date": "2026-06-20", "status": "in_transit"},
    "ORD006": {"order_id": "ORD006", "customer_id": "CUST102", "item": "Mechanical Keyboard", "category": "electronics", "price": 5499.0, "order_date": "2026-06-12", "status": "delivered"},
    "ORD007": {"order_id": "ORD007", "customer_id": "CUST103", "item": "Organic Mangoes 5kg", "category": "perishables", "price": 650.0,  "order_date": "2026-06-19", "status": "delivered"},
    "ORD008": {"order_id": "ORD008", "customer_id": "CUST104", "item": "Denim Jacket",        "category": "apparel",     "price": 2499.0, "order_date": "2026-06-14", "status": "delivered"},
    "ORD009": {"order_id": "ORD009", "customer_id": "CUST106", "item": "Smartwatch",          "category": "electronics", "price": 8999.0, "order_date": "2026-05-01", "status": "delivered"},
    "ORD010": {"order_id": "ORD010", "customer_id": "CUST109", "item": "Steam Gift Card",     "category": "gift_card",   "price": 1500.0, "order_date": "2026-06-16", "status": "delivered"},
    "ORD011": {"order_id": "ORD011", "customer_id": "CUST110", "item": "Yoga Mat",            "category": "apparel",     "price": 1299.0, "order_date": "2026-06-11", "status": "delivered"},
    "ORD012": {"order_id": "ORD012", "customer_id": "CUST112", "item": "USB-C Hub",           "category": "electronics", "price": 1899.0, "order_date": "2026-06-21", "status": "delivered"},
    "ORD013": {"order_id": "ORD013", "customer_id": "CUST113", "item": "Fresh Strawberries",  "category": "perishables", "price": 320.0,  "order_date": "2026-06-20", "status": "delivered"},
    "ORD014": {"order_id": "ORD014", "customer_id": "CUST114", "item": "Noise-Cancel Earbuds","category": "electronics", "price": 6499.0, "order_date": "2026-06-17", "status": "delivered"},
    "ORD015": {"order_id": "ORD015", "customer_id": "CUST107", "item": "Wool Sweater",        "category": "apparel",     "price": 1999.0, "order_date": "2026-03-20", "status": "delivered"},
    "ORD016": {"order_id": "ORD016", "customer_id": "CUST105", "item": "Phone Case",          "category": "electronics", "price": 499.0,  "order_date": "2026-06-13", "status": "delivered"},
}
 
# category policy (window_days = None => non-refundable / final sale) 
CATEGORY_POLICY = {
    "electronics": {"refundable": True,  "window_days": 30,   "note": "Returnable within 30 days if undamaged."},
    "apparel":     {"refundable": True,  "window_days": 15,   "note": "Returnable within 15 days, unworn with tags."},
    "gift_card":   {"refundable": False, "window_days": None, "note": "Gift cards are final sale and non-refundable."},
    "perishables": {"refundable": False, "window_days": None, "note": "Perishable goods are final sale."},
}
 
# ---- risk flags (customers not listed default to a clean record) ----
CUSTOMER_FLAGS = {
    "CUST100": {"customer_id": "CUST100", "refund_abuse_score": 0, "refunds_last_90d": 1, "blocked": False},
    "CUST103": {"customer_id": "CUST103", "refund_abuse_score": 2, "refunds_last_90d": 2, "blocked": False},
    "CUST105": {"customer_id": "CUST105", "refund_abuse_score": 6, "refunds_last_90d": 5, "blocked": False},
    "CUST111": {"customer_id": "CUST111", "refund_abuse_score": 8, "refunds_last_90d": 6, "blocked": False},
    "CUST113": {"customer_id": "CUST113", "refund_abuse_score": 9, "refunds_last_90d": 7, "blocked": True},
}
 
