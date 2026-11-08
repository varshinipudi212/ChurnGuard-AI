
import requests

API_URL = "http://127.0.0.1:8000"


def handle_response(response):
    """Return API JSON or a readable error."""
    try:
        response.raise_for_status()
        return response.json(), None
    except requests.HTTPError:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text

        return None, f"API error ({response.status_code}): {detail}"
    except ValueError:
        return None, "The backend returned an invalid JSON response."


def check_backend():
    """Check FastAPI health and return (connected, model_name)."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        response.raise_for_status()

        data = response.json()
        return True, data.get("model_name", "Loaded")

    except (requests.RequestException, ValueError):
        return False, "Unavailable"


def register_user(username, email, password):
    """Register a new user."""
    try:
        response = requests.post(
            f"{API_URL}/register",
            json={
                "username": username,
                "email": email,
                "password": password
            },
            timeout=10
        )
        return handle_response(response)

    except requests.RequestException as exc:
        return None, f"Could not reach FastAPI: {exc}"


def login_user(email, password):
    """Authenticate user and return token information."""
    try:
        response = requests.post(
            f"{API_URL}/login",
            json={
                "email": email,
                "password": password
            },
            timeout=10
        )
        return handle_response(response)

    except requests.RequestException as exc:
        return None, f"Could not reach FastAPI: {exc}"


def get_current_user(token):
    """Verify token and retrieve logged-in user details."""
    try:
        response = requests.get(
            f"{API_URL}/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        return handle_response(response)

    except requests.RequestException as exc:
        return None, f"Could not reach FastAPI: {exc}"


def predict_customer(customer, token=None):
    """Send a customer profile to the prediction API."""
    try:
        headers = {}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.post(
            f"{API_URL}/predict",
            json=customer,
            headers=headers,
            timeout=30
        )

        return handle_response(response)

    except requests.RequestException as exc:
        return None, f"Could not reach FastAPI: {exc}"


def get_customers(token):
    response = requests.get(
        f"{API_URL}/customers",
        headers={"Authorization": f"Bearer {token}"}
    )
    return handle_response(response)


def get_prediction_history(token):
    response = requests.get(
        f"{API_URL}/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    return handle_response(response)


def get_customer_by_code(token, customer_code):
    response = requests.get(
        f"{API_URL}/customers/{customer_code}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return handle_response(response)


def get_customer_history(token, customer_code):
    response = requests.get(
        f"{API_URL}/customers/{customer_code}/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    return handle_response(response)
