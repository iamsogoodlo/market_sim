"""
Strategy 6: Earnings Surprise & Revision Drift (PEAD)
Post-Earnings Announcement Drift with analyst revisions

Stocks with positive earnings surprises tend to drift upward
Analyst estimate revisions predict future returns
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
import sys
sys.path.append('server')
import stock_data

# Mock earnings data (in production, fetch from OpenBB earnings calendar)
EARNINGS_DATA = {
    "AAPL": {"eps_surprise_pct": 5.2, "analyst_revisions_30d": 3, "days_since_earnings": 12},
    "MSFT": {"eps_surprise_pct": 8.1, "analyst_revisions_30d": 5, "days_since_earnings": 8},
    "GOOGL": {"eps_surprise_pct": -2.3, "analyst_revisions_30d": -2, "days_since_earnings": 15},
    "AMZN": {"eps_surprise_pct": 12.5, "analyst_revisions_30d": 7, "days_since_earnings": 22},
    "META": {"eps_surprise_pct": 15.8, "analyst_revisions_30d": 9, "days_since_earnings": 5},
    "NVDA": {"eps_surprise_pct": 22.3, "analyst_revisions_30d": 12, "days_since_earnings": 18},
    "TSLA": {"eps_surprise_pct": -8.5, "analyst_revisions_30d": -5, "days_since_earnings": 28},
    "JPM": {"eps_surprise_pct": 3.2, "analyst_revisions_30d": 2, "days_since_earnings": 35},
    "BAC": {"eps_surprise_pct": 1.8, "analyst_revisions_30d": 1, "days_since_earnings": 42},
    "WMT": {"eps_surprise_pct": 2.5, "analyst_revisions_30d": 0, "days_since_earnings": 19},
    "AMD": {"eps_surprise_pct": 18.2, "analyst_revisions_30d": 6, "days_since_earnings": 11},
    "INTC": {"eps_surprise_pct": -12.3, "analyst_revisions_30d": -8, "days_since_earnings": 25},
}

def get_earnings_data(symbol: str) -> Dict[str, float]:
    """Get earnings surprise and analyst revision data"""
    if symbol in EARNINGS_DATA:
        return EARNINGS_DATA[symbol]
    else:
        return {
            "eps_surprise_pct": 0.0,
            "analyst_revisions_30d": 0,
            "days_since_earnings": 60
        }

def compute_earnings_drift_signal(symbol: str) -> Dict[str, float]:
    """
    Compute PEAD signal

    Components:
    1. EPS surprise (actual vs consensus estimate)
    2. Analyst estimate revisions (upgrades - downgrades)
    3. Time decay (drift is strongest in first 60 days)

    Signal = (eps_surprise_normalized + revisions_normalized) * time_decay
    """
    data = get_earnings_data(symbol)

    eps_surprise_pct = data["eps_surprise_pct"]
    revisions = data["analyst_revisions_30d"]
    days_since = data["days_since_earnings"]

    # Normalize EPS surprise (typical range -20% to +20%)
    eps_normalized = np.clip(eps_surprise_pct / 20.0, -1.0, 1.0)

    # Normalize revisions (typical range -10 to +10)
    revisions_normalized = np.clip(revisions / 10.0, -1.0, 1.0)

    # Time decay: drift is strongest in first 60 days post-earnings
    # Exponential decay: e^(-days/60)
    time_decay = np.exp(-days_since / 60.0) if days_since < 90 else 0.0

    # Composite signal
    raw_signal = (eps_normalized + revisions_normalized) / 2.0
    drift_signal = raw_signal * time_decay

    return {
        "drift_signal": drift_signal,
        "eps_surprise_pct": eps_surprise_pct,
        "analyst_revisions_30d": revisions,
        "days_since_earnings": days_since,
        "time_decay": time_decay
    }

def earnings_drift_rating(symbol: str) -> Dict[str, Any]:
    """
    Generate 1-5 rating for earnings drift strategy

    Rating Scale (based on drift signal):
    - signal > 0.4 → 5 (strong positive drift)
    - 0.2 < signal ≤ 0.4 → 4
    - -0.2 ≤ signal ≤ 0.2 → 3 (neutral)
    - -0.4 ≤ signal < -0.2 → 2
    - signal < -0.4 → 1 (strong negative drift)

    Quality filters:
    - Days since earnings < 90 (drift fades after 3 months)
    - EPS surprise or revisions must be non-zero
    """
    signal_data = compute_earnings_drift_signal(symbol)

    drift_signal = signal_data["drift_signal"]
    eps_surprise = signal_data["eps_surprise_pct"]
    revisions = signal_data["analyst_revisions_30d"]
    days_since = signal_data["days_since_earnings"]

    # Rating logic
    if drift_signal > 0.4:
        rating = 5
    elif drift_signal > 0.2:
        rating = 4
    elif drift_signal >= -0.2:
        rating = 3
    elif drift_signal >= -0.4:
        rating = 2
    else:
        rating = 1

    # Quality adjustments
    if days_since > 90:
        # Too far from earnings, cap at 3
        rating = min(rating, 3)
        rationale_suffix = " (stale earnings)"
    elif eps_surprise == 0 and revisions == 0:
        # No signal, neutral
        rating = 3
        rationale_suffix = " (no surprise/revisions)"
    else:
        if rating >= 4:
            rationale_suffix = " ⇒ positive drift expected"
        elif rating <= 2:
            rationale_suffix = " ⇒ negative drift expected"
        else:
            rationale_suffix = " ⇒ neutral"

    rationale = f"PEAD: eps_surprise={eps_surprise:.1f}%, revisions={revisions}, days_since={days_since}" + rationale_suffix

    return {
        "rating": rating,
        "metrics": {
            "drift_signal": round(drift_signal, 3),
            "eps_surprise_pct": round(eps_surprise, 2),
            "analyst_revisions_30d": revisions,
            "days_since_earnings": days_since,
            "time_decay": round(signal_data["time_decay"], 3)
        },
        "rationale": rationale
    }


if __name__ == "__main__":
    import json
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = earnings_drift_rating(symbol)
    print(json.dumps(result, indent=2))
