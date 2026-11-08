
import streamlit as st

from api import (
    check_backend,
    predict_customer,
    register_user,
    login_user,
    get_current_user,
    get_customers,
    get_prediction_history,
    get_customer_by_code,
    get_customer_history
)

from components import (
    inject_css,
    show_hero,
    metric_card,
    create_gauge,
    show_retention_advice
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="ChurnGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


# --------------------------------------------------
# SESSION INITIALIZATION
# --------------------------------------------------

defaults = {
    "token": None,
    "user": None,
    "history": [],
    "page": "Overview",
    "latest_result": None,
    "auth_page": "Login"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def load_saved_data():
    """Load the logged-in user's customers and prediction history from FastAPI."""
    token = st.session_state.token
    customers_data, customers_error = get_customers(token)
    history_data, history_error = get_prediction_history(token)

    customers = []
    history = []

    if not customers_error and isinstance(customers_data, dict):
        customers = customers_data.get("customers", []) or []

    if not history_error and isinstance(history_data, dict):
        history = history_data.get("history", []) or []

    return customers, history, customers_error or history_error


def display_saved_history(history):
    """Render prediction records returned by the persistent history endpoint."""
    if not history:
        st.info("No saved predictions yet. Visit Predict Churn to analyze a customer.")
        return

    st.metric("Total saved predictions", len(history))

    for number, item in enumerate(reversed(history), start=1):
        prediction = item.get("prediction", "Unknown")
        probability = float(item.get("churn_probability", item.get("probability", 0)) or 0)
        # The API stores probabilities as fractions (for example, 0.56).
        created_at = item.get("created_at", item.get("time", "—"))
        customer_code = item.get("customer_code", "—")
        risk = item.get("risk_level", item.get("risk", "—"))
        model = item.get("model_name", item.get("model", "ML Model"))

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"**Prediction {len(history) - number + 1}**")
            c2.write(f"Customer: {customer_code}")
            c3.write("Churn" if prediction == "Yes" else "No churn")
            c4.write(f"{probability * 100:.2f}% · {risk} risk")
            st.caption(f"Created: {created_at} · Model: {model}")


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

def show_authentication():

    st.markdown(
        "<h1 style='text-align:center;'>🛡️ ChurnGuard AI</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;'>"
        "INTELLIGENT CUSTOMER RETENTION PLATFORM"
        "</p>",
        unsafe_allow_html=True
    )

    st.divider()

    _, center, _ = st.columns([1, 1.5, 1])

    with center:

        auth_choice = st.radio(
            "Choose an option",
            ["Login", "Register"],
            horizontal=True,
            key="auth_page"
        )

        if auth_choice == "Login":

            st.subheader("Welcome back!")
            st.caption("Sign in to access your churn analytics dashboard.")

            with st.form("login_form"):

                email = st.text_input("Email address")

                password = st.text_input(
                    "Password",
                    type="password"
                )

                submitted = st.form_submit_button(
                    "Sign in",
                    type="primary",
                    width="stretch"
                )

            if submitted:

                if not email.strip() or not password:
                    st.warning("Please enter your email and password.")

                else:
                    with st.spinner("Signing in..."):

                        data, error = login_user(email, password)

                    if error:
                        st.error(error)

                    else:
                        st.session_state.token = data["access_token"]
                        st.session_state.user = data["user"]
                        st.session_state.page = "Overview"
                        st.session_state.history = []
                        st.session_state.latest_result = None

                        st.success("Login successful!")
                        st.rerun()

        else:

            st.subheader("Create your account")
            st.caption("Join ChurnGuard AI to manage customer churn predictions.")

            with st.form("register_form"):

                username = st.text_input("Full name")

                email = st.text_input("Email address")

                password = st.text_input(
                    "Password",
                    type="password"
                )

                confirm_password = st.text_input(
                    "Confirm password",
                    type="password"
                )

                submitted = st.form_submit_button(
                    "Create account",
                    type="primary",
                    width="stretch"
                )

            if submitted:

                if not username.strip() or not email.strip():
                    st.warning("Please complete all fields.")

                elif len(password) < 8:
                    st.warning("Password must contain at least 8 characters.")

                elif password != confirm_password:
                    st.error("Passwords do not match.")

                else:
                    with st.spinner("Creating your account..."):

                        data, error = register_user(
                            username,
                            email,
                            password
                        )

                    if error:
                        st.error(error)

                    else:
                        st.success(
                            "Account created successfully! Please log in."
                            "Please select Login above to sign in."
                        )

                       


# --------------------------------------------------
# VERIFY LOGIN SESSION
# --------------------------------------------------

if st.session_state.token:

    user_data, auth_error = get_current_user(
        st.session_state.token
    )

    if auth_error:
        st.session_state.token = None
        st.session_state.user = None
        st.session_state.page = "Overview"

        st.warning("Your session expired. Please log in again.")
        st.rerun()

    else:
        st.session_state.user = user_data["user"]


# --------------------------------------------------
# SHOW LOGIN IF NOT AUTHENTICATED
# --------------------------------------------------

if not st.session_state.token:

    connected, _ = check_backend()

    if not connected:
        st.error("FastAPI backend is offline. Start the backend first.")

    show_authentication()

    st.stop()


# --------------------------------------------------
# AUTHENTICATED DASHBOARD
# --------------------------------------------------

with st.sidebar:

    st.markdown("# 🛡️ ChurnGuard")
    st.caption("PREDICT • PREVENT • RETAIN")

    st.divider()

    st.write(f"Welcome, **{st.session_state.user['username']}**")

    page = st.radio(
        "NAVIGATION",
        ["Overview", "Predict Churn", "Customer Management", "Prediction History"],
        index=[
            "Overview",
            "Predict Churn",
            "Customer Management",
            "Prediction History"
        ].index(st.session_state.page) if st.session_state.page in [
            "Overview", "Predict Churn", "Customer Management", "Prediction History"
        ] else 0
    )

    st.session_state.page = page

    st.divider()

    connected, model_name = check_backend()

    if connected:
        st.success("Backend connected")
    else:
        st.error("Backend offline")

    st.caption(f"Model: {model_name}")

    st.divider()

    if st.button("Logout", width="stretch"):

        st.session_state.token = None
        st.session_state.user = None
        st.session_state.history = []
        st.session_state.latest_result = None
        st.session_state.page = "Overview"

        st.rerun()


def navigate(target):
    st.session_state.page = target
    st.rerun()


# --------------------------------------------------
# OVERVIEW
# --------------------------------------------------

if page == "Overview":

    show_hero(
        "Customer Churn Intelligence",
        "Understand customer risk, generate predictions, "
        "and make smarter retention decisions."
    )

    customers, saved_history, data_error = load_saved_data()

    total_customers = len(customers)
    total_predictions = len(saved_history)
    churned = sum(item.get("prediction") == "Yes" for item in saved_history)
    high_risk = sum(
        item.get("risk_level", item.get("risk")) == "High"
        for item in saved_history
    )
    probabilities = [
        float(item.get("churn_probability", item.get("probability", 0)) or 0)
        for item in saved_history
    ]
    avg_probability = (
        sum(probabilities) / len(probabilities) * 100 if probabilities else 0
    )

    cols = st.columns(4)
    metrics = [
        ("SAVED CUSTOMERS", total_customers, "Customer profiles in your account"),
        ("TOTAL PREDICTIONS", total_predictions, "Saved across all sessions"),
        ("PREDICTED CHURN", churned, "Customers predicted to leave"),
        ("AVERAGE CHURN PROBABILITY", f"{avg_probability:.1f}%", "All saved predictions"),
    ]
    for col, item in zip(cols, metrics):
        with col:
            metric_card(*item)

    if data_error:
        st.warning(f"Some saved dashboard data could not be loaded: {data_error}")

    st.markdown("### Your AI workspace")

    left, right, extra = st.columns(3)

    with left:
        with st.container(border=True):

            st.markdown("#### 🎯 Predict customer churn")

            st.write(
                "Submit a customer profile and receive "
                "a prediction from your trained model."
            )

            if st.button(
                "Start prediction →",
                type="primary",
                width="stretch"
            ):
                navigate("Predict Churn")

    with right:
        with st.container(border=True):

            st.markdown("#### 📊 Prediction history")

            st.write(
                "Review saved predictions and customer churn outcomes."
            )

            if st.button(
                "View history →",
                width="stretch"
            ):
                navigate("Prediction History")

    with extra:
        with st.container(border=True):
            st.markdown("#### 👥 Customer records")
            st.write("Find saved customers and review their prediction history.")
            if st.button("Manage customers →", width="stretch"):
                navigate("Customer Management")


# --------------------------------------------------
# PREDICT CHURN
# --------------------------------------------------

elif page == "Predict Churn":

    show_hero(
        "Customer Risk Assessment",
        "Enter the customer's profile and service details "
        "to estimate churn probability."
    )

    connected, _ = check_backend()

    if not connected:

        st.error(
            "FastAPI is offline. Start the backend in a separate terminal."
        )

    else:

        with st.form("customer_form"):

            existing_customer_code = st.text_input(
                "Existing customer code (optional)",
                placeholder="Leave blank to create a new customer"
            ).strip().upper()
            st.caption("Enter a saved customer code to update that customer's profile. Leave it blank to create a new customer record.")

            st.markdown("#### 👤 Personal information")

            c1, c2, c3 = st.columns(3)

            with c1:
                gender = st.selectbox(
                    "Gender", ["Female", "Male"]
                )

                senior = st.selectbox(
                    "Senior citizen",
                    [0, 1],
                    format_func=lambda x: "Yes" if x else "No"
                )

            with c2:
                partner = st.selectbox(
                    "Partner", ["Yes", "No"]
                )

                dependents = st.selectbox(
                    "Dependents", ["Yes", "No"]
                )

            with c3:
                tenure = st.number_input(
                    "Tenure (months)",
                    min_value=0,
                    max_value=100,
                    value=12
                )

            st.divider()

            st.markdown("#### 📡 Services")

            c1, c2, c3 = st.columns(3)

            with c1:
                phone = st.selectbox(
                    "Phone service", ["Yes", "No"]
                )

                multiple_lines = st.selectbox(
                    "Multiple lines",
                    ["No", "Yes", "No phone service"]
                )

                internet = st.selectbox(
                    "Internet service",
                    ["Fiber optic", "DSL", "No"]
                )

            with c2:
                security = st.selectbox(
                    "Online security",
                    ["No", "Yes", "No internet service"]
                )

                backup = st.selectbox(
                    "Online backup",
                    ["No", "Yes", "No internet service"]
                )

                protection = st.selectbox(
                    "Device protection",
                    ["No", "Yes", "No internet service"]
                )

            with c3:
                support = st.selectbox(
                    "Tech support",
                    ["No", "Yes", "No internet service"]
                )

                tv = st.selectbox(
                    "Streaming TV",
                    ["No", "Yes", "No internet service"]
                )

                movies = st.selectbox(
                    "Streaming movies",
                    ["No", "Yes", "No internet service"]
                )

            st.divider()

            st.markdown("#### 💳 Contract and billing")

            c1, c2, c3 = st.columns(3)

            with c1:
                contract = st.selectbox(
                    "Contract",
                    ["Month-to-month", "One year", "Two year"]
                )

                paperless = st.selectbox(
                    "Paperless billing",
                    ["Yes", "No"]
                )

            with c2:
                payment = st.selectbox(
                    "Payment method",
                    [
                        "Electronic check",
                        "Mailed check",
                        "Bank transfer (automatic)",
                        "Credit card (automatic)"
                    ]
                )

            with c3:
                monthly = st.number_input(
                    "Monthly charges",
                    min_value=0.0,
                    value=70.0,
                    step=1.0
                )

                total_charges = st.number_input(
                    "Total charges",
                    min_value=0.0,
                    value=840.0,
                    step=10.0
                )

            submitted = st.form_submit_button(
                "🚀 Analyze customer churn",
                type="primary",
                width="stretch"
            )

        if submitted:

            customer = {
                "customer_code": existing_customer_code or None,
                "gender": gender,
                "SeniorCitizen": senior,
                "Partner": partner,
                "Dependents": dependents,
                "tenure": tenure,
                "PhoneService": phone,
                "MultipleLines": multiple_lines,
                "InternetService": internet,
                "OnlineSecurity": security,
                "OnlineBackup": backup,
                "DeviceProtection": protection,
                "TechSupport": support,
                "StreamingTV": tv,
                "StreamingMovies": movies,
                "Contract": contract,
                "PaperlessBilling": paperless,
                "PaymentMethod": payment,
                "MonthlyCharges": monthly,
                "TotalCharges": total_charges,
            }

            with st.spinner("Analyzing customer profile..."):

                result, error = predict_customer(
                    customer,
                    st.session_state.token
                )

            if error:

                st.error(error)

            else:

                st.session_state.latest_result = result

                st.session_state.history.append({
                    "time": __import__("datetime").datetime.now().strftime(
                        "%H:%M:%S"
                    ),
                    "prediction": result["prediction"],
                    "probability": float(
                        result["churn_probability"]
                    ),
                    "risk": result["risk_level"],
                    "model": result.get("model", "ML Model"),
                })

    # Display latest result

    result = st.session_state.latest_result

    if result:

        probability = float(result["churn_probability"])
        prediction = result["prediction"]
        risk = result["risk_level"]

        st.divider()

        st.markdown("## Prediction results")

        left, right = st.columns([1, 1])

        with left:

            st.plotly_chart(
                create_gauge(probability),
                width="stretch"
            )

        with right:

            if prediction == "Yes":
                st.error("⚠️ Customer predicted to churn")
            else:
                st.success("✅ Customer predicted to stay")

            st.markdown(f"### Risk level: {risk}")

            st.write(
                f"**Churn probability:** {probability * 100:.2f}%"
            )

            st.caption(
                f"Model: {result.get('model', 'ML Model')}"
            )
            if result.get("customer_code"):
                st.success(f"Customer saved with code: {result['customer_code']}")
                st.caption("Keep this code to find and reuse this customer later.")

            show_retention_advice(risk, prediction)


# --------------------------------------------------
# PREDICTION HISTORY
# --------------------------------------------------

elif page == "Customer Management":

    show_hero(
        "Customer Management",
        "Browse saved customer profiles and inspect their prediction history."
    )

    customers, saved_history, data_error = load_saved_data()
    if data_error:
        st.error(f"Could not load customer data: {data_error}")

    st.metric("Total saved customers", len(customers))

    st.markdown("### Search customer")
    customer_code_input = st.text_input(
        "Enter customer code",
        value=st.session_state.pop("customer_search_code", ""),
        placeholder="For example: CG-54867EDD"
    ).strip().upper()

    if customer_code_input:
        customer_data, customer_error = get_customer_by_code(
            st.session_state.token, customer_code_input
        )
        if customer_error:
            st.warning(customer_error)
        else:
            customer = customer_data.get("customer", customer_data) if isinstance(customer_data, dict) else customer_data
            st.markdown("#### Customer details")
            st.json(customer)

            customer_history_data, history_error = get_customer_history(
                st.session_state.token, customer_code_input
            )
            if history_error:
                st.warning(f"Could not load this customer's history: {history_error}")
            else:
                customer_history = customer_history_data.get("history", []) if isinstance(customer_history_data, dict) else []
                st.markdown("#### This customer's prediction history")
                display_saved_history(customer_history)

    st.markdown("### All saved customers")
    if not customers:
        st.info("No customers saved yet. Make a prediction to create your first customer record.")
    else:
        for customer in customers:
            code = customer.get("customer_code", "—")
            with st.container(border=True):
                left, right = st.columns([3, 1])
                with left:
                    st.markdown(f"**{code}**")
                    st.caption(
                        f"Tenure: {customer.get('tenure', '—')} months · "
                        f"Monthly charges: {customer.get('MonthlyCharges', '—')}"
                    )
                with right:
                    if st.button("Search", key=f"search_{code}"):
                        st.session_state["customer_search_code"] = code
                        st.rerun()


elif page == "Prediction History":

    show_hero(
        "Prediction History",
        "Review predictions saved to your account across sessions."
    )

    _, saved_history, data_error = load_saved_data()
    if data_error:
        st.error(f"Could not load prediction history: {data_error}")
    else:
        display_saved_history(saved_history)


# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "CHURNGUARD AI • Intelligent customer retention "
    "• Powered by machine learning"
)
