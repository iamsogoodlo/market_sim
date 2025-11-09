"""
Strategy 2: Ornstein-Uhlenbeck Mean Reversion
Model price as a mean-reverting stochastic process

OU Process: dX_t = θ(μ - X_t)dt + σdW_t
where θ = mean reversion speed, μ = long-term mean
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any
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

def estimate_ou_parameters(prices: pd.Series) -> Dict[str, float]:
    """
    Estimate Ornstein-Uhlenbeck parameters from price data

    Using log prices: X_t = log(P_t)
    AR(1) estimation: X_t - X_{t-1} = θ(μ - X_{t-1})Δt + σ√Δt·ε
    """
    if len(prices) < 30:
        return {"theta": 0.0, "mu": 0.0, "sigma": 0.0, "half_life": 999}

    # Log prices for better stationarity
    log_prices = np.log(prices)

    # Time interval (assuming daily data)
    dt = 1.0  # 1 day

    # Price changes
    X_t = log_prices.values[1:]
    X_lag = log_prices.values[:-1]
    dX = X_t - X_lag

    # OLS regression: dX = a + b·X_{t-1} + ε
    # where a = θμΔt, b = -θΔt
    X_design = np.vstack([np.ones(len(X_lag)), X_lag]).T
    coeffs, residuals, _, _ = np.linalg.lstsq(X_design, dX, rcond=None)

    a, b = coeffs

    # Extract OU parameters
    theta = -b / dt  # Mean reversion speed
    mu = a / (-b) if b != 0 else log_prices.mean()  # Long-term mean

    # Volatility from residuals
    sigma = np.std(dX - (a + b * X_lag)) / np.sqrt(dt)

    # Half-life: time for process to move halfway back to mean
    # HL = ln(2) / θ
    half_life = np.log(2) / theta if theta > 0 else 999

    return {
        "theta": theta,
        "mu": mu,
        "sigma": sigma,
        "half_life": half_life
    }

def compute_ou_z_score(prices: pd.Series, params: Dict[str, float]) -> float:
    """
    Compute z-score based on OU model

    Z = (X_current - μ) / σ_eq
    where σ_eq = σ / sqrt(2θ) is equilibrium volatility
    """
    if len(prices) == 0:
        return 0.0

    current_log_price = np.log(prices.iloc[-1])
    mu = params["mu"]
    theta = params["theta"]
    sigma = params["sigma"]

    if theta <= 0 or sigma <= 0:
        return 0.0

    # Equilibrium volatility
    sigma_eq = sigma / np.sqrt(2 * theta)

    # Z-score
    z_score = (current_log_price - mu) / sigma_eq

    return z_score

def ou_mean_reversion_rating(symbol: str) -> Dict[str, Any]:
    """
    Generate 1-5 rating for OU mean reversion strategy

    Rating Scale:
    - z ≤ -2.0 → 5 (strong buy - price far below mean)
    - -2.0 < z ≤ -1.0 → 4
    - -1.0 < z < 1.0 → 3 (neutral)
    - 1.0 ≤ z < 2.0 → 2
    - z ≥ 2.0 → 1 (strong sell - price far above mean)

    Quality filters:
    - θ > 0 (mean-reverting)
    - Half-life 3-90 days (reasonable reversion speed)
    - R² > 0.1 (model explains some variance)
    """
    prices = get_price_history(symbol, days=90)

    if len(prices) < 30:
        return {
            "rating": 3,
            "metrics": {
                "theta": 0.0,
                "mu": 0.0,
                "half_life_days": 999,
                "z_score": 0.0,
                "r_squared": 0.0
            },
            "rationale": "Insufficient data for OU estimation"
        }

    # Estimate OU parameters
    params = estimate_ou_parameters(prices)

    # Compute z-score
    z_score = compute_ou_z_score(prices, params)

    # Compute R² for model quality
    log_prices = np.log(prices)
    X_lag = log_prices.values[:-1]
    dX_actual = np.diff(log_prices.values)
    dX_predicted = params["theta"] * (params["mu"] - X_lag)

    ss_res = np.sum((dX_actual - dX_predicted)**2)
    ss_tot = np.sum((dX_actual - np.mean(dX_actual))**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Rating logic
    theta = params["theta"]
    half_life = params["half_life"]

    # Base rating from z-score
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

    # Quality adjustments
    if theta <= 0:
        # Not mean-reverting, cap at 3
        rating = 3
        rationale_suffix = " (non-mean-reverting)"
    elif half_life > 90 or half_life < 3:
        # Poor half-life, cap at 3
        rating = min(rating, 3)
        rationale_suffix = " (slow/fast reversion)"
    elif r_squared < 0.1:
        # Model explains little variance, cap at 3
        rating = min(rating, 3)
        rationale_suffix = " (weak model fit)"
    else:
        rationale_suffix = " ⇒ mean reversion expected" if rating >= 4 else (" ⇒ price expensive" if rating <= 2 else " ⇒ neutral")

    exp_mu = np.exp(params["mu"])
    rationale = f"OU: θ={theta:.3f}, μ=${exp_mu:.2f}, HL~{half_life:.0f}d, z={z_score:.2f}σ" + rationale_suffix

    return {
        "rating": rating,
        "metrics": {
            "theta": round(theta, 4),
            "mu_log": round(params["mu"], 3),
            "mu_price": round(exp_mu, 2),
            "sigma": round(params["sigma"], 4),
            "half_life_days": round(half_life, 1),
            "z_score": round(z_score, 2),
            "r_squared": round(r_squared, 3)
        },
        "rationale": rationale
    }


if __name__ == "__main__":
    import json
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = ou_mean_reversion_rating(symbol)
    print(json.dumps(result, indent=2))
