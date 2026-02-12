from storage import initialize_data
from shop import (
    register_user,
    login_user,
    browse_products,
    search_products,
    view_cart,
    checkout,
    view_order_history,
)


def main():
    users, products, _orders = initialize_data()
    current_user = None

    while True:
        if current_user and current_user.is_logged_in:
            print(
                "\n1. Browse Products | 2. Search | 3. View Cart | 4. Checkout | "
                "5. Order History | 6. Logout | 7. Exit"
            )
        else:
            print("\n1. Login | 2. Register | 3. Exit")

        choice = input("Choose: ").strip()

        if not (current_user and current_user.is_logged_in):
            if choice == "1":
                users, products, _orders = initialize_data()
                current_user = login_user(users)

            elif choice == "2":
                users, products, _orders = initialize_data()
                register_user(users)
                users, products, _orders = initialize_data()

            elif choice == "3":
                print("Goodbye!")
                break
            else:
                print("Invalid choice")

        else:
            users, products, _orders = initialize_data()
            current_user.cart = users[current_user.username].get("cart", current_user.cart)

            if choice == "1":
                browse_products(users, current_user, products)

            elif choice == "2":
                search_products(products)

            elif choice == "3":
                view_cart(users, current_user)

            elif choice == "4":
                checkout(users, current_user, products)

            elif choice == "5":
                view_order_history(current_user)

            elif choice == "6":
                print("Logged out!")
                current_user = None

            elif choice == "7":
                print("Goodbye!")
                break

            else:
                print("Invalid choice")


if __name__ == "__main__":
    main()
