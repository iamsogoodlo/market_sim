"""
Quantitative Trading Strategies Engine
Implements 7 institutional-grade strategies with 1-5 rating system
"""

from .pairs_trading import cointegration_pairs_rating
from .ou_mean_reversion import ou_mean_reversion_rating
from .ts_momentum import time_series_momentum_rating
from .value import cross_sectional_value_rating
from .quality import quality_profitability_rating
from .earnings import earnings_surprise_rating
from .residual_momentum import residual_momentum_rating

__all__ = [
    'cointegration_pairs_rating',
    'ou_mean_reversion_rating',
    'time_series_momentum_rating',
    'cross_sectional_value_rating',
    'quality_profitability_rating',
    'earnings_surprise_rating',
    'residual_momentum_rating'
]
