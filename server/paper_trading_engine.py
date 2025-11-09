"""
Paper Trading Fill Simulator
Implements execution model from PRD Section 8: Execution Simulator (Paper)

Features:
- Market orders: fill at next-bar open ± slippage (≥ 1 tick)
- Limit orders: fill if price within bar range, partial fills allowed
- Stop/Stop-Limit: trigger logic → market/limit rules
- Slippage model: max(1 tick, k * volume_ratio)
- Risk checks: leverage, position size, order notional
"""

import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import logging

from schemas import (
    Order, OrderCreate, OrderStatus, OrderType, OrderSide,
    Fill, Position, Account, RiskLimits, RiskCheck, Bar
)

logger = logging.getLogger(__name__)


class PaperTradingEngine:
    """
    Deterministic paper trading engine with realistic fill simulation.
    """

    def __init__(
        self,
        account_id: str = "paper_default",
        initial_cash: float = 100000.0,
        risk_limits: Optional[RiskLimits] = None,
        tick_size: float = 0.01,
        slippage_k: float = 0.01,  # Slippage coefficient
        participation_rate: float = 0.10,  # Max % of bar volume
    ):
        self.account_id = account_id
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.risk_limits = risk_limits or RiskLimits()
        self.tick_size = tick_size
        self.slippage_k = slippage_k
        self.participation_rate = participation_rate

        # State
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.fills: List[Fill] = []
        self.current_prices: Dict[str, float] = {}
        self.current_timestamp: int = 0

        # Commission: $0.001 per share or 0.1%
        self.commission_per_share = 0.001

    def _generate_id(self) -> str:
        """Generate unique ID"""
        return uuid.uuid4().hex[:16]

    # ========================================================================
    # Order Submission & Risk Checks
    # ========================================================================

    def submit_order(self, order_req: OrderCreate, timestamp: int) -> Tuple[Optional[Order], Optional[str]]:
        """
        Submit order with risk checks.
        Returns: (Order, error_message)
        """
        self.current_timestamp = timestamp

        # Risk check
        check = self._risk_check(order_req)
        if not check.passed:
            logger.warning(f"Order rejected: {check.violations}")
            return None, "; ".join(check.violations)

        # Create order
        order = Order(
            id=self._generate_id(),
            symbol=order_req.symbol,
            side=order_req.side,
            type=order_req.type,
            qty=order_req.qty,
            filled_qty=0,
            remaining_qty=order_req.qty,
            limit_price=order_req.limit_price,
            stop_price=order_req.stop_price,
            tif=order_req.tif,
            status=OrderStatus.NEW,
            created_at=timestamp,
            updated_at=timestamp,
        )

        # Market orders → WORKING immediately
        if order.type == OrderType.MARKET:
            order.status = OrderStatus.WORKING

        # Stop orders → NEW until triggered
        elif order.type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            order.status = OrderStatus.NEW
        else:
            # Limit orders → WORKING
            order.status = OrderStatus.WORKING

        self.orders[order.id] = order
        logger.info(f"Order submitted: {order.id} {order.side} {order.qty} {order.symbol} @ {order.type}")
        return order, None

    def _risk_check(self, order: OrderCreate) -> RiskCheck:
        """
        Perform risk checks per PRD Section 8.
        """
        violations = []
        current_leverage = self._calculate_leverage()

        # Estimate order value
        price = order.limit_price or self.current_prices.get(order.symbol, 0)
        if price == 0:
            violations.append(f"No price data for {order.symbol}")
            return RiskCheck(
                passed=False,
                order=order,
                violations=violations,
                current_leverage=current_leverage,
                resulting_leverage=current_leverage,
                timestamp=self.current_timestamp,
            )

        order_notional = price * order.qty

        # 1. Max order notional
        if order_notional > self.risk_limits.max_order_notional:
            violations.append(
                f"Order notional ${order_notional:.2f} exceeds limit ${self.risk_limits.max_order_notional:.2f}"
            )

        # 2. Max position size % (of equity)
        equity = self._calculate_equity()
        max_position_value = equity * self.risk_limits.max_position_size_pct

        # Calculate resulting position
        current_pos = self.positions.get(order.symbol)
        current_qty = current_pos.qty if current_pos else 0
        resulting_qty = current_qty + (order.qty if order.side == OrderSide.BUY else -order.qty)
        resulting_position_value = abs(resulting_qty * price)

        if resulting_position_value > max_position_value:
            violations.append(
                f"Resulting position ${resulting_position_value:.2f} exceeds {self.risk_limits.max_position_size_pct*100}% limit"
            )

        # 3. Max symbols
        if order.symbol not in self.positions and len(self.positions) >= self.risk_limits.max_symbols:
            violations.append(f"Max symbols limit ({self.risk_limits.max_symbols}) reached")

        # 4. Leverage check (buying power)
        buying_power = self._calculate_buying_power()
        if order.side == OrderSide.BUY and order_notional > buying_power:
            violations.append(
                f"Insufficient buying power ${buying_power:.2f} for order ${order_notional:.2f}"
            )

        # 5. Leverage limit
        # Estimate resulting leverage
        positions_value = sum(abs(p.qty * self.current_prices.get(p.symbol, p.current_price))
                             for p in self.positions.values())
        resulting_positions_value = positions_value + (order_notional if order.side == OrderSide.BUY else -order_notional)
        resulting_leverage = resulting_positions_value / equity if equity > 0 else 0

        if resulting_leverage > self.risk_limits.max_leverage:
            violations.append(
                f"Resulting leverage {resulting_leverage:.2f}x exceeds limit {self.risk_limits.max_leverage:.2f}x"
            )

        return RiskCheck(
            passed=len(violations) == 0,
            order=order,
            violations=violations,
            current_leverage=current_leverage,
            resulting_leverage=resulting_leverage,
            timestamp=self.current_timestamp,
        )

    # ========================================================================
    # Order Processing on Bar Update
    # ========================================================================

    def process_bar(self, symbol: str, bar: Bar) -> List[Fill]:
        """
        Process all orders for a symbol given a new bar.
        Returns list of fills generated.
        """
        self.current_timestamp = bar.ts
        self.current_prices[symbol] = bar.close
        fills = []

        # Get all orders for this symbol
        symbol_orders = [o for o in self.orders.values() if o.symbol == symbol and o.status in [OrderStatus.NEW, OrderStatus.WORKING]]

        for order in symbol_orders:
            # Check stop triggers first
            if order.type in [OrderType.STOP, OrderType.STOP_LIMIT]:
                triggered = self._check_stop_trigger(order, bar)
                if triggered and order.status == OrderStatus.NEW:
                    order.status = OrderStatus.WORKING
                    order.updated_at = bar.ts
                    logger.info(f"Stop order triggered: {order.id}")

            # Process working orders
            if order.status == OrderStatus.WORKING:
                fill = self._try_fill_order(order, bar)
                if fill:
                    fills.append(fill)
                    self._process_fill(order, fill)

        return fills

    def _check_stop_trigger(self, order: Order, bar: Bar) -> bool:
        """Check if stop order should trigger"""
        if not order.stop_price:
            return False

        if order.side == OrderSide.BUY:
            # Buy stop triggers when price goes above stop
            return bar.high >= order.stop_price
        else:
            # Sell stop triggers when price goes below stop
            return bar.low <= order.stop_price

    def _try_fill_order(self, order: Order, bar: Bar) -> Optional[Fill]:
        """
        Attempt to fill order based on type and bar data.
        Returns Fill if successful, None otherwise.
        """
        if order.type == OrderType.MARKET or (order.type == OrderType.STOP and order.status == OrderStatus.WORKING):
            return self._fill_market_order(order, bar)

        elif order.type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
            return self._fill_limit_order(order, bar)

        return None

    def _fill_market_order(self, order: Order, bar: Bar) -> Fill:
        """
        Fill market order at next-bar open ± slippage.
        Per PRD: fill at open with slippage ≥ 1 tick.
        """
        # Use open price as base
        base_price = bar.open

        # Calculate slippage
        volume_ratio = min(order.remaining_qty / bar.volume, self.participation_rate) if bar.volume > 0 else self.participation_rate
        slippage_dollars = max(self.tick_size, self.slippage_k * volume_ratio * base_price)

        # Apply slippage direction (unfavorable)
        if order.side == OrderSide.BUY:
            fill_price = base_price + slippage_dollars
        else:
            fill_price = base_price - slippage_dollars

        fill_price = round(fill_price, 2)

        # Calculate commission
        commission = order.remaining_qty * self.commission_per_share

        fill = Fill(
            id=self._generate_id(),
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            price=fill_price,
            qty=order.remaining_qty,
            commission=commission,
            slippage=slippage_dollars * order.remaining_qty,
            timestamp=bar.ts,
        )

        logger.info(f"Market fill: {order.id} {fill.qty} @ ${fill.price:.2f} (slippage: ${slippage_dollars:.4f})")
        return fill

    def _fill_limit_order(self, order: Order, bar: Bar) -> Optional[Fill]:
        """
        Fill limit order if price within bar range.
        Partial fills allowed based on volume participation.
        Per PRD: fill at limit ± partial slippage if (low ≤ limit ≤ high).
        """
        if not order.limit_price:
            return None

        # Check if limit is within bar range
        if not (bar.low <= order.limit_price <= bar.high):
            return None

        # Calculate fillable quantity (max participation_rate of bar volume)
        max_fillable = int(bar.volume * self.participation_rate)
        fill_qty = min(order.remaining_qty, max_fillable)

        if fill_qty == 0:
            return None

        # Fill at limit price with small slippage for partial fills
        fill_price = order.limit_price
        partial_slippage = 0.0

        if fill_qty < order.remaining_qty:
            # Partial fill → add tick of slippage
            if order.side == OrderSide.BUY:
                fill_price += self.tick_size
            else:
                fill_price -= self.tick_size
            partial_slippage = self.tick_size * fill_qty

        fill_price = round(fill_price, 2)

        # Calculate commission
        commission = fill_qty * self.commission_per_share

        fill = Fill(
            id=self._generate_id(),
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            price=fill_price,
            qty=fill_qty,
            commission=commission,
            slippage=partial_slippage,
            timestamp=bar.ts,
        )

        logger.info(f"Limit fill: {order.id} {fill.qty}/{order.remaining_qty} @ ${fill.price:.2f}")
        return fill

    def _process_fill(self, order: Order, fill: Fill):
        """Process fill: update order, position, cash"""
        # Update order
        order.filled_qty += fill.qty
        order.remaining_qty -= fill.qty
        order.avg_fill_price = (
            (order.avg_fill_price or 0) * (order.filled_qty - fill.qty) + fill.price * fill.qty
        ) / order.filled_qty if order.filled_qty > 0 else fill.price

        if order.remaining_qty == 0:
            order.status = OrderStatus.FILLED
        else:
            order.status = OrderStatus.PARTIALLY_FILLED

        order.updated_at = fill.timestamp

        # Update position
        self._update_position(fill)

        # Update cash
        if fill.side == OrderSide.BUY:
            self.cash -= (fill.price * fill.qty + fill.commission)
        else:
            self.cash += (fill.price * fill.qty - fill.commission)

        # Store fill
        self.fills.append(fill)

    def _update_position(self, fill: Fill):
        """Update or create position from fill"""
        if fill.symbol not in self.positions:
            # New position
            position = Position(
                symbol=fill.symbol,
                qty=fill.qty if fill.side == OrderSide.BUY else -fill.qty,
                avg_price=fill.price,
                cost_basis=fill.price * fill.qty,
                current_price=fill.price,
                market_value=fill.price * fill.qty,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                last_updated=fill.timestamp,
            )
            self.positions[fill.symbol] = position
        else:
            position = self.positions[fill.symbol]
            old_qty = position.qty

            # Update quantity
            if fill.side == OrderSide.BUY:
                position.qty += fill.qty
            else:
                position.qty -= fill.qty

            # Update avg price (for same direction) or realize P&L (for closing)
            if (old_qty > 0 and fill.side == OrderSide.BUY) or (old_qty < 0 and fill.side == OrderSide.SELL):
                # Adding to position
                total_cost = position.avg_price * abs(old_qty) + fill.price * fill.qty
                position.avg_price = total_cost / abs(position.qty) if position.qty != 0 else fill.price
                position.cost_basis = position.avg_price * abs(position.qty)
            else:
                # Closing or reversing
                closed_qty = min(abs(old_qty), fill.qty)
                realized = (fill.price - position.avg_price) * closed_qty * (1 if old_qty > 0 else -1)
                position.realized_pnl += realized

                if position.qty == 0:
                    # Fully closed
                    position.avg_price = 0
                    position.cost_basis = 0
                elif abs(position.qty) < abs(old_qty):
                    # Partial close
                    position.cost_basis = position.avg_price * abs(position.qty)
                else:
                    # Reversal → new position
                    position.avg_price = fill.price
                    position.cost_basis = fill.price * abs(position.qty)

            position.current_price = fill.price
            position.market_value = fill.price * abs(position.qty)
            position.unrealized_pnl = (fill.price - position.avg_price) * position.qty if position.qty != 0 else 0
            position.last_updated = fill.timestamp

        # Remove position if qty = 0
        if position.qty == 0:
            logger.info(f"Position closed: {fill.symbol}, realized P&L: ${position.realized_pnl:.2f}")
            # Keep in dict for realized P&L tracking, or remove:
            # del self.positions[fill.symbol]

    # ========================================================================
    # Account Queries
    # ========================================================================

    def get_account(self) -> Account:
        """Get current account snapshot"""
        positions_value = sum(
            abs(p.qty) * self.current_prices.get(p.symbol, p.current_price)
            for p in self.positions.values()
        )
        unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        realized_pnl = sum(p.realized_pnl for p in self.positions.values())
        equity = self.cash + positions_value + unrealized_pnl
        leverage = positions_value / equity if equity > 0 else 0
        buying_power = self._calculate_buying_power()

        return Account(
            account_id=self.account_id,
            cash=self.cash,
            equity=equity,
            buying_power=buying_power,
            positions_value=positions_value,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            leverage=leverage,
            margin_used=max(0, positions_value - self.cash),
            timestamp=self.current_timestamp,
        )

    def get_positions(self) -> List[Position]:
        """Get all positions"""
        # Update current prices
        for symbol, position in self.positions.items():
            if symbol in self.current_prices:
                position.current_price = self.current_prices[symbol]
                position.market_value = self.current_prices[symbol] * abs(position.qty)
                position.unrealized_pnl = (self.current_prices[symbol] - position.avg_price) * position.qty

        return [p for p in self.positions.values() if p.qty != 0]

    def get_orders(self, active_only: bool = False) -> List[Order]:
        """Get orders"""
        if active_only:
            return [o for o in self.orders.values() if o.status in [OrderStatus.NEW, OrderStatus.WORKING, OrderStatus.PARTIALLY_FILLED]]
        return list(self.orders.values())

    def get_fills(self, symbol: Optional[str] = None) -> List[Fill]:
        """Get fills, optionally filtered by symbol"""
        if symbol:
            return [f for f in self.fills if f.symbol == symbol]
        return self.fills

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id not in self.orders:
            return False

        order = self.orders[order_id]
        if order.status not in [OrderStatus.NEW, OrderStatus.WORKING, OrderStatus.PARTIALLY_FILLED]:
            return False

        order.status = OrderStatus.CANCELED
        order.updated_at = self.current_timestamp
        logger.info(f"Order canceled: {order_id}")
        return True

    # ========================================================================
    # Internal Helpers
    # ========================================================================

    def _calculate_equity(self) -> float:
        """Calculate total equity"""
        positions_value = sum(
            abs(p.qty) * self.current_prices.get(p.symbol, p.current_price)
            for p in self.positions.values()
        )
        unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        return self.cash + positions_value + unrealized_pnl

    def _calculate_leverage(self) -> float:
        """Calculate current leverage"""
        equity = self._calculate_equity()
        if equity <= 0:
            return 0
        positions_value = sum(
            abs(p.qty) * self.current_prices.get(p.symbol, p.current_price)
            for p in self.positions.values()
        )
        return positions_value / equity

    def _calculate_buying_power(self) -> float:
        """Calculate available buying power"""
        equity = self._calculate_equity()
        max_leverage_value = equity * self.risk_limits.max_leverage
        positions_value = sum(
            abs(p.qty) * self.current_prices.get(p.symbol, p.current_price)
            for p in self.positions.values()
        )
        return max(0, max_leverage_value - positions_value)
