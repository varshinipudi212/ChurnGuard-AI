import sqlite3
from pathlib import Path

# Database location
BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "churnguard.db"


def get_connection():
    """Create and return a SQLite database connection."""
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    # Enable foreign key constraints
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_db():
    """Create all ChurnGuard AI database tables."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # 1. Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,

                gender TEXT,
                SeniorCitizen INTEGER,
                Partner TEXT,
                Dependents TEXT,
                tenure INTEGER,
                PhoneService TEXT,
                MultipleLines TEXT,
                InternetService TEXT,
                OnlineSecurity TEXT,
                OnlineBackup TEXT,
                DeviceProtection TEXT,
                TechSupport TEXT,
                StreamingTV TEXT,
                StreamingMovies TEXT,
                Contract TEXT,
                PaperlessBilling TEXT,
                PaymentMethod TEXT,
                MonthlyCharges REAL,
                TotalCharges REAL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 3. Predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,

                prediction TEXT NOT NULL,
                churn_probability REAL NOT NULL,
                risk_level TEXT NOT NULL,
                model_name TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id) ON DELETE CASCADE,

                FOREIGN KEY (customer_id)
                    REFERENCES customers(id) ON DELETE CASCADE
            )
        """)

        # Indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_customers_user
            ON customers(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_user
            ON predictions(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_customer
            ON predictions(customer_id)
        """)

        connection.commit()

        print("ChurnGuard AI database initialized successfully!")
        print(f"Database location: {DATABASE_PATH}")

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()

def migrate_customer_schema():
    """Add unique customer IDs to existing customer records."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Check existing customer columns
        cursor.execute("PRAGMA table_info(customers)")
        columns = [
            row["name"] for row in cursor.fetchall()
        ]

        # Add customer_code if it doesn't exist
        if "customer_code" not in columns:
            cursor.execute("""
                ALTER TABLE customers
                ADD COLUMN customer_code TEXT
            """)

        # Add updated_at if it doesn't exist
        if "updated_at" not in columns:
            cursor.execute("""
                ALTER TABLE customers
                ADD COLUMN updated_at TIMESTAMP
            """)

        # Unique customer ID within each user's account
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_unique_customer_code
            ON customers(user_id, customer_code)
        """)

        connection.commit()

        print("Customer database migration completed!")
        print("Unique Customer ID support is ready.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
