import requests
from datetime import datetime, timedelta
from flask import current_app
from typing import Optional, Dict, List, Any

class FudoAPIClient:
    def __init__(self):
        self.base_url = None
        self.api_key = None
        self.api_secret = None
        self.auth_url = "https://auth.fu.do/api"
        self._token = None
        self._token_expiry = None
    
    def _load_config(self):
        if not self.base_url:
            self.base_url = current_app.config.get('FUDO_API_BASE_URL', 'https://api.fu.do/v1alpha1')
            self.api_key = current_app.config.get('FUDO_CLIENT_ID')
            self.api_secret = current_app.config.get('FUDO_CLIENT_SECRET')
    
    def _is_token_valid(self) -> bool:
        if not self._token or not self._token_expiry:
            return False
        return datetime.now() < self._token_expiry - timedelta(minutes=5)
    
    def _authenticate(self) -> str:
        self._load_config()
        
        if not self.api_key or not self.api_secret:
            raise ValueError("FUdo API credentials not configured")
        
        if self._is_token_valid():
            return self._token
        
        try:
            response = requests.post(
                self.auth_url,
                json={
                    "apiKey": self.api_key,
                    "apiSecret": self.api_secret
                },
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            self._token = data.get('token')
            exp_timestamp = data.get('exp')
            
            if exp_timestamp:
                self._token_expiry = datetime.fromtimestamp(exp_timestamp)
            else:
                self._token_expiry = datetime.now() + timedelta(hours=23)
            
            return self._token
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to authenticate with FUdo API: {str(e)}")
    
    def _get_headers(self) -> Dict[str, str]:
        token = self._authenticate()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        self._load_config()
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"FUdo API request failed: {str(e)}")
    
    def get_sales(self, page_size: int = 500, page_number: int = 1, 
                  filters: Optional[Dict] = None) -> Dict[str, Any]:
        params = {
            'page[size]': page_size,
            'page[number]': page_number
        }
        
        if filters:
            for key, value in filters.items():
                params[f'filter[{key}]'] = value
        
        return self._make_request('GET', '/sales', params=params)
    
    def get_sale(self, sale_id: str, include: Optional[List[str]] = None) -> Dict[str, Any]:
        params = {}
        if include:
            params['include'] = ','.join(include)
        
        return self._make_request('GET', f'/sales/{sale_id}', params=params)
    
    def create_sale(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request('POST', '/sales', data=sale_data)
    
    def get_expenses(self, page_size: int = 500, page_number: int = 1,
                     filters: Optional[Dict] = None) -> Dict[str, Any]:
        params = {
            'page[size]': page_size,
            'page[number]': page_number
        }
        
        if filters:
            for key, value in filters.items():
                params[f'filter[{key}]'] = value
        
        return self._make_request('GET', '/expenses', params=params)
    
    def get_expense(self, expense_id: str) -> Dict[str, Any]:
        return self._make_request('GET', f'/expenses/{expense_id}')
    
    def create_expense(self, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request('POST', '/expenses', data=expense_data)
    
    def update_expense(self, expense_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request('PATCH', f'/expenses/{expense_id}', data=expense_data)
    
    def get_expense_categories(self, page_size: int = 500, page_number: int = 1) -> Dict[str, Any]:
        params = {
            'page[size]': page_size,
            'page[number]': page_number
        }
        return self._make_request('GET', '/expense-categories', params=params)
    
    def get_payments(self, page_size: int = 500, page_number: int = 1,
                     filters: Optional[Dict] = None) -> Dict[str, Any]:
        params = {
            'page[size]': page_size,
            'page[number]': page_number
        }
        
        if filters:
            for key, value in filters.items():
                params[f'filter[{key}]'] = value
        
        return self._make_request('GET', '/payments', params=params)
    
    def get_payment_methods(self, page_size: int = 500, page_number: int = 1) -> Dict[str, Any]:
        params = {
            'page[size]': page_size,
            'page[number]': page_number
        }
        return self._make_request('GET', '/payment-methods', params=params)
