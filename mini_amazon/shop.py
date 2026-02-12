from datetime import datetime
from storage import load_json, save_json


class User:
    def __init__(self, username, password=None):
        self.username = username
        self.password = password
        self.cart = []
        self.is_logged_in = False


def register_user(users):
    name = input("Username: ").strip()
    pw = input("Password: ").strip()

    if len(pw) < 6:
        print("Password must be at least 6 characters long.")
        return

    if name in users:
        print("Username taken")
        return

    users[name] = {"password": pw, "cart": []}
    save_json("users.json", users)
    print("Account created!")


def login_user(users):
    name = input("Username: ").strip()
    pw = input("Password: ").strip()

    if name in users and users[name]["password"] == pw:
        u = User(name, pw)
        u.is_logged_in = True
        u.cart = users[name].get("cart", [])
        print("Logged in!")
        return u

    print("Invalid login")
    return None


def print_products(products):
    print("\nProducts:")
    for pid, p in products.items():
        print(f"{pid}. {p['name']} - ${p['price']} (Stock: {p['stock']})")


def browse_products(users, current_user, products):
    print_products(products)

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

    if qty <= 0:
        print("Quantity must be positive")
        return

    if p["stock"] < qty:
        print("Not enough stock")
        return

    merged = False
    for item in current_user.cart:
        if item["product"] == product_id:
            new_qty = item["quantity"] + qty
            if new_qty > p["stock"]:
                print("Not enough stock for that total quantity")
                return
            item["quantity"] = new_qty
            merged = True
            break

    if not merged:
        current_user.cart.append(
            {"product": product_id, "name": p["name"], "quantity": qty, "price": p["price"]}
        )

    users[current_user.username]["cart"] = current_user.cart
    save_json("users.json", users)
    print("Added to cart!")


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

    pid = input("\nEnter product ID to remove/reduce (or press Enter to go back): ").strip()
    if not pid:
        return

    idx = None
    for i, item in enumerate(cart):
        if item["product"] == pid:
            idx = i
            break

    if idx is None:
        print("That product is not in your cart.")
        return

    amt = input("How many to remove? (number or 'all'): ").strip().lower()
    if amt == "all":
        cart.pop(idx)
    else:
        try:
            remove_qty = int(amt)
        except ValueError:
            print("Invalid amount")
            return

        if remove_qty <= 0:
            print("Remove quantity must be positive")
            return

        if remove_qty >= cart[idx]["quantity"]:
            cart.pop(idx)
        else:
            cart[idx]["quantity"] -= remove_qty

    users[current_user.username]["cart"] = cart
    current_user.cart = cart
    save_json("users.json", users)
    print("Cart updated!")


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
        total += item["price"] * item["quantity"]
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

    print("\nReceipt")
    print("-" * 30)
    print(f"Order ID: {order_id}")
    print(f"Username: {current_user.username}")
    print(f"Time: {timestamp}")
    print("-" * 30)
    for it in items_out:
        print(f"{it['name']} x{it['qty']} @ ${it['unit_price']}")
    print("-" * 30)
    print(f"Total: ${total}")
    print("-" * 30)
    print("Purchase complete!")


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
            print(f"  - {it.get('name')} x{it.get('qty')} (${it.get('unit_price')} each)")
    print("-" * 30)
