import json
import os


def load_json(filename, default):
    """Load JSON from disk; return default if missing/invalid."""
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default
    return default


def save_json(filename, data):
    """Save JSON to disk."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def initialize_data():
    users = load_json("users.json", {})
    products = load_json("products.json", {})
    orders = load_json("orders.json", [])

    if not products:
        products = {
            "1": {"name": "Laptop", "price": 999, "stock": 5},
            "2": {"name": "Phone", "price": 599, "stock": 10},
            "3": {"name": "Headphones", "price": 149, "stock": 20},
        }
        save_json("products.json", products)

    if not os.path.exists("orders.json"):
        save_json("orders.json", orders)

    return users, products, orders
