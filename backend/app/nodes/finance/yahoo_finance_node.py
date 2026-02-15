"""
Yahoo Finance Node - Studio Standard (Universal Method)
Batch 112: Advanced Search & Knowledge
"""
from typing import Any, Dict, Optional, List
import yfinance as yf
from ...base import BaseNode
from ...registry import register_node

@register_node("yahoo_finance_node")
class YahooFinanceNode(BaseNode):
    """
    Access financial data and market information from Yahoo! Finance.
    """
    node_type = "yahoo_finance_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = []

    inputs = {
        "symbol": {
            "type": "string",
            "required": True,
            "description": "The stock symbol to retrieve data for (e.g., AAPL, GOOG)"
        },
        "method": {
            "type": "dropdown",
            "default": "get_info",
            "options": [
                "get_info", "get_news", "get_actions", "get_analysis", 
                "get_balance_sheet", "get_calendar", "get_cashflow", 
                "get_institutional_holders", "get_recommendations", 
                "get_sustainability", "get_major_holders", "get_dividends",
                "get_splits", "get_shares", "get_fast_info", "get_income_stmt"
            ],
            "description": "The type of data to retrieve"
        },
        "num_news": {
            "type": "number",
            "default": 5,
            "optional": True,
            "description": "Number of news articles to retrieve (if method is get_news)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            symbol = self.get_config("symbol") or str(input_data)
            method = self.get_config("method", "get_info")
            num_news = int(self.get_config("num_news", 5))

            ticker = yf.Ticker(symbol)
            
            if method == "get_info":
                data = ticker.info
            elif method == "get_news":
                data = ticker.news[:num_news]
            else:
                # Dynamically call the method on the ticker object
                func = getattr(ticker, method, None)
                if not func:
                    return {"status": "error", "error": f"Method {method} not found on ticker"}
                
                # Check if it's a property or a method
                if callable(func):
                    data = func()
                else:
                    data = func

            # Handle non-serializable data (like DataFrames)
            if hasattr(data, 'to_dict'):
                 data = data.to_dict()

            return {
                "status": "success", 
                "data": {
                    "result": data
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Yahoo Finance Failed: {str(e)}"}
