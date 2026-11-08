import os
import json
import time
import hmac
import hashlib
import secrets
import base64

from pathlib import Path
from dotenv import load_dotenv

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import get_connection


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing. Configure it in the project .env file.")

TOKEN_EXPIRY_SECONDS = 60 * 60 * 24  # 24 hours

security = HTTPBearer(auto_error=False)


# --------------------------------------------------
# PASSWORD SECURITY
# --------------------------------------------------

def hash_password(password: str, salt: bytes = None):
    """Hash a password using PBKDF2-HMAC-SHA256."""

    if salt is None:
        salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    return (
        base64.b64encode(password_hash).decode("utf-8"),
        base64.b64encode(salt).decode("utf-8")
    )


def verify_password(password: str, stored_hash: str, stored_salt: str):
    """Verify a password against its stored hash."""

    salt = base64.b64decode(stored_salt)

    calculated_hash, _ = hash_password(password, salt)

    return hmac.compare_digest(calculated_hash, stored_hash)


# --------------------------------------------------
# USER REGISTRATION
# --------------------------------------------------

def register_user(username: str, email: str, password: str):
    """Register a new user."""

    username = username.strip()
    email = email.strip().lower()

    if not username or not email or not password:
        raise ValueError("All fields are required.")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    password_hash, salt = hash_password(password)

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, salt)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, salt)
        )

        connection.commit()

        return {
            "id": cursor.lastrowid,
            "username": username,
            "email": email
        }

    except Exception as error:
        connection.rollback()

        if "UNIQUE constraint failed" in str(error):
            raise ValueError("This email is already registered.")

        raise

    finally:
        connection.close()


# --------------------------------------------------
# USER LOGIN
# --------------------------------------------------

def authenticate_user(email: str, password: str):
    """Verify login credentials."""

    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT id, username, email, password_hash, salt
            FROM users
            WHERE email = ?
            """,
            (email.strip().lower(),)
        ).fetchone()

        if not user:
            return None

        if not verify_password(
            password,
            user["password_hash"],
            user["salt"]
        ):
            return None

        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }

    finally:
        connection.close()


# --------------------------------------------------
# TOKEN HELPERS
# --------------------------------------------------

def encode_base64(data: bytes):
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def decode_base64(data: str):
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(user_id: int):
    """Create a signed authentication token."""

    payload = {
        "user_id": user_id,
        "expires_at": int(time.time()) + TOKEN_EXPIRY_SECONDS,
        "nonce": secrets.token_hex(8)
    }

    payload_bytes = json.dumps(
        payload,
        separators=(",", ":")
    ).encode("utf-8")

    encoded_payload = encode_base64(payload_bytes)

    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256
    ).digest()

    return encoded_payload + "." + encode_base64(signature)


def verify_access_token(token: str):
    """Validate token signature and expiration."""

    try:
        encoded_payload, encoded_signature = token.split(".")

        expected_signature = hmac.new(
            SECRET_KEY.encode("utf-8"),
            encoded_payload.encode("utf-8"),
            hashlib.sha256
        ).digest()

        actual_signature = decode_base64(encoded_signature)

        if not hmac.compare_digest(
            expected_signature,
            actual_signature
        ):
            return None

        payload = json.loads(decode_base64(encoded_payload))

        if payload["expires_at"] < int(time.time()):
            return None

        return payload["user_id"]

    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


# --------------------------------------------------
# FASTAPI AUTHENTICATION DEPENDENCY
# --------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Protect API routes and identify the logged-in user."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in to continue."
        )

    user_id = verify_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired login session."
        )

    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT id, username, email
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found."
            )

        return dict(user)

    finally:
        connection.close()