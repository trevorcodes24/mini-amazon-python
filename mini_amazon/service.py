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
