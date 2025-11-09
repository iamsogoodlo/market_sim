"""
Strategy 7: Factor-Neutral Residual Momentum
Momentum unexplained by Fama-French factors

Process:
1. Regress stock returns on FF5 factors (market, size, value, profitability, investment)
2. Extract residual returns (alpha + idiosyncratic component)
3. Compute momentum on residuals → factor-neutral momentum

This isolates stock-specific momentum from systematic factor exposure
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
import sys
sys.path.append('server')
import stock_data

def get_price_history(symbol: str, days: int = 252) -> pd.Series:
    """Get historical closing prices"""
    data = stock_data.get_historical_data(symbol, period="1y")
    if not data:
        return pd.Series()

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    return df['close'].iloc[-days:] if len(df) >= days else df['close']

def get_market_returns(days: int = 252) -> pd.Series:
    """Get market returns (SPY proxy)"""
    # In production, fetch SPY returns from market data
    # For demo, simulate market returns
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='D')
    market_returns = pd.Series(
        np.random.normal(0.0004, 0.01, days),  # ~10% annual return, 16% vol
        index=dates
    )
    return market_returns

def get_ff5_factors(days: int = 252) -> pd.DataFrame:
    """
    Get Fama-French 5-factor returns
    Factors: Mkt-RF, SMB, HML, RMW, CMA

    In production, fetch from Ken French Data Library
    For demo, simulate correlated factors
    """
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='D')

    # Simulated factor returns
    mkt_rf = np.random.normal(0.0004, 0.01, days)  # Market excess return
    smb = np.random.normal(0.0001, 0.005, days)    # Size factor
    hml = np.random.normal(0.0001, 0.005, days)    # Value factor
    rmw = np.random.normal(0.0001, 0.004, days)    # Profitability factor
    cma = np.random.normal(0.00005, 0.003, days)   # Investment factor

    factors = pd.DataFrame({
        'Mkt-RF': mkt_rf,
        'SMB': smb,
        'HML': hml,
        'RMW': rmw,
        'CMA': cma
    }, index=dates)

    return factors

def compute_residual_returns(prices: pd.Series) -> pd.Series:
    """
    Compute residual returns after FF5 factor regression

    Model: R_i,t - R_f,t = α + β_mkt*(Mkt-RF) + β_smb*SMB + β_hml*HML + β_rmw*RMW + β_cma*CMA + ε_t

    Return: residual series (α + ε_t)
    """
    if len(prices) < 180:
        return pd.Series()

    # Compute stock returns
    returns = prices.pct_change().dropna()

    # Get FF5 factors
    factors = get_ff5_factors(len(returns))

    # Align dates
    common_idx = returns.index.intersection(factors.index)
    if len(common_idx) < 60:
        return pd.Series()

    y = returns.loc[common_idx].values
    X = factors.loc[common_idx].values

    # Add intercept
    X_with_const = np.column_stack([np.ones(len(X)), X])

    # OLS regression
    try:
        betas, residuals, _, _ = np.linalg.lstsq(X_with_const, y, rcond=None)
        alpha = betas[0]
        factor_betas = betas[1:]

        # Compute fitted values and residuals
        fitted = X_with_const @ betas
        residual_returns = y - fitted

        residual_series = pd.Series(residual_returns, index=common_idx)
        return residual_series
    except:
        return pd.Series()

def compute_residual_momentum_signal(symbol: str) -> Dict[str, float]:
    """
    Compute momentum on residual returns (12-1 window)

    Returns:
        residual_mom_12_1: Cumulative residual return from t-252 to t-21
        raw_mom_12_1: Raw total return momentum for comparison
        alpha_contribution: Average residual return (annualized)
    """
    prices = get_price_history(symbol, days=300)

    if len(prices) < 252:
        return {
            "residual_mom_12_1": 0.0,
            "raw_mom_12_1": 0.0,
            "alpha_contribution": 0.0
        }

    # Compute residual returns
    residual_returns = compute_residual_returns(prices)

    if len(residual_returns) < 252:
        # Fallback: use raw returns
        residual_returns = prices.pct_change().dropna()

    # 12-1 momentum on residuals
    if len(residual_returns) >= 252:
        residual_mom_12_1 = residual_returns.iloc[-252:-21].sum()  # Cumulative return
    else:
        residual_mom_12_1 = 0.0

    # Raw 12-1 momentum for comparison
    if len(prices) >= 252:
        raw_mom_12_1 = (prices.iloc[-21] / prices.iloc[-252]) - 1.0
    else:
        raw_mom_12_1 = 0.0

    # Alpha contribution (average residual return, annualized)
    alpha_contribution = residual_returns.mean() * 252

    return {
        "residual_mom_12_1": residual_mom_12_1,
        "raw_mom_12_1": raw_mom_12_1,
        "alpha_contribution": alpha_contribution
    }

def residual_momentum_rating(symbol: str) -> Dict[str, Any]:
    """
    Generate 1-5 rating for factor-neutral residual momentum

    Rating Scale (based on residual momentum):
    - mom > 0.15 → 5 (strong idiosyncratic momentum)
    - 0.08 < mom ≤ 0.15 → 4
    - -0.08 ≤ mom ≤ 0.08 → 3 (neutral)
    - -0.15 ≤ mom < -0.08 → 2
    - mom < -0.15 → 1 (strong negative momentum)
    """
    signal_data = compute_residual_momentum_signal(symbol)

    residual_mom = signal_data["residual_mom_12_1"]
    raw_mom = signal_data["raw_mom_12_1"]
    alpha = signal_data["alpha_contribution"]

    # Rating logic
    if residual_mom > 0.15:
        rating = 5
    elif residual_mom > 0.08:
        rating = 4
    elif residual_mom >= -0.08:
        rating = 3
    elif residual_mom >= -0.15:
        rating = 2
    else:
        rating = 1

    if rating >= 4:
        rationale_suffix = " ⇒ strong factor-neutral momentum"
    elif rating <= 2:
        rationale_suffix = " ⇒ weak idiosyncratic performance"
    else:
        rationale_suffix = " ⇒ neutral"

    rationale = f"Residual mom={residual_mom*100:.1f}% (raw={raw_mom*100:.1f}%, α={alpha*100:.1f}%)" + rationale_suffix

    return {
        "rating": rating,
        "metrics": {
            "residual_mom_12_1": round(residual_mom, 4),
            "raw_mom_12_1": round(raw_mom, 4),
            "alpha_contribution": round(alpha, 4),
            "residual_mom_pct": round(residual_mom * 100, 2),
            "raw_mom_pct": round(raw_mom * 100, 2)
        },
        "rationale": rationale
    }


if __name__ == "__main__":
    import json
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = residual_momentum_rating(symbol)
    print(json.dumps(result, indent=2))
