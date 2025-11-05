"""
Strategy 1: Cointegration Pairs Trading
Statistical arbitrage based on mean-reversion of cointegrated spreads
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint, adfuller
from typing import Dict, Any, Optional
import sys
sys.path.append('server')
import stock_data

def get_price_history(symbol: str, days: int = 90) -> pd.Series:
    """Get historical closing prices"""
    data = stock_data.get_historical_data(symbol, period="3mo")
    if not data:
        return pd.Series()

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    return df['close'].iloc[-days:] if len(df) >= days else df['close']

def find_best_peer(symbol: str, peer_symbols: list) -> Optional[tuple]:
    """
    Find best cointegrated peer using Engle-Granger test
    Returns: (peer_symbol, p_value, hedge_ratio) or None
    """
    target = get_price_history(symbol)
    if len(target) < 30:
        return None

    best_peer = None
    best_pvalue = 1.0
    best_hedge_ratio = 0.0

    for peer in peer_symbols:
        if peer == symbol:
            continue

        peer_prices = get_price_history(peer)
        if len(peer_prices) < 30:
            continue

        # Align series
        common_idx = target.index.intersection(peer_prices.index)
        if len(common_idx) < 30:
            continue

        y = target.loc[common_idx]
        x = peer_prices.loc[common_idx]

        # Log prices for better stationarity
        log_y = np.log(y)
        log_x = np.log(x)

        # Regression: log(P_i) = α + β·log(P_j) + ε
        hedge_ratio = np.polyfit(log_x, log_y, 1)[0]
        spread = log_y - hedge_ratio * log_x

        # Engle-Granger cointegration test
        try:
            _, p_value, _ = coint(y, x)

            # Check if spread is stationary
            adf_result = adfuller(spread, maxlag=10)
            spread_pvalue = adf_result[1]

            # Both tests should indicate cointegration
            combined_pvalue = max(p_value, spread_pvalue)

            if combined_pvalue < best_pvalue and combined_pvalue < 0.10:
                best_pvalue = combined_pvalue
                best_peer = peer
                best_hedge_ratio = hedge_ratio
        except:
            continue

    if best_peer:
        return (best_peer, best_pvalue, best_hedge_ratio)
    return None

def compute_spread_zscore(symbol: str, peer: str, hedge_ratio: float, window: int = 60) -> tuple:
    """
    Compute z-score of the spread
    Returns: (z_score, half_life_days)
    """
    target = get_price_history(symbol, days=window)
    peer_prices = get_price_history(peer, days=window)

    if len(target) < 30 or len(peer_prices) < 30:
        return (0.0, 999)

    # Align
    common_idx = target.index.intersection(peer_prices.index)
    if len(common_idx) < 30:
        return (0.0, 999)

    y = target.loc[common_idx]
    x = peer_prices.loc[common_idx]

    # Compute spread
    log_y = np.log(y)
    log_x = np.log(x)
    spread = log_y - hedge_ratio * log_x

    # Z-score
    mean_spread = spread.mean()
    std_spread = spread.std()
    current_z = (spread.iloc[-1] - mean_spread) / std_spread if std_spread > 0 else 0.0

    # Half-life from AR(1) model: spread_t = α + ρ·spread_{t-1} + ε
    # Half-life HL = ln(2) / ln(1/ρ)
    try:
        lag_spread = spread.iloc[:-1].values
        current_spread = spread.iloc[1:].values

        # OLS: spread_t = α + ρ·spread_{t-1}
        X = np.vstack([np.ones(len(lag_spread)), lag_spread]).T
        rho = np.linalg.lstsq(X, current_spread, rcond=None)[0][1]

        if 0 < rho < 1:
            half_life = np.log(2) / np.log(1 / rho)
        else:
            half_life = 999
    except:
        half_life = 999

    return (current_z, half_life)

def cointegration_pairs_rating(symbol: str, peers: list = None) -> Dict[str, Any]:
    """
    Generate 1-5 rating for cointegration pairs trading

    Rating Scale:
    - z ≤ -2.0 → 5 (strong buy - spread very cheap)
    - -2.0 < z ≤ -1.0 → 4
    - -1.0 < z < 1.0 → 3 (neutral)
    - 1.0 ≤ z < 2.0 → 2
    - z ≥ 2.0 → 1 (strong sell - spread very expensive)
    """

    # Default peers (tech stocks for cointegration)
    if peers is None:
        peers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]

    # Find best peer
    peer_result = find_best_peer(symbol, peers)

    if not peer_result:
        return {
            "rating": 3,
            "metrics": {
                "peer": None,
                "z_score": 0.0,
                "p_value": 1.0,
                "half_life_days": 999
            },
            "rationale": "No cointegrated peer found (p>0.10)"
        }

    peer, p_value, hedge_ratio = peer_result

    # Compute spread z-score
    z_score, half_life = compute_spread_zscore(symbol, peer, hedge_ratio)

    # Rating logic
    if z_score <= -2.0:
        rating = 5
    elif z_score <= -1.0:
        rating = 4
    elif z_score < 1.0:
        rating = 3
    elif z_score < 2.0:
        rating = 2
    else:
        rating = 1

    # Adjust for half-life quality
    if half_life > 90 or half_life < 3:
        # Bad half-life: cap rating at 3
        rating = min(rating, 3)

    rationale = f"Spread vs {peer} at {z_score:.2f}σ (p={p_value:.3f}, HL~{half_life:.0f}d)"

    if rating >= 4:
        rationale += " ⇒ mean reversion expected"
    elif rating <= 2:
        rationale += " ⇒ spread expensive"
    else:
        rationale += " ⇒ neutral"

    return {
        "rating": rating,
        "metrics": {
            "peer": peer,
            "z_score": round(z_score, 2),
            "p_value": round(p_value, 3),
            "half_life_days": round(half_life, 1),
            "hedge_ratio": round(hedge_ratio, 3)
        },
        "rationale": rationale
    }


if __name__ == "__main__":
    # Test
    import json
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = cointegration_pairs_rating(symbol)
    print(json.dumps(result, indent=2))
