"""
Quantitative Trading Strategies Engine
Implements 7 institutional-grade strategies with 1-5 rating system
"""

from .pairs_trading import cointegration_pairs_rating
from .ou_mean_reversion import ou_mean_reversion_rating
from .ts_momentum import ts_momentum_rating
from .value_strategy import value_strategy_rating
from .quality_strategy import quality_strategy_rating
from .earnings_drift import earnings_drift_rating
from .residual_momentum import residual_momentum_rating

__all__ = [
    'cointegration_pairs_rating',
    'ou_mean_reversion_rating',
    'ts_momentum_rating',
    'value_strategy_rating',
    'quality_strategy_rating',
    'earnings_drift_rating',
    'residual_momentum_rating'
]
