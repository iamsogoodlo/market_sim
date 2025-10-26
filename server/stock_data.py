#!/usr/bin/env python3
"""
Stock data service using OpenBB to fetch NASDAQ stock information
"""

import json
import sys
from openbb import obb

def get_nasdaq_stocks(limit=100):
    """
    Fetch list of NASDAQ stocks with their current prices
    Returns: List of dicts with symbol, name, and price
    """
    try:
        # Get NASDAQ 100 stocks (major tech stocks)
        # Using yfinance provider which doesn't require API key
        result = obb.equity.screener.screen(
            provider="yfinance",
            exchange="NASDAQ",
            limit=limit
        )

        stocks = []
        if result and hasattr(result, 'results'):
            for stock in result.results[:limit]:
                stocks.append({
                    "symbol": stock.symbol if hasattr(stock, 'symbol') else "",
                    "name": stock.name if hasattr(stock, 'name') else stock.symbol,
                    "price": float(stock.price) if hasattr(stock, 'price') else 100.0,
                    "volume": int(stock.volume) if hasattr(stock, 'volume') else 0
                })

        return stocks
    except Exception as e:
        print(f"Error fetching NASDAQ stocks: {e}", file=sys.stderr)
        # Return some default stocks if API fails
        return get_default_stocks()

def get_default_stocks():
    """
    Return a curated list of major NASDAQ stocks as fallback
    """
    return [
        {"symbol": "AAPL", "name": "Apple Inc.", "price": 175.0, "volume": 50000000},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "price": 380.0, "volume": 25000000},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": 140.0, "volume": 20000000},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "price": 145.0, "volume": 30000000},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "price": 480.0, "volume": 40000000},
        {"symbol": "META", "name": "Meta Platforms Inc.", "price": 350.0, "volume": 15000000},
        {"symbol": "TSLA", "name": "Tesla, Inc.", "price": 240.0, "volume": 100000000},
        {"symbol": "NFLX", "name": "Netflix, Inc.", "price": 450.0, "volume": 5000000},
        {"symbol": "INTC", "name": "Intel Corporation", "price": 45.0, "volume": 35000000},
        {"symbol": "AMD", "name": "Advanced Micro Devices", "price": 120.0, "volume": 50000000},
    ]

def get_stock_quote(symbol):
    """
    Get current quote for a specific stock symbol
    """
    try:
        quote = obb.equity.price.quote(symbol=symbol, provider="yfinance")
        if quote and hasattr(quote, 'results') and len(quote.results) > 0:
            data = quote.results[0]
            return {
                "symbol": symbol,
                "price": float(data.last_price) if hasattr(data, 'last_price') else 100.0,
                "bid": float(data.bid) if hasattr(data, 'bid') else None,
                "ask": float(data.ask) if hasattr(data, 'ask') else None,
                "volume": int(data.volume) if hasattr(data, 'volume') else 0,
            }
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {e}", file=sys.stderr)

    # Fallback
    defaults = {s["symbol"]: s for s in get_default_stocks()}
    return defaults.get(symbol, {"symbol": symbol, "price": 100.0, "bid": None, "ask": None, "volume": 0})

def get_historical_data(symbol, period="1mo"):
    """
    Get historical price data for charting
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    try:
        historical = obb.equity.price.historical(
            symbol=symbol,
            provider="yfinance",
            interval="1d",
            period=period
        )

        if historical and hasattr(historical, 'results'):
            data = []
            for row in historical.results:
                data.append({
                    "date": str(row.date),
                    "open": float(row.open),
                    "high": float(row.high),
                    "low": float(row.low),
                    "close": float(row.close),
                    "volume": int(row.volume) if hasattr(row, 'volume') else 0
                })
            return data
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {e}", file=sys.stderr)

    return []

def search_stocks(query):
    """
    Search for stocks by symbol or name
    """
    try:
        # Search using yfinance
        results = obb.equity.search(query=query, provider="yfinance")

        stocks = []
        if results and hasattr(results, 'results'):
            for stock in results.results[:10]:
                stocks.append({
                    "symbol": stock.symbol if hasattr(stock, 'symbol') else "",
                    "name": stock.name if hasattr(stock, 'name') else ""
                })
        return stocks
    except Exception as e:
        print(f"Error searching stocks: {e}", file=sys.stderr)
        # Fallback: filter default stocks
        defaults = get_default_stocks()
        query_upper = query.upper()
        return [
            {"symbol": s["symbol"], "name": s["name"]}
            for s in defaults
            if query_upper in s["symbol"] or query_upper in s["name"].upper()
        ]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            # Get list of stocks
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            stocks = get_nasdaq_stocks(limit)
            print(json.dumps(stocks))

        elif command == "quote":
            # Get quote for specific symbol
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Symbol required"}))
                sys.exit(1)
            symbol = sys.argv[2]
            quote = get_stock_quote(symbol)
            print(json.dumps(quote))

        elif command == "historical":
            # Get historical data
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Symbol required"}))
                sys.exit(1)
            symbol = sys.argv[2]
            period = sys.argv[3] if len(sys.argv) > 3 else "1mo"
            data = get_historical_data(symbol, period)
            print(json.dumps(data))

        elif command == "search":
            # Search for stocks
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Query required"}))
                sys.exit(1)
            query = sys.argv[2]
            results = search_stocks(query)
            print(json.dumps(results))

        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
            sys.exit(1)
    else:
        # Default: return top 10 stocks
        stocks = get_default_stocks()
        print(json.dumps(stocks))
