"""
Strategy 4: Cross-Sectional Value
Cheap stocks outperform expensive ones within industries

Uses: P/E, P/B, EV/EBITDA, Dividend Yield
Industry-neutral: rank within sector
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
import sys
sys.path.append('server')
import stock_data

# Industry groupings (simplified GICS sectors)
INDUSTRY_PEERS = {
    # Technology
    "AAPL": ["MSFT", "GOOGL", "META", "NVDA", "AMD", "INTC"],
    "MSFT": ["AAPL", "GOOGL", "META", "NVDA", "AMD", "INTC"],
    "GOOGL": ["AAPL", "MSFT", "META", "NVDA", "AMD", "INTC"],
    "META": ["AAPL", "MSFT", "GOOGL", "NVDA", "AMD", "INTC"],
    "NVDA": ["AAPL", "MSFT", "GOOGL", "META", "AMD", "INTC"],
    "AMD": ["NVDA", "INTC", "AAPL", "MSFT"],
    "INTC": ["AMD", "NVDA", "AAPL", "MSFT"],

    # E-commerce / Consumer
    "AMZN": ["WMT", "TGT", "COST", "EBAY"],
    "WMT": ["AMZN", "TGT", "COST"],
    "TGT": ["WMT", "AMZN", "COST"],
    "COST": ["WMT", "TGT", "AMZN"],

    # Autos
    "TSLA": ["F", "GM", "RIVN", "LCID"],
    "F": ["GM", "TSLA"],
    "GM": ["F", "TSLA"],

    # Finance
    "JPM": ["BAC", "WFC", "C", "GS", "MS"],
    "BAC": ["JPM", "WFC", "C"],
    "WFC": ["JPM", "BAC", "C"],
    "GS": ["MS", "JPM", "C"],
    "MS": ["GS", "JPM", "C"],

    # Default: use SPY components
    "default": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
}

def get_valuation_metrics(symbol: str) -> Dict[str, float]:
    """
    Get valuation metrics for a stock
    Uses OpenBB or mock data for demo

    Returns: {
        "pe_ratio": Forward P/E
        "pb_ratio": Price-to-Book
        "ev_ebitda": Enterprise Value / EBITDA
        "div_yield": Dividend Yield
    }
    """
    # Mock data for demo (in production, fetch from OpenBB fundamentals)
    # This would normally come from stock_data.get_fundamentals(symbol)

    mock_valuations = {
        "AAPL": {"pe": 28.5, "pb": 42.0, "ev_ebitda": 22.3, "div_yield": 0.5},
        "MSFT": {"pe": 32.1, "pb": 12.8, "ev_ebitda": 24.1, "div_yield": 0.8},
        "GOOGL": {"pe": 24.2, "pb": 6.1, "ev_ebitda": 15.3, "div_yield": 0.0},
        "AMZN": {"pe": 52.3, "pb": 8.4, "ev_ebitda": 28.7, "div_yield": 0.0},
        "META": {"pe": 22.4, "pb": 6.8, "ev_ebitda": 13.2, "div_yield": 0.4},
        "NVDA": {"pe": 65.2, "pb": 45.3, "ev_ebitda": 48.1, "div_yield": 0.1},
        "TSLA": {"pe": 78.3, "pb": 15.2, "ev_ebitda": 42.5, "div_yield": 0.0},
        "JPM": {"pe": 11.2, "pb": 1.6, "ev_ebitda": None, "div_yield": 2.8},
        "BAC": {"pe": 10.5, "pb": 1.3, "ev_ebitda": None, "div_yield": 2.5},
        "WMT": {"pe": 28.2, "pb": 5.1, "ev_ebitda": 14.8, "div_yield": 1.5},
        "AMD": {"pe": 142.3, "pb": 3.8, "ev_ebitda": 38.2, "div_yield": 0.0},
        "INTC": {"pe": 18.5, "pb": 1.9, "ev_ebitda": 11.2, "div_yield": 1.3},
    }

    if symbol in mock_valuations:
        data = mock_valuations[symbol]
        return {
            "pe_ratio": data["pe"],
            "pb_ratio": data["pb"],
            "ev_ebitda": data["ev_ebitda"],
            "div_yield": data["div_yield"]
        }
    else:
        # Default fallback
        return {
            "pe_ratio": 20.0,
            "pb_ratio": 3.0,
            "ev_ebitda": 12.0,
            "div_yield": 1.0
        }

def compute_value_z_score(symbol: str, peers: List[str]) -> Dict[str, float]:
    """
    Compute z-score of valuation metrics relative to peers

    Lower P/E, P/B, EV/EBITDA = cheaper = positive z-score
    Higher dividend yield = cheaper = positive z-score
    """
    target_metrics = get_valuation_metrics(symbol)

    # Get peer metrics
    peer_metrics_list = []
    for peer in peers:
        if peer != symbol:
            pm = get_valuation_metrics(peer)
            peer_metrics_list.append(pm)

    if len(peer_metrics_list) == 0:
        return {
            "value_z_score": 0.0,
            "pe_z": 0.0,
            "pb_z": 0.0,
            "ev_z": 0.0,
            "div_z": 0.0
        }

    # Extract arrays
    pe_array = [pm["pe_ratio"] for pm in peer_metrics_list if pm["pe_ratio"] is not None]
    pb_array = [pm["pb_ratio"] for pm in peer_metrics_list if pm["pb_ratio"] is not None]
    ev_array = [pm["ev_ebitda"] for pm in peer_metrics_list if pm["ev_ebitda"] is not None]
    div_array = [pm["div_yield"] for pm in peer_metrics_list if pm["div_yield"] is not None]

    # Compute z-scores (invert for P/E, P/B, EV - lower is better)
    pe_z = 0.0
    if len(pe_array) > 1 and target_metrics["pe_ratio"] is not None:
        pe_mean = np.mean(pe_array)
        pe_std = np.std(pe_array)
        if pe_std > 0:
            pe_z = -(target_metrics["pe_ratio"] - pe_mean) / pe_std  # Negative: lower is better

    pb_z = 0.0
    if len(pb_array) > 1 and target_metrics["pb_ratio"] is not None:
        pb_mean = np.mean(pb_array)
        pb_std = np.std(pb_array)
        if pb_std > 0:
            pb_z = -(target_metrics["pb_ratio"] - pb_mean) / pb_std

    ev_z = 0.0
    if len(ev_array) > 1 and target_metrics["ev_ebitda"] is not None:
        ev_mean = np.mean(ev_array)
        ev_std = np.std(ev_array)
        if ev_std > 0:
            ev_z = -(target_metrics["ev_ebitda"] - ev_mean) / ev_std

    div_z = 0.0
    if len(div_array) > 1 and target_metrics["div_yield"] is not None:
        div_mean = np.mean(div_array)
        div_std = np.std(div_array)
        if div_std > 0:
            div_z = (target_metrics["div_yield"] - div_mean) / div_std  # Positive: higher is better

    # Composite value z-score (equal weight)
    value_z_score = (pe_z + pb_z + ev_z + div_z) / 4.0

    return {
        "value_z_score": value_z_score,
        "pe_z": pe_z,
        "pb_z": pb_z,
        "ev_z": ev_z,
        "div_z": div_z
    }

def value_rating(symbol: str) -> Dict[str, Any]:
    """
    Generate 1-5 rating for cross-sectional value strategy

    Rating Scale (based on composite value z-score):
    - z > 1.0 → 5 (very cheap relative to peers)
    - 0.5 < z ≤ 1.0 → 4
    - -0.5 ≤ z ≤ 0.5 → 3 (neutral)
    - -1.0 ≤ z < -0.5 → 2
    - z < -1.0 → 1 (very expensive relative to peers)
    """
    # Get industry peers
    peers = INDUSTRY_PEERS.get(symbol, INDUSTRY_PEERS["default"])

    # Compute value z-score
    z_scores = compute_value_z_score(symbol, peers)
    value_z = z_scores["value_z_score"]

    # Rating logic
    if value_z > 1.0:
        rating = 5
    elif value_z > 0.5:
        rating = 4
    elif value_z >= -0.5:
        rating = 3
    elif value_z >= -1.0:
        rating = 2
    else:
        rating = 1

    if rating >= 4:
        rationale_suffix = " ⇒ cheap relative to peers"
    elif rating <= 2:
        rationale_suffix = " ⇒ expensive relative to peers"
    else:
        rationale_suffix = " ⇒ neutral valuation"

    rationale = f"Value z-score={value_z:.2f} (PE_z={z_scores['pe_z']:.2f}, PB_z={z_scores['pb_z']:.2f})" + rationale_suffix

    return {
        "rating": rating,
        "metrics": {
            "value_z_score": round(value_z, 3),
            "pe_z": round(z_scores["pe_z"], 3),
            "pb_z": round(z_scores["pb_z"], 3),
            "ev_z": round(z_scores["ev_z"], 3),
            "div_z": round(z_scores["div_z"], 3),
            "num_peers": len(peers)
        },
        "rationale": rationale
    }


if __name__ == "__main__":
    import json
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = value_rating(symbol)
    print(json.dumps(result, indent=2))
