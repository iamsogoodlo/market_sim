"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Play, Calendar } from "lucide-react";
import { useState } from "react";
import BacktestResults from "@/components/BacktestResults";
import { BacktestRun } from "@/types/api";

export default function BacktestPage() {
  const [symbol, setSymbol] = useState("AAPL");
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState("2024-12-31");
  const [backtestRun, setBacktestRun] = useState<BacktestRun | null>(null);

  const runBacktest = async () => {
    // Create initial running state
    const runId = `run_${Date.now()}`;
    setBacktestRun({
      id: runId,
      strategy_id: "demo_strategy",
      config: {
        strategy_id: "demo_strategy",
        start_date: startDate,
        end_date: endDate,
        symbols: [symbol],
        initial_cash: 100000,
        commission: 0.001,
        slippage: 0.01,
        seed: 42,
      },
      status: "running",
      progress: 0.5,
    });

    // Simulate backtest completion
    setTimeout(() => {
      setBacktestRun({
        id: runId,
        strategy_id: "demo_strategy",
        config: {
          strategy_id: "demo_strategy",
          start_date: startDate,
          end_date: endDate,
          symbols: [symbol],
          initial_cash: 100000,
          commission: 0.001,
          slippage: 0.01,
          seed: 42,
        },
        status: "completed",
        progress: 1.0,
        metrics: {
          total_return: 0.152,
          cagr: 0.148,
          sharpe_ratio: 1.8,
          sortino_ratio: 2.1,
          calmar_ratio: 1.5,
          max_drawdown: -0.085,
          volatility: 0.082,
          win_rate: 0.625,
          profit_factor: 2.3,
          total_trades: 48,
          avg_holding_period_days: 7.5,
          turnover: 4.2,
          exposure: 0.85,
        },
        trades: [
          {
            entry_date: "2024-01-15",
            exit_date: "2024-01-22",
            symbol: symbol,
            side: "BUY",
            qty: 100,
            entry_price: 150.25,
            exit_price: 156.80,
            pnl: 655.0,
            pnl_pct: 0.0436,
          },
          {
            entry_date: "2024-02-03",
            exit_date: "2024-02-10",
            symbol: symbol,
            side: "BUY",
            qty: 150,
            entry_price: 148.50,
            exit_price: 152.30,
            pnl: 570.0,
            pnl_pct: 0.0256,
          },
          {
            entry_date: "2024-03-12",
            exit_date: "2024-03-18",
            symbol: symbol,
            side: "BUY",
            qty: 120,
            entry_price: 155.00,
            exit_price: 149.75,
            pnl: -630.0,
            pnl_pct: -0.0339,
          },
        ],
        data_hash: "sha256:a1b2c3d4e5f6",
        code_sha: "git:abc123def456",
        env_hash: "sha256:env789xyz",
      });
    }, 2500);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[hsl(var(--tv-text-primary))]">Backtesting</h1>
        <p className="text-[hsl(var(--tv-text-secondary))]">
          Test strategies with historical data
        </p>
      </div>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Backtest Configuration</CardTitle>
          <CardDescription>Set parameters for historical analysis</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[hsl(var(--tv-text-primary))]">Symbol</label>
              <Input
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="AAPL"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-[hsl(var(--tv-text-primary))]">Start Date</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-[hsl(var(--tv-text-primary))]">End Date</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
          <Button onClick={runBacktest} disabled={backtestRun?.status === "running"} className="w-full">
            <Play className="mr-2 h-4 w-4" />
            {backtestRun?.status === "running" ? "Running Backtest..." : "Run Backtest"}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {backtestRun && <BacktestResults run={backtestRun} />}

      {/* Coming Soon Features */}
      <Card>
        <CardHeader>
          <CardTitle>Advanced Features (Coming Soon)</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-[hsl(var(--tv-text-secondary))]">
            <li>• Multi-timeframe analysis (1m, 5m, 15m, 1h, 1d)</li>
            <li>• Monte Carlo simulations for risk analysis</li>
            <li>• Factor model analysis (Fama-French 5-factor)</li>
            <li>• Transaction cost modeling</li>
            <li>• Slippage simulation</li>
            <li>• Portfolio optimization</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
