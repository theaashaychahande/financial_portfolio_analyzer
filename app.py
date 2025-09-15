import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
from portfolio_analyzer import FinancialPortfolioAnalyzer


st.set_page_config(
    page_title="Financial Portfolio Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .positive-change {
        color: green;
        font-weight: bold;
    }
    .negative-change {
        color: red;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_analyzer():
    return FinancialPortfolioAnalyzer()

analyzer = get_analyzer()


st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Portfolio Management", "Market Analysis", "Recommendations"])


if 'user_id' not in st.session_state:
    st.session_state.user_id = None

if st.session_state.user_id is None:
    st.title("Financial Portfolio Analyzer")
    auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
    
    with auth_tab1:
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            
            if login_btn:
                user_id = analyzer.verify_user(username, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with auth_tab2:
        with st.form("register_form"):
            st.subheader("Create Account")
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            risk_profile = st.selectbox(
                "Risk Profile",
                options=list(analyzer.risk_profiles.keys()),
                index=1
            )
            register_btn = st.form_submit_button("Register")
            
            if register_btn:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    user_id = analyzer.create_user(new_username, new_password, risk_profile)
                    st.session_state.user_id = user_id
                    st.session_state.username = new_username
                    st.success("Account created successfully!")
                    time.sleep(1)
                    st.rerun()
    
    st.stop()

