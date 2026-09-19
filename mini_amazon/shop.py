import os
from service import (
    register_account,
    authenticate_user,
    add_item_to_cart,
    remove_item_from_cart,
    checkout_account,
    get_order_history,
    format_receipt,
)

class User:
    def __init__(self, username, password=None):
        self.username = username
        self.password = password
        self.cart = []
        self.is_logged_in = False


def register_user(users):
    name = input("Username: ").strip()
    pw = input("Password: ").strip()

    success, message = register_account(users, name, pw)
    print(message)


def login_user(users):
    name = input("Username: ").strip()
    pw = input("Password: ").strip()

    success, message = authenticate_user(users, name, pw)

    if success:
        user = User(name, pw)
        user.is_logged_in = True
        user.cart = users[name].get("cart", [])
        print(message)
        return user

    print(message)
    return None


def browse_products(users, current_user, products):
    print("\nProducts:")
    for pid, p in products.items():
        print(f"{pid}. {p['name']} - ${p['price']} (Stock: {p['stock']})")

    product_id = input("\nEnter product ID to view details (or press Enter to go back): ").strip()
    if not product_id:
        return

    if product_id not in products:
        print("Invalid product ID")
        return

    p = products[product_id]
    print("\nProduct Details")
    print("-" * 30)
    print(f"ID: {product_id}")
    print(f"Name: {p['name']}")
    print(f"Price: ${p['price']}")
    print(f"Stock: {p['stock']}")
    print("-" * 30)

    action = input("1) Add to cart  2) Back : ").strip()
    if action != "1":
        return

    try:
        qty = int(input("Quantity: ").strip())
    except ValueError:
        print("Quantity must be a number")
        return

    success, message = add_item_to_cart(
        users,
        products,
        current_user.username,
        product_id,
        qty,
    )

    if success:
        current_user.cart = users[current_user.username]["cart"]

    print(message)


def search_products(products):
    keyword = input("Search keyword: ").strip().lower()
    if not keyword:
        print("Search cannot be empty.")
        return

    found = False
    print("\nSearch results:")
    for pid, product in products.items():
        if keyword in product["name"].lower():
            print(f"{pid}. {product['name']} - ${product['price']} (Stock: {product['stock']})")
            found = True

    if not found:
        print("No matching products found.")


def view_cart(users, current_user):
    cart = current_user.cart
    if not cart:
        print("Cart is empty")
        return

    print("\nYour Cart:")
    total = 0
    for item in cart:
        line_total = item["price"] * item["quantity"]
        total += line_total
        print(
            f"- {item['product']}: {item['name']} | Qty: {item['quantity']} | "
            f"Unit: ${item['price']} | Subtotal: ${line_total}"
        )
    print(f"Total: ${total}")

    pid = input(
        "Enter product ID to remove/reduce (or press Enter to go back): "
    ).strip()

    if not pid:
        return

    amt = input(
        "How many to remove? (number or 'all'): "
    ).strip().lower()

    success, message = remove_item_from_cart(
        users,
        current_user.username,
        pid,
        amt,
    )

    if success:
        current_user.cart = users[current_user.username]["cart"]

    print(message)

def checkout(users, current_user, products):
    success, message, order = checkout_account(
        users,
        products,
        current_user.username,
    )

    if not success:
        print(message)
        return

    current_user.cart = users[current_user.username]["cart"]

    receipt = format_receipt(order)

    print("\n" + receipt)
    print(message)

    os.makedirs("receipts", exist_ok=True)
    receipt_path = os.path.join(
        "receipts",
        f"{order['order_id']}.txt",
    )

    with open(receipt_path, "w", encoding="utf-8") as file:
        file.write(receipt + "\n")

    print(f"Receipt saved to: {receipt_path}")

def view_order_history(current_user):
    orders = get_order_history(current_user.username)

    if not orders:
        print("No orders yet.")
        return

    print("\nOrder History:")

    for order in orders:
        print("-" * 30)
        print(
            f"Order: {order['order_id']} | "
            f"Time: {order['timestamp']} | "
            f"Total: ${order['total']}"
        )

        for item in order["items"]:
            print(
                f"  - {item['name']} x{item['qty']} "
                f"(${item['unit_price']} each)"
            )

    print("-" * 30)