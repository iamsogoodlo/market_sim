"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Download, TrendingUp, TrendingDown } from "lucide-react";
import { BacktestRun, BacktestMetrics, BacktestTrade } from "@/types/api";

interface BacktestResultsProps {
  run: BacktestRun;
}

export default function BacktestResults({ run }: BacktestResultsProps) {
  const [selectedTab, setSelectedTab] = useState<"overview" | "metrics" | "trades" | "curve">(
    "overview"
  );

  if (run.status === "queued" || run.status === "running") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Backtest Running...</CardTitle>
          <CardDescription>
            {run.status === "queued" ? "Waiting in queue" : `Progress: ${(run.progress * 100).toFixed(1)}%`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="w-full bg-[hsl(var(--tv-surface-elevated))] rounded h-2">
            <div
              className="bg-[hsl(var(--tv-blue))] h-2 rounded transition-all"
              style={{ width: `${run.progress * 100}%` }}
            />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (run.status === "failed") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-[hsl(var(--tv-red))]">Backtest Failed</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-[hsl(var(--tv-text-secondary))]">{run.error_message}</p>
        </CardContent>
      </Card>
    );
  }

  const metrics = run.metrics;
  if (!metrics) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[hsl(var(--tv-text-primary))]">
            Backtest Results
          </h2>
          <p className="text-sm text-[hsl(var(--tv-text-secondary))]">
            {run.config.strategy_id} • {run.config.start_date} to {run.config.end_date}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              /* Export CSV */
            }}
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              /* Export PDF */
            }}
          >
            <Download className="h-4 w-4 mr-2" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-[hsl(var(--tv-text-secondary))] uppercase font-semibold mb-1">
              Total Return
            </p>
            <p
              className={`text-2xl font-bold ${
                metrics.total_return >= 0
                  ? "text-[hsl(var(--tv-green))]"
                  : "text-[hsl(var(--tv-red))]"
              }`}
            >
              {metrics.total_return >= 0 ? "+" : ""}
              {(metrics.total_return * 100).toFixed(2)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-[hsl(var(--tv-text-secondary))] uppercase font-semibold mb-1">
              Sharpe Ratio
            </p>
            <p className="text-2xl font-bold text-[hsl(var(--tv-text-primary))]">
              {metrics.sharpe_ratio.toFixed(2)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-[hsl(var(--tv-text-secondary))] uppercase font-semibold mb-1">
              Max Drawdown
            </p>
            <p className="text-2xl font-bold text-[hsl(var(--tv-red))]">
              {(metrics.max_drawdown * 100).toFixed(2)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-[hsl(var(--tv-text-secondary))] uppercase font-semibold mb-1">
              Win Rate
            </p>
            <p className="text-2xl font-bold text-[hsl(var(--tv-text-primary))]">
              {(metrics.win_rate * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={selectedTab} onValueChange={(v: any) => setSelectedTab(v)}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="trades">Trades</TabsTrigger>
          <TabsTrigger value="curve">Equity Curve</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Performance Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Returns Section */}
                <div>
                  <h3 className="text-sm font-semibold text-[hsl(var(--tv-text-primary))] mb-3">
                    Returns
                  </h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-[hsl(var(--tv-text-secondary))]">CAGR</p>
                      <p className="text-lg font-semibold text-[hsl(var(--tv-text-primary))]">
                        {(metrics.cagr * 100).toFixed(2)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[hsl(var(--tv-text-secondary))]">Volatility</p>
                      <p className="text-lg font-semibold text-[hsl(var(--tv-text-primary))]">
                        {(metrics.volatility * 100).toFixed(2)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[hsl(var(--tv-text-secondary))]">Exposure</p>
                      <p className="text-lg font-semibold text-[hsl(var(--tv-text-primary))]">
                        {(metrics.exposure * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>

                {/* Risk-Adjusted Section */}
                <div>
                  <h3 className="text-sm font-semibold text-[hsl(var(--tv-text-primary))] mb-3">
                    Risk-Adjusted
                  </h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-[hsl(var(--tv-text-secondary))]">Sharpe Ratio</p>
                      <p className="text-lg font-semibold text-[hsl(var(--tv-text-primary))]">
                        {metrics.sharpe_ratio.toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[hsl(var(--tv-text-secondary))]">Sortino Ratio</p>
                      <p className="text-lg font-semibold text-[hsl(var(--tv-text-primary))]">
                        {metrics.sortino_ratio.toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[hsl(var(--tv-text-secondary))]">Calmar Ratio</p>
                      <p className="text-lg font-semibold text-[hsl(var(--tv-text-primary))]">
                        {metrics.calmar_ratio.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Trading Activity */}
                <div>
                  <h3 className="text-sm font-semibold text-[hsl(var(--tv-text-primary))] mb-3">
                    Trading Activity
                  </h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-[hsl(var(--tv-text-secondary))]">Total Trades</p>
                      <p className="text-lg font-semibold text-[hsl(var(--tv-text-primary))]">
                        {metrics.total_trades}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[hsl(var(--tv-text-secondary))]">Avg Hold (days)</p>
                      <p className="text-lg font-semibold text-[hsl(var(--tv-text-primary))]">
                        {metrics.avg_holding_period_days.toFixed(1)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[hsl(var(--tv-text-secondary))]">Turnover</p>
                      <p className="text-lg font-semibold text-[hsl(var(--tv-text-primary))]">
                        {metrics.turnover.toFixed(2)}x
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle>All Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                {Object.entries(metrics).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center">
                    <span className="text-sm text-[hsl(var(--tv-text-secondary))] capitalize">
                      {key.replace(/_/g, " ")}:
                    </span>
                    <span className="text-sm font-semibold text-[hsl(var(--tv-text-primary))]">
                      {typeof value === "number"
                        ? key.includes("ratio") || key.includes("turnover")
                          ? value.toFixed(2)
                          : key.includes("rate") || key.includes("return") || key.includes("drawdown")
                          ? `${(value * 100).toFixed(2)}%`
                          : key.includes("days")
                          ? Math.round(value)
                          : value.toFixed(2)
                        : value}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trades Tab */}
        <TabsContent value="trades">
          <Card>
            <CardHeader>
              <CardTitle>Trade History</CardTitle>
              <CardDescription>{run.trades?.length || 0} trades</CardDescription>
            </CardHeader>
            <CardContent>
              {run.trades && run.trades.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[hsl(var(--tv-border))]">
                        <th className="text-left py-2 px-3 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">
                          Entry
                        </th>
                        <th className="text-left py-2 px-3 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">
                          Exit
                        </th>
                        <th className="text-left py-2 px-3 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">
                          Symbol
                        </th>
                        <th className="text-left py-2 px-3 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">
                          Side
                        </th>
                        <th className="text-right py-2 px-3 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">
                          Qty
                        </th>
                        <th className="text-right py-2 px-3 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">
                          Entry $
                        </th>
                        <th className="text-right py-2 px-3 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">
                          Exit $
                        </th>
                        <th className="text-right py-2 px-3 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">
                          P&L
                        </th>
                        <th className="text-right py-2 px-3 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">
                          P&L %
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {run.trades.map((trade, idx) => (
                        <tr
                          key={idx}
                          className="border-b border-[hsl(var(--tv-border))] hover:bg-[hsl(var(--tv-surface-elevated))] transition-colors"
                        >
                          <td className="py-2 px-3 text-[hsl(var(--tv-text-primary))]">
                            {trade.entry_date}
                          </td>
                          <td className="py-2 px-3 text-[hsl(var(--tv-text-primary))]">
                            {trade.exit_date}
                          </td>
                          <td className="py-2 px-3 font-semibold text-[hsl(var(--tv-text-primary))]">
                            {trade.symbol}
                          </td>
                          <td className="py-2 px-3">
                            {trade.side === "BUY" ? (
                              <span className="text-[hsl(var(--tv-green))]">BUY</span>
                            ) : (
                              <span className="text-[hsl(var(--tv-red))]">SELL</span>
                            )}
                          </td>
                          <td className="py-2 px-3 text-right text-[hsl(var(--tv-text-primary))]">
                            {trade.qty}
                          </td>
                          <td className="py-2 px-3 text-right text-[hsl(var(--tv-text-primary))]">
                            ${trade.entry_price.toFixed(2)}
                          </td>
                          <td className="py-2 px-3 text-right text-[hsl(var(--tv-text-primary))]">
                            ${trade.exit_price.toFixed(2)}
                          </td>
                          <td
                            className={`py-2 px-3 text-right font-semibold ${
                              trade.pnl >= 0
                                ? "text-[hsl(var(--tv-green))]"
                                : "text-[hsl(var(--tv-red))]"
                            }`}
                          >
                            ${trade.pnl >= 0 ? "+" : ""}
                            {trade.pnl.toFixed(2)}
                          </td>
                          <td
                            className={`py-2 px-3 text-right font-semibold ${
                              trade.pnl_pct >= 0
                                ? "text-[hsl(var(--tv-green))]"
                                : "text-[hsl(var(--tv-red))]"
                            }`}
                          >
                            {trade.pnl_pct >= 0 ? "+" : ""}
                            {(trade.pnl_pct * 100).toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-[hsl(var(--tv-text-secondary))] text-center py-8">
                  No trades to display
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Equity Curve Tab */}
        <TabsContent value="curve">
          <Card>
            <CardHeader>
              <CardTitle>Equity Curve</CardTitle>
              <CardDescription>Portfolio value over time</CardDescription>
            </CardHeader>
            <CardContent>
              {/* TODO: Integrate with chart library for equity curve visualization */}
              <div className="h-96 bg-[hsl(var(--tv-surface-elevated))] rounded flex items-center justify-center">
                <p className="text-[hsl(var(--tv-text-secondary))]">
                  Equity curve chart (integrate with lightweight-charts)
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Reproducibility Metadata */}
      {(run.data_hash || run.code_sha || run.env_hash) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Reproducibility Metadata</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-xs font-mono">
              {run.data_hash && (
                <div className="flex justify-between">
                  <span className="text-[hsl(var(--tv-text-secondary))]">Data Hash:</span>
                  <span className="text-[hsl(var(--tv-text-primary))]">{run.data_hash}</span>
                </div>
              )}
              {run.code_sha && (
                <div className="flex justify-between">
                  <span className="text-[hsl(var(--tv-text-secondary))]">Code SHA:</span>
                  <span className="text-[hsl(var(--tv-text-primary))]">{run.code_sha}</span>
                </div>
              )}
              {run.env_hash && (
                <div className="flex justify-between">
                  <span className="text-[hsl(var(--tv-text-secondary))]">Env Hash:</span>
                  <span className="text-[hsl(var(--tv-text-primary))]">{run.env_hash}</span>
                </div>
              )}
              {run.config.seed !== undefined && (
                <div className="flex justify-between">
                  <span className="text-[hsl(var(--tv-text-secondary))]">Seed:</span>
                  <span className="text-[hsl(var(--tv-text-primary))]">{run.config.seed}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
