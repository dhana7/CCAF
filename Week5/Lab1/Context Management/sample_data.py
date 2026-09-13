"""Mock customer + orders database for the support agent lab."""

CUSTOMERS = {
    "C-1001": {
        "customer_id": "C-1001",
        "name": "Aarti Sharma",
        "email": "aarti.sharma@example.com",
        "tier": "Gold",
        "shipping_address": "12 MG Road, Hyderabad, TS 500001",
    }
}

ORDERS = {
    "O-9001": {
        "order_id": "O-9001",
        "customer_id": "C-1001",
        "status": "Delivered",
        "total": 1499.0,
        "placed_on": "2026-05-12",
        "items": [{"sku": "SKU-AAA", "name": "Bluetooth Headphones", "qty": 1}],
    },
    "O-9002": {
        "order_id": "O-9002",
        "customer_id": "C-1001",
        "status": "Shipped",
        "total": 2799.0,
        "placed_on": "2026-06-15",
        "items": [{"sku": "SKU-BBB", "name": "Smart Watch", "qty": 1}],
    },
    "O-9003": {
        "order_id": "O-9003",
        "customer_id": "C-1001",
        "status": "Processing",
        "total": 549.0,
        "placed_on": "2026-06-18",
        "items": [{"sku": "SKU-CCC", "name": "Phone Case", "qty": 2}],
    },
}


def get_customer(customer_id: str) -> dict | None:
    return CUSTOMERS.get(customer_id)


def get_orders_for_customer(customer_id: str) -> list[dict]:
    """ALL orders for a customer — in real life this is hundreds of rows."""
    return [o for o in ORDERS.values() if o["customer_id"] == customer_id]


def get_open_orders_for_customer(customer_id: str) -> list[dict]:
    """Open = anything not yet delivered. Used for the ambiguity demo."""
    return [o for o in ORDERS.values()
            if o["customer_id"] == customer_id and o["status"] != "Delivered"]
