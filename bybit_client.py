import time
import hmac
import hashlib
import requests
from typing import Dict, List, Any, Optional

class BybitClient:
    """
    Bybit API 클라이언트
    """
    def __init__(self, api_key: str, api_secret: str):
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
    
    def _send_post_request(self, endpoint: str, params: Dict = None, auth: bool = False) -> Dict:
        """POST 요청 전송"""
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
        
        response = requests.post(url, json=params if not auth else None, params=params if auth else None, headers=headers)
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
    
    def get_position_info(self, symbol: str) -> Dict:
        """
        포지션 정보 조회
        
        Args:
            symbol: 심볼 (예: "BTCUSDT")
        
        Returns:
            포지션 정보
        """
        params = {
            "category": "linear",
            "symbol": symbol
        }
        
        response = self._send_get_request("/v5/position/list", params, True)
        
        if response.get("retCode") == 0:
            positions = response.get("result", {}).get("list", [])
            if positions:
                position = positions[0]
                size = self.safe_float_conversion(position.get("size", 0))
                
                if size > 0:
                    return {
                        "exists": True,
                        "size": size,
                        "side": position.get("side", ""),
                        "entry_price": self.safe_float_conversion(position.get("entryPrice", 0)),
                        "leverage": self.safe_float_conversion(position.get("leverage", 0)),
                        "unrealized_pnl": self.safe_float_conversion(position.get("unrealisedPnl", 0)),
                        "take_profit": self.safe_float_conversion(position.get("takeProfit", 0)),
                        "stop_loss": self.safe_float_conversion(position.get("stopLoss", 0)),
                        "position_type": "long" if position.get("side") == "Buy" else "short"
                    }
        
        return {"exists": False}
    
    def get_market_price(self, symbol: str) -> float:
        """
        현재 시장 가격 조회
        
        Args:
            symbol: 심볼 (예: "BTCUSDT")
        
        Returns:
            현재 가격
        """
        params = {
            "category": "spot",
            "symbol": symbol
        }
        
        response = self._send_get_request("/v5/market/tickers", params)
        
        if response.get("retCode") == 0:
            tickers = response.get("result", {}).get("list", [])
            if tickers:
                return self.safe_float_conversion(tickers[0].get("lastPrice", 0))
        
        return 0.0
