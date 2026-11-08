from pathlib import Path
import streamlit as st
import plotly.graph_objects as go

CSS_PATH = Path(__file__).with_name("style.css")



def inject_css():
    css_path = Path(__file__).with_name("style.css")
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def show_hero(title, description):
    st.markdown(
        f"""
        <section class="hero">
            <div class="hero-label">CHURNGUARD AI / CUSTOMER INTELLIGENCE</div>
            <h1>{title}</h1>
            <p>{description}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

def metric_card(label, value, note):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def create_gauge(probability):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability * 100,
        number={"suffix": "%", "font": {"size": 35, "color": "white"}},
        title={"text": "Churn probability", "font": {"color": "#cbd5e1"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
            "bar": {"color": "#38bdf8"},
            "bgcolor": "#172840",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 30], "color": "#164e45"},
                {"range": [30, 60], "color": "#59451d"},
                {"range": [60, 100], "color": "#622d3c"},
            ],
        },
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
    )
    return fig

def show_retention_advice(risk, prediction):
    st.markdown("### 💡 Retention recommendations")
    if prediction == "No":
        advice = [
            "Continue providing consistent service quality.",
            "Monitor customer satisfaction regularly.",
            "Offer relevant upgrades based on customer needs.",
        ]
    elif risk == "High":
        advice = [
            "Contact the customer with a personalized retention offer.",
            "Investigate billing or service-related complaints.",
            "Consider a suitable long-term contract incentive.",
        ]
    elif risk == "Medium":
        advice = [
            "Schedule a customer satisfaction check-in.",
            "Review service usage and identify possible concerns.",
            "Share relevant loyalty benefits.",
        ]
    else:
        advice = [
            "Maintain regular customer engagement.",
            "Provide proactive support when needed.",
            "Continue monitoring customer activity.",
        ]
    for item in advice:
        st.markdown(f"- {item}")
