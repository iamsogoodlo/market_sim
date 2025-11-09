/**
 * TypeScript types matching backend Pydantic schemas
 * Auto-generated from server/schemas.py
 */

// ============================================================================
// Market Data Types
// ============================================================================

export interface Bar {
  ts: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adj: boolean;
}

export interface Meta {
  symbol: string;
  currency: string;
  source: string;
  name?: string;
  sector?: string;
  industry?: string;
  market_cap?: number;
}

export interface Quote {
  symbol: string;
  name?: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  open?: number;
  high?: number;
  low?: number;
  prev_close?: number;
  timestamp: number;
}

// ============================================================================
// Order & Trading Types
// ============================================================================

export enum OrderSide {
  BUY = "BUY",
  SELL = "SELL",
}

export enum OrderType {
  MARKET = "MKT",
  LIMIT = "LMT",
  STOP = "STP",
  STOP_LIMIT = "STP_LMT",
}

export enum OrderStatus {
  NEW = "NEW",
  WORKING = "WORKING",
  PARTIALLY_FILLED = "PARTIALLY_FILLED",
  FILLED = "FILLED",
  CANCELED = "CANCELED",
  REJECTED = "REJECTED",
}

export enum TimeInForce {
  DAY = "DAY",
  GTC = "GTC",
  IOC = "IOC",
  FOK = "FOK",
}

export interface OrderCreate {
  symbol: string;
  side: OrderSide;
  type: OrderType;
  qty: number;
  limit_price?: number;
  stop_price?: number;
  tif: TimeInForce;
}

export interface Order {
  id: string;
  symbol: string;
  side: OrderSide;
  type: OrderType;
  qty: number;
  filled_qty: number;
  remaining_qty: number;
  limit_price?: number;
  stop_price?: number;
  avg_fill_price?: number;
  tif: TimeInForce;
  status: OrderStatus;
  created_at: number;
  updated_at: number;
  reject_reason?: string;
}

export interface Fill {
  id: string;
  order_id: string;
  symbol: string;
  side: OrderSide;
  price: number;
  qty: number;
  commission: number;
  slippage: number;
  timestamp: number;
}

export interface Position {
  symbol: string;
  qty: number;
  avg_price: number;
  cost_basis: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
  last_updated: number;
}

export interface Account {
  account_id: string;
  cash: number;
  equity: number;
  buying_power: number;
  positions_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
  leverage: number;
  margin_used: number;
  timestamp: number;
}

// ============================================================================
// Backtest Types
// ============================================================================

export interface BacktestConfig {
  strategy_id: string;
  params: Record<string, any>;
  universe: string[];
  interval: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission: number;
  slippage_bps: number;
  seed?: number;
}

export interface BacktestMetrics {
  total_return: number;
  cagr: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  max_drawdown: number;
  max_drawdown_duration_days: number;
  volatility: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  avg_trade: number;
  avg_win: number;
  avg_loss: number;
  largest_win: number;
  largest_loss: number;
  avg_holding_period_days: number;
  exposure: number;
  turnover: number;
}

export interface BacktestTrade {
  entry_date: string;
  exit_date: string;
  symbol: string;
  side: OrderSide;
  qty: number;
  entry_price: number;
  exit_price: number;
  pnl: number;
  pnl_pct: number;
  commission: number;
  slippage: number;
  mae: number;
  mfe: number;
  holding_period_days: number;
}

export interface BacktestArtifact {
  type: 'pdf' | 'csv' | 'png' | 'parquet' | 'html';
  url: string;
  size_bytes?: number;
}

export interface BacktestRun {
  id: string;
  strategy_id: string;
  config: BacktestConfig;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number;
  data_hash?: string;
  code_sha?: string;
  env_hash?: string;
  metrics?: BacktestMetrics;
  trades?: BacktestTrade[];
  equity_curve?: Array<{ date: string; equity: number }>;
  drawdown_curve?: Array<{ date: string; drawdown: number }>;
  artifacts: BacktestArtifact[];
  created_at: number;
  started_at?: number;
  completed_at?: number;
  error_message?: string;
}

// ============================================================================
// Alert Types
// ============================================================================

export enum AlertCondition {
  PRICE_ABOVE = "PRICE_ABOVE",
  PRICE_BELOW = "PRICE_BELOW",
  PRICE_CROSSES_ABOVE = "PRICE_CROSSES_ABOVE",
  PRICE_CROSSES_BELOW = "PRICE_CROSSES_BELOW",
  PERCENT_CHANGE = "PERCENT_CHANGE",
}

export enum AlertChannel {
  IN_APP = "IN_APP",
  EMAIL = "EMAIL",
  WEBHOOK = "WEBHOOK",
}

export interface AlertCreate {
  symbol: string;
  condition: AlertCondition;
  value: number;
  message?: string;
  channels: AlertChannel[];
  webhook_url?: string;
  expires_at?: number;
}

export interface Alert {
  id: string;
  user_id: string;
  symbol: string;
  condition: AlertCondition;
  value: number;
  message?: string;
  channels: AlertChannel[];
  webhook_url?: string;
  status: 'active' | 'triggered' | 'expired' | 'disabled';
  triggered_at?: number;
  created_at: number;
  expires_at?: number;
}

export interface AlertHistory {
  id: string;
  alert_id: string;
  symbol: string;
  condition: AlertCondition;
  trigger_price: number;
  message: string;
  timestamp: number;
}

// ============================================================================
// Screener Types
// ============================================================================

export interface ScreenerFilter {
  field: string;
  operator: 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'between';
  value: any;
}

export interface ScreenerRequest {
  filters: ScreenerFilter[];
  sort_by?: string;
  sort_order: 'asc' | 'desc';
  limit: number;
  offset: number;
}

export interface ScreenerResult {
  symbol: string;
  name?: string;
  price: number;
  change_percent: number;
  volume: number;
  market_cap?: number;
  pe_ratio?: number;
  metadata: Record<string, any>;
}

export interface ScreenerView {
  id: string;
  name: string;
  filters: ScreenerFilter[];
  sort_by?: string;
  sort_order: 'asc' | 'desc';
  created_at: number;
  updated_at: number;
}

// ============================================================================
// Indicator Types
// ============================================================================

export interface IndicatorParam {
  name: string;
  type: 'int' | 'float' | 'bool' | 'string';
  default: any;
  min?: number;
  max?: number;
  options?: any[];
}

export interface IndicatorConfig {
  id: string;
  type: string;
  params: Record<string, any>;
  visible: boolean;
  pane: number;
  style: Record<string, any>;
}

export interface ChartLayout {
  id: string;
  name: string;
  symbol: string;
  interval: string;
  indicators: IndicatorConfig[];
  drawings: any[];
  created_at: number;
  updated_at: number;
}

export interface IndicatorDefinition {
  type: string;
  display_name: string;
  description: string;
  category: 'trend' | 'momentum' | 'volatility' | 'volume' | 'overlay';
  params: IndicatorParam[];
  default_style: Record<string, any>;
}

// ============================================================================
// Risk Types
// ============================================================================

export interface RiskLimits {
  max_leverage: number;
  max_position_size_pct: number;
  max_order_notional: number;
  max_daily_loss_pct: number;
  max_symbols: number;
}

export interface RiskCheck {
  passed: boolean;
  order?: OrderCreate;
  violations: string[];
  current_leverage: number;
  resulting_leverage: number;
  timestamp: number;
}

// ============================================================================
// Response Types
// ============================================================================

export interface ErrorResponse {
  error: string;
  detail?: string;
  timestamp: number;
}

export interface SuccessResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
}
