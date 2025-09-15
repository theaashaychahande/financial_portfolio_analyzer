# Financial Portfolio Analyzer

A comprehensive financial portfolio analysis tool built with Python and Streamlit that provides investment recommendations and portfolio optimization.

financial-portfolio-analyzer/
│
├── app.py                 # Main Streamlit application
├── portfolio_analyzer.py  # Core financial analysis logic
├── config.ini            # Configuration file
├── requirements.txt      # Python dependencies
├── risk_profiles.json    # Risk profile definitions (auto-generated)
├── portfolio_data.db     # SQLite database (auto-generated)
└── README.md            # Project documentation

## Features

- **Portfolio Management**: Create portfolios and track holdings
- **Market Analysis**: View current quotes and historical trends
- **Performance Metrics**: Calculate returns, volatility, and risk metrics
- **Investment Recommendations**: Get personalized recommendations based on your risk profile
- **Portfolio Optimization**: Optimize your portfolio allocation

## Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`

## Usage

1. Create an account with your risk profile
2. Create one or more portfolios
3. Add holdings to your portfolios
4. View performance metrics and get recommendations

## Note

This application uses demo data from Alpha Vantage API. For real-time data, you need to obtain an API key from [Alpha Vantage](https://www.alphavantage.com/) and update the config.ini file.
