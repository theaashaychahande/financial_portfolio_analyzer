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
            
          
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            price_data = []
            
            for symbol in selected_stocks:
                base_price = market_data[symbol]['price'] if symbol in market_data else 100
                
                prices = [base_price * (1 + np.random.normal(0, 0.02)) for _ in range(30)]
              
                prices = np.abs(prices)
                trend = np.linspace(0, 0.1, 30)
                prices = prices * (1 + trend)
                
                for i, date in enumerate(dates):
                    price_data.append({
                        'Date': date,
                        'Symbol': symbol,
                        'Price': prices[i]
                    })
            
            price_df = pd.DataFrame(price_data)
            
            fig = px.line(
                price_df, 
                x='Date', 
                y='Price', 
                color='Symbol',
                title='Historical Price Trends (Simulated)'
            )
            st.plotly_chart(fig, use_container_width=True)
            
         
            st.subheader("Volatility Analysis")
            
            vol_df = price_df.copy()
            vol_df['Daily Return'] = vol_df.groupby('Symbol')['Price'].pct_change()
            vol_df = vol_df.dropna()
            
            vol_summary = vol_df.groupby('Symbol')['Daily Return'].agg(['mean', 'std']).reset_index()
            vol_summary['Volatility (Annualized)'] = vol_summary['std'] * np.sqrt(252)  # Annualize
            
            fig = px.bar(
                vol_summary, 
                x='Symbol', 
                y='Volatility (Annualized)',
                title='Annualized Volatility by Stock'
            )
            st.plotly_chart(fig, use_container_width=True)

elif page == "Recommendations":
    st.title("Investment Recommendations")
    
    if portfolios_df.empty:
        st.warning("You need to create a portfolio first to get recommendations.")
    else:
        selected_portfolio = st.selectbox(
            "Select Portfolio",
            options=portfolios_df['id'].tolist(),
            format_func=lambda x: portfolios_df[portfolios_df['id'] == x]['name'].iloc[0],
            key="rec_portfolio"
        )
        
        portfolio = analyzer.get_portfolio(selected_portfolio)
        
        if portfolio and portfolio['holdings']:
        
            with analyzer.db_path.connect() as conn:
                risk_profile = pd.read_sql(
                    "SELECT risk_profile FROM users WHERE id = ?", 
                    conn, params=(st.session_state.user_id,)
                ).iloc[0]['risk_profile']
            
            st.write(f"Your risk profile: **{risk_profile}**")
            st.write(analyzer.risk_profiles[risk_profile]['description'])
            
        
            recommendations = analyzer.generate_recommendations(portfolio, risk_profile)
            
            if recommendations:
                st.subheader("Personalized Recommendations")
                
                for rec in recommendations:
                    priority_color = {
                        'High': 'red',
                        'Medium': 'orange',
                        'Low': 'green'
                    }.get(rec['priority'], 'black')
                    
                    st.markdown(
                        f"**{rec['type']}** - <span style='color:{priority_color}'>{rec['priority']} Priority</span>",
                        unsafe_allow_html=True
                    )
                    st.write(rec['message'])
                    st.divider()
            else:
                st.info("No specific recommendations at this time. Your portfolio looks well-balanced!")
            
         
            st.subheader("Portfolio Optimization")
            optimization = analyzer.optimize_portfolio(portfolio, risk_profile)
            
            if optimization:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Current Allocation**")
                    for asset, percent in optimization['current'].items():
                        if percent > 0:
                            st.write(f"{asset.capitalize()}: {percent:.1f}%")
                
                with col2:
                    st.write("**Target Allocation**")
                    for asset, percent in optimization['target'].items():
                        st.write(f"{asset.capitalize()}: {percent}%")
                
              
                st.write("**Recommended Adjustments**")
                for asset, adjustment in optimization['adjustments'].items():
                    if abs(adjustment) > 1:  # Only show adjustments > 1%
                        action = "Increase" if adjustment > 0 else "Reduce"
                        st.write(f"{action} {asset} by {abs(adjustment):.1f}%")
        else:
            st.info("Add some holdings to your portfolio to get personalized recommendations.")


st.sidebar.markdown("---")
st.sidebar.info(
    "This is a demonstration application for financial portfolio analysis. "
    "Not intended for actual investment advice."
)

