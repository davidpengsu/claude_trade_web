from flask import Flask, render_template, jsonify
import pymysql
import json
from datetime import datetime
import decimal
import os

app = Flask(__name__)

# Load database configuration
def load_db_config():
    with open('db_config.json', 'r') as f:
        return json.load(f)

# Connect to database
def get_db_connection():
    config = load_db_config()
    return pymysql.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        port=config['port'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# Helper function to convert MySQL data types to JSON-serializable types
def convert_to_serializable(data):
    if isinstance(data, dict):
        return {k: convert_to_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_serializable(item) for item in data]
    elif isinstance(data, decimal.Decimal):
        return float(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

# PyMySQL with DictCursor already returns rows as dictionaries
# This function is kept for compatibility but simplified
def row_to_dict(cursor, row):
    return row

# Get all trades
def get_all_trades():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM trades ORDER BY executionTime DESC")
        trades = cursor.fetchall()
    conn.close()
    return convert_to_serializable(trades)

# Get trades by symbol
def get_trades_by_symbol(symbol):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM trades WHERE symbol = %s ORDER BY executionTime DESC", (symbol,))
        trades = cursor.fetchall()
    conn.close()
    return convert_to_serializable(trades)

# Get unique symbols
def get_symbols():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT DISTINCT symbol FROM trades")
        result = cursor.fetchall()
        symbols = [row['symbol'] for row in result]
    conn.close()
    return symbols

# Process trades to identify open and closed positions
def process_trades(trades):
    # Parse additionalInfo JSON strings
    for trade in trades:
        if trade['additionalInfo']:
            try:
                trade['additionalInfo'] = json.loads(trade['additionalInfo'])
            except:
                trade['additionalInfo'] = {}
    
    # Identify exit trades (FILLED with additionalInfo containing prices)
    exit_trades = [t for t in trades if t['orderStatus'] == 'FILLED' and 
                   t['additionalInfo'] and 
                   isinstance(t['additionalInfo'], dict) and
                   'entry_price' in t['additionalInfo'] and 
                   'exit_price' in t['additionalInfo']]
    
    # Identify entry trades (CLOSED or OPEN status)
    entry_trades = [t for t in trades if t['orderStatus'] in ['CLOSED', 'OPEN']]
    
    # Match entry and exit trades
    closed_positions = []
    matched_entry_ids = set()
    
    for exit_trade in exit_trades:
        # Find matching entry trade
        matching_entry = None
        
        for entry_trade in entry_trades:
            if (entry_trade['tradeId'] not in matched_entry_ids and
                entry_trade['symbol'] == exit_trade['symbol'] and
                entry_trade['positionType'] == exit_trade['positionType'] and
                entry_trade['side'] != exit_trade['side']):
                
                matching_entry = entry_trade
                matched_entry_ids.add(entry_trade['tradeId'])
                break
        
        if matching_entry:
            closed_positions.append({
                'entry_trade': matching_entry,
                'exit_trade': exit_trade,
                'entry_price': exit_trade['additionalInfo']['entry_price'],
                'exit_price': exit_trade['additionalInfo']['exit_price'],
                'pnl': exit_trade['pnl'],
                'symbol': matching_entry['symbol'],
                'side': matching_entry['side'],
                'positionType': matching_entry['positionType'],
                'quantity': matching_entry['quantity'],
                'leverage': matching_entry['leverage'],
                'entry_time': matching_entry['executionTime'],
                'exit_time': exit_trade['executionTime']
            })
    
    # Open positions are entry trades that don't have a matching exit trade
    open_positions = [
        {
            'trade': t,
            'symbol': t['symbol'],
            'side': t['side'],
            'positionType': t['positionType'],
            'quantity': t['quantity'],
            'price': t['price'],
            'leverage': t['leverage'],
            'takeProfit': t['takeProfit'],
            'stopLoss': t['stopLoss'],
            'entry_time': t['executionTime']
        }
        for t in entry_trades if t['tradeId'] not in matched_entry_ids
    ]
    
    return open_positions, closed_positions

# Routes
@app.route('/')
def index():
    try:
        symbols = get_symbols()
        return render_template('index.html', symbols=symbols)
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}", 500

@app.route('/test')
def test():
    return "서버가 정상적으로 실행 중입니다!"

@app.route('/api/trades/<symbol>')
def api_trades_by_symbol(symbol):
    trades = get_trades_by_symbol(symbol)
    open_positions, closed_positions = process_trades(trades)
    return jsonify({
        'open_positions': open_positions,
        'closed_positions': closed_positions
    })

@app.route('/api/trades')
def api_all_trades():
    trades = get_all_trades()
    open_positions, closed_positions = process_trades(trades)
    return jsonify({
        'open_positions': open_positions,
        'closed_positions': closed_positions
    })

if __name__ == '__main__':
    try:
        # 모든 네트워크 인터페이스(0.0.0.0)에 바인딩하여 외부에서도 접속 가능하게 함
        print("서버를 시작합니다. http://127.0.0.1:5000 또는 http://localhost:5000 에서 접속하세요.")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"서버 시작 중 오류가 발생했습니다: {e}")