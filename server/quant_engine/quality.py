"""
Strategy 5: Quality/Profitability Composite (QMJ)
High-quality firms earn superior risk-adjusted returns

Quality dimensions:
- Profitability: ROE, ROA, gross margin
- Growth: earnings growth, sales growth
- Safety: low leverage, low earnings volatility
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
import sys
sys.path.append('server')
import stock_data

# Mock fundamental data (in production, fetch from OpenBB)
QUALITY_DATA = {
    "AAPL": {"roe": 0.95, "roa": 0.27, "gross_margin": 0.43, "earnings_growth": 0.11, "debt_to_equity": 1.70, "earnings_vol": 0.08},
    "MSFT": {"roe": 0.38, "roa": 0.18, "gross_margin": 0.68, "earnings_growth": 0.15, "debt_to_equity": 0.36, "earnings_vol": 0.06},
    "GOOGL": {"roe": 0.24, "roa": 0.17, "gross_margin": 0.57, "earnings_growth": 0.10, "debt_to_equity": 0.08, "earnings_vol": 0.12},
    "AMZN": {"roe": 0.18, "roa": 0.06, "gross_margin": 0.47, "earnings_growth": 0.28, "debt_to_equity": 0.48, "earnings_vol": 0.35},
    "META": {"roe": 0.31, "roa": 0.22, "gross_margin": 0.81, "earnings_growth": 0.12, "debt_to_equity": 0.00, "earnings_vol": 0.15},
    "NVDA": {"roe": 0.82, "roa": 0.51, "gross_margin": 0.72, "earnings_growth": 1.26, "debt_to_equity": 0.15, "earnings_vol": 0.28},
    "TSLA": {"roe": 0.28, "roa": 0.09, "gross_margin": 0.25, "earnings_growth": 0.42, "debt_to_equity": 0.08, "earnings_vol": 0.85},
    "JPM": {"roe": 0.15, "roa": 0.01, "gross_margin": None, "earnings_growth": 0.22, "debt_to_equity": 1.20, "earnings_vol": 0.18},
    "BAC": {"roe": 0.10, "roa": 0.01, "gross_margin": None, "earnings_growth": 0.15, "debt_to_equity": 1.18, "earnings_vol": 0.22},
    "WMT": {"roe": 0.20, "roa": 0.07, "gross_margin": 0.24, "earnings_growth": 0.05, "debt_to_equity": 0.78, "earnings_vol": 0.04},
    "AMD": {"roe": 0.02, "roa": 0.01, "gross_margin": 0.51, "earnings_growth": 0.38, "debt_to_equity": 0.04, "earnings_vol": 0.95},
    "INTC": {"roe": 0.12, "roa": 0.08, "gross_margin": 0.42, "earnings_growth": -0.15, "debt_to_equity": 0.41, "earnings_vol": 0.35},
}

def get_quality_metrics(symbol: str) -> Dict[str, float]:
    """Get quality/profitability metrics for a stock"""
    if symbol in QUALITY_DATA:
        return QUALITY_DATA[symbol]
    else:
        # Default average quality
        return {
            "roe": 0.15,
            "roa": 0.08,
            "gross_margin": 0.40,
            "earnings_growth": 0.08,
            "debt_to_equity": 0.60,
            "earnings_vol": 0.20
        }

def compute_quality_score(symbol: str, universe: list = None) -> Dict[str, float]:
    """
    Compute composite quality score

    Profitability: ROE, ROA, Gross Margin (higher = better)
    Growth: Earnings growth (higher = better)
    Safety: Debt-to-equity, earnings volatility (lower = better)
    """
    target = get_quality_metrics(symbol)

    if universe is None:
        universe = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]

    # Get universe metrics
    universe_metrics = [get_quality_metrics(s) for s in universe if s != symbol]

    if len(universe_metrics) == 0:
        return {"quality_score": 0.0, "prof_z": 0.0, "growth_z": 0.0, "safety_z": 0.0}

    # Extract arrays
    roe_array = [m["roe"] for m in universe_metrics]
    roa_array = [m["roa"] for m in universe_metrics]
    gm_array = [m["gross_margin"] for m in universe_metrics if m["gross_margin"] is not None]
    eg_array = [m["earnings_growth"] for m in universe_metrics]
    dte_array = [m["debt_to_equity"] for m in universe_metrics]
    ev_array = [m["earnings_vol"] for m in universe_metrics]

    # Z-scores for each dimension
    # Profitability (higher = better)
    roe_z = (target["roe"] - np.mean(roe_array)) / np.std(roe_array) if np.std(roe_array) > 0 else 0.0
    roa_z = (target["roa"] - np.mean(roa_array)) / np.std(roa_array) if np.std(roa_array) > 0 else 0.0
    if target["gross_margin"] is not None and len(gm_array) > 0:
        gm_z = (target["gross_margin"] - np.mean(gm_array)) / np.std(gm_array) if np.std(gm_array) > 0 else 0.0
    else:
        gm_z = 0.0

    prof_z = (roe_z + roa_z + gm_z) / 3.0

    # Growth (higher = better)
    growth_z = (target["earnings_growth"] - np.mean(eg_array)) / np.std(eg_array) if np.std(eg_array) > 0 else 0.0

    # Safety (lower = better, so invert)
    dte_z = -(target["debt_to_equity"] - np.mean(dte_array)) / np.std(dte_array) if np.std(dte_array) > 0 else 0.0
    ev_z = -(target["earnings_vol"] - np.mean(ev_array)) / np.std(ev_array) if np.std(ev_array) > 0 else 0.0
    safety_z = (dte_z + ev_z) / 2.0

    # Composite quality score (equal weight)
    quality_score = (prof_z + growth_z + safety_z) / 3.0

    return {
        "quality_score": quality_score,
        "prof_z": prof_z,
        "growth_z": growth_z,
        "safety_z": safety_z
    }

def quality_rating(symbol: str) -> Dict[str, Any]:
    """
    Generate 1-5 rating for quality/profitability strategy

    Rating Scale (based on composite quality score):
    - score > 1.0 → 5 (very high quality)
    - 0.5 < score ≤ 1.0 → 4
    - -0.5 ≤ score ≤ 0.5 → 3 (neutral)
    - -1.0 ≤ score < -0.5 → 2
    - score < -1.0 → 1 (low quality)
    """
    scores = compute_quality_score(symbol)
    quality_score = scores["quality_score"]

    # Rating logic
    if quality_score > 1.0:
        rating = 5
    elif quality_score > 0.5:
        rating = 4
    elif quality_score >= -0.5:
        rating = 3
    elif quality_score >= -1.0:
        rating = 2
    else:
        rating = 1

    if rating >= 4:
        rationale_suffix = " ⇒ high quality firm"
    elif rating <= 2:
        rationale_suffix = " ⇒ low quality/risky"
    else:
        rationale_suffix = " ⇒ neutral quality"

    rationale = f"Quality score={quality_score:.2f} (prof={scores['prof_z']:.2f}, growth={scores['growth_z']:.2f}, safety={scores['safety_z']:.2f})" + rationale_suffix

    return {
        "rating": rating,
        "metrics": {
            "quality_score": round(quality_score, 3),
            "profitability_z": round(scores["prof_z"], 3),
            "growth_z": round(scores["growth_z"], 3),
            "safety_z": round(scores["safety_z"], 3)
        },
        "rationale": rationale
    }


if __name__ == "__main__":
    import json
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = quality_rating(symbol)
    print(json.dumps(result, indent=2))
