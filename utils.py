import json
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Any, Optional

def load_config(config_file: str) -> Dict:
    """Load configuration from a JSON file"""
    try:
        with open(config_file, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def save_config(config_file: str, config_data: Dict) -> bool:
    """Save configuration to a JSON file"""
    try:
        with open(config_file, 'w') as file:
            json.dump(config_data, file, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config file {config_file}: {e}")
        return False

def parse_json_field(json_str: str) -> Dict:
    """Parse a JSON string and return a dictionary"""
    if not json_str:
        return {}
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {}

def format_currency(value: float, decimals: int = 2) -> str:
    """Format a value as currency with specified decimal places"""
    if value is None:
        return "$0.00"
    return f"${value:.{decimals}f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format a value as percentage with specified decimal places"""
    if value is None:
        return "0.00%"
    return f"{value:.{decimals}f}%"

def calculate_profit_loss(initial: float, current: float) -> Dict[str, float]:
    """Calculate profit/loss and profit/loss percentage"""
    if initial <= 0:
        return {
            "profit": 0.0,
            "profit_percentage": 0.0
        }
    
    profit = current - initial
    profit_percentage = (profit / initial) * 100
    
    return {
        "profit": profit,
        "profit_percentage": profit_percentage
    }

def generate_date_range(days: int = 30) -> List[str]:
    """Generate a list of dates for the last n days"""
    dates = []
    today = datetime.now()
    
    for i in range(days, 0, -1):
        date = today - timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
    
    return dates

def aggregate_daily_data(trades: List[Dict], days: int = 30) -> pd.DataFrame:
    """Aggregate trade data by day for the last n days"""
    # Create a date range
    date_range = generate_date_range(days)
    
    # Convert to DataFrame
    try:
        df = pd.DataFrame(trades)
        
        # Convert executionTime to datetime if it's not already
        if 'executionTime' in df.columns:
            df['executionTime'] = pd.to_datetime(df['executionTime'])
            
            # Extract date
            df['date'] = df['executionTime'].dt.strftime('%Y-%m-%d')
            
            # Create a date range DataFrame
            date_df = pd.DataFrame({'date': date_range})
            
            # Group by date and calculate stats
            daily_stats = df.groupby('date').agg({
                'pnl': ['sum', 'count', 'mean'],
                'tradeId': 'count'
            }).reset_index()
            
            # Rename columns
            daily_stats.columns = ['date', 'pnl_sum', 'pnl_count', 'pnl_mean', 'trade_count']
            
            # Merge with date range to ensure all dates are included
            result = pd.merge(date_df, daily_stats, on='date', how='left').fillna(0)
            
            # Calculate cumulative PnL
            result['cumulative_pnl'] = result['pnl_sum'].cumsum()
            
            return result
        
        return pd.DataFrame()
    except Exception as e:
        print(f"Error aggregating data: {e}")
        return pd.DataFrame()

def get_win_rate(stats: Dict) -> float:
    """Calculate win rate from trade statistics"""
    if not stats:
        return 0.0
    
    profitable_trades = stats.get('profitable_trades', 0)
    trade_count = stats.get('trade_count', 0)
    
    if trade_count > 0:
        return (profitable_trades / trade_count) * 100
    
    return 0.0

def safe_json_dumps(obj: Any) -> str:
    """Safely convert an object to JSON string, handling datetime objects"""
    def default_serializer(o):
        if isinstance(o, (datetime, pd.Timestamp)):
            return o.isoformat()
        return str(o)
    
    try:
        return json.dumps(obj, default=default_serializer)
    except Exception as e:
        print(f"Error serializing to JSON: {e}")
        return "{}"
