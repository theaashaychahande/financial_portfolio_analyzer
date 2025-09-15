# Financial Portfolio Analyzer

A comprehensive financial portfolio analysis tool built with Python and Streamlit that provides investment recommendations and portfolio optimization.

## Project Structure
## Features

- **Portfolio Management**: Create portfolios and track holdings
- **Market Analysis**: View current quotes and historical trends
- **Performance Metrics**: Calculate returns, volatility, and risk metrics
- **Investment Recommendations**: Get personalized recommendations based on your risk profile
- **Portfolio Optimization**: Optimize your portfolio allocation
- **User Authentication**: Secure login and registration system
- **Data Visualization**: Interactive charts and performance dashboards

## Installation

1. Clone this repository or download all files to a directory
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`

## Usage

1. Create an account with your risk profile (Conservative, Moderate, or Aggressive)
2. Create one or more portfolios
3. Add holdings to your portfolios with purchase details
4. View performance metrics and get personalized recommendations
5. Analyze market trends and optimize your portfolio allocation

## File Details

### app.py
The main Streamlit application that provides the user interface for the portfolio analyzer. It includes:
- User authentication (login/registration)
- Portfolio management interface
- Market analysis dashboard
- Investment recommendations
- Data visualization with Plotly charts

### portfolio_analyzer.py
The core financial analysis engine that contains:
- Database management with SQLite
- Market data fetching from Alpha Vantage API
- Portfolio calculation and optimization algorithms
- Risk assessment and recommendation generation
- Financial metrics calculation (returns, volatility, Sharpe ratio, etc.)

### config.ini
Configuration file that stores:
- Database path
- API keys for market data
- Risk profiles path
- Application settings

### requirements.txt
Python dependencies including:
- Streamlit for the web interface
- Pandas for data manipulation
- Plotly for interactive visualizations
- NumPy for numerical computations

### risk_profiles.json (auto-generated)
Defines different risk profiles with their target allocations:
- Conservative: 40% stocks, 50% bonds, 10% cash
- Moderate: 60% stocks, 35% bonds, 5% cash  
- Aggressive: 80% stocks, 15% bonds, 5% cash

### portfolio_data.db (auto-generated)
SQLite database that stores:
- User accounts and credentials (hashed passwords)
- Portfolio definitions
- Holding details
- Market data cache

## API Integration

This application uses the Alpha Vantage API for market data. By default, it uses the demo API key. For production use:

1. Get a free API key from [Alpha Vantage](https://www.alphavantage.com/support/#api-key)
2. Update the `api_key` value in `config.ini`
3. The application will automatically use your key for real-time data

## Note

This application is designed for educational and demonstration purposes. It uses simulated historical data for visualization and provides general investment recommendations. For actual investment decisions, consult with a qualified financial advisor.

The application demonstrates the use of multiple Python libraries including:
- Data processing: pandas, numpy
- Visualization: plotly, streamlit
- Database: sqlite3
- Utilities: os, sys, json, datetime, logging, collections, typing, pathlib, math, statistics, etc.
- Security: hashlib, secrets
- Web: urllib, webbrowser
- Concurrency: asyncio, threading

## Demo Instructions

1. The app will auto-create sample data on first run
2. Use these demo credentials:
   - Username: `test_user`
   - Password: `password123`
3. Or create a new account with any credentials
4. The portfolio will already have sample holdings (AAPL, MSFT)
   
## License

This project is for educational purposes. Please ensure compliance with Alpha Vantage's terms of service when using their API.
