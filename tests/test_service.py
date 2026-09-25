from mini_amazon.service import (
    register_account,
    authenticate_user,
    get_user_cart,
    add_item_to_cart,
    remove_item_from_cart,
    checkout_account,
    get_order_history,
    format_receipt,
)


def test_register_account_creates_user(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    users = {}

    success, message = register_account(
        users,
        "trevor",
        "secure123",
    )

    assert success is True
    assert message == "Account created."
    assert "trevor" in users
    assert users["trevor"]["cart"] == []
    assert users["trevor"]["password"] != "secure123"


def test_register_account_rejects_duplicate_username(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    users = {}

    register_account(users, "trevor", "secure123")

    success, message = register_account(
        users,
        "trevor",
        "another123",
    )

    assert success is False
    assert message == "Username already exists."


def test_register_account_rejects_short_password(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    users = {}

    success, message = register_account(
        users,
        "trevor",
        "123",
    )

    assert success is False
    assert message == "Password must be at least 6 characters long."
    assert "trevor" not in users


def test_authenticate_user_accepts_correct_password(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    users = {}

    register_account(users, "trevor", "secure123")

    success, message = authenticate_user(
        users,
        "trevor",
        "secure123",
    )

    assert success is True
    assert message == "Logged in."


def test_authenticate_user_rejects_wrong_password(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    users = {}

    register_account(users, "trevor", "secure123")

    success, message = authenticate_user(
        users,
        "trevor",
        "wrong-password",
    )

    assert success is False
    assert message == "Invalid username or password."


def test_add_item_to_cart_creates_cart_item(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    users = {
        "trevor": {
            "password": "unused",
            "cart": [],
        }
    }

    products = {
        "1": {
            "name": "Laptop",
            "price": 999,
            "stock": 5,
        }
    }

    success, message = add_item_to_cart(
        users,
        products,
        "trevor",
        "1",
        2,
    )

    assert success is True
    assert message == "Added to cart."
    assert users["trevor"]["cart"] == [
        {
            "product": "1",
            "name": "Laptop",
            "quantity": 2,
            "price": 999,
        }
    ]


def test_add_item_to_cart_merges_existing_quantity(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    users = {
        "trevor": {
            "password": "unused",
            "cart": [],
        }
    }

    products = {
        "1": {
            "name": "Laptop",
            "price": 999,
            "stock": 5,
        }
    }

    add_item_to_cart(users, products, "trevor", "1", 1)

    success, message = add_item_to_cart(
        users,
        products,
        "trevor",
        "1",
        2,
    )

    assert success is True
    assert message == "Cart updated."
    assert len(users["trevor"]["cart"]) == 1
    assert users["trevor"]["cart"][0]["quantity"] == 3


def test_add_item_to_cart_rejects_quantity_above_stock(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    users = {
        "trevor": {
            "password": "unused",
            "cart": [],
        }
    }

    products = {
        "1": {
            "name": "Laptop",
            "price": 999,
            "stock": 5,
        }
    }

    success, message = add_item_to_cart(
        users,
        products,
        "trevor",
        "1",
        6,
    )

    assert success is False
    assert message == "Not enough stock. Available: 5"
    assert users["trevor"]["cart"] == []


def test_add_item_to_cart_rejects_invalid_quantity(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    users = {
        "trevor": {
            "password": "unused",
            "cart": [],
        }
    }

    products = {
        "1": {
            "name": "Laptop",
            "price": 999,
            "stock": 5,
        }
    }

    success, message = add_item_to_cart(
        users,
        products,
        "trevor",
        "1",
        0,
    )

    assert success is False
    assert message == "Quantity must be greater than 0."
    assert users["trevor"]["cart"] == []


def test_remove_item_from_cart_reduces_quantity(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    users = {
        "trevor": {
            "password": "unused",
            "cart": [
                {
                    "product": "1",
                    "name": "Laptop",
                    "quantity": 3,
                    "price": 999,
                }
            ],
        }
    }

    success, message = remove_item_from_cart(
        users,
        "trevor",
        "1",
        1,
    )

    assert success is True
    assert message == "Cart updated."
    assert users["trevor"]["cart"][0]["quantity"] == 2


def test_remove_item_from_cart_removes_entire_item(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    users = {
        "trevor": {
            "password": "unused",
            "cart": [
                {
                    "product": "1",
                    "name": "Laptop",
                    "quantity": 3,
                    "price": 999,
                }
            ],
        }
    }

    success, message = remove_item_from_cart(
        users,
        "trevor",
        "1",
        "all",
    )

    assert success is True
    assert message == "Item removed."
    assert users["trevor"]["cart"] == []


def test_get_user_cart_returns_saved_cart():
    users = {
        "trevor": {
            "password": "unused",
            "cart": [
                {
                    "product": "1",
                    "name": "Laptop",
                    "quantity": 2,
                    "price": 999,
                }
            ],
        }
    }

    cart = get_user_cart(users, "trevor")

    assert len(cart) == 1
    assert cart[0]["product"] == "1"
    assert cart[0]["quantity"] == 2


def test_checkout_creates_order_and_updates_state(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    users = {
        "trevor": {
            "password": "unused",
            "cart": [
                {
                    "product": "1",
                    "name": "Laptop",
                    "quantity": 2,
                    "price": 999,
                }
            ],
        }
    }

    products = {
        "1": {
            "name": "Laptop",
            "price": 999,
            "stock": 5,
        }
    }

    success, message, order = checkout_account(
        users,
        products,
        "trevor",
    )

    assert success is True
    assert message == "Purchase complete."
    assert order["order_id"] == "O0001"
    assert order["username"] == "trevor"
    assert order["total"] == 1998

    assert products["1"]["stock"] == 3
    assert users["trevor"]["cart"] == []

    orders = get_order_history("trevor")

    assert len(orders) == 1
    assert orders[0]["order_id"] == "O0001"
    assert orders[0]["items"][0]["qty"] == 2


def test_checkout_rejects_empty_cart(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    users = {
        "trevor": {
            "password": "unused",
            "cart": [],
        }
    }

    products = {
        "1": {
            "name": "Laptop",
            "price": 999,
            "stock": 5,
        }
    }

    success, message, order = checkout_account(
        users,
        products,
        "trevor",
    )

    assert success is False
    assert message == "Cart is empty."
    assert order is None
    assert products["1"]["stock"] == 5


def test_failed_checkout_does_not_modify_stock_or_cart(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    users = {
        "trevor": {
            "password": "unused",
            "cart": [
                {
                    "product": "1",
                    "name": "Laptop",
                    "quantity": 6,
                    "price": 999,
                }
            ],
        }
    }

    products = {
        "1": {
            "name": "Laptop",
            "price": 999,
            "stock": 5,
        }
    }

    success, message, order = checkout_account(
        users,
        products,
        "trevor",
    )

    assert success is False
    assert message == "Not enough stock for Laptop. Available: 5"
    assert order is None

    assert products["1"]["stock"] == 5
    assert users["trevor"]["cart"][0]["quantity"] == 6


def test_checkout_generates_sequential_order_ids(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    users = {
        "trevor": {
            "password": "unused",
            "cart": [
                {
                    "product": "1",
                    "name": "Laptop",
                    "quantity": 1,
                    "price": 999,
                }
            ],
        }
    }

    products = {
        "1": {
            "name": "Laptop",
            "price": 999,
            "stock": 5,
        }
    }

    _, _, first_order = checkout_account(
        users,
        products,
        "trevor",
    )

    users["trevor"]["cart"] = [
        {
            "product": "1",
            "name": "Laptop",
            "quantity": 1,
            "price": 999,
        }
    ]

    _, _, second_order = checkout_account(
        users,
        products,
        "trevor",
    )

    assert first_order["order_id"] == "O0001"
    assert second_order["order_id"] == "O0002"
    assert products["1"]["stock"] == 3


def test_order_history_returns_only_users_orders(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    users = {
        "trevor": {
            "password": "unused",
            "cart": [
                {
                    "product": "1",
                    "name": "Laptop",
                    "quantity": 1,
                    "price": 999,
                }
            ],
        },
        "alex": {
            "password": "unused",
            "cart": [
                {
                    "product": "1",
                    "name": "Laptop",
                    "quantity": 1,
                    "price": 999,
                }
            ],
        },
    }

    products = {
        "1": {
            "name": "Laptop",
            "price": 999,
            "stock": 5,
        }
    }

    checkout_account(users, products, "trevor")
    checkout_account(users, products, "alex")

    trevor_orders = get_order_history("trevor")
    alex_orders = get_order_history("alex")

    assert len(trevor_orders) == 1
    assert len(alex_orders) == 1

    assert trevor_orders[0]["username"] == "trevor"
    assert alex_orders[0]["username"] == "alex"


def test_format_receipt_contains_order_details():
    order = {
        "order_id": "O0001",
        "username": "trevor",
        "timestamp": "2026-09-25 12:00:00",
        "items": [
            {
                "product_id": "1",
                "name": "Laptop",
                "qty": 2,
                "unit_price": 999,
            }
        ],
        "total": 1998,
    }

    receipt = format_receipt(order)

    assert "O0001" in receipt
    assert "trevor" in receipt
    assert "Laptop x2 @ $999" in receipt
    assert "Total: $1998" in receipt
