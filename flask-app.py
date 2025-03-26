from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import mysql.connector
import json
import os
import requests
import hmac
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Load configurations
def load_config(config_file):
    with open(config_file, 'r') as file:
        return json.load(file)

# Database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "password",
    "database": "trading_system",
    "port": 3306
}

# Bybit API configuration
api_config = {
    "bybit_api": {
        "BTC": {
            "key": "your-btc-api-key",
            "secret": "your-btc-api-secret"
        },
        "ETH": {
            "key": "your-btc-api-key",
            "secret": "your-btc-api-secret"
        },
        "SOL": {
            "key": "your-sol-api-key",
            "secret": "your-sol-api-secret"
        }
    }
}

# Initial investments (will be updated through settings)
initial_investments = {
    "BTC": 1000.0,
    "ETH": 1000.0,
    "SOL": 1000.0
}

# Database connection
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# Bybit API Client
class BybitClient:
    def __init__(self, api_key, api_secret):
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.BASE_URL = "https://api.bybit.com"
    
    def _generate_signature(self, params: Dict) -> str:
        """HMAC SHA256 서명 생성"""
        param_str = ''
        
        # 타임스탬프 추가
        timestamp = int(time.time() * 1000)
        params['timestamp'] = timestamp
        
        # 파라미터 정렬
        sorted_params = sorted(params.items())
        param_str = '&'.join([f"{key}={value}" for key, value in sorted_params])
        
        # 서명 생성
        signature = hmac.new(
            bytes(self.API_SECRET, 'utf-8'),
            bytes(param_str, 'utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _send_get_request(self, endpoint: str, params: Dict = None, auth: bool = False) -> Dict:
        """GET 요청 전송"""
        if params is None:
            params = {}
        
        url = f"{self.BASE_URL}{endpoint}"
        
        # 인증이 필요한 경우 서명 추가
        if auth:
            signature = self._generate_signature(params)
            headers = {
                'X-BAPI-API-KEY': self.API_KEY,
                'X-BAPI-SIGN': signature,
                'X-BAPI-TIMESTAMP': str(params['timestamp']),
                'X-BAPI-RECV-WINDOW': '5000'
            }
        else:
            headers = {}
        
        response = requests.get(url, params=params, headers=headers)
        return response.json()
    
    def safe_float_conversion(self, value):
        """안전하게 float로 변환"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def get_account_balance(self, coin: str = "USDT") -> Dict[str, float]:
        """
        계좌 잔고 조회
        
        Args:
            coin: 화폐 단위 (예: "USDT")
        
        Returns:
            잔고 정보
        """
        params = {
            "accountType": "UNIFIED",
            "coin": coin
        }
        
        response = self._send_get_request("/v5/account/wallet-balance", params, True)
        
        if response.get("retCode") == 0:
            account_list = response.get("result", {}).get("list", [])
            if account_list:
                coins = account_list[0].get("coin", [])
                for coin_data in coins:
                    if coin_data.get("coin") == coin:
                        return {
                            "total": self.safe_float_conversion(coin_data.get("walletBalance", 0)),
                            "available": self.safe_float_conversion(coin_data.get("availableToWithdraw", 0)),
                            "margin_balance": self.safe_float_conversion(coin_data.get("totalMarginBalance", 0))
                        }
        
        # Default return if no data is found
        return {
            "total": 0.0,
            "available": 0.0,
            "margin_balance": 0.0
        }

# Routes
@app.route('/')
def index():
    # Get trade data for all symbols
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get the latest trade for each symbol
    cursor.execute("""
        SELECT t.* 
        FROM trades t
        INNER JOIN (
            SELECT symbol, MAX(executionTime) as max_time
            FROM trades
            GROUP BY symbol
        ) m ON t.symbol = m.symbol AND t.executionTime = m.max_time
    """)
    latest_trades = cursor.fetchall()
    
    # Get trade counts and profit statistics for each symbol
    cursor.execute("""
        SELECT 
            symbol, 
            COUNT(*) as trade_count,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as profitable_trades,
            SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as loss_trades,
            SUM(pnl) as total_pnl
        FROM trades
        WHERE pnl IS NOT NULL
        GROUP BY symbol
    """)
    trade_stats = cursor.fetchall()
    
    # Convert to dict for easier access
    stats_dict = {stat['symbol']: stat for stat in trade_stats}
    
    # Get decision events for today
    cursor.execute("""
        SELECT * FROM decision_events
        WHERE DATE(occurUtcDate) = CURDATE()
        ORDER BY occurUtcDate DESC
        LIMIT 10
    """)
    recent_decisions = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Get account balances for each coin
    account_balances = {}
    performance = {}
    
    for symbol_full in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']:
        symbol = symbol_full.replace('USDT', '')
        try:
            if symbol in api_config['bybit_api'] and api_config['bybit_api'][symbol]['key'] != 'your-btc-api-key':
                client = BybitClient(
                    api_config['bybit_api'][symbol]['key'],
                    api_config['bybit_api'][symbol]['secret']
                )
                account_balances[symbol] = client.get_account_balance("USDT")
                
                # Calculate performance if we have initial investment
                if symbol in initial_investments:
                    initial = initial_investments[symbol]
                    current = account_balances[symbol]['total']
                    profit = current - initial
                    profit_percentage = (profit / initial) * 100 if initial > 0 else 0
                    
                    performance[symbol] = {
                        'initial': initial,
                        'current': current,
                        'profit': profit,
                        'profit_percentage': profit_percentage
                    }
            else:
                account_balances[symbol] = {'total': 0.0, 'available': 0.0, 'margin_balance': 0.0}
                performance[symbol] = {'initial': 0.0, 'current': 0.0, 'profit': 0.0, 'profit_percentage': 0.0}
        except Exception as e:
            print(f"Error getting balance for {symbol}: {e}")
            account_balances[symbol] = {'total': 0.0, 'available': 0.0, 'margin_balance': 0.0}
            performance[symbol] = {'initial': 0.0, 'current': 0.0, 'profit': 0.0, 'profit_percentage': 0.0}
    
    return render_template('index.html', 
                          latest_trades=latest_trades, 
                          stats=stats_dict, 
                          recent_decisions=recent_decisions,
                          account_balances=account_balances,
                          performance=performance)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    global initial_investments
    
    if request.method == 'POST':
        # Update initial investments
        initial_investments['BTC'] = float(request.form.get('btc_initial', 0))
        initial_investments['ETH'] = float(request.form.get('eth_initial', 0))
        initial_investments['SOL'] = float(request.form.get('sol_initial', 0))
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('settings'))
        
    return render_template('settings.html', investments=initial_investments)

@app.route('/data')
def data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get table names
    cursor.execute("SHOW TABLES")
    tables = [table['Tables_in_trading_system'] for table in cursor.fetchall()]
    
    # Get data for selected table (default to trades)
    selected_table = request.args.get('table', 'trades')
    if selected_table not in tables:
        selected_table = 'trades'
    
    cursor.execute(f"SELECT * FROM {selected_table} ORDER BY createdAt DESC LIMIT 100")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute(f"SHOW COLUMNS FROM {selected_table}")
    columns = [column['Field'] for column in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template('data.html', 
                          tables=tables, 
                          selected_table=selected_table,
                          columns=columns, 
                          rows=rows)

@app.route('/api/trades/<symbol>')
def get_trades(symbol):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get trades for the symbol
    cursor.execute("""
        SELECT * FROM trades
        WHERE symbol = %s
        ORDER BY executionTime DESC
        LIMIT 100
    """, (symbol,))
    trades = cursor.fetchall()
    
    # Convert datetime objects to strings for JSON serialization
    for trade in trades:
        if 'executionTime' in trade and trade['executionTime']:
            trade['executionTime'] = trade['executionTime'].strftime('%Y-%m-%d %H:%M:%S')
        if 'createdAt' in trade and trade['createdAt']:
            trade['createdAt'] = trade['createdAt'].strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.close()
    conn.close()
    
    return jsonify(trades)

@app.route('/symbol/<symbol>')
def symbol_detail(symbol):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get trades for the symbol
    cursor.execute("""
        SELECT * FROM trades
        WHERE symbol = %s
        ORDER BY executionTime DESC
        LIMIT 100
    """, (symbol,))
    trades = cursor.fetchall()
    
    # Get trade statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as trade_count,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as profitable_trades,
            SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as loss_trades,
            SUM(pnl) as total_pnl,
            AVG(pnl) as avg_pnl
        FROM trades
        WHERE symbol = %s AND pnl IS NOT NULL
    """, (symbol,))
    stats = cursor.fetchone()
    
    # Get recent decisions for this symbol
    cursor.execute("""
        SELECT * FROM decision_events
        WHERE eventSymbol = %s
        ORDER BY occurUtcDate DESC
        LIMIT 20
    """, (symbol,))
    decisions = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Get account balance if API is configured
    account_balance = {'total': 0.0, 'available': 0.0, 'margin_balance': 0.0}
    performance = {'initial': 0.0, 'current': 0.0, 'profit': 0.0, 'profit_percentage': 0.0}
    
    symbol_base = symbol.replace('USDT', '')
    if symbol_base in api_config['bybit_api'] and api_config['bybit_api'][symbol_base]['key'] != f'your-{symbol_base.lower()}-api-key':
        try:
            client = BybitClient(
                api_config['bybit_api'][symbol_base]['key'],
                api_config['bybit_api'][symbol_base]['secret']
            )
            account_balance = client.get_account_balance("USDT")
            
            # Calculate performance
            if symbol_base in initial_investments:
                initial = initial_investments[symbol_base]
                current = account_balance['total']
                profit = current - initial
                profit_percentage = (profit / initial) * 100 if initial > 0 else 0
                
                performance = {
                    'initial': initial,
                    'current': current,
                    'profit': profit,
                    'profit_percentage': profit_percentage
                }
        except Exception as e:
            print(f"Error getting balance for {symbol_base}: {e}")
    
    return render_template('symbol_detail.html', 
                          symbol=symbol,
                          trades=trades,
                          stats=stats,
                          decisions=decisions,
                          account_balance=account_balance,
                          performance=performance)

if __name__ == '__main__':
    app.run(debug=True)
