import os
import sys
import json
import datetime
import logging
import argparse
from collections import defaultdict, namedtuple, Counter
import itertools
import functools
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import re
import math
import random
import statistics
import copy
import unittest
import doctest
import time
import sqlite3
import csv
import pickle
import hashlib
import secrets
import socket
import ssl
import asyncio
import threading
import multiprocessing
import subprocess
import configparser
import glob
import shutil
import tempfile
import urllib.request
import urllib.parse
import urllib.error
import webbrowser
import warnings
warnings.filterwarnings('ignore')


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialPortfolioAnalyzer:
    def __init__(self, config_file: str = "config.ini"):
        self.config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            self._create_default_config(config_file)
        self.config.read(config_file)
        
      
        self.db_path = Path(self.config['DEFAULT']['db_path'])
        self._init_database()
        
       
        self.risk_profiles = self._load_risk_profiles()
        
    def _create_default_config(self, config_file: str):
        """Create default configuration file"""
        config = configparser.ConfigParser()
        config['DEFAULT'] = {
            'db_path': 'portfolio_data.db',
            'risk_profiles_path': 'risk_profiles.json',
            'api_key': 'demo',
            'max_threads': '5'
        }
        with open(config_file, 'w') as f:
            config.write(f)
        logger.info(f"Created default config file: {config_file}")
        
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
          
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    risk_profile TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolios (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS holdings (
                    id INTEGER PRIMARY KEY,
                    portfolio_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    purchase_price REAL NOT NULL,
                    purchase_date TEXT NOT NULL,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    symbol TEXT PRIMARY KEY,
                    data JSON NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
        logger.info("Database initialized successfully")
    
    def _load_risk_profiles(self) -> Dict:
        """Load risk profiles from JSON configuration"""
        profiles_path = Path(self.config['DEFAULT']['risk_profiles_path'])
        if not profiles_path.exists():
            default_profiles = {
                "conservative": {
                    "stocks": 40,
                    "bonds": 50,
                    "cash": 10,
                    "description": "Low risk, income-focused portfolio"
                },
                "moderate": {
                    "stocks": 60,
                    "bonds": 35,
                    "cash": 5,
                    "description": "Balanced growth and income portfolio"
                },
                "aggressive": {
                    "stocks": 80,
                    "bonds": 15,
                    "cash": 5,
                    "description": "High growth potential with higher risk"
                }
            }
            with open(profiles_path, 'w') as f:
                json.dump(default_profiles, f, indent=4)
            logger.info(f"Created default risk profiles at: {profiles_path}")
            return default_profiles
        
        with open(profiles_path, 'r') as f:
            return json.load(f)
    
    def _fetch_from_api(self, symbol: str) -> Optional[Dict]:
        """Fetch stock data from Alpha Vantage API (demo version)"""
        try:
            api_key = self.config['DEFAULT']['api_key']
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                
            if "Global Quote" in data and data["Global Quote"]:
                quote = data["Global Quote"]
                return {
                    "symbol": symbol,
                    "price": float(quote.get("05. price", 0)),
                    "change": float(quote.get("09. change", 0)),
                    "change_percent": quote.get("10. change percent", "0%"),
                    "volume": int(quote.get("06. volume", 0)),
                    "latest_trading_day": quote.get("07. latest trading day", "")
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    async def fetch_market_data(self, symbols: List[str]) -> Dict:
        """Asynchronously fetch market data for given symbols"""
        results = {}
        
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(self.config['DEFAULT']['max_threads'])) as executor:
            loop = asyncio.get_event_loop()
            futures = [
                loop.run_in_executor(executor, self._fetch_from_api, symbol)
                for symbol in symbols
            ]
            for symbol, result in zip(symbols, await asyncio.gather(*futures)):
                if result:
                    results[symbol] = result
        
       
        self._update_market_data(results)
        
        return results
    
    def _update_market_data(self, market_data: Dict):
        """Update market data in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for symbol, data in market_data.items():
                cursor.execute(
                    "INSERT OR REPLACE INTO market_data (symbol, data) VALUES (?, ?)",
                    (symbol, json.dumps(data))
                )
            conn.commit()
    
    def get_cached_market_data(self, symbols: List[str]) -> Dict:
        """Get market data from cache/database"""
        results = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for symbol in symbols:
                cursor.execute(
                    "SELECT data FROM market_data WHERE symbol = ?",
                    (symbol,)
                )
                row = cursor.fetchone()
                if row:
                    results[symbol] = json.loads(row[0])
        return results
    
    def create_user(self, username: str, password: str, risk_profile: str = "moderate") -> int:
        """Create a new user with hashed password"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, risk_profile) VALUES (?, ?, ?)",
                (username, password_hash, risk_profile)
            )
            user_id = cursor.lastrowid
            conn.commit()
        
        logger.info(f"Created user {username} with ID {user_id}")
        return user_id
    
    def verify_user(self, username: str, password: str) -> Optional[int]:
        """Verify user credentials"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def create_portfolio(self, user_id: int, name: str) -> int:
        """Create a new portfolio for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO portfolios (user_id, name) VALUES (?, ?)",
                (user_id, name)
            )
            portfolio_id = cursor.lastrowid
            conn.commit()
        
        logger.info(f"Created portfolio {name} with ID {portfolio_id} for user {user_id}")
        return portfolio_id
    
    def add_holding(self, portfolio_id: int, symbol: str, quantity: float, 
                   purchase_price: float, purchase_date: str):
        """Add a holding to a portfolio"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO holdings (portfolio_id, symbol, quantity, purchase_price, purchase_date)
                   VALUES (?, ?, ?, ?, ?)""",
                (portfolio_id, symbol, quantity, purchase_price, purchase_date)
            )
            conn.commit()
        
        logger.info(f"Added {quantity} shares of {symbol} to portfolio {portfolio_id}")
    
    def get_portfolio(self, portfolio_id: int) -> Dict:
        """Get portfolio details with current values"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
           
            cursor.execute(
                "SELECT id, user_id, name FROM portfolios WHERE id = ?",
                (portfolio_id,)
            )
            portfolio_row = cursor.fetchone()
            if not portfolio_row:
                return {}
            
            portfolio = {
                'id': portfolio_row[0],
                'user_id': portfolio_row[1],
                'name': portfolio_row[2],
                'holdings': [],
                'total_value': 0,
                'total_cost': 0,
                'total_gain': 0,
                'total_gain_percent': 0
            }
            
          
            cursor.execute(
                """SELECT symbol, quantity, purchase_price, purchase_date 
                   FROM holdings WHERE portfolio_id = ?""",
                (portfolio_id,)
            )
            holdings = cursor.fetchall()
            
            symbols = [holding[0] for holding in holdings]
            market_data = self.get_cached_market_data(symbols)
            
            for symbol, quantity, purchase_price, purchase_date in holdings:
                current_data = market_data.get(symbol, {})
                current_price = current_data.get('price', 0)
                current_value = quantity * current_price
                cost_basis = quantity * purchase_price
                gain = current_value - cost_basis
                gain_percent = (gain / cost_basis * 100) if cost_basis > 0 else 0
                
                portfolio['holdings'].append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'purchase_price': purchase_price,
                    'purchase_date': purchase_date,
                    'current_price': current_price,
                    'current_value': current_value,
                    'cost_basis': cost_basis,
                    'gain': gain,
                    'gain_percent': gain_percent
                })
                
                portfolio['total_value'] += current_value
                portfolio['total_cost'] += cost_basis
            
            portfolio['total_gain'] = portfolio['total_value'] - portfolio['total_cost']
            if portfolio['total_cost'] > 0:
                portfolio['total_gain_percent'] = (portfolio['total_gain'] / portfolio['total_cost'] * 100)
            
            return portfolio
    
    def calculate_portfolio_metrics(self, portfolio: Dict) -> Dict:
        """Calculate various financial metrics for a portfolio"""
        if not portfolio['holdings']:
            return {}
        
        metrics = {}
        
   
        returns = [holding['gain_percent'] / 100 for holding in portfolio['holdings'] 
                  if holding['gain_percent'] != 0]
        
        if returns:
            metrics['avg_return'] = statistics.mean(returns)
            metrics['volatility'] = statistics.stdev(returns) if len(returns) > 1 else 0
            metrics['sharpe_ratio'] = metrics['avg_return'] / metrics['volatility'] if metrics['volatility'] > 0 else 0
        
       
        sectors = {
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
            'AMZN': 'Consumer Cyclical', 'TSLA': 'Automotive', 'JPM': 'Financial',
            'JNJ': 'Healthcare', 'XOM': 'Energy', 'WMT': 'Consumer Defensive',
            'V': 'Financial', 'PG': 'Consumer Defensive', 'DIS': 'Communication Services'
        }
        
        sector_allocation = defaultdict(float)
        for holding in portfolio['holdings']:
            sector = sectors.get(holding['symbol'], 'Other')
            sector_allocation[sector] += holding['current_value']
        
        metrics['sector_allocation'] = dict(sector_allocation)
        
       
        tech_weight = sector_allocation.get('Technology', 0) / portfolio['total_value'] if portfolio['total_value'] > 0 else 0
        if tech_weight > 0.4:
            metrics['risk_level'] = 'High'
        elif tech_weight > 0.2:
            metrics['risk_level'] = 'Medium'
        else:
            metrics['risk_level'] = 'Low'
        
        return metrics
    
    def generate_recommendations(self, portfolio: Dict, risk_profile: str) -> List[Dict]:
        """Generate personalized investment recommendations"""
        recommendations = []
        target_allocation = self.risk_profiles.get(risk_profile, self.risk_profiles['moderate'])
        
       
        total_value = portfolio['total_value']
        if total_value == 0:
            return recommendations
    
        metrics = self.calculate_portfolio_metrics(portfolio)
        sector_allocation = metrics.get('sector_allocation', {})
        
        
        tech_weight = sector_allocation.get('Technology', 0) / total_value
        if tech_weight > 0.4:
            recommendations.append({
                'type': 'Rebalance',
                'message': 'Technology sector overweight. Consider diversifying into other sectors.',
                'priority': 'High'
            })
        
        if risk_profile == 'conservative' and sector_allocation.get('Bonds', 0) / total_value < 0.4:
            recommendations.append({
                'type': 'Diversification',
                'message': 'Consider adding bond ETFs for stability and income.',
                'priority': 'Medium'
            })
       
