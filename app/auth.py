import bcrypt
import re
from app.database import create_user, get_user_by_email


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    return True, ""


def signup(email, password):
    email = email.strip().lower()

    if not validate_email(email):
        return None, "Please enter a valid email address."

    valid, msg = validate_password(password)
    if not valid:
        return None, msg

    existing = get_user_by_email(email)
    if existing:
        return None, "An account with this email already exists."

    password_hash = hash_password(password)

    try:
        user = create_user(email, password_hash)
        return user, None
    except Exception:
        return None, "Could not create account. Please try again."


def login(email, password):
    email = email.strip().lower()

    user = get_user_by_email(email)
    if not user:
        return None, "Invalid email or password."

    if not check_password(password, user["password_hash"]):
        return None, "Invalid email or password."

    return user, None
