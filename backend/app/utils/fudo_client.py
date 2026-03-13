import requests
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any


class FudoClient:
    """Client for interacting with Fudo API"""
    
    AUTH_URL = "https://auth.fu.do/api"
    BASE_URL = "https://api.fu.do/v1alpha1"
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or os.getenv('FUDO_API_KEY')
        self.api_secret = api_secret or os.getenv('FUDO_API_SECRET')
        self.token = None
        self.token_expiration = None
        
        if not self.api_key or not self.api_secret:
            raise ValueError("FUDO_API_KEY and FUDO_API_SECRET must be set in environment variables")
    
    def _authenticate(self) -> str:
        """Authenticate with Fudo API and get access token"""
        payload = {
            "apiKey": self.api_key,
            "apiSecret": self.api_secret
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.AUTH_URL, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get('token')
            exp_timestamp = data.get('exp')
            
            if exp_timestamp:
                self.token_expiration = datetime.fromtimestamp(exp_timestamp)
            else:
                self.token_expiration = datetime.now() + timedelta(hours=23)
            
            return self.token
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error authenticating with Fudo API: {str(e)}")
    
    def _get_valid_token(self) -> str:
        """Get a valid token, refreshing if necessary"""
        if not self.token or not self.token_expiration:
            return self._authenticate()
        
        if datetime.now() >= self.token_expiration - timedelta(minutes=5):
            return self._authenticate()
        
        return self.token
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Fudo API"""
        token = self._get_valid_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error making request to Fudo API: {str(e)}")
    
    def get_sales(self, 
                  page_size: int = 500, 
                  page_number: int = 1,
                  filters: Optional[Dict] = None) -> Dict:
        """
        Get sales from Fudo API
        
        Args:
            page_size: Number of items per page (max 500)
            page_number: Page number to retrieve
            filters: Optional filters (e.g., {'closedAt': 'and(gte.2024-01-01T00:00:00Z,lte.2024-01-31T23:59:59Z)'})
        
        Returns:
            Dictionary with sales data
        """
        params = {
            'page[size]': min(page_size, 500),
            'page[number]': page_number
        }
        
        if filters:
            for key, value in filters.items():
                params[f'filter[{key}]'] = value
        
        return self._make_request('/sales', params)
    
    def get_all_sales(self, 
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> List[Dict]:
        """
        Get all sales from Fudo API with pagination
        
        Args:
            start_date: Start date in ISO format (e.g., '2024-01-01T00:00:00Z')
            end_date: End date in ISO format (e.g., '2024-01-31T23:59:59Z')
        
        Returns:
            List of all sales
        """
        all_sales = []
        page_number = 1
        page_size = 500
        
        # Use API date filters if provided
        filters = {}
        if start_date and end_date:
            # Format: and(gte.2024-01-01T00:00:00Z,lte.2024-01-31T23:59:59Z)
            filters['createdAt'] = f'and(gte.{start_date},lte.{end_date})'
        elif start_date:
            # Format: gte.2024-01-01T00:00:00Z
            filters['createdAt'] = f'gte.{start_date}'
        elif end_date:
            # Format: lte.2024-01-31T23:59:59Z
            filters['createdAt'] = f'lte.{end_date}'
        
        while True:
            response = self.get_sales(page_size=page_size, page_number=page_number, filters=filters)
            sales_data = response.get('data', [])
            
            if not sales_data:
                break
            
            all_sales.extend(sales_data)
            
            if len(sales_data) < page_size:
                break
            
            page_number += 1
        
        return all_sales
    
    def get_expenses(self, 
                     page_size: int = 500, 
                     page_number: int = 1,
                     filters: Optional[Dict] = None) -> Dict:
        """
        Get expenses from Fudo API
        
        Args:
            page_size: Number of items per page (max 500)
            page_number: Page number to retrieve
            filters: Optional filters (e.g., {'date': 'and(gte.2024-01-01,lte.2024-01-31)'})
        
        Returns:
            Dictionary with expenses data
        """
        params = {
            'page[size]': min(page_size, 500),
            'page[number]': page_number,
            'include': 'provider,expenseCategory,paymentMethod,user,receiptType,commercialDocument'
        }
        
        if filters:
            for key, value in filters.items():
                params[f'filter[{key}]'] = value
        
        return self._make_request('/expenses', params)
    
    def get_all_expenses(self, 
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> List[Dict]:
        """
        Get all expenses from Fudo API with pagination
        
        Args:
            start_date: Start date in format YYYY-MM-DD
            end_date: End date in format YYYY-MM-DD
        
        Returns:
            List of all expenses
        """
        all_expenses = []
        page_number = 1
        page_size = 500
        
        # Use API date filters if provided
        filters = {}
        if start_date and end_date:
            # Format: and(gte.2024-01-01,lte.2024-01-31)
            filters['date'] = f'and(gte.{start_date},lte.{end_date})'
        elif start_date:
            # Format: gte.2024-01-01
            filters['date'] = f'gte.{start_date}'
        elif end_date:
            # Format: lte.2024-01-31
            filters['date'] = f'lte.{end_date}'
        
        while True:
            response = self.get_expenses(page_size=page_size, page_number=page_number, filters=filters)
            expenses_data = response.get('data', [])
            
            if not expenses_data:
                break
            
            all_expenses.extend(expenses_data)
            
            if len(expenses_data) < page_size:
                break
            
            page_number += 1
        
        return all_expenses
    
    def get_expense_categories(self, page_size: int = 500, page_number: int = 1) -> Dict:
        """Get expense categories from Fudo API"""
        params = {
            'page[size]': min(page_size, 500),
            'page[number]': page_number,
            'fields[expenseCategory]': 'active,financialCategory,name,parentCategory'
        }
        return self._make_request('/expense-categories', params)
    
    def get_payment_methods(self, page_size: int = 500, page_number: int = 1) -> Dict:
        """Get payment methods from Fudo API"""
        params = {
            'page[size]': min(page_size, 500),
            'page[number]': page_number
        }
        return self._make_request('/payment-methods', params)
