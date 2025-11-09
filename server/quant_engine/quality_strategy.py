"""
Strategy 5: Quality/Profitability (QMJ - Quality Minus Junk)
High-quality firms earn superior risk-adjusted returns
Based on profitability, growth, and safety metrics
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import sys
sys.path.append('server')
import stock_data

def get_quality_metrics(symbol: str) -> Optional[Dict[str, float]]:
    """
    Get quality/profitability metrics

    Key metrics:
    - ROE (Return on Equity)
    - ROA (Return on Assets)
    - Gross Margin
    - Operating Margin
    - Asset Turnover
    - Leverage (Debt/Equity)
    - Earnings Growth
    - Payout Ratio
    """
    info = stock_data.get_stock_info(symbol)
    if not info:
        return None

    metrics = {}

    # Profitability
    metrics['roe'] = info.get('returnOnEquity', 0) or 0.0  # As decimal (e.g., 0.15 = 15%)
    metrics['roa'] = info.get('returnOnAssets', 0) or 0.0
    metrics['gross_margin'] = info.get('grossMargins', 0) or 0.0
    metrics['operating_margin'] = info.get('operatingMargins', 0) or 0.0

    # Growth
    metrics['earnings_growth'] = info.get('earningsGrowth', 0) or 0.0
    metrics['revenue_growth'] = info.get('revenueGrowth', 0) or 0.0

    # Safety/Leverage
    metrics['debt_to_equity'] = info.get('debtToEquity', 0) or 0.0
    metrics['current_ratio'] = info.get('currentRatio', 0) or 1.0

    # Payout
    metrics['payout_ratio'] = info.get('payoutRatio', 0) or 0.0

    return metrics

def compute_quality_score(metrics: Dict[str, float]) -> tuple:
    """
    Compute composite quality score from three pillars:
    1. Profitability
    2. Growth
    3. Safety

    Returns: (composite_score, profitability_score, growth_score, safety_score)
    """
    if not metrics:
        return (0.0, 0.0, 0.0, 0.0)

    # 1. Profitability Score (ROE, ROA, Margins)
    roe = metrics.get('roe', 0) * 100  # Convert to %
    roa = metrics.get('roa', 0) * 100
    gross_margin = metrics.get('gross_margin', 0) * 100
    operating_margin = metrics.get('operating_margin', 0) * 100

    prof_score = 0.0
    if roe > 20:
        prof_score += 1.0
    elif roe > 15:
        prof_score += 0.5
    elif roe > 10:
        prof_score += 0.0
    else:
        prof_score -= 0.5

    if operating_margin > 20:
        prof_score += 1.0
    elif operating_margin > 10:
        prof_score += 0.5
    elif operating_margin > 5:
        prof_score += 0.0
    else:
        prof_score -= 0.5

    # 2. Growth Score (Earnings and Revenue Growth)
    earnings_growth = metrics.get('earnings_growth', 0) * 100
    revenue_growth = metrics.get('revenue_growth', 0) * 100

    growth_score = 0.0
    if earnings_growth > 15:
        growth_score += 1.0
    elif earnings_growth > 10:
        growth_score += 0.5
    elif earnings_growth > 5:
        growth_score += 0.0
    elif earnings_growth > 0:
        growth_score -= 0.5
    else:
        growth_score -= 1.0

    if revenue_growth > 10:
        growth_score += 0.5
    elif revenue_growth > 5:
        growth_score += 0.0
    else:
        growth_score -= 0.5

    # 3. Safety Score (Low leverage, good liquidity)
    debt_to_equity = metrics.get('debt_to_equity', 0) / 100  # Normalize
    current_ratio = metrics.get('current_ratio', 1.0)

    safety_score = 0.0
    if debt_to_equity < 0.5:
        safety_score += 1.0
    elif debt_to_equity < 1.0:
        safety_score += 0.5
    elif debt_to_equity < 2.0:
        safety_score += 0.0
    else:
        safety_score -= 1.0

    if current_ratio > 2.0:
        safety_score += 0.5
    elif current_ratio > 1.5:
        safety_score += 0.0
    else:
        safety_score -= 0.5

    # Composite: weighted average
    composite = (prof_score * 0.4 + growth_score * 0.3 + safety_score * 0.3)

    return (composite, prof_score, growth_score, safety_score)

def quality_strategy_rating(symbol: str) -> Dict[str, Any]:
    """
    Generate 1-5 rating for quality/profitability strategy

    Rating Scale:
    - Exceptional quality (composite > 1.5) → 5 (strong buy)
    - High quality (composite > 0.5) → 4 (buy)
    - Average quality (-0.5 to +0.5) → 3 (neutral)
    - Low quality (-1.5 to -0.5) → 2 (sell)
    - Junk (composite < -1.5) → 1 (strong sell)
    """

    # Get quality metrics
    metrics = get_quality_metrics(symbol)

    if not metrics:
        return {
            "rating": 3,
            "metrics": {
                "roe": 0.0,
                "operating_margin": 0.0,
                "earnings_growth": 0.0,
                "debt_to_equity": 0.0,
                "quality_score": 0.0
            },
            "rationale": "Insufficient fundamental data for quality assessment"
        }

    # Compute quality score
    composite, prof_score, growth_score, safety_score = compute_quality_score(metrics)

    # Rating logic
    if composite >= 1.5:
        rating = 5
        action = "exceptional quality, strong buy"
    elif composite >= 0.5:
        rating = 4
        action = "high quality, buy"
    elif composite >= -0.5:
        rating = 3
        action = "average quality, neutral"
    elif composite >= -1.5:
        rating = 2
        action = "low quality, sell"
    else:
        rating = 1
        action = "junk, strong sell"

    roe = metrics.get('roe', 0) * 100
    operating_margin = metrics.get('operating_margin', 0) * 100
    earnings_growth = metrics.get('earnings_growth', 0) * 100
    debt_to_equity = metrics.get('debt_to_equity', 0)

    rationale = f"ROE={roe:.1f}%, OpMargin={operating_margin:.1f}%, EarningsGrowth={earnings_growth:.1f}% | Quality={composite:.2f} ⇒ {action}"

    return {
        "rating": rating,
        "metrics": {
            "roe": round(roe, 2),
            "operating_margin": round(operating_margin, 2),
            "earnings_growth": round(earnings_growth, 2),
            "debt_to_equity": round(debt_to_equity, 2),
            "quality_score": round(composite, 2),
            "profitability_score": round(prof_score, 2),
            "growth_score": round(growth_score, 2),
            "safety_score": round(safety_score, 2)
        },
        "rationale": rationale
    }


if __name__ == "__main__":
    import json
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = quality_strategy_rating(symbol)
    print(json.dumps(result, indent=2))
