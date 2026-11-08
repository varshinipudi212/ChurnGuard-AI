
import streamlit as st
import requests

# Page configuration
st.set_page_config(
    page_title="ChurnGuard AI",
    page_icon="📊",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

# Custom styling
st.markdown("""
<style>
.stApp {
    background-color: #F4F7FC;
}

[data-testid="stSidebar"] {
    background-color: #14243D;
}

[data-testid="stSidebar"] * {
    color: white;
}

.main-title {
    font-size: 38px;
    font-weight: 800;
    color: #14243D;
}

.subtitle {
    color: #64748B;
    font-size: 16px;
}

div.stButton > button {
    background-color: #2563EB;
    color: white;
    border-radius: 9px;
    height: 48px;
    font-weight: bold;
    border: none;
}

div.stButton > button:hover {
    background-color: #1D4ED8;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🛡️ ChurnGuard AI")
    st.caption("Intelligent Customer Retention")

    st.divider()

    page = st.radio(
        "NAVIGATION",
        ["Dashboard", "Churn Prediction", "About Model"]
    )

    st.divider()
    st.caption("Powered by Machine Learning")

# Dashboard
if page == "Dashboard":

    st.markdown(
        '<div class="main-title">Customer Analytics</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Understand customer behavior and predict churn risks.</div>',
        unsafe_allow_html=True
    )

    st.write("")

    col1, col2, col3 = st.columns(3)

    col1.metric("AI Engine", "Online", "Connected")
    col2.metric("Backend", "Active", "FastAPI")
    col3.metric("Prediction", "Ready", "ML Model")

    st.divider()

    st.subheader("Welcome to ChurnGuard AI")

    st.write("""
    ChurnGuard AI helps businesses identify customers who may
    discontinue their services.

    Use the Churn Prediction section to analyze an individual
    customer's likelihood of leaving.
    """)

    if st.button("Start Churn Prediction →"):
        st.session_state["navigation"] = "Churn Prediction"
        st.rerun()

# Prediction page
elif page == "Churn Prediction":

    st.title("🔍 Customer Churn Prediction")

    st.write(
        "Enter customer information to generate an ML prediction."
    )

    with st.form("customer_form"):

        st.subheader("Personal Information")

        c1, c2, c3 = st.columns(3)

        with c1:
            gender = st.selectbox("Gender", ["Female", "Male"])
            senior = st.selectbox("Senior Citizen", [0, 1])

        with c2:
            partner = st.selectbox("Partner", ["Yes", "No"])
            dependents = st.selectbox("Dependents", ["Yes", "No"])

        with c3:
            tenure = st.number_input(
                "Tenure (months)", min_value=0, max_value=100, value=12
            )

        st.divider()
        st.subheader("Service Information")

        c1, c2, c3 = st.columns(3)

        with c1:
            phone = st.selectbox("Phone Service", ["Yes", "No"])
            multiple = st.selectbox(
                "Multiple Lines",
                ["No", "Yes", "No phone service"]
            )
            internet = st.selectbox(
                "Internet Service", ["DSL", "Fiber optic", "No"]
            )

        with c2:
            security = st.selectbox(
                "Online Security",
                ["Yes", "No", "No internet service"]
            )
            backup = st.selectbox(
                "Online Backup",
                ["Yes", "No", "No internet service"]
            )
            device = st.selectbox(
                "Device Protection",
                ["Yes", "No", "No internet service"]
            )

        with c3:
            support = st.selectbox(
                "Tech Support",
                ["Yes", "No", "No internet service"]
            )
            tv = st.selectbox(
                "Streaming TV",
                ["Yes", "No", "No internet service"]
            )
            movies = st.selectbox(
                "Streaming Movies",
                ["Yes", "No", "No internet service"]
            )

        st.divider()
        st.subheader("Billing Information")

        c1, c2, c3 = st.columns(3)

        with c1:
            contract = st.selectbox(
                "Contract",
                ["Month-to-month", "One year", "Two year"]
            )

        with c2:
            paperless = st.selectbox(
                "Paperless Billing", ["Yes", "No"]
            )

        with c3:
            payment = st.selectbox(
                "Payment Method",
                [
                    "Electronic check",
                    "Mailed check",
                    "Bank transfer (automatic)",
                    "Credit card (automatic)"
                ]
            )

        c1, c2 = st.columns(2)

        with c1:
            monthly = st.number_input(
                "Monthly Charges",
                min_value=0.0,
                value=70.0
            )

        with c2:
            total = st.number_input(
                "Total Charges",
                min_value=0.0,
                value=840.0
            )

        submitted = st.form_submit_button(
            "🚀 Predict Customer Churn",
            use_container_width=True
        )

    if submitted:

        customer = {
            "gender": gender,
            "SeniorCitizen": senior,
            "Partner": partner,
            "Dependents": dependents,
            "tenure": tenure,
            "PhoneService": phone,
            "MultipleLines": multiple,
            "InternetService": internet,
            "OnlineSecurity": security,
            "OnlineBackup": backup,
            "DeviceProtection": device,
            "TechSupport": support,
            "StreamingTV": tv,
            "StreamingMovies": movies,
            "Contract": contract,
            "PaperlessBilling": paperless,
            "PaymentMethod": payment,
            "MonthlyCharges": monthly,
            "TotalCharges": total
        }

        try:
            with st.spinner("Analyzing customer data..."):

                response = requests.post(
                    f"{API_URL}/predict",
                    json=customer,
                    timeout=30
                )

                response.raise_for_status()
                result = response.json()

            st.success("Prediction completed successfully!")

            r1, r2, r3 = st.columns(3)

            r1.metric(
                "Churn Prediction",
                "Yes" if result["prediction"] == "Yes" else "No"
            )

            r2.metric(
                "Churn Probability",
                f'{result["churn_probability"] * 100:.2f}%'
            )

            r3.metric(
                "Risk Level",
                result["risk_level"]
            )

            st.progress(
                float(result["churn_probability"])
            )

            st.info(f'Model used: {result["model"]}')

        except requests.exceptions.RequestException as e:
            st.error(f"Could not connect to FastAPI: {e}")

        except Exception as e:
            st.error(f"Prediction error: {e}")

# Model information
elif page == "About Model":

    st.title("🧠 About the ML Model")

    st.write("""
    ChurnGuard AI uses a trained machine learning pipeline
    to predict customer churn.

    The pipeline includes preprocessing and a trained
    classification algorithm.

    Predictions are generated through the FastAPI backend.
    """)

    st.info("The selected model name is returned by the prediction API.")
