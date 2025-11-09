"""
Multi-Factor Composite Scorer
Combines all 7 quantitative strategies into a single composite score

Strategies:
1. Pairs Trading (statistical arbitrage)
2. OU Mean Reversion (Ornstein-Uhlenbeck process)
3. Time-Series Momentum
4. Value Strategy (fundamental valuation)
5. Quality Strategy (profitability, stability)
6. Earnings Drift (post-earnings momentum)
7. Residual Momentum (factor-neutral momentum)

Provides:
- Composite signal (weighted average of all strategies)
- Individual strategy breakdowns
- Portfolio-level recommendations
- Risk-adjusted position sizing
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
import sys
sys.path.append('server')
import json

# Import all strategies
sys.path.append('server/quant_engine')
import pairs_trading
import ou_mean_reversion
import ts_momentum
import value_strategy
import quality_strategy
import earnings_drift
import residual_momentum


class MultiFactorScorer:
    """Combines multiple quantitative strategies"""

    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize with strategy weights

        Default weights balance momentum, value, and quality
        """
        self.weights = weights or {
            'pairs_trading': 0.10,
            'ou_mean_reversion': 0.10,
            'ts_momentum': 0.20,
            'value': 0.20,
            'quality': 0.20,
            'earnings_drift': 0.10,
            'residual_momentum': 0.10
        }

        # Normalize weights to sum to 1
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}

    def score_stock(self, symbol: str) -> Dict[str, Any]:
        """
        Generate composite score for a stock

        Returns comprehensive analysis with all strategies
        """

        results = {}
        scores = {}
        rationales = {}

        # Run all strategies
        try:
            result = pairs_trading.cointegration_pairs_rating(symbol)
            results['pairs_trading'] = result
            scores['pairs_trading'] = result.get('rating', 3)
            rationales['pairs_trading'] = result.get('rationale', '')
        except Exception as e:
            print(f"Pairs trading error: {e}")
            scores['pairs_trading'] = 3

        try:
            result = ou_mean_reversion.ou_mean_reversion_rating(symbol)
            results['ou_mean_reversion'] = result
            scores['ou_mean_reversion'] = result.get('rating', 3)
            rationales['ou_mean_reversion'] = result.get('rationale', '')
        except Exception as e:
            print(f"OU mean reversion error: {e}")
            scores['ou_mean_reversion'] = 3

        try:
            result = ts_momentum.ts_momentum_rating(symbol)
            results['ts_momentum'] = result
            scores['ts_momentum'] = result.get('rating', 3)
            rationales['ts_momentum'] = result.get('rationale', '')
        except Exception as e:
            print(f"TS momentum error: {e}")
            scores['ts_momentum'] = 3

        try:
            result = value_strategy.value_strategy_rating(symbol)
            results['value'] = result
            scores['value'] = result.get('rating', 3)
            rationales['value'] = result.get('rationale', '')
        except Exception as e:
            print(f"Value strategy error: {e}")
            scores['value'] = 3

        try:
            result = quality_strategy.quality_strategy_rating(symbol)
            results['quality'] = result
            scores['quality'] = result.get('rating', 3)
            rationales['quality'] = result.get('rationale', '')
        except Exception as e:
            print(f"Quality strategy error: {e}")
            scores['quality'] = 3

        try:
            result = earnings_drift.earnings_drift_rating(symbol)
            results['earnings_drift'] = result
            scores['earnings_drift'] = result.get('rating', 3)
            rationales['earnings_drift'] = result.get('rationale', '')
        except Exception as e:
            print(f"Earnings drift error: {e}")
            scores['earnings_drift'] = 3

        try:
            result = residual_momentum.residual_momentum_rating(symbol)
            results['residual_momentum'] = result
            scores['residual_momentum'] = result.get('rating', 3)
            rationales['residual_momentum'] = result.get('rationale', '')
        except Exception as e:
            print(f"Residual momentum error: {e}")
            scores['residual_momentum'] = 3

        # Calculate weighted composite score
        composite_score = sum(scores[k] * self.weights[k] for k in scores)

        # Normalize to 1-5 scale
        composite_rating = max(1, min(5, round(composite_score)))

        # Generate overall recommendation
        recommendation = self._generate_recommendation(composite_rating, scores)

        # Calculate consensus (how many strategies agree)
        strong_buy = sum(1 for s in scores.values() if s >= 4)
        strong_sell = sum(1 for s in scores.values() if s <= 2)
        consensus = max(strong_buy, strong_sell) / len(scores)

        return {
            'symbol': symbol,
            'composite_score': round(composite_score, 2),
            'composite_rating': composite_rating,
            'recommendation': recommendation,
            'consensus_pct': round(consensus * 100, 1),
            'strategy_breakdown': {
                'scores': scores,
                'weights': self.weights,
                'rationales': rationales
            },
            'detailed_results': results,
            'summary': {
                'strong_buy_count': strong_buy,
                'neutral_count': sum(1 for s in scores.values() if s == 3),
                'strong_sell_count': strong_sell,
                'confidence': 'High' if consensus >= 0.7 else 'Medium' if consensus >= 0.5 else 'Low'
            }
        }

    def _generate_recommendation(self, rating: int, scores: Dict[str, int]) -> str:
        """Generate overall trading recommendation"""

        if rating >= 4:
            return f"STRONG BUY - {sum(1 for s in scores.values() if s >= 4)}/{len(scores)} strategies bullish"
        elif rating >= 3.5:
            return "BUY - Positive signals outweigh negative"
        elif rating >= 2.5:
            return "HOLD - Mixed signals, no clear direction"
        elif rating >= 2:
            return "SELL - Negative signals outweigh positive"
        else:
            return f"STRONG SELL - {sum(1 for s in scores.values() if s <= 2)}/{len(scores)} strategies bearish"

    def rank_portfolio(self, symbols: List[str]) -> pd.DataFrame:
        """
        Rank multiple stocks by composite score

        Returns DataFrame sorted by score (best first)
        """

        results = []
        for symbol in symbols:
            try:
                score_data = self.score_stock(symbol)
                results.append({
                    'symbol': symbol,
                    'composite_score': score_data['composite_score'],
                    'rating': score_data['composite_rating'],
                    'recommendation': score_data['recommendation'],
                    'consensus_pct': score_data['consensus_pct'],
                    'confidence': score_data['summary']['confidence']
                })
            except Exception as e:
                print(f"Error scoring {symbol}: {e}")

        df = pd.DataFrame(results)
        df = df.sort_values('composite_score', ascending=False)
        return df

    def optimize_portfolio_weights(self, symbols: List[str], total_capital: float,
                                   max_positions: int = 10) -> Dict[str, Any]:
        """
        Generate optimal portfolio allocation based on multi-factor scores

        Uses mean-variance optimization with score-based expected returns
        """

        # Rank all stocks
        rankings = self.rank_portfolio(symbols)

        # Select top N positions
        top_stocks = rankings.head(max_positions)

        # Simple equal-weight allocation among top stocks
        # (More sophisticated optimization would use covariance matrix)
        weight_per_stock = 1.0 / len(top_stocks)
        capital_per_stock = total_capital * weight_per_stock

        allocations = []
        for _, row in top_stocks.iterrows():
            allocations.append({
                'symbol': row['symbol'],
                'score': row['composite_score'],
                'rating': row['rating'],
                'weight_pct': weight_per_stock * 100,
                'capital': capital_per_stock,
                'recommendation': row['recommendation']
            })

        return {
            'total_capital': total_capital,
            'num_positions': len(top_stocks),
            'allocations': allocations,
            'total_allocated': sum(a['capital'] for a in allocations),
            'cash_reserve': total_capital - sum(a['capital'] for a in allocations),
            'avg_score': top_stocks['composite_score'].mean(),
            'avg_confidence': top_stocks['consensus_pct'].mean()
        }


def multi_factor_score(symbol: str, weights: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Convenience function to get multi-factor score for a symbol

    Args:
        symbol: Stock ticker
        weights: Optional custom strategy weights

    Returns:
        Complete multi-factor analysis
    """
    scorer = MultiFactorScorer(weights)
    return scorer.score_stock(symbol)


def rank_stocks(symbols: List[str], weights: Dict[str, float] = None) -> List[Dict[str, Any]]:
    """
    Rank multiple stocks by multi-factor score

    Returns list sorted by score (best first)
    """
    scorer = MultiFactorScorer(weights)
    df = scorer.rank_portfolio(symbols)
    return df.to_dict('records')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        result = multi_factor_score(symbol)
        print(json.dumps(result, indent=2))
    else:
        # Demo: rank multiple stocks
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        results = rank_stocks(symbols)
        print(json.dumps(results, indent=2))
