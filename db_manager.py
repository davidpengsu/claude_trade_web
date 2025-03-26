import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime

class DatabaseManager:
    """
    Database management class for MySQL operations
    """
    def __init__(self, config_file=None, config_dict=None):
        """
        Initialize with either a config file path or a config dictionary
        """
        if config_file:
            with open(config_file, 'r') as file:
                self.config = json.load(file)
        elif config_dict:
            self.config = config_dict
        else:
            raise ValueError("Either config_file or config_dict must be provided")
    
    def get_connection(self):
        """
        Create and return a database connection
        """
        try:
            conn = mysql.connector.connect(
                host=self.config["host"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                port=self.config["port"]
            )
            return conn
        except Error as e:
            print(f"Error connecting to database: {e}")
            return None
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Tuple[bool, Any]:
        """
        Execute a query with optional parameters
        
        Args:
            query: SQL query string
            params: Parameters for the query
            fetch: Whether to fetch results or not
            
        Returns:
            Tuple of (success, result)
                - If fetch=True, result is the query result
                - If fetch=False, result is the last insert ID
        """
        connection = self.get_connection()
        if not connection:
            return False, "Failed to connect to database"
        
        cursor = connection.cursor(dictionary=True)
        result = None
        success = False
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                result = cursor.fetchall()
            else:
                connection.commit()
                result = cursor.lastrowid
            
            success = True
        except Error as e:
            print(f"Error executing query: {e}")
            result = str(e)
        finally:
            cursor.close()
            connection.close()
        
        return success, result
    
    def get_latest_trades(self, limit: int = 10) -> List[Dict]:
        """
        Get the latest trades from all symbols
        """
        query = """
            SELECT * FROM trades
            ORDER BY executionTime DESC
            LIMIT %s
        """
        success, result = self.execute_query(query, (limit,))
        return result if success else []
    
    def get_trades_by_symbol(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        Get trades for a specific symbol
        """
        query = """
            SELECT * FROM trades
            WHERE symbol = %s
            ORDER BY executionTime DESC
            LIMIT %s
        """
        success, result = self.execute_query(query, (symbol, limit))
        return result if success else []
    
    def get_trade_statistics(self, symbol: Optional[str] = None) -> Dict:
        """
        Get trade statistics for a symbol or all symbols
        """
        query = """
            SELECT 
                symbol, 
                COUNT(*) as trade_count,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as profitable_trades,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as loss_trades,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl
            FROM trades
            WHERE pnl IS NOT NULL
        """
        
        if symbol:
            query += " AND symbol = %s"
            query += " GROUP BY symbol"
            success, result = self.execute_query(query, (symbol,))
        else:
            query += " GROUP BY symbol"
            success, result = self.execute_query(query)
        
        # Convert to dictionary with symbol as key for easier access
        if success and result:
            if symbol:
                return result[0] if result else {}
            else:
                return {item['symbol']: item for item in result}
        return {}
    
    def get_recent_decisions(self, symbol: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Get recent decisions for a symbol or all symbols
        """
        query = """
            SELECT * FROM decision_events
        """
        
        if symbol:
            query += " WHERE eventSymbol = %s"
            query += " ORDER BY occurUtcDate DESC LIMIT %s"
            success, result = self.execute_query(query, (symbol, limit))
        else:
            query += " ORDER BY occurUtcDate DESC LIMIT %s"
            success, result = self.execute_query(query, (limit,))
        
        return result if success else []
    
    def get_execution_events(self, symbol: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Get execution events for a symbol or all symbols
        """
        query = """
            SELECT * FROM execution_events
        """
        
        if symbol:
            query += " WHERE symbol = %s"
            query += " ORDER BY requestTime DESC LIMIT %s"
            success, result = self.execute_query(query, (symbol, limit))
        else:
            query += " ORDER BY requestTime DESC LIMIT %s"
            success, result = self.execute_query(query, (limit,))
        
        return result if success else []
    
    def get_table_data(self, table_name: str, filter_column: Optional[str] = None, 
                      filter_value: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get data from any table with optional filtering
        """
        # Validate table name to prevent SQL injection
        valid_tables = ['trades', 'decision_events', 'execution_events']
        if table_name not in valid_tables:
            return []
        
        query = f"SELECT * FROM {table_name}"
        
        params = []
        if filter_column and filter_value:
            query += f" WHERE {filter_column} LIKE %s"
            params.append(f"%{filter_value}%")
        
        query += " ORDER BY createdAt DESC LIMIT %s"
        params.append(limit)
        
        success, result = self.execute_query(query, tuple(params))
        return result if success else []
    
    def get_monthly_statistics(self, symbol: str) -> List[Dict]:
        """
        Get monthly trading statistics for a symbol
        """
        query = """
            SELECT 
                DATE_FORMAT(executionTime, '%Y-%m') as month,
                COUNT(*) as trade_count,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as profitable_trades,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as loss_trades,
                SUM(pnl) as total_pnl
            FROM trades
            WHERE symbol = %s AND pnl IS NOT NULL
            GROUP BY DATE_FORMAT(executionTime, '%Y-%m')
            ORDER BY month DESC
            LIMIT 6
        """
        
        success, result = self.execute_query(query, (symbol,))
        return result if success else []
