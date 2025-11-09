"""
Strategy 3: Time-Series Momentum (12-1)
Past winners continue to outperform with volatility targeting

Classic momentum: Look at past 12-month returns, skip last month
Vol-targeting: Scale positions inversely with volatility
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
import sys
sys.path.append('server')
import stock_data

def get_price_history(symbol: str, days: int = 365) -> pd.Series:
    """Get historical closing prices"""
    data = stock_data.get_historical_data(symbol, period="1y")
    if not data:
        return pd.Series()

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    return df['close'].iloc[-days:] if len(df) >= days else df['close']

def compute_momentum_signal(prices: pd.Series) -> Dict[str, float]:
    """
    Compute 12-1 momentum signal

    Returns: {
        "mom_12_1": Total return from t-252 to t-21 (skip last month)
        "vol_60d": 60-day rolling volatility (annualized)
        "vol_adj_signal": momentum / volatility
    }
    """
    if len(prices) < 252:
        return {
            "mom_12_1": 0.0,
            "vol_60d": 0.0,
            "vol_adj_signal": 0.0
        }

    # 12-month momentum, skipping last month
    # t-252 to t-21 (12 months to 1 month ago)
    if len(prices) >= 252:
        price_12m_ago = prices.iloc[-252]
        price_1m_ago = prices.iloc[-21] if len(prices) >= 21 else prices.iloc[-1]
        mom_12_1 = (price_1m_ago / price_12m_ago) - 1.0
    else:
        mom_12_1 = 0.0

    # 60-day volatility (annualized)
    returns = prices.pct_change().dropna()
    if len(returns) >= 60:
        vol_60d = returns.iloc[-60:].std() * np.sqrt(252)  # Annualize
    else:
        vol_60d = returns.std() * np.sqrt(252) if len(returns) > 0 else 0.15

    # Volatility-adjusted signal
    # Target vol = 15% (typical equity vol)
    target_vol = 0.15
    if vol_60d > 0:
        vol_adj_signal = mom_12_1 * (target_vol / vol_60d)
    else:
        vol_adj_signal = 0.0

    return {
        "mom_12_1": mom_12_1,
        "vol_60d": vol_60d,
        "vol_adj_signal": vol_adj_signal
    }

def ts_momentum_rating(symbol: str) -> Dict[str, Any]:
    """
    Generate 1-5 rating for time-series momentum strategy

    Rating Scale (based on vol-adjusted signal):
    - signal > 0.20 → 5 (strong momentum)
    - 0.10 < signal ≤ 0.20 → 4
    - -0.10 ≤ signal ≤ 0.10 → 3 (neutral)
    - -0.20 ≤ signal < -0.10 → 2
    - signal < -0.20 → 1 (strong negative momentum)

    Quality filters:
    - Volatility 5-50% (reasonable range)
    - Data coverage > 252 days
    """
    prices = get_price_history(symbol, days=365)

    if len(prices) < 252:
        return {
            "rating": 3,
            "metrics": {
                "mom_12_1": 0.0,
                "vol_60d_ann": 0.0,
                "vol_adj_signal": 0.0
            },
            "rationale": "Insufficient data (need 12 months)"
        }

    # Compute momentum signal
    signal_data = compute_momentum_signal(prices)

    mom_12_1 = signal_data["mom_12_1"]
    vol_60d = signal_data["vol_60d"]
    vol_adj_signal = signal_data["vol_adj_signal"]

    # Rating logic
    if vol_adj_signal > 0.20:
        rating = 5
    elif vol_adj_signal > 0.10:
        rating = 4
    elif vol_adj_signal >= -0.10:
        rating = 3
    elif vol_adj_signal >= -0.20:
        rating = 2
    else:
        rating = 1

    # Quality adjustments
    if vol_60d < 0.05 or vol_60d > 0.50:
        # Abnormal volatility, cap at 3
        rating = min(rating, 3)
        rationale_suffix = " (abnormal vol)"
    else:
        if rating >= 4:
            rationale_suffix = " ⇒ positive momentum"
        elif rating <= 2:
            rationale_suffix = " ⇒ negative momentum"
        else:
            rationale_suffix = " ⇒ neutral"

    rationale = f"12-1 mom={mom_12_1*100:.1f}%, vol={vol_60d*100:.1f}%, adj_signal={vol_adj_signal*100:.1f}%" + rationale_suffix

    return {
        "rating": rating,
        "metrics": {
            "mom_12_1": round(mom_12_1, 4),
            "vol_60d_ann": round(vol_60d, 4),
            "vol_adj_signal": round(vol_adj_signal, 4),
            "raw_mom_pct": round(mom_12_1 * 100, 2),
            "vol_pct": round(vol_60d * 100, 2)
        },
        "rationale": rationale
    }


if __name__ == "__main__":
    import json
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = ts_momentum_rating(symbol)
    print(json.dumps(result, indent=2))
