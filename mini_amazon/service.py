from security import hash_password, verify_password
from storage import save_json


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
