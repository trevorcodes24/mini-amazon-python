import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from storage import initialize_data, load_json, save_json, hash_password, verify_password


class MiniAmazonGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini-Amazon")
        self.geometry("980x640")
        self.minsize(920, 600)

        self.users, self.products, self.orders = initialize_data()
        self.current_user = None

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"))
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 11))
        self.style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))
        self.style.configure("TButton", font=("Segoe UI", 10), padding=8)
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=10)
        self.style.configure("TEntry", padding=6)
        self.style.configure("TNotebook.Tab", padding=(14, 10))
        self.style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("Status.TLabel", font=("Segoe UI", 10))

        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (WelcomeFrame, AppFrame):
            frame = F(self.container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        self.show("WelcomeFrame")

    def show(self, name):
        frame = self.frames[name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

    def reload_data(self):
        self.users, self.products, self.orders = initialize_data()

    def set_status(self, text):
        app = self.frames.get("AppFrame")
        if app:
            app.status_var.set(text)

    def register(self, username, password):
        username = username.strip()
        if not username:
            return False, "Username cannot be empty."
        if len(password) < 6:
            return False, "Password must be at least 6 characters long."
        if username in self.users:
            return False, "Username already exists."
        self.users[username] = {"password": hash_password(password), "cart": []}
        save_json("users.json", self.users)
        self.reload_data()
        return True, "Account created."

    def login(self, username, password):
        username = username.strip()
        if username in self.users and verify_password(self.users[username]["password"], password):
            if "$" not in self.users[username]["password"]:
                self.users[username]["password"] = hash_password(password)
                save_json("users.json", self.users)
                self.reload_data()
            self.current_user = username
            self.reload_data()
            return True, "Logged in."
        return False, "Invalid username or password."

    def logout(self):
        self.current_user = None
        self.set_status("Logged out.")

    def get_cart(self):
        if not self.current_user:
            return []
        return self.users.get(self.current_user, {}).get("cart", [])

    def set_cart(self, cart):
        self.users[self.current_user]["cart"] = cart
        save_json("users.json", self.users)
        self.reload_data()

    def add_to_cart(self, product_id, qty):
        if product_id not in self.products:
            return False, "Invalid product."
        try:
            qty = int(qty)
        except ValueError:
            return False, "Quantity must be a number."
        if qty <= 0:
            return False, "Quantity must be greater than 0."
        stock = int(self.products[product_id]["stock"])
        if qty > stock:
            return False, f"Not enough stock. Available: {stock}"

        cart = self.get_cart()
        for item in cart:
            if item["product"] == product_id:
                new_qty = item["quantity"] + qty
                if new_qty > stock:
                    return False, f"Not enough stock for that total quantity. Available: {stock}"
                item["quantity"] = new_qty
                self.set_cart(cart)
                return True, "Cart updated."

        cart.append({
            "product": product_id,
            "name": self.products[product_id]["name"],
            "quantity": qty,
            "price": self.products[product_id]["price"],
        })
        self.set_cart(cart)
        return True, "Added to cart."

    def remove_from_cart(self, product_id, amt):
        cart = self.get_cart()
        idx = next((i for i, it in enumerate(cart) if it["product"] == product_id), None)
        if idx is None:
            return False, "Item not in cart."

        if isinstance(amt, str) and amt.strip().lower() == "all":
            cart.pop(idx)
            self.set_cart(cart)
            return True, "Item removed."

        try:
            amt = int(amt)
        except ValueError:
            return False, "Remove amount must be a number or 'all'."
        if amt <= 0:
            return False, "Remove amount must be greater than 0."

        if amt >= cart[idx]["quantity"]:
            cart.pop(idx)
        else:
            cart[idx]["quantity"] -= amt

        self.set_cart(cart)
        return True, "Cart updated."

    def next_order_id(self):
        orders = load_json("orders.json", [])
        max_n = 0
        for o in orders:
            oid = str(o.get("order_id", ""))
            if oid.startswith("O") and oid[1:].isdigit():
                max_n = max(max_n, int(oid[1:]))
        return f"O{max_n + 1:04d}"

    def checkout(self):
        cart = self.get_cart()
        if not cart:
            return False, "Cart is empty."

        for item in cart:
            pid = item["product"]
            if pid not in self.products:
                return False, f"Product {pid} no longer exists."
            if item["quantity"] > int(self.products[pid]["stock"]):
                return False, f"Not enough stock for {self.products[pid]['name']}."

        for item in cart:
            pid = item["product"]
            self.products[pid]["stock"] -= item["quantity"]

        order_id = self.next_order_id()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        items_out = []
        total = 0
        for item in cart:
            total += item["price"] * item["quantity"]
            items_out.append({
                "product_id": item["product"],
                "name": item["name"],
                "qty": item["quantity"],
                "unit_price": item["price"],
            })

        order = {
            "order_id": order_id,
            "username": self.current_user,
            "items": items_out,
            "total": total,
            "timestamp": timestamp,
        }

        orders = load_json("orders.json", [])
        orders.append(order)

        save_json("products.json", self.products)
        save_json("orders.json", orders)

        self.users[self.current_user]["cart"] = []
        save_json("users.json", self.users)
        self.reload_data()

        receipt_lines = [
            "Receipt",
            "-" * 36,
            f"Order ID: {order_id}",
            f"Username: {self.current_user}",
            f"Time: {timestamp}",
            "-" * 36,
        ]
        for it in items_out:
            receipt_lines.append(f"{it['name']}  x{it['qty']}  @ ${it['unit_price']}")
        receipt_lines += ["-" * 36, f"Total: ${total}", "-" * 36]

        os.makedirs("receipts", exist_ok=True)
        receipt_path = os.path.join("receipts", f"{order_id}.txt")
        with open(receipt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(receipt_lines))

        return True, "\n".join(receipt_lines) + f"\n\nSaved: {receipt_path}"

    def user_orders(self):
        orders = load_json("orders.json", [])
        return [o for o in orders if o.get("username") == self.current_user]


class WelcomeFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        outer = ttk.Frame(self, padding=28)
        outer.pack(fill="both", expand=True)

        card = ttk.Frame(outer, padding=22)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(card, text="Mini-Amazon", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        ttk.Label(card, text="Login or create an account to continue.", style="SubHeader.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 18))

        ttk.Label(card, text="Username").grid(row=2, column=0, sticky="w")
        self.username = ttk.Entry(card, width=34)
        self.username.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 10))

        ttk.Label(card, text="Password").grid(row=4, column=0, sticky="w")
        self.password = ttk.Entry(card, width=34, show="•")
        self.password.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 14))

        ttk.Button(card, text="Login", style="Accent.TButton", command=self.do_login).grid(row=6, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(card, text="Register", command=self.do_register).grid(row=6, column=1, sticky="ew")

        ttk.Separator(card).grid(row=7, column=0, columnspan=2, sticky="ew", pady=16)
        ttk.Button(card, text="Exit", command=self.app.destroy).grid(row=8, column=0, columnspan=2, sticky="ew")

        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

    def do_register(self):
        ok, msg = self.app.register(self.username.get(), self.password.get())
        if ok:
            messagebox.showinfo("Register", msg)
        else:
            messagebox.showerror("Register", msg)

    def do_login(self):
        ok, msg = self.app.login(self.username.get(), self.password.get())
        if ok:
            self.app.show("AppFrame")
            self.app.set_status(f"Logged in as {self.app.current_user}")
        else:
            messagebox.showerror("Login", msg)


class AppFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.status_var = tk.StringVar(value="")

        top = ttk.Frame(self, padding=(14, 12))
        top.pack(fill="x")

        ttk.Label(top, text="Store", style="Header.TLabel").pack(side="left")
        self.user_lbl = ttk.Label(top, text="", style="SubHeader.TLabel")
        self.user_lbl.pack(side="left", padx=(12, 0))

        ttk.Button(top, text="Logout", command=self.do_logout).pack(side="right")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.store_tab = StoreTab(self.notebook, app)
        self.cart_tab = CartTab(self.notebook, app)
        self.orders_tab = OrdersTab(self.notebook, app)

        self.notebook.add(self.store_tab, text="Store")
        self.notebook.add(self.cart_tab, text="Cart")
        self.notebook.add(self.orders_tab, text="Orders")

        status = ttk.Frame(self, padding=(14, 8))
        status.pack(fill="x")
        ttk.Label(status, textvariable=self.status_var, style="Status.TLabel").pack(side="left")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_show(self):
        self.user_lbl.config(text=f"Signed in: {self.app.current_user}")
        self.store_tab.refresh()
        self.cart_tab.refresh()
        self.orders_tab.refresh()

    def on_tab_change(self, _event=None):
        idx = self.notebook.index(self.notebook.select())
        if idx == 0:
            self.store_tab.refresh()
            self.app.set_status("Browsing products.")
        elif idx == 1:
            self.cart_tab.refresh()
            self.app.set_status("Viewing cart.")
        else:
            self.orders_tab.refresh()
            self.app.set_status("Viewing order history.")

    def do_logout(self):
        self.app.logout()
        self.app.show("WelcomeFrame")


class StoreTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=14)
        self.app = app

        row = ttk.Frame(self)
        row.pack(fill="x", pady=(0, 10))

        ttk.Label(row, text="Search").pack(side="left")
        self.search = ttk.Entry(row, width=36)
        self.search.pack(side="left", padx=8)
        ttk.Button(row, text="Go", command=self.do_search).pack(side="left")
        ttk.Button(row, text="Clear", command=self.refresh).pack(side="left", padx=(8, 0))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(body, columns=("id", "name", "price", "stock"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("price", text="Price")
        self.tree.heading("stock", text="Stock")
        self.tree.column("id", width=80, anchor="w")
        self.tree.column("name", width=360, anchor="w")
        self.tree.column("price", width=120, anchor="e")
        self.tree.column("stock", width=120, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        self.details_var = tk.StringVar(value="Select a product to see details.")
        ttk.Label(self, textvariable=self.details_var, style="SubHeader.TLabel").pack(anchor="w", pady=(10, 0))

        addbox = ttk.Frame(self)
        addbox.pack(fill="x", pady=(10, 0))

        ttk.Label(addbox, text="Quantity").pack(side="left")
        self.qty = ttk.Entry(addbox, width=10)
        self.qty.pack(side="left", padx=8)
        self.qty.insert(0, "1")
        ttk.Button(addbox, text="Add to Cart", style="Accent.TButton", command=self.add_selected).pack(side="left")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        self.app.reload_data()
        self.tree.delete(*self.tree.get_children())
        for pid, p in self.app.products.items():
            self.tree.insert("", "end", values=(pid, p["name"], f"${p['price']}", p["stock"]))
        self.details_var.set("Select a product to see details.")
        self.qty.delete(0, tk.END)
        self.qty.insert(0, "1")

    def do_search(self):
        key = self.search.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        for pid, p in self.app.products.items():
            if key in p["name"].lower():
                self.tree.insert("", "end", values=(pid, p["name"], f"${p['price']}", p["stock"]))
        if not self.tree.get_children():
            messagebox.showinfo("Search", "No matching products found.")
            self.details_var.set("No results.")
        else:
            self.details_var.set("Select a product to see details.")

    def selected_pid(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        return vals[0]

    def on_select(self, _event=None):
        pid = self.selected_pid()
        if not pid:
            return
        p = self.app.products[pid]
        self.details_var.set(f"ID: {pid}  •  {p['name']}  •  ${p['price']}  •  Stock: {p['stock']}")

    def add_selected(self):
        pid = self.selected_pid()
        if not pid:
            messagebox.showwarning("Add to cart", "Select a product first.")
            return
        ok, msg = self.app.add_to_cart(pid, self.qty.get())
        if ok:
            self.app.set_status(msg)
            messagebox.showinfo("Cart", msg)
        else:
            messagebox.showerror("Cart", msg)

    def on_show(self):
        self.refresh()


class CartTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=14)
        self.app = app

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(body, columns=("id", "name", "qty", "unit", "sub"), show="headings")
        for c, t, w, a in [
            ("id", "ID", 80, "w"),
            ("name", "Name", 320, "w"),
            ("qty", "Qty", 80, "e"),
            ("unit", "Unit", 120, "e"),
            ("sub", "Subtotal", 140, "e"),
        ]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor=a)
        self.tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(10, 0))

        ttk.Label(controls, text="Remove qty (number or 'all')").pack(side="left")
        self.rm_amt = ttk.Entry(controls, width=12)
        self.rm_amt.pack(side="left", padx=8)
        self.rm_amt.insert(0, "1")
        ttk.Button(controls, text="Remove/Reduce", command=self.remove_selected).pack(side="left")
        ttk.Button(controls, text="Checkout", style="Accent.TButton", command=self.do_checkout).pack(side="right")

        self.total_var = tk.StringVar(value="Total: $0")
        ttk.Label(self, textvariable=self.total_var, style="Title.TLabel").pack(anchor="e", pady=(10, 0))

    def refresh(self):
        self.app.reload_data()
        self.tree.delete(*self.tree.get_children())
        total = 0
        for it in self.app.get_cart():
            sub = it["price"] * it["quantity"]
            total += sub
            self.tree.insert("", "end", values=(it["product"], it["name"], it["quantity"], f"${it['price']}", f"${sub}"))
        self.total_var.set(f"Total: ${total}")

    def selected_pid(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        return vals[0]

    def remove_selected(self):
        pid = self.selected_pid()
        if not pid:
            messagebox.showwarning("Cart", "Select an item first.")
            return
        ok, msg = self.app.remove_from_cart(pid, self.rm_amt.get().strip() or "all")
        if ok:
            self.refresh()
            self.app.set_status(msg)
        else:
            messagebox.showerror("Cart", msg)

    def do_checkout(self):
        ok, receipt_or_msg = self.app.checkout()
        if ok:
            messagebox.showinfo("Checkout", receipt_or_msg)
            self.refresh()
            self.app.set_status("Checkout complete.")
        else:
            messagebox.showerror("Checkout", receipt_or_msg)

    def on_show(self):
        self.refresh()


class OrdersTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=14)
        self.app = app

        self.tree = ttk.Treeview(self, columns=("oid", "time", "total"), show="headings")
        self.tree.heading("oid", text="Order ID")
        self.tree.heading("time", text="Timestamp")
        self.tree.heading("total", text="Total")
        self.tree.column("oid", width=120, anchor="w")
        self.tree.column("time", width=260, anchor="w")
        self.tree.column("total", width=120, anchor="e")
        self.tree.pack(fill="both", expand=True, side="left")

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        self.details = tk.Text(self, height=10, wrap="word")
        self.details.pack(fill="x", pady=(10, 0))
        self.details.configure(state="disabled")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        self.app.reload_data()
        self.tree.delete(*self.tree.get_children())
        self._orders = self.app.user_orders()
        for o in reversed(self._orders):
            self.tree.insert("", "end", values=(o["order_id"], o["timestamp"], f"${o['total']}"))
        self.set_details("Select an order to view items.")

    def set_details(self, text):
        self.details.configure(state="normal")
        self.details.delete("1.0", tk.END)
        self.details.insert(tk.END, text)
        self.details.configure(state="disabled")

    def on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        oid = self.tree.item(sel[0], "values")[0]
        order = next((o for o in self._orders if o["order_id"] == oid), None)
        if not order:
            return
        lines = [
            f"Order ID: {order['order_id']}",
            f"Time: {order['timestamp']}",
            f"Total: ${order['total']}",
            "",
            "Items:",
        ]
        for it in order.get("items", []):
            qty = it.get("qty", it.get("quantity"))
            lines.append(f"- {it.get('name')} x{qty} @ ${it.get('unit_price')}")
        self.set_details("\n".join(lines))

    def on_show(self):
        self.refresh()


if __name__ == "__main__":
    app = MiniAmazonGUI()
    app.mainloop()
