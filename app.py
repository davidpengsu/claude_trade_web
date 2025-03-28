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
            
            # 더 자세한 디버깅 로그
            print(f"PnL 요약 쿼리 결과: {results}")
            for row in results:
                print(f"Symbol: {row['symbol']}, PnL: {row['total_pnl']}")
            
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
        import traceback
        traceback.print_exc()
        return []

# Process trades to identify open and closed positions
def process_trades(trades):
    """
    Process trades to identify open and closed positions.
    
    This function takes a list of trades and processes them to identify:
    1. Open positions (trades with orderStatus 'OPEN')
    2. Closed positions (matching CLOSED and FILLED trades)
    
    For closed positions, it attempts to find the matching entry trade (CLOSED)
    for each exit trade (FILLED) based on symbol, price, and chronological order.
    """
    # Parse additionalInfo JSON strings
    for trade in trades:
        if trade['additionalInfo']:
            try:
                trade['additionalInfo'] = json.loads(trade['additionalInfo'])
            except:
                trade['additionalInfo'] = {}
        
        # Parse datetime for comparison purposes
        if 'executionTime' in trade and trade['executionTime']:
            try:
                trade['_datetime'] = parse_datetime(trade['executionTime'])
            except:
                trade['_datetime'] = None
    
    # 1. Extract open positions
    open_positions = [
        {
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
    
    # 2. Group trades by symbol and status for efficient processing
    closed_trades = {}  # Symbol -> list of CLOSED trades
    filled_trades = []  # List of FILLED trades with additionalInfo
    
    for trade in trades:
        if trade['orderStatus'] == 'CLOSED':
            symbol = trade['symbol']
            if symbol not in closed_trades:
                closed_trades[symbol] = []
            closed_trades[symbol].append(trade)
        elif (trade['orderStatus'] == 'FILLED' and 
              trade['additionalInfo'] and 
              isinstance(trade['additionalInfo'], dict) and
              'entry_price' in trade['additionalInfo'] and 
              'exit_price' in trade['additionalInfo']):
            filled_trades.append(trade)
    
    # 디버깅: 심볼별로 분류된 거래 수 출력
    for symbol, trades_list in closed_trades.items():
        print(f"심볼 {symbol}의 CLOSED 거래 수: {len(trades_list)}")
    print(f"FILLED 거래 수: {len(filled_trades)}")
    
    # 3. Process closed positions
    closed_positions = []
    
    for exit_trade in filled_trades:
        symbol = exit_trade['symbol']
        entry_price = exit_trade['additionalInfo']['entry_price']
        exit_price = exit_trade['additionalInfo']['exit_price']
        
        # 디버깅: 현재 처리 중인 거래 정보 출력
        print(f"처리 중: {symbol} 종료 거래 - 진입가: {entry_price}, 청산가: {exit_price}, 시간: {exit_trade['executionTime']}")
        
        # Find matching entry trade for this exit
        best_match = None
        min_time_diff = float('inf')
        
        if symbol in closed_trades:
            # Look through all CLOSED trades for this symbol
            for entry_trade in closed_trades[symbol]:
                # Check price match within tolerance
                if abs(float(entry_trade['price']) - float(entry_price)) < 0.01:
                    # Always prefer matching by eventId if available
                    if entry_trade['eventId'] and exit_trade['eventId'] and entry_trade['eventId'] == exit_trade['eventId']:
                        best_match = entry_trade
                        print(f"이벤트 ID 일치: {entry_trade['eventId']}")
                        break
                    
                    # Check chronological order (entry before exit)
                    if (entry_trade['_datetime'] and exit_trade['_datetime'] and
                        entry_trade['_datetime'] < exit_trade['_datetime']):
                        # Calculate time difference to find closest match
                        time_diff = (exit_trade['_datetime'] - entry_trade['_datetime']).total_seconds()
                        if time_diff < min_time_diff:
                            min_time_diff = time_diff
                            best_match = entry_trade
                            print(f"시간 기반 매칭: 진입 {entry_trade['executionTime']} -> 청산 {exit_trade['executionTime']}")
        
        # Create closed position with matched entry or fallback
        position = {
            'symbol': symbol,
            'side': exit_trade['side'],
            'positionType': exit_trade['positionType'],
            'quantity': exit_trade['quantity'],
            'leverage': exit_trade['leverage'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': exit_trade['pnl'],
            'exit_time': exit_trade['executionTime']
        }
        
        if best_match:
            position['entry_time'] = best_match['executionTime']
            print(f"매칭 성공: {symbol} 진입시간 {best_match['executionTime']} -> 청산시간 {exit_trade['executionTime']}")
        else:
            # No match found, use exit_time as fallback
            position['entry_time'] = exit_trade['executionTime']
            print(f"매칭 실패: 매칭되는 {symbol}의 CLOSED 거래를 찾지 못함. 대체 시간 사용")
        
        closed_positions.append(position)
    
    return open_positions, closed_positions

def parse_datetime(dt_str):
    """
    Parse a datetime string in various formats to a datetime object.
    
    Tries multiple formats and returns None if parsing fails.
    """
    if not dt_str:
        return None
    
    # Try common datetime formats
    formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S.%f'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    # Try ISO format as last resort
    try:
        return datetime.fromisoformat(dt_str.replace(' ', 'T'))
    except ValueError:
        return None
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
    print(f"\n============ 심볼 필터링: {symbol} ============")
    trades = get_trades_by_symbol(symbol)
    print(f"데이터베이스에서 검색된 {symbol} 거래 수: {len(trades)}")
    
    # 거래 상태별 개수 확인
    statuses = {}
    for trade in trades:
        status = trade['orderStatus']
        if status not in statuses:
            statuses[status] = 0
        statuses[status] += 1
    
    for status, count in statuses.items():
        print(f"상태 '{status}'의 거래: {count}개")
    
    open_positions, closed_positions = process_trades(trades)
    print(f"처리 결과: 오픈 포지션 {len(open_positions)}개, 클로즈 포지션 {len(closed_positions)}개")
    print(f"============ 심볼 {symbol} 처리 완료 ============\n")
    
    return jsonify({
        'open_positions': open_positions,
        'closed_positions': closed_positions
    })

@app.route('/api/trades')
def api_all_trades():
    print("\n============ 전체 거래 검색 ============")
    trades = get_all_trades()
    print(f"데이터베이스에서 검색된 전체 거래 수: {len(trades)}")
    
    # 심볼별 거래 개수 확인
    symbols = {}
    for trade in trades:
        symbol = trade['symbol']
        if symbol not in symbols:
            symbols[symbol] = 0
        symbols[symbol] += 1
    
    for symbol, count in symbols.items():
        print(f"심볼 '{symbol}'의 거래: {count}개")
    
    open_positions, closed_positions = process_trades(trades)
    print(f"처리 결과: 오픈 포지션 {len(open_positions)}개, 클로즈 포지션 {len(closed_positions)}개")
    print("============ 전체 거래 처리 완료 ============\n")
    
    return jsonify({
        'open_positions': open_positions,
        'closed_positions': closed_positions
    })

@app.route('/api/pnl-summary')
def api_pnl_summary():
    pnl_data = get_symbol_pnl_summary()
    return jsonify(pnl_data)

if __name__ == '__main__':
    try:
        # 모든 네트워크 인터페이스(0.0.0.0)에 바인딩하여 외부에서도 접속 가능하게 함
        print("서버를 시작합니다. http://127.0.0.1:5000 또는 http://localhost:5000 에서 접속하세요.")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"서버 시작 중 오류가 발생했습니다: {e}")