"""
Strategy 4: Cross-Sectional Value
Cheap stocks outperform expensive ones within industries
Based on P/E, P/B, EV/EBITDA ratios
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import sys
sys.path.append('server')
import stock_data

def get_fundamental_data(symbol: str) -> Optional[Dict[str, float]]:
    """
    Get fundamental ratios for valuation
    In production, use API like Alpha Vantage or Financial Modeling Prep

    For now, approximate using available data
    """
    # Try to get stock info
    info = stock_data.get_stock_info(symbol)
    if not info:
        return None

    # Extract valuation metrics
    fundamentals = {}

    # Market cap
    fundamentals['market_cap'] = info.get('marketCap', 0)

    # P/E ratio
    fundamentals['pe_ratio'] = info.get('trailingPE', 0) or info.get('forwardPE', 0)

    # P/B ratio
    fundamentals['pb_ratio'] = info.get('priceToBook', 0)

    # EV/EBITDA (if available)
    fundamentals['ev_ebitda'] = info.get('enterpriseToEbitda', 0)

    # Dividend yield
    fundamentals['div_yield'] = info.get('dividendYield', 0) or 0.0

    return fundamentals

def compute_value_score(fundamentals: Dict[str, float], sector_medians: Dict[str, float] = None) -> float:
    """
    Compute composite value score
    Lower is cheaper (better value)

    Z-score approach: (metric - sector_median) / sector_std
    """
    if not fundamentals:
        return 0.0

    pe = fundamentals.get('pe_ratio', 0)
    pb = fundamentals.get('pb_ratio', 0)
    ev_ebitda = fundamentals.get('ev_ebitda', 0)

    # Simple composite: average of normalized ratios
    # If no sector data, use absolute thresholds
    if sector_medians is None:
        # Heuristic percentile ranks (lower is better)
        pe_score = 0.0
        if pe > 0:
            if pe < 15:
                pe_score = -1.5  # Very cheap
            elif pe < 20:
                pe_score = -0.5  # Cheap
            elif pe < 30:
                pe_score = 0.0  # Fair
            elif pe < 50:
                pe_score = 0.5  # Expensive
            else:
                pe_score = 1.5  # Very expensive

        pb_score = 0.0
        if pb > 0:
            if pb < 1.5:
                pb_score = -1.0
            elif pb < 3.0:
                pb_score = 0.0
            elif pb < 5.0:
                pb_score = 0.5
            else:
                pb_score = 1.0

        ev_score = 0.0
        if ev_ebitda > 0:
            if ev_ebitda < 10:
                ev_score = -1.0
            elif ev_ebitda < 15:
                ev_score = 0.0
            elif ev_ebitda < 25:
                ev_score = 0.5
            else:
                ev_score = 1.0

        # Composite: average
        scores = [pe_score, pb_score, ev_score]
        valid_scores = [s for s in scores if s != 0.0]
        if valid_scores:
            composite = sum(valid_scores) / len(valid_scores)
        else:
            composite = 0.0

        return composite

    # TODO: Cross-sectional ranking within sector
    return 0.0

def value_strategy_rating(symbol: str) -> Dict[str, Any]:
    """
    Generate 1-5 rating for value strategy

    Rating Scale:
    - Deep value (composite < -1.0) → 5 (strong buy)
    - Value (composite < -0.5) → 4 (buy)
    - Fair value (-0.5 to +0.5) → 3 (neutral)
    - Expensive (+0.5 to +1.0) → 2 (sell)
    - Very expensive (> +1.0) → 1 (strong sell)
    """

    # Get fundamental data
    fundamentals = get_fundamental_data(symbol)

    if not fundamentals or fundamentals.get('pe_ratio', 0) <= 0:
        return {
            "rating": 3,
            "metrics": {
                "pe_ratio": 0.0,
                "pb_ratio": 0.0,
                "ev_ebitda": 0.0,
                "value_score": 0.0
            },
            "rationale": "Insufficient fundamental data"
        }

    # Compute value score
    value_score = compute_value_score(fundamentals)

    # Rating logic
    if value_score <= -1.0:
        rating = 5
        action = "deep value, strong buy"
    elif value_score <= -0.5:
        rating = 4
        action = "value buy"
    elif value_score < 0.5:
        rating = 3
        action = "fair value"
    elif value_score < 1.0:
        rating = 2
        action = "expensive, sell"
    else:
        rating = 1
        action = "very expensive, strong sell"

    pe = fundamentals.get('pe_ratio', 0)
    pb = fundamentals.get('pb_ratio', 0)
    ev_ebitda = fundamentals.get('ev_ebitda', 0)
    div_yield = fundamentals.get('div_yield', 0) * 100  # Convert to %

    rationale = f"P/E={pe:.1f}, P/B={pb:.1f}, EV/EBITDA={ev_ebitda:.1f} | Score={value_score:.2f} ⇒ {action}"

    return {
        "rating": rating,
        "metrics": {
            "pe_ratio": round(pe, 2),
            "pb_ratio": round(pb, 2),
            "ev_ebitda": round(ev_ebitda, 2),
            "div_yield": round(div_yield, 2),
            "value_score": round(value_score, 2)
        },
        "rationale": rationale
    }


if __name__ == "__main__":
    import json
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = value_strategy_rating(symbol)
    print(json.dumps(result, indent=2))
