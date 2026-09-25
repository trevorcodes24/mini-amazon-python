import json
import os


def load_json(filename, default):
    """Load JSON data from a file, returning the default if unavailable."""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return default

    return default


def save_json(filename, data):
    """Write data to a JSON file."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def initialize_data():
    """Load application data and create the default product catalogue."""
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
