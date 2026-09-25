from datetime import datetime

from .security import hash_password, verify_password
from .storage import load_json, save_json


def register_account(users, username, password):
    """Create a new user account after validating the credentials."""
    username = username.strip()

    if not username:
        return False, "Username cannot be empty."

    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    if username in users:
        return False, "Username already exists."

    users[username] = {
        "password": hash_password(password),
        "cart": [],
    }

    save_json("users.json", users)
    return True, "Account created."


def authenticate_user(users, username, password):
    """Validate a username and password."""
    username = username.strip()

    if username in users and verify_password(
        users[username]["password"],
        password,
    ):
        return True, "Logged in."

    return False, "Invalid username or password."


def get_user_cart(users, username):
    """Return a user's current cart."""
    return users.get(username, {}).get("cart", [])


def add_item_to_cart(users, products, username, product_id, quantity):
    """Validate and add a product quantity to a user's cart."""
    if username not in users:
        return False, "User account not found."

    if product_id not in products:
        return False, "Invalid product."

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return False, "Quantity must be a number."

    if quantity <= 0:
        return False, "Quantity must be greater than 0."

    product = products[product_id]
    stock = int(product["stock"])

    if quantity > stock:
        return False, f"Not enough stock. Available: {stock}"

    cart = users[username].setdefault("cart", [])

    for item in cart:
        if item["product"] == product_id:
            new_quantity = item["quantity"] + quantity

            if new_quantity > stock:
                return (
                    False,
                    f"Not enough stock for that total quantity. Available: {stock}",
                )

            item["quantity"] = new_quantity
            save_json("users.json", users)
            return True, "Cart updated."

    cart.append(
        {
            "product": product_id,
            "name": product["name"],
            "quantity": quantity,
            "price": product["price"],
        }
    )

    save_json("users.json", users)
    return True, "Added to cart."


def remove_item_from_cart(users, username, product_id, amount):
    """Remove some or all of a product from a user's cart."""
    if username not in users:
        return False, "User account not found."

    cart = users[username].setdefault("cart", [])

    index = next(
        (i for i, item in enumerate(cart) if item["product"] == product_id),
        None,
    )

    if index is None:
        return False, "Item not in cart."

    if isinstance(amount, str) and amount.strip().lower() == "all":
        cart.pop(index)
        save_json("users.json", users)
        return True, "Item removed."

    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return False, "Remove amount must be a number or 'all'."

    if amount <= 0:
        return False, "Remove amount must be greater than 0."

    if amount >= cart[index]["quantity"]:
        cart.pop(index)
    else:
        cart[index]["quantity"] -= amount

    save_json("users.json", users)
    return True, "Cart updated."

def _next_order_id(orders):
    """Generate the next sequential order ID."""
    max_number = 0

    for order in orders:
        order_id = str(order.get("order_id", ""))

        if order_id.startswith("O") and order_id[1:].isdigit():
            max_number = max(max_number, int(order_id[1:]))

    return f"O{max_number + 1:04d}"


def checkout_account(users, products, username):
    """Validate a cart, create an order, update stock, and clear the cart."""
    if username not in users:
        return False, "User account not found.", None

    cart = users[username].get("cart", [])

    if not cart:
        return False, "Cart is empty.", None

    # Validate the whole cart before modifying anything.
    for item in cart:
        product_id = item["product"]

        if product_id not in products:
            return (
                False,
                f"Product {product_id} no longer exists.",
                None,
            )

        available_stock = int(products[product_id]["stock"])

        if item["quantity"] > available_stock:
            return (
                False,
                (
                    f"Not enough stock for "
                    f"{products[product_id]['name']}. "
                    f"Available: {available_stock}"
                ),
                None,
            )

    orders = load_json("orders.json", [])
    order_id = _next_order_id(orders)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    order_items = []
    total = 0

    for item in cart:
        line_total = item["price"] * item["quantity"]
        total += line_total

        order_items.append(
            {
                "product_id": item["product"],
                "name": item["name"],
                "qty": item["quantity"],
                "unit_price": item["price"],
            }
        )

    order = {
        "order_id": order_id,
        "username": username,
        "items": order_items,
        "total": total,
        "timestamp": timestamp,
    }

    # Only mutate state after every cart item has passed validation.
    for item in cart:
        products[item["product"]]["stock"] -= item["quantity"]

    orders.append(order)
    users[username]["cart"] = []

    save_json("products.json", products)
    save_json("orders.json", orders)
    save_json("users.json", users)

    return True, "Purchase complete.", order


def get_order_history(username):
    """Return all orders belonging to a user."""
    orders = load_json("orders.json", [])

    return [
        order
        for order in orders
        if order.get("username") == username
    ]


def format_receipt(order):
    """Create a printable receipt for an order."""
    lines = [
        "Receipt",
        "-" * 36,
        f"Order ID: {order['order_id']}",
        f"Username: {order['username']}",
        f"Time: {order['timestamp']}",
        "-" * 36,
    ]

    for item in order["items"]:
        lines.append(
            f"{item['name']} x{item['qty']} @ ${item['unit_price']}"
        )

    lines.extend(
        [
            "-" * 36,
            f"Total: ${order['total']}",
            "-" * 36,
        ]
    )

    return "\n".join(lines)
