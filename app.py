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

# Get unique symbols
def get_symbols():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT DISTINCT symbol FROM trades")
        result = cursor.fetchall()
        symbols = [row['symbol'] for row in result]
    conn.close()
    return symbols

# 심볼별 총 PnL 계산
def get_symbol_pnl_summary():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 심볼별 총 PnL 집계
            cursor.execute("""
                SELECT symbol, SUM(pnl) as total_pnl
                FROM trades 
                WHERE pnl IS NOT NULL
                GROUP BY symbol
            """)
            results = cursor.fetchall()
            
            # 디버깅을 위한 로그
            print(f"PnL 요약 쿼리 결과: {results}")
            
        conn.close()
        
        # 결과가 비어있는지 확인
        if not results:
            print("PnL 데이터가 없습니다")
            return []
        
        # 결과 정렬 (총 PnL 내림차순)
        pnl_summary = []
        for row in results:
            pnl_summary.append({
                'symbol': row['symbol'],
                'total_pnl': row['total_pnl']
            })
        
        # PnL 기준 내림차순 정렬
        pnl_summary = sorted(pnl_summary, key=lambda x: x['total_pnl'] if x['total_pnl'] is not None else 0, reverse=True)
        return convert_to_serializable(pnl_summary)
    except Exception as e:
        print(f"PnL 요약 데이터 가져오기 오류: {e}")
        return []

# Process trades to identify open and closed positions
def process_trades(trades):
    # Parse additionalInfo JSON strings
    for trade in trades:
        if trade['additionalInfo']:
            try:
                trade['additionalInfo'] = json.loads(trade['additionalInfo'])
            except:
                trade['additionalInfo'] = {}
    
    # 단순히 OPEN 상태인 거래를 오픈 포지션으로 취급
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
        for t in trades if t['orderStatus'] == 'OPEN'
    ]
    
    # 클로즈 포지션은 원래처럼 FILLED 중에서 additionalInfo에 진입/청산 가격이 있는 거래만
    exit_trades = [t for t in trades if t['orderStatus'] == 'FILLED' and 
                   t['additionalInfo'] and 
                   isinstance(t['additionalInfo'], dict) and
                   'entry_price' in t['additionalInfo'] and 
                   'exit_price' in t['additionalInfo']]
    
    closed_positions = []
    for exit_trade in exit_trades:
        closed_positions.append({
            'entry_trade': {},  # 매칭된 entry_trade 정보는 더 이상 필요 없음
            'exit_trade': exit_trade,
            'entry_price': exit_trade['additionalInfo']['entry_price'],
            'exit_price': exit_trade['additionalInfo']['exit_price'],
            'pnl': exit_trade['pnl'],
            'symbol': exit_trade['symbol'],
            'side': exit_trade['side'],
            'positionType': exit_trade['positionType'],
            'quantity': exit_trade['quantity'],
            'leverage': exit_trade['leverage'],
            'entry_time': exit_trade['executionTime'],  # entry_time 정보가 없으므로 청산 시간으로 대체
            'exit_time': exit_trade['executionTime']
        })
    
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