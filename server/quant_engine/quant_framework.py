"""
QuantLab Framework - Core utilities for quantitative analysis
Provides backtesting, risk metrics, portfolio analysis, and position sizing
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import sys
sys.path.append('server')
import stock_data


@dataclass
class BacktestResult:
    """Results from a backtest run"""
    equity_curve: pd.Series
    trades: pd.DataFrame
    metrics: Dict[str, float]
    positions: pd.DataFrame


@dataclass
class PositionSizing:
    """Position sizing recommendation"""
    shares: int
    notional: float
    pct_portfolio: float
    risk_pct: float
    kelly_fraction: Optional[float] = None
    volatility_adjusted: bool = False


@dataclass
class RiskMetrics:
    """Risk metrics for a strategy or position"""
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    volatility: float
    beta: Optional[float] = None
    alpha: Optional[float] = None


class QuantFramework:
    """Core framework for quantitative analysis"""

    @staticmethod
    def get_historical_data(symbol: str, period: str = "2y") -> pd.DataFrame:
        """Get historical OHLCV data"""
        data = stock_data.get_historical_data(symbol, period=period)
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()
        return df

    @staticmethod
    def calculate_returns(prices: pd.Series) -> pd.Series:
        """Calculate returns from prices"""
        return prices.pct_change().dropna()

    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio (annualized)"""
        if len(returns) < 2:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0

        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    @staticmethod
    def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if len(returns) < 2:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0

        return np.sqrt(252) * excess_returns.mean() / downside_returns.std()

    @staticmethod
    def calculate_max_drawdown(equity_curve: pd.Series) -> Tuple[float, int]:
        """Calculate maximum drawdown and its duration (days)"""
        if len(equity_curve) < 2:
            return 0.0, 0

        cummax = equity_curve.expanding().max()
        drawdown = (equity_curve - cummax) / cummax
        max_dd = drawdown.min()

        # Calculate duration
        dd_duration = 0
        current_dd_duration = 0
        in_drawdown = False

        for dd in drawdown:
            if dd < 0:
                current_dd_duration += 1
                in_drawdown = True
            else:
                if in_drawdown:
                    dd_duration = max(dd_duration, current_dd_duration)
                current_dd_duration = 0
                in_drawdown = False

        return abs(max_dd), dd_duration

    @staticmethod
    def calculate_calmar_ratio(returns: pd.Series, max_drawdown: float) -> float:
        """Calculate Calmar ratio (return / max drawdown)"""
        if max_drawdown == 0:
            return 0.0

        annualized_return = (1 + returns.mean()) ** 252 - 1
        return annualized_return / abs(max_drawdown)

    @staticmethod
    def calculate_win_rate(trades: pd.DataFrame) -> float:
        """Calculate win rate from trades"""
        if len(trades) == 0:
            return 0.0

        winning_trades = trades[trades['pnl'] > 0]
        return len(winning_trades) / len(trades)

    @staticmethod
    def calculate_profit_factor(trades: pd.DataFrame) -> float:
        """Calculate profit factor (gross wins / gross losses)"""
        if len(trades) == 0:
            return 0.0

        gross_profit = trades[trades['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(trades[trades['pnl'] < 0]['pnl'].sum())

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0

        return gross_profit / gross_loss

    @staticmethod
    def calculate_risk_metrics(returns: pd.Series, equity_curve: pd.Series,
                              trades: pd.DataFrame, benchmark_returns: Optional[pd.Series] = None) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""

        sharpe = QuantFramework.calculate_sharpe_ratio(returns)
        sortino = QuantFramework.calculate_sortino_ratio(returns)
        max_dd, dd_duration = QuantFramework.calculate_max_drawdown(equity_curve)
        calmar = QuantFramework.calculate_calmar_ratio(returns, max_dd)
        win_rate = QuantFramework.calculate_win_rate(trades)
        profit_factor = QuantFramework.calculate_profit_factor(trades)

        winning_trades = trades[trades['pnl'] > 0]
        losing_trades = trades[trades['pnl'] < 0]

        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0.0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0.0
        volatility = returns.std() * np.sqrt(252)

        # Calculate beta and alpha if benchmark provided
        beta = None
        alpha = None
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            common_idx = returns.index.intersection(benchmark_returns.index)
            if len(common_idx) > 20:
                cov = np.cov(returns.loc[common_idx], benchmark_returns.loc[common_idx])[0, 1]
                benchmark_var = benchmark_returns.loc[common_idx].var()
                if benchmark_var > 0:
                    beta = cov / benchmark_var
                    alpha = (returns.loc[common_idx].mean() - beta * benchmark_returns.loc[common_idx].mean()) * 252

        return RiskMetrics(
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            max_drawdown_duration=dd_duration,
            calmar_ratio=calmar,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            volatility=volatility,
            beta=beta,
            alpha=alpha
        )

    @staticmethod
    def simple_backtest(prices: pd.Series, signals: pd.Series,
                       initial_capital: float = 100000,
                       commission: float = 0.001) -> BacktestResult:
        """
        Simple vectorized backtest

        signals: 1 (long), 0 (cash), -1 (short)
        """

        # Align signals with prices
        signals = signals.reindex(prices.index, method='ffill').fillna(0)

        # Calculate returns
        returns = prices.pct_change()

        # Strategy returns (shifted to avoid look-ahead bias)
        strategy_returns = signals.shift(1) * returns

        # Apply commission on trades (when signal changes)
        signal_changes = signals.diff().abs()
        commission_costs = signal_changes * commission
        strategy_returns = strategy_returns - commission_costs

        # Calculate equity curve
        equity_curve = initial_capital * (1 + strategy_returns).cumprod()
        equity_curve = equity_curve.fillna(initial_capital)

        # Generate trades dataframe
        trades_list = []
        position = 0
        entry_price = 0
        entry_date = None

        for date, signal in signals.items():
            if signal != position:
                # Close existing position if any
                if position != 0 and entry_price > 0:
                    exit_price = prices.loc[date]
                    pnl = (exit_price - entry_price) / entry_price * position
                    trades_list.append({
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position': position,
                        'pnl': pnl,
                        'pnl_dollars': pnl * initial_capital
                    })

                # Open new position
                if signal != 0:
                    position = signal
                    entry_price = prices.loc[date]
                    entry_date = date
                else:
                    position = 0
                    entry_price = 0

        trades_df = pd.DataFrame(trades_list)

        # Positions dataframe
        positions = pd.DataFrame({
            'signal': signals,
            'price': prices,
            'equity': equity_curve
        })

        # Calculate metrics
        metrics = {
            'total_return': (equity_curve.iloc[-1] / initial_capital - 1) * 100,
            'annualized_return': ((equity_curve.iloc[-1] / initial_capital) ** (252 / len(equity_curve)) - 1) * 100,
            'num_trades': len(trades_df),
            'total_commission': (commission_costs.sum() * initial_capital)
        }

        return BacktestResult(
            equity_curve=equity_curve,
            trades=trades_df,
            metrics=metrics,
            positions=positions
        )

    @staticmethod
    def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Calculate Kelly Criterion for position sizing"""
        if avg_loss == 0:
            return 0.0

        win_loss_ratio = abs(avg_win / avg_loss)
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio

        # Use fractional Kelly (half Kelly is common)
        return max(0, min(kelly * 0.5, 1.0))

    @staticmethod
    def volatility_position_sizing(price: float, portfolio_value: float,
                                   volatility: float, target_vol: float = 0.15) -> PositionSizing:
        """
        Calculate position size based on volatility targeting

        target_vol: target portfolio volatility (default 15%)
        """
        if volatility == 0 or price == 0:
            return PositionSizing(0, 0, 0, 0, volatility_adjusted=True)

        # Calculate position size to achieve target volatility
        position_pct = target_vol / volatility
        position_pct = min(position_pct, 1.0)  # Max 100% of portfolio

        notional = portfolio_value * position_pct
        shares = int(notional / price)
        actual_notional = shares * price
        actual_pct = actual_notional / portfolio_value

        return PositionSizing(
            shares=shares,
            notional=actual_notional,
            pct_portfolio=actual_pct * 100,
            risk_pct=actual_pct * volatility * 100,
            volatility_adjusted=True
        )

    @staticmethod
    def fixed_fractional_sizing(price: float, portfolio_value: float,
                               risk_per_trade: float = 0.02) -> PositionSizing:
        """
        Fixed fractional position sizing (e.g., 2% risk per trade)
        """
        if price == 0:
            return PositionSizing(0, 0, 0, 0)

        notional = portfolio_value * risk_per_trade
        shares = int(notional / price)
        actual_notional = shares * price
        actual_pct = actual_notional / portfolio_value

        return PositionSizing(
            shares=shares,
            notional=actual_notional,
            pct_portfolio=actual_pct * 100,
            risk_pct=risk_per_trade * 100
        )

    @staticmethod
    def portfolio_heat_check(holdings: List[Dict], portfolio_value: float,
                           max_total_risk: float = 0.20) -> Dict[str, Any]:
        """
        Check total portfolio risk ('heat')

        Returns risk metrics and whether it's safe to add new positions
        """
        total_exposure = sum(h.get('notional', 0) for h in holdings)
        total_risk = sum(h.get('risk', 0) for h in holdings)

        exposure_pct = total_exposure / portfolio_value if portfolio_value > 0 else 0
        risk_pct = total_risk / portfolio_value if portfolio_value > 0 else 0

        available_risk = max(0, max_total_risk - risk_pct)
        can_add_position = risk_pct < max_total_risk

        return {
            'total_exposure': total_exposure,
            'exposure_pct': exposure_pct * 100,
            'total_risk': total_risk,
            'risk_pct': risk_pct * 100,
            'available_risk_pct': available_risk * 100,
            'can_add_position': can_add_position,
            'risk_limit_pct': max_total_risk * 100
        }


# Convenience functions
def backtest_strategy(symbol: str, generate_signals_func, period: str = "2y") -> Dict[str, Any]:
    """
    Convenience function to backtest a strategy

    generate_signals_func should take a DataFrame and return a Series of signals (1, 0, -1)
    """
    framework = QuantFramework()

    # Get data
    df = framework.get_historical_data(symbol, period)
    if df.empty:
        return {"error": "No data available"}

    # Generate signals
    signals = generate_signals_func(df)

    # Run backtest
    result = framework.simple_backtest(df['close'], signals)

    # Calculate risk metrics
    returns = framework.calculate_returns(result.equity_curve)
    risk_metrics = framework.calculate_risk_metrics(returns, result.equity_curve, result.trades)

    return {
        'backtest_result': result,
        'risk_metrics': risk_metrics,
        'final_equity': result.equity_curve.iloc[-1],
        'total_return_pct': result.metrics['total_return'],
        'annualized_return_pct': result.metrics['annualized_return'],
        'num_trades': result.metrics['num_trades'],
        'sharpe_ratio': risk_metrics.sharpe_ratio,
        'max_drawdown_pct': risk_metrics.max_drawdown * 100,
        'win_rate_pct': risk_metrics.win_rate * 100
    }
