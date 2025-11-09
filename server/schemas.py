"""
Data contracts and Pydantic schemas for the quantitative trading platform.
Aligned with PRD Section 7: Data Contracts
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, validator


# ============================================================================
# Market Data Schemas
# ============================================================================

class Bar(BaseModel):
    """OHLCV bar data"""
    ts: int = Field(..., description="Unix timestamp (seconds)")
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: int = Field(..., ge=0)
    adj: bool = Field(default=True, description="Whether data is adjusted for splits/dividends")

    @validator('high')
    def high_ge_low(cls, v, values):
        if 'low' in values and v < values['low']:
            raise ValueError('high must be >= low')
        return v


class Meta(BaseModel):
    """Security metadata"""
    symbol: str = Field(..., min_length=1, max_length=10)
    currency: str = Field(default="USD")
    source: str = Field(..., description="Data provider (e.g., 'openbb')")
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None


class Quote(BaseModel):
    """Real-time quote"""
    symbol: str
    name: Optional[str] = None
    price: float = Field(..., gt=0)
    change: float
    change_percent: float
    volume: int = Field(..., ge=0)
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    prev_close: Optional[float] = None
    timestamp: int = Field(..., description="Unix timestamp")


# ============================================================================
# Order & Trading Schemas
# ============================================================================

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"
    STOP_LIMIT = "STP_LMT"


class OrderStatus(str, Enum):
    NEW = "NEW"
    WORKING = "WORKING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"


class TimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class OrderCreate(BaseModel):
    """Order submission request"""
    symbol: str = Field(..., min_length=1, max_length=10)
    side: OrderSide
    type: OrderType
    qty: int = Field(..., gt=0)
    limit_price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    tif: TimeInForce = TimeInForce.DAY

    @validator('limit_price')
    def validate_limit_price(cls, v, values):
        if values.get('type') in [OrderType.LIMIT, OrderType.STOP_LIMIT] and v is None:
            raise ValueError('limit_price required for LIMIT/STOP_LIMIT orders')
        return v

    @validator('stop_price')
    def validate_stop_price(cls, v, values):
        if values.get('type') in [OrderType.STOP, OrderType.STOP_LIMIT] and v is None:
            raise ValueError('stop_price required for STOP/STOP_LIMIT orders')
        return v


class Order(BaseModel):
    """Order representation"""
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    qty: int
    filled_qty: int = 0
    remaining_qty: int
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    avg_fill_price: Optional[float] = None
    tif: TimeInForce
    status: OrderStatus
    created_at: int  # Unix timestamp
    updated_at: int
    reject_reason: Optional[str] = None


class Fill(BaseModel):
    """Trade fill"""
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    price: float = Field(..., gt=0)
    qty: int = Field(..., gt=0)
    commission: float = Field(..., ge=0)
    slippage: float = Field(default=0.0, description="Slippage in dollars")
    timestamp: int


class Position(BaseModel):
    """Position snapshot"""
    symbol: str
    qty: int  # Can be negative for short positions
    avg_price: float = Field(..., gt=0)
    cost_basis: float
    current_price: float = Field(..., gt=0)
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    last_updated: int


class Account(BaseModel):
    """Account snapshot"""
    account_id: str
    cash: float
    equity: float
    buying_power: float
    positions_value: float
    unrealized_pnl: float
    realized_pnl: float
    leverage: float = Field(..., ge=0)
    margin_used: float = Field(..., ge=0)
    timestamp: int


# ============================================================================
# Backtest Schemas
# ============================================================================

class BacktestConfig(BaseModel):
    """Backtest configuration"""
    strategy_id: str
    params: Dict[str, Any] = Field(default_factory=dict)
    universe: List[str] = Field(..., min_items=1)
    interval: str = Field(..., description="e.g., '1D', '1H', '5m'")
    start_date: str = Field(..., description="ISO date YYYY-MM-DD")
    end_date: str = Field(..., description="ISO date YYYY-MM-DD")
    initial_capital: float = Field(default=100000.0, gt=0)
    commission: float = Field(default=0.001, ge=0, description="Commission rate (e.g., 0.001 = 0.1%)")
    slippage_bps: float = Field(default=5.0, ge=0, description="Slippage in basis points")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")


class BacktestMetrics(BaseModel):
    """Backtest performance metrics"""
    total_return: float
    cagr: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_duration_days: int
    volatility: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_holding_period_days: float
    exposure: float = Field(..., description="Fraction of time in market")
    turnover: float = Field(..., description="Annual turnover rate")


class BacktestTrade(BaseModel):
    """Individual backtest trade record"""
    entry_date: str
    exit_date: str
    symbol: str
    side: OrderSide
    qty: int
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    commission: float
    slippage: float
    mae: float = Field(..., description="Maximum Adverse Excursion")
    mfe: float = Field(..., description="Maximum Favorable Excursion")
    holding_period_days: int


class BacktestArtifact(BaseModel):
    """Artifact produced by backtest"""
    type: Literal['pdf', 'csv', 'png', 'parquet', 'html']
    url: str
    size_bytes: Optional[int] = None


class BacktestRun(BaseModel):
    """Complete backtest run record"""
    id: str
    strategy_id: str
    config: BacktestConfig
    status: Literal['queued', 'running', 'completed', 'failed']
    progress: float = Field(default=0.0, ge=0, le=1.0)

    # Reproducibility metadata
    data_hash: Optional[str] = Field(None, description="Hash of input data snapshot")
    code_sha: Optional[str] = Field(None, description="Git commit SHA of strategy code")
    env_hash: Optional[str] = Field(None, description="Hash of Python environment")

    # Results
    metrics: Optional[BacktestMetrics] = None
    trades: Optional[List[BacktestTrade]] = None
    equity_curve: Optional[List[Dict[str, Any]]] = None  # [{date: str, equity: float}]
    drawdown_curve: Optional[List[Dict[str, Any]]] = None
    artifacts: List[BacktestArtifact] = Field(default_factory=list)

    # Timestamps
    created_at: int
    started_at: Optional[int] = None
    completed_at: Optional[int] = None
    error_message: Optional[str] = None


# ============================================================================
# Alert Schemas
# ============================================================================

class AlertCondition(str, Enum):
    PRICE_ABOVE = "PRICE_ABOVE"
    PRICE_BELOW = "PRICE_BELOW"
    PRICE_CROSSES_ABOVE = "PRICE_CROSSES_ABOVE"
    PRICE_CROSSES_BELOW = "PRICE_CROSSES_BELOW"
    PERCENT_CHANGE = "PERCENT_CHANGE"


class AlertChannel(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"


class AlertCreate(BaseModel):
    """Create alert request"""
    symbol: str
    condition: AlertCondition
    value: float
    message: Optional[str] = None
    channels: List[AlertChannel] = Field(default_factory=lambda: [AlertChannel.IN_APP])
    webhook_url: Optional[str] = None
    expires_at: Optional[int] = None  # Unix timestamp


class Alert(BaseModel):
    """Alert representation"""
    id: str
    user_id: str
    symbol: str
    condition: AlertCondition
    value: float
    message: Optional[str] = None
    channels: List[AlertChannel]
    webhook_url: Optional[str] = None
    status: Literal['active', 'triggered', 'expired', 'disabled']
    triggered_at: Optional[int] = None
    created_at: int
    expires_at: Optional[int] = None


class AlertHistory(BaseModel):
    """Alert trigger history"""
    id: str
    alert_id: str
    symbol: str
    condition: AlertCondition
    trigger_price: float
    message: str
    timestamp: int


# ============================================================================
# Screener Schemas
# ============================================================================

class ScreenerFilter(BaseModel):
    """Single screener filter"""
    field: str  # e.g., 'market_cap', 'pe_ratio', 'price'
    operator: Literal['gt', 'gte', 'lt', 'lte', 'eq', 'between']
    value: Any  # Can be float, int, or [min, max] for 'between'


class ScreenerRequest(BaseModel):
    """Screener query request"""
    filters: List[ScreenerFilter] = Field(default_factory=list)
    sort_by: Optional[str] = None
    sort_order: Literal['asc', 'desc'] = 'desc'
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class ScreenerResult(BaseModel):
    """Screener result item"""
    symbol: str
    name: Optional[str] = None
    price: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    # Additional fields as needed
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScreenerView(BaseModel):
    """Saved screener view"""
    id: str
    name: str
    filters: List[ScreenerFilter]
    sort_by: Optional[str] = None
    sort_order: Literal['asc', 'desc'] = 'desc'
    created_at: int
    updated_at: int


# ============================================================================
# Risk Management Schemas
# ============================================================================

class RiskLimits(BaseModel):
    """Risk limits configuration"""
    max_leverage: float = Field(default=2.0, gt=0)
    max_position_size_pct: float = Field(default=0.10, gt=0, le=1.0, description="Max % of portfolio per position")
    max_order_notional: float = Field(default=50000.0, gt=0)
    max_daily_loss_pct: float = Field(default=0.05, gt=0, le=1.0)
    max_symbols: int = Field(default=20, gt=0)


class RiskCheck(BaseModel):
    """Risk check result"""
    passed: bool
    order: Optional[OrderCreate] = None
    violations: List[str] = Field(default_factory=list)
    current_leverage: float
    resulting_leverage: float
    timestamp: int


# ============================================================================
# Indicator Schemas
# ============================================================================

class IndicatorParam(BaseModel):
    """Indicator parameter definition"""
    name: str
    type: Literal['int', 'float', 'bool', 'string']
    default: Any
    min: Optional[float] = None
    max: Optional[float] = None
    options: Optional[List[Any]] = None  # For enum-like params


class IndicatorConfig(BaseModel):
    """Indicator configuration"""
    id: str
    type: str  # e.g., 'SMA', 'RSI', 'MACD'
    params: Dict[str, Any]
    visible: bool = True
    pane: int = 0  # Which pane (0=main chart, 1+=subpanes)
    style: Dict[str, Any] = Field(default_factory=dict)  # colors, line width, etc.


class ChartLayout(BaseModel):
    """Chart layout persistence"""
    id: str
    name: str
    symbol: str
    interval: str
    indicators: List[IndicatorConfig]
    drawings: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: int
    updated_at: int


# ============================================================================
# Response Wrappers
# ============================================================================

class ErrorResponse(BaseModel):
    """API error response"""
    error: str
    detail: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
