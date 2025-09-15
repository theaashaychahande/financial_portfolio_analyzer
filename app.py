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

st.sidebar.write(f"Logged in as: {st.session_state.username}")
if st.sidebar.button("Logout"):
    st.session_state.user_id = None
    st.rerun()


@st.cache_data
def get_user_portfolios(user_id):
    with analyzer.db_path.connect() as conn:
        df = pd.read_sql("SELECT id, name FROM portfolios WHERE user_id = ?", conn, params=(user_id,))
    return df

portfolios_df = get_user_portfolios(st.session_state.user_id)

if page == "Dashboard":
    st.markdown('<h1 class="main-header">Financial Portfolio Analyzer</h1>', unsafe_allow_html=True)
    
    if portfolios_df.empty:
        st.warning("You don't have any portfolios yet. Create one in the Portfolio Management section.")
    else:
        selected_portfolio = st.selectbox(
            "Select Portfolio",
            options=portfolios_df['id'].tolist(),
            format_func=lambda x: portfolios_df[portfolios_df['id'] == x]['name'].iloc[0]
        )
        
        portfolio = analyzer.get_portfolio(selected_portfolio)
        
        if portfolio and portfolio['holdings']:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Value", f"${portfolio['total_value']:,.2f}")
            with col2:
                st.metric("Total Cost", f"${portfolio['total_cost']:,.2f}")
            with col3:
                gain_class = "positive-change" if portfolio['total_gain'] >= 0 else "negative-change"
                st.metric("Total Gain/Loss", f"${portfolio['total_gain']:,.2f}", 
                         delta=f"{portfolio['total_gain_percent']:.2f}%")
            with col4:
                st.metric("Number of Holdings", len(portfolio['holdings']))
            
     
            st.subheader("Holdings")
            holdings_df = pd.DataFrame(portfolio['holdings'])
            if not holdings_df.empty:
                holdings_df = holdings_df[[
                    'symbol', 'quantity', 'purchase_price', 'current_price',
                    'current_value', 'gain', 'gain_percent'
                ]]
                holdings_df.columns = ['Symbol', 'Quantity', 'Purchase Price', 'Current Price', 
                                      'Current Value', 'Gain/Loss', 'Gain/Loss %']
                holdings_df['Gain/Loss %'] = holdings_df['Gain/Loss %'].round(2)
                
             
                for col in ['Purchase Price', 'Current Price', 'Current Value', 'Gain/Loss']:
                    holdings_df[col] = holdings_df[col].apply(lambda x: f"${x:,.2f}")
                
                st.dataframe(holdings_df, use_container_width=True)
            
        
            metrics = analyzer.calculate_portfolio_metrics(portfolio)
            if metrics:
                st.subheader("Portfolio Metrics")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'avg_return' in metrics:
                        st.metric("Average Return", f"{metrics['avg_return']*100:.2f}%")
                    if 'volatility' in metrics:
                        st.metric("Volatility", f"{metrics['volatility']*100:.2f}%")
                    if 'sharpe_ratio' in metrics:
                        st.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
                
                with col2:
                    if 'risk_level' in metrics:
                        risk_color = "red" if metrics['risk_level'] == 'High' else "orange" if metrics['risk_level'] == 'Medium' else "green"
                        st.markdown(f"**Risk Level**: <span style='color:{risk_color}'>{metrics['risk_level']}</span>", 
                                   unsafe_allow_html=True)
                
            
                if 'sector_allocation' in metrics and metrics['sector_allocation']:
                    st.subheader("Sector Allocation")
                    sector_df = pd.DataFrame(
                        list(metrics['sector_allocation'].items()), 
                        columns=['Sector', 'Value']
                    )
                    sector_df['Percentage'] = (sector_df['Value'] / portfolio['total_value'] * 100).round(2)
                    
                    fig = px.pie(
                        sector_df, 
                        values='Value', 
                        names='Sector',
                        title='Portfolio by Sector'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("This portfolio is empty. Add some holdings in the Portfolio Management section.")

elif page == "Portfolio Management":
    st.title("Portfolio Management")
    
    tab1, tab2, tab3 = st.tabs(["Create Portfolio", "Add Holdings", "View Portfolios"])
    
    with tab1:
        st.subheader("Create New Portfolio")
        with st.form("create_portfolio"):
            portfolio_name = st.text_input("Portfolio Name")
            create_btn = st.form_submit_button("Create Portfolio")
            
            if create_btn and portfolio_name:
                portfolio_id = analyzer.create_portfolio(st.session_state.user_id, portfolio_name)
                st.success(f"Portfolio '{portfolio_name}' created successfully!")
        
                st.cache_data.clear()
    
    with tab2:
        st.subheader("Add Holdings to Portfolio")
        
        if portfolios_df.empty:
            st.warning("You need to create a portfolio first.")
        else:
            selected_portfolio = st.selectbox(
                "Select Portfolio",
                options=portfolios_df['id'].tolist(),
                format_func=lambda x: portfolios_df[portfolios_df['id'] == x]['name'].iloc[0],
                key="add_holding"
            )
            
            with st.form("add_holding_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    symbol = st.text_input("Symbol (e.g., AAPL, MSFT)", value="AAPL").upper()
                    quantity = st.number_input("Quantity", min_value=0.0, value=10.0, step=1.0)
                
                with col2:
                    purchase_price = st.number_input("Purchase Price", min_value=0.0, value=150.0, step=0.01)
                    purchase_date = st.date_input("Purchase Date", value=datetime.now() - timedelta(days=30))
                
                add_btn = st.form_submit_button("Add Holding")
                
                if add_btn:
                    analyzer.add_holding(
                        selected_portfolio, symbol, quantity, 
                        purchase_price, purchase_date.strftime("%Y-%m-%d")
                    )
                    st.success(f"Added {quantity} shares of {symbol} to portfolio")
                   
                    asyncio.run(analyzer.fetch_market_data([symbol]))
    
    with tab3:
        st.subheader("Your Portfolios")
        
        if portfolios_df.empty:
            st.info("You don't have any portfolios yet.")
        else:
            for _, row in portfolios_df.iterrows():
                with st.expander(row['name']):
                    portfolio = analyzer.get_portfolio(row['id'])
                    
                    if portfolio and portfolio['holdings']:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Total Value:** ${portfolio['total_value']:,.2f}")
                            st.write(f"**Total Gain/Loss:** ${portfolio['total_gain']:,.2f} "
                                    f"({portfolio['total_gain_percent']:.2f}%)")
                        
                        with col2:
                            st.write(f"**Number of Holdings:** {len(portfolio['holdings'])}")
                        
                   
                        holdings_df = pd.DataFrame(portfolio['holdings'])
                        holdings_df = holdings_df[['symbol', 'quantity', 'current_price', 'current_value']]
                        holdings_df.columns = ['Symbol', 'Quantity', 'Price', 'Value']
                        st.dataframe(holdings_df, use_container_width=True)
                    else:
                        st.info("This portfolio is empty.")

elif page == "Market Analysis":
    st.title("Market Analysis")
    

    popular_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'BRK.B', 'JNJ', 'JPM', 'V', 'PG', 'NVDA']
    
    selected_stocks = st.multiselect(
        "Select stocks to analyze",
        options=popular_stocks,
        default=['AAPL', 'MSFT', 'GOOGL']
    )
    
    if selected_stocks:
     
        market_data = asyncio.run(analyzer.fetch_market_data(selected_stocks))
        
        if market_data:
          
            st.subheader("Current Quotes")
            
            quotes_data = []
            for symbol, data in market_data.items():
                quotes_data.append({
                    'Symbol': symbol,
                    'Price': data.get('price', 0),
                    'Change': data.get('change', 0),
                    'Change %': data.get('change_percent', '0%'),
                    'Volume': data.get('volume', 0)
                })
            
            quotes_df = pd.DataFrame(quotes_data)
            st.dataframe(quotes_df, use_container_width=True)
            
           
            st.subheader("Price Comparison")
            
          
