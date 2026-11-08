
from pathlib import Path

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from auth import (
    register_user,
    authenticate_user,
    create_access_token,
    get_current_user
)

from customer_service import (
    save_customer,
    get_customers,
    get_customer_by_code,
    save_prediction,
    get_prediction_history
)


# --------------------------------------------------
# LOAD EXISTING ML MODEL
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "churn_pipeline.joblib"

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

artifact = joblib.load(MODEL_PATH)

model = artifact["model"]
MODEL_NAME = artifact["model_name"]
FEATURE_COLUMNS = artifact["feature_columns"]


# --------------------------------------------------
# INITIALIZE FASTAPI
# --------------------------------------------------

app = FastAPI(
    title="ChurnGuard AI",
    description="Customer Churn Prediction and Management API",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"]
)


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class Customer(BaseModel):
    customer_code: str | None = None

    gender: str
    SeniorCitizen: int = Field(ge=0, le=1)
    Partner: str
    Dependents: str
    tenure: int = Field(ge=0)
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float = Field(ge=0)
    TotalCharges: float = Field(ge=0)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


# --------------------------------------------------
# HOME AND HEALTH
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to ChurnGuard AI!",
        "status": "running",
        "model": MODEL_NAME
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": True,
        "model_name": MODEL_NAME
    }


# --------------------------------------------------
# REGISTRATION
# --------------------------------------------------

@app.post("/register", status_code=201)
def register(request: RegisterRequest):

    if "@" not in request.email or "." not in request.email.split("@")[-1]:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid email address."
        )

    try:
        user = register_user(
            request.username,
            request.email,
            request.password
        )

        return {
            "message": "Account created successfully!",
            "user": user
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.post("/login")
def login(request: LoginRequest):

    user = authenticate_user(request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password."
        )

    return {
        "message": "Login successful!",
        "access_token": create_access_token(user["id"]),
        "token_type": "bearer",
        "user": user
    }


# --------------------------------------------------
# CURRENT USER
# --------------------------------------------------

@app.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):

    return {
        "message": "Authenticated successfully!",
        "user": current_user
    }


# --------------------------------------------------
# PREDICT AND SAVE CUSTOMER
# --------------------------------------------------

@app.post("/predict")
def predict(
    customer: Customer,
    current_user: dict = Depends(get_current_user)
):

    try:
        customer_data = customer.model_dump(exclude={"customer_code"})

        input_df = pd.DataFrame(
            [customer_data],
            columns=FEATURE_COLUMNS
        )

        prediction_value = int(model.predict(input_df)[0])

        probability = float(
            model.predict_proba(input_df)[0, 1]
        )

        prediction_label = (
            "Yes" if prediction_value == 1 else "No"
        )

        risk = (
            "High" if probability >= 0.60
            else "Medium" if probability >= 0.30
            else "Low"
        )

        # Save new customer or update an existing customer
        customer_record = save_customer(
            current_user["id"],
            {
                **customer_data,
                "customer_code": customer.customer_code
            }
        )

        # Save prediction linked to customer and user
        prediction_id = save_prediction(
            user_id=current_user["id"],
            customer_id=customer_record["id"],
            prediction=prediction_label,
            churn_probability=round(probability, 4),
            risk_level=risk,
            model_name=MODEL_NAME
        )

        return {
            "prediction_id": prediction_id,
            "customer_id": customer_record["id"],
            "customer_code": customer_record["customer_code"],
            "prediction": prediction_label,
            "churn_probability": round(probability, 4),
            "risk_level": risk,
            "model": MODEL_NAME,
            "message": "Prediction and customer saved successfully."
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(error)}"
        )


# --------------------------------------------------
# LIST CUSTOMERS
# --------------------------------------------------

@app.get("/customers")
def list_customers(
    current_user: dict = Depends(get_current_user)
):

    return {
        "customers": get_customers(current_user["id"])
    }


# --------------------------------------------------
# GET CUSTOMER BY CUSTOMER ID
# --------------------------------------------------

@app.get("/customers/{customer_code}")
def customer_details(
    customer_code: str,
    current_user: dict = Depends(get_current_user)
):

    customer = get_customer_by_code(
        current_user["id"],
        customer_code
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found."
        )

    return {"customer": customer}


# --------------------------------------------------
# CUSTOMER-SPECIFIC PREDICTION HISTORY
# --------------------------------------------------

@app.get("/customers/{customer_code}/history")
def customer_history(
    customer_code: str,
    current_user: dict = Depends(get_current_user)
):

    customer = get_customer_by_code(
        current_user["id"],
        customer_code
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found."
        )

    history = get_prediction_history(
        current_user["id"],
        customer["id"]
    )

    return {
        "customer_code": customer_code,
        "history": history
    }


# --------------------------------------------------
# ALL PREDICTION HISTORY
# --------------------------------------------------

@app.get("/history")
def all_prediction_history(
    current_user: dict = Depends(get_current_user)
):

    history = get_prediction_history(current_user["id"])

    return {"history": history}
