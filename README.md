## Mini-Amazon / E-Commerce System (Python)

This is a Console based mini amazon system with persistent storage using JSON files. Also includes an additional Tkinter GUI. 

## Requirements 
Python 3.x, No external libraries are required

## How to run
Open console and type "python main.py". To use the GUI type "python gui.py"

## Features Implemented 
- Register + login (username must be unique, password must be at least 6 characters)
- Password hashing (saved as a salted hash, not plain text)
- Browse products + view product details (ID, name, price, stock)
- Search products by name (case-insensitive)
- Cart system (add items, merge quantities, remove/reduce items, view totals)
- Checkout (re-checks stock, deducts stock, clears cart)
- Orders saved to order history
- Receipt export (receipt is also saved as a .txt file)

## How data is stored
- `users.json` stores usernames, hashed passwords, and each user’s cart
- `products.json` stores the product catalog (name, price, stock)
- `orders.json` stores past orders (order ID, user, items, total, timestamp)
- `receipts/` folder stores exported receipt text files (example: `O0001.txt`)

## Limitaitons 
- Passwords are hashed using SHA-256 for this project (not bcrypt)
- No admin mode to add/update products
- Products are auto-generated with defaults if `products.json` is missing/empty
