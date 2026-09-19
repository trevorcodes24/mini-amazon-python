import os
from datetime import datetime
from storage import load_json, save_json
from service import (
    register_account,
    authenticate_user,
    add_item_to_cart,
    remove_item_from_cart,
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
    if not current_user.cart:
        print("Cart is empty")
        return

    for item in current_user.cart:
        pid = item["product"]
        qty = item["quantity"]

        if pid not in products:
            print(f"Product {pid} no longer exists. Remove it from cart first.")
            return

        if qty > products[pid]["stock"]:
            print(
                f"Not enough stock for {products[pid]['name']}. "
                f"Requested: {qty}, Available: {products[pid]['stock']}"
            )
            return

    for item in current_user.cart:
        pid = item["product"]
        products[pid]["stock"] -= item["quantity"]

    orders = load_json("orders.json", [])

    max_n = 0
    for o in orders:
        oid = str(o.get("order_id", ""))
        if oid.startswith("O") and oid[1:].isdigit():
            max_n = max(max_n, int(oid[1:]))
    order_id = f"O{max_n + 1:04d}"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    items_out = []
    total = 0
    for item in current_user.cart:
        line_total = item["price"] * item["quantity"]
        total += line_total
        items_out.append(
            {
                "product_id": item["product"],
                "name": item["name"],
                "qty": item["quantity"],
                "unit_price": item["price"],
            }
        )

    order = {
        "order_id": order_id,
        "username": current_user.username,
        "items": items_out,
        "total": total,
        "timestamp": timestamp,
    }

    orders.append(order)
    save_json("orders.json", orders)

    current_user.cart = []
    users[current_user.username]["cart"] = []
    save_json("users.json", users)
    save_json("products.json", products)

    receipt_lines = []
    receipt_lines.append("Receipt")
    receipt_lines.append("-" * 30)
    receipt_lines.append(f"Order ID: {order_id}")
    receipt_lines.append(f"Username: {current_user.username}")
    receipt_lines.append(f"Time: {timestamp}")
    receipt_lines.append("-" * 30)
    for it in items_out:
        receipt_lines.append(f"{it['name']} x{it['qty']} @ ${it['unit_price']}")
    receipt_lines.append("-" * 30)
    receipt_lines.append(f"Total: ${total}")
    receipt_lines.append("-" * 30)

    print("\n" + "\n".join(receipt_lines))
    print("Purchase complete!")

    os.makedirs("receipts", exist_ok=True)
    receipt_path = os.path.join("receipts", f"{order_id}.txt")
    with open(receipt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(receipt_lines))
    print(f"Receipt saved to: {receipt_path}")


def view_order_history(current_user):
    orders = load_json("orders.json", [])
    user_orders = [o for o in orders if o.get("username") == current_user.username]

    if not user_orders:
        print("No orders yet.")
        return

    print("\nOrder History:")
    for o in user_orders:
        print("-" * 30)
        print(f"Order: {o.get('order_id')} | Time: {o.get('timestamp')} | Total: ${o.get('total')}")
        for it in o.get("items", []):
            qty = it.get("qty", it.get("quantity"))
            print(f"  - {it.get('name')} x{qty} (${it.get('unit_price')} each)")
    print("-" * 30)
