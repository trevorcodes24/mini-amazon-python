import json
import os
import hashlib
import hmac
import secrets


def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default
    return default


def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(stored: str, provided: str) -> bool:
    if "$" not in stored:
        return stored == provided
    salt, digest = stored.split("$", 1)
    check = hashlib.sha256((salt + provided).encode("utf-8")).hexdigest()
    return hmac.compare_digest(digest, check)


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
