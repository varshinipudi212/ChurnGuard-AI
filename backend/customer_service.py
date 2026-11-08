
import secrets
import sqlite3

try:
    from .database import get_connection
except ImportError:
    from database import get_connection


def generate_customer_code():
    """Generate a unique-looking customer identifier."""
    return f"CG-{secrets.token_hex(4).upper()}"


def save_customer(user_id, customer_data):
    """Save a new customer or update an existing customer."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        customer_code = customer_data.get("customer_code")

        # Update existing customer
        if customer_code:

            existing = cursor.execute(
                """
                SELECT id FROM customers
                WHERE user_id = ? AND customer_code = ?
                """,
                (user_id, customer_code)
            ).fetchone()

            if not existing:
                raise ValueError("Customer ID not found in your account.")

            fields = [
                "gender", "SeniorCitizen", "Partner", "Dependents",
                "tenure", "PhoneService", "MultipleLines",
                "InternetService", "OnlineSecurity", "OnlineBackup",
                "DeviceProtection", "TechSupport", "StreamingTV",
                "StreamingMovies", "Contract", "PaperlessBilling",
                "PaymentMethod", "MonthlyCharges", "TotalCharges"
            ]

            values = [customer_data.get(field) for field in fields]

            assignments = ", ".join(
                f"{field} = ?" for field in fields
            )

            cursor.execute(
                f"""
                UPDATE customers
                SET {assignments}, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND customer_code = ?
                """,
                values + [user_id, customer_code]
            )

            customer_id = existing["id"]

        # Create new customer
        else:

            customer_code = generate_customer_code()

            fields = [
                "gender", "SeniorCitizen", "Partner", "Dependents",
                "tenure", "PhoneService", "MultipleLines",
                "InternetService", "OnlineSecurity", "OnlineBackup",
                "DeviceProtection", "TechSupport", "StreamingTV",
                "StreamingMovies", "Contract", "PaperlessBilling",
                "PaymentMethod", "MonthlyCharges", "TotalCharges"
            ]

            values = [customer_data.get(field) for field in fields]

            columns = ", ".join(
                ["user_id", "customer_code"] + fields
            )

            placeholders = ", ".join(
                ["?"] * (len(fields) + 2)
            )

            cursor.execute(
                f"""
                INSERT INTO customers ({columns})
                VALUES ({placeholders})
                """,
                [user_id, customer_code] + values
            )

            customer_id = cursor.lastrowid

        connection.commit()

        return {
            "id": customer_id,
            "customer_code": customer_code
        }

    except sqlite3.IntegrityError:
        connection.rollback()
        raise ValueError("Could not save customer. Please try again.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_customers(user_id):
    """Retrieve customers belonging to one user."""

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM customers
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_customer_by_code(user_id, customer_code):
    """Find a customer using their unique ID."""

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM customers
            WHERE user_id = ? AND customer_code = ?
            """,
            (user_id, customer_code)
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


def save_prediction(
    user_id,
    customer_id,
    prediction,
    churn_probability,
    risk_level,
    model_name
):
    """Store a prediction linked to its customer and user."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Verify that this customer belongs to the user
        customer = cursor.execute(
            """
            SELECT id FROM customers
            WHERE id = ? AND user_id = ?
            """,
            (customer_id, user_id)
        ).fetchone()

        if not customer:
            raise ValueError("Customer does not belong to this account.")

        cursor.execute(
            """
            INSERT INTO predictions (
                user_id,
                customer_id,
                prediction,
                churn_probability,
                risk_level,
                model_name
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                customer_id,
                prediction,
                churn_probability,
                risk_level,
                model_name
            )
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_prediction_history(user_id, customer_id=None):
    """Retrieve prediction history for a user or a specific customer."""

    connection = get_connection()

    try:
        if customer_id is not None:
            rows = connection.execute(
                """
                SELECT p.*, c.customer_code
                FROM predictions p
                JOIN customers c ON p.customer_id = c.id
                WHERE p.user_id = ?
                AND p.customer_id = ?
                ORDER BY p.created_at DESC
                """,
                (user_id, customer_id)
            ).fetchall()

        else:
            rows = connection.execute(
                """
                SELECT p.*, c.customer_code
                FROM predictions p
                JOIN customers c ON p.customer_id = c.id
                WHERE p.user_id = ?
                ORDER BY p.created_at DESC
                """,
                (user_id,)
            ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()
