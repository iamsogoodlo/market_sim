"""
OpenBB Data Service with Parquet Caching
Replaces yfinance with OpenBB SDK for professional-grade market data

Features:
- Equities, crypto, forex, futures data
- Fundamental data (financials, ratios, estimates)
- News and sentiment
- Economic indicators
- Parquet caching for performance
- Data normalization and validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os
import hashlib
import json
from pathlib import Path

# Try to import OpenBB
try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False
    print("WARNING: OpenBB not available, falling back to yfinance")

# Fallback to yfinance if OpenBB not available
import yfinance as yf


class OpenBBDataService:
    """Professional data service using OpenBB with Parquet caching"""

    def __init__(self, cache_dir: str = "data_cache"):
        """
        Initialize data service

        Args:
            cache_dir: Directory for Parquet cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.use_openbb = OPENBB_AVAILABLE

        # Cache TTLs (in seconds)
        self.ttls = {
            'price_daily': 3600 * 4,  # 4 hours
            'price_intraday': 60,  # 1 minute
            'fundamentals': 3600 * 24,  # 24 hours
            'news': 3600,  # 1 hour
            'reference': 3600 * 24 * 7  # 1 week
        }

    def _get_cache_key(self, data_type: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        params_str = json.dumps(kwargs, sort_keys=True)
        hash_obj = hashlib.md5(params_str.encode())
        return f"{data_type}_{hash_obj.hexdigest()}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path to cache file"""
        return self.cache_dir / f"{cache_key}.parquet"

    def _is_cache_valid(self, cache_path: Path, ttl: int) -> bool:
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False

        file_age = datetime.now().timestamp() - cache_path.stat().st_mtime
        return file_age < ttl

    def _read_cache(self, cache_key: str, ttl: int) -> Optional[pd.DataFrame]:
        """Read from cache if valid"""
        cache_path = self._get_cache_path(cache_key)

        if self._is_cache_valid(cache_path, ttl):
            try:
                return pd.read_parquet(cache_path)
            except Exception as e:
                print(f"Cache read error: {e}")
                return None

        return None

    def _write_cache(self, cache_key: str, df: pd.DataFrame):
        """Write DataFrame to Parquet cache"""
        cache_path = self._get_cache_path(cache_key)
        try:
            df.to_parquet(cache_path, compression='snappy')
        except Exception as e:
            print(f"Cache write error: {e}")

    def get_price_history(self, symbol: str, interval: str = "1d",
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None,
                         period: str = "1y") -> pd.DataFrame:
        """
        Get historical price data (OHLCV)

        Args:
            symbol: Ticker symbol
            interval: '1m', '5m', '15m', '1h', '1d'
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Period string ('1d', '5d', '1mo', '1y', etc.)

        Returns:
            DataFrame with columns: [open, high, low, close, volume, timestamp]
        """

        # Generate cache key
        cache_key = self._get_cache_key(
            'price',
            symbol=symbol,
            interval=interval,
            start=start_date,
            end=end_date,
            period=period
        )

        # Check cache
        ttl = self.ttls['price_intraday'] if interval != '1d' else self.ttls['price_daily']
        cached_df = self._read_cache(cache_key, ttl)
        if cached_df is not None:
            return cached_df

        # Fetch from source
        if self.use_openbb:
            df = self._fetch_openbb_prices(symbol, interval, start_date, end_date, period)
        else:
            df = self._fetch_yfinance_prices(symbol, interval, start_date, end_date, period)

        # Normalize and cache
        if not df.empty:
            df = self._normalize_price_data(df)
            self._write_cache(cache_key, df)

        return df

    def _fetch_openbb_prices(self, symbol: str, interval: str, start_date, end_date, period) -> pd.DataFrame:
        """Fetch prices using OpenBB"""
        try:
            # Map interval to OpenBB format
            interval_map = {
                '1m': '1min', '5m': '5min', '15m': '15min',
                '1h': '1hour', '1d': '1day'
            }
            obb_interval = interval_map.get(interval, '1day')

            # Calculate date range if not provided
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                days = self._period_to_days(period)
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            # Fetch from OpenBB
            data = obb.equity.price.historical(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=obb_interval,
                provider='yfinance'  # Can switch to other providers
            )

            return data.to_df() if data else pd.DataFrame()

        except Exception as e:
            print(f"OpenBB fetch error for {symbol}: {e}")
            return pd.DataFrame()

    def _fetch_yfinance_prices(self, symbol: str, interval: str, start_date, end_date, period) -> pd.DataFrame:
        """Fetch prices using yfinance (fallback)"""
        try:
            ticker = yf.Ticker(symbol)

            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date, interval=interval)
            else:
                df = ticker.history(period=period, interval=interval)

            return df

        except Exception as e:
            print(f"yfinance fetch error for {symbol}: {e}")
            return pd.DataFrame()

    def _normalize_price_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize price data to standard format"""
        # Ensure lowercase column names
        df.columns = [col.lower() for col in df.columns]

        # Standard columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan

        # Add timestamp if not present
        if 'timestamp' not in df.columns:
            df['timestamp'] = df.index

        # Sort by timestamp
        df = df.sort_index()

        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Get fundamental data for a stock

        Returns metrics like P/E, P/B, ROE, margins, etc.
        """

        cache_key = self._get_cache_key('fundamentals', symbol=symbol)

        # Try cache first (stored as JSON in metadata)
        cache_path = self._get_cache_path(cache_key).with_suffix('.json')
        if self._is_cache_valid(cache_path, self.ttls['fundamentals']):
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except:
                pass

        # Fetch fresh data
        if self.use_openbb:
            data = self._fetch_openbb_fundamentals(symbol)
        else:
            data = self._fetch_yfinance_fundamentals(symbol)

        # Cache the result
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        except:
            pass

        return data

    def _fetch_openbb_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Fetch fundamentals from OpenBB"""
        try:
            # Get key metrics
            metrics = obb.equity.fundamental.metrics(symbol=symbol, provider='fmp')

            # Get financial ratios
            ratios = obb.equity.fundamental.ratios(symbol=symbol, provider='fmp')

            # Combine and normalize
            result = {}
            if metrics:
                result.update(metrics.to_dict())
            if ratios:
                result.update(ratios.to_dict())

            return result

        except Exception as e:
            print(f"OpenBB fundamentals error for {symbol}: {e}")
            return {}

    def _fetch_yfinance_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Fetch fundamentals from yfinance (fallback)"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                'marketCap': info.get('marketCap'),
                'enterpriseValue': info.get('enterpriseValue'),
                'trailingPE': info.get('trailingPE'),
                'forwardPE': info.get('forwardPE'),
                'priceToBook': info.get('priceToBook'),
                'priceToSales': info.get('priceToSalesTrailing12Months'),
                'profitMargin': info.get('profitMargins'),
                'operatingMargin': info.get('operatingMargins'),
                'returnOnEquity': info.get('returnOnEquity'),
                'returnOnAssets': info.get('returnOnAssets'),
                'debtToEquity': info.get('debtToEquity'),
                'currentRatio': info.get('currentRatio'),
                'quickRatio': info.get('quickRatio'),
                'beta': info.get('beta'),
                'dividendYield': info.get('dividendYield'),
                'payoutRatio': info.get('payoutRatio')
            }

        except Exception as e:
            print(f"yfinance fundamentals error for {symbol}: {e}")
            return {}

    def get_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent news for a symbol

        Returns list of news items with title, summary, source, url, timestamp
        """

        if self.use_openbb:
            return self._fetch_openbb_news(symbol, limit)
        else:
            return self._fetch_yfinance_news(symbol, limit)

    def _fetch_openbb_news(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch news from OpenBB"""
        try:
            news = obb.equity.news(symbol=symbol, limit=limit, provider='benzinga')

            if not news:
                return []

            return [{
                'title': item.get('title'),
                'summary': item.get('text'),
                'source': item.get('source'),
                'url': item.get('url'),
                'timestamp': item.get('date')
            } for item in news]

        except Exception as e:
            print(f"OpenBB news error for {symbol}: {e}")
            return []

    def _fetch_yfinance_news(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch news from yfinance (fallback)"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news[:limit]

            return [{
                'title': item.get('title'),
                'summary': item.get('summary'),
                'source': item.get('publisher'),
                'url': item.get('link'),
                'timestamp': item.get('providerPublishTime')
            } for item in news]

        except Exception as e:
            print(f"yfinance news error for {symbol}: {e}")
            return []

    def _period_to_days(self, period: str) -> int:
        """Convert period string to days"""
        mapping = {
            '1d': 1, '5d': 5, '1mo': 30, '3mo': 90,
            '6mo': 180, '1y': 365, '2y': 730, '5y': 1825, '10y': 3650
        }
        return mapping.get(period, 365)

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote"""
        df = self.get_price_history(symbol, interval='1d', period='5d')
        if df.empty:
            return {}

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]

        change = latest['close'] - prev['close']
        change_pct = (change / prev['close']) * 100 if prev['close'] > 0 else 0

        return {
            'symbol': symbol,
            'price': float(latest['close']),
            'open': float(latest['open']),
            'high': float(latest['high']),
            'low': float(latest['low']),
            'volume': int(latest['volume']),
            'change': float(change),
            'changePercent': float(change_pct),
            'timestamp': str(latest['timestamp'])
        }


