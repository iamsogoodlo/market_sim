#!/usr/bin/env python3
"""
Redis-based caching layer for market data
Provides sub-second access to stock quotes, historical data, and search results
"""

import json
import redis
from typing import Optional, List, Dict, Any
from datetime import timedelta
import stock_data

# Redis connection
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
    protocol=3
)

# Cache TTLs
QUOTE_TTL = 5  # 5 seconds for real-time quotes
HISTORICAL_TTL = 3600  # 1 hour for historical data
SEARCH_TTL = 86400  # 24 hours for search results
STOCK_LIST_TTL = 3600  # 1 hour for stock lists

def cache_key(prefix: str, *args) -> str:
    """Generate cache key with prefix and arguments"""
    return f"market:{prefix}:{':'.join(str(arg) for arg in args)}"

def get_stock_quote_cached(symbol: str) -> Dict[str, Any]:
    """
    Get stock quote with Redis caching
    Cache hit: <1ms, Cache miss: ~100-200ms
    """
    key = cache_key("quote", symbol.upper())

    # Try cache first
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    # Cache miss - fetch from OpenBB
    quote = stock_data.get_stock_quote(symbol)

    # Cache for 5 seconds
    redis_client.setex(
        key,
        QUOTE_TTL,
        json.dumps(quote)
    )

    return quote

def get_historical_data_cached(symbol: str, period: str = "1mo") -> List[Dict[str, Any]]:
    """
    Get historical data with Redis caching
    Cache hit: <1ms, Cache miss: ~500ms-1s
    """
    key = cache_key("historical", symbol.upper(), period)

    # Try cache first
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    # Cache miss - fetch from OpenBB
    data = stock_data.get_historical_data(symbol, period)

    # Cache for 1 hour
    redis_client.setex(
        key,
        HISTORICAL_TTL,
        json.dumps(data)
    )

    return data

def search_stocks_cached(query: str) -> List[Dict[str, str]]:
    """
    Search stocks with Redis caching
    Cache hit: <1ms, Cache miss: ~200-300ms
    """
    key = cache_key("search", query.lower())

    # Try cache first
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    # Cache miss - search via OpenBB
    results = stock_data.search_stocks(query)

    # Cache for 24 hours
    redis_client.setex(
        key,
        SEARCH_TTL,
        json.dumps(results)
    )

    return results

def get_nasdaq_stocks_cached(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get NASDAQ stocks list with Redis caching
    Cache hit: <1ms, Cache miss: ~1-2s
    """
    key = cache_key("stocks", "nasdaq", limit)

    # Try cache first
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    # Cache miss - fetch from OpenBB
    stocks = stock_data.get_nasdaq_stocks(limit)

    # Cache for 1 hour
    redis_client.setex(
        key,
        STOCK_LIST_TTL,
        json.dumps(stocks)
    )

    return stocks

def invalidate_quote(symbol: str):
    """Invalidate cached quote for a symbol"""
    key = cache_key("quote", symbol.upper())
    redis_client.delete(key)

def invalidate_all():
    """Clear all market data cache"""
    keys = redis_client.keys("market:*")
    if keys:
        redis_client.delete(*keys)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    info = redis_client.info("stats")
    return {
        "total_keys": redis_client.dbsize(),
        "hits": info.get("keyspace_hits", 0),
        "misses": info.get("keyspace_misses", 0),
        "hit_rate": (
            info.get("keyspace_hits", 0) /
            max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
        ) * 100
    }

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "quote":
            symbol = sys.argv[2] if len(sys.argv) > 2 else "AAPL"
            quote = get_stock_quote_cached(symbol)
            print(json.dumps(quote))

        elif command == "historical":
            symbol = sys.argv[2] if len(sys.argv) > 2 else "AAPL"
            period = sys.argv[3] if len(sys.argv) > 3 else "1mo"
            data = get_historical_data_cached(symbol, period)
            print(json.dumps(data))

        elif command == "search":
            query = sys.argv[2] if len(sys.argv) > 2 else "AAPL"
            results = search_stocks_cached(query)
            print(json.dumps(results))

        elif command == "list":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            stocks = get_nasdaq_stocks_cached(limit)
            print(json.dumps(stocks))

        elif command == "stats":
            stats = get_cache_stats()
            print(json.dumps(stats, indent=2))

        elif command == "clear":
            invalidate_all()
            print(json.dumps({"status": "ok", "message": "Cache cleared"}))

        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
    else:
        # Test cache
        print("Testing Redis cache...")
        stats = get_cache_stats()
        print(f"Cache stats: {json.dumps(stats, indent=2)}")