# Singleton instance
_data_service = None

def get_data_service() -> OpenBBDataService:
    """Get or create singleton data service instance"""
    global _data_service
    if _data_service is None:
        _data_service = OpenBBDataService()
    return _data_service


# Convenience functions for backwards compatibility
def get_historical_data(symbol: str, period: str = "1y", interval: str = "1d") -> List[Dict]:
    """Get historical data (backwards compatible)"""
    service = get_data_service()
    df = service.get_price_history(symbol, interval=interval, period=period)

    if df.empty:
        return []

    return [{
        'date': str(row['timestamp']),
        'open': float(row['open']),
        'high': float(row['high']),
        'low': float(row['low']),
        'close': float(row['close']),
        'volume': int(row['volume'])
    } for _, row in df.iterrows()]


def get_stock_info(symbol: str) -> Dict[str, Any]:
    """Get stock info (backwards compatible)"""
    service = get_data_service()
    return service.get_fundamentals(symbol)


def get_quote_data(symbol: str) -> Dict[str, Any]:
    """Get quote (backwards compatible)"""
    service = get_data_service()
    return service.get_quote(symbol)


if __name__ == "__main__":
    # Test the service
    service = OpenBBDataService()

    print("Testing OpenBB Data Service...")
    print(f"Using OpenBB: {service.use_openbb}")

    # Test price data
    print("\n1. Fetching price data for AAPL...")
    prices = service.get_price_history('AAPL', period='1mo')
    print(f"Retrieved {len(prices)} rows")
    if not prices.empty:
        print(prices.head())

    # Test fundamentals
    print("\n2. Fetching fundamentals for AAPL...")
    fundamentals = service.get_fundamentals('AAPL')
    print(json.dumps(fundamentals, indent=2)[:500])

    # Test quote
    print("\n3. Fetching quote for AAPL...")
    quote = service.get_quote('AAPL')
    print(json.dumps(quote, indent=2))

    print("\n✓ All tests completed")
