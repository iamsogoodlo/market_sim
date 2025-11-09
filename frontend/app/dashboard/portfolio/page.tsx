"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, DollarSign } from "lucide-react";
import { useEffect, useState } from "react";

interface Holding {
  symbol: string;
  name: string;
  quantity: number;
  avgCost: number;
  currentPrice: number;
  totalValue: number;
  pnl: number;
  pnlPercent: number;
}

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [totalValue, setTotalValue] = useState(0);
  const [cashBalance, setCashBalance] = useState(100000);
  const [totalPnL, setTotalPnL] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch portfolio data
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      // Fetch holdings from database
      const holdingsResponse = await fetch("/api/portfolio/holdings");
      const holdingsData = await holdingsResponse.json();

      // Fetch cash balance
      const balanceResponse = await fetch("/api/portfolio/balance");
      const balanceData = await balanceResponse.json();
      const cash = balanceData.cashBalance || 100000;
      setCashBalance(cash);

      // Fetch current prices and build holdings array
      const enrichedHoldings: Holding[] = await Promise.all(
        holdingsData.map(async (h: { symbol: string; quantity: number; avgCost: number }) => {
          try {
            const quoteResponse = await fetch(`/api/stocks/quote/${h.symbol}`);
            const quoteData = await quoteResponse.json();
            const currentPrice = quoteData.price || h.avgCost;
            const totalValue = currentPrice * h.quantity;
            const pnl = totalValue - (h.avgCost * h.quantity);
            const pnlPercent = ((currentPrice - h.avgCost) / h.avgCost) * 100;

            return {
              symbol: h.symbol,
              name: quoteData.name || h.symbol,
              quantity: h.quantity,
              avgCost: h.avgCost,
              currentPrice,
              totalValue,
              pnl,
              pnlPercent,
            };
          } catch (error) {
            console.error(`Error fetching quote for ${h.symbol}:`, error);
            // Fallback to avg cost if quote fails
            const totalValue = h.avgCost * h.quantity;
            return {
              symbol: h.symbol,
              name: h.symbol,
              quantity: h.quantity,
              avgCost: h.avgCost,
              currentPrice: h.avgCost,
              totalValue,
              pnl: 0,
              pnlPercent: 0,
            };
          }
        })
      );

      setHoldings(enrichedHoldings);
      const portfolioValue = enrichedHoldings.reduce((sum, h) => sum + h.totalValue, 0);
      const pnl = enrichedHoldings.reduce((sum, h) => sum + h.pnl, 0);
      setTotalValue(portfolioValue + cash);
      setTotalPnL(pnl);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching portfolio:", error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-[hsl(var(--tv-text-primary))]">Loading portfolio...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[hsl(var(--tv-text-primary))]">Portfolio</h1>
        <p className="text-[hsl(var(--tv-text-secondary))]">
          Track your holdings and performance
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <p className="text-xs text-muted-foreground">
              Cash: ${cashBalance.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
            {totalPnL >= 0 ? (
              <TrendingUp className="h-4 w-4 text-[hsl(var(--tv-green))]" />
            ) : (
              <TrendingDown className="h-4 w-4 text-[hsl(var(--tv-red))]" />
            )}
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                totalPnL >= 0 ? "text-[hsl(var(--tv-green))]" : "text-[hsl(var(--tv-red))]"
              }`}
            >
              ${totalPnL >= 0 ? "+" : ""}
              {totalPnL.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <p className="text-xs text-muted-foreground">
              {((totalPnL / (totalValue - totalPnL)) * 100).toFixed(2)}% return
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Holdings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{holdings.length}</div>
            <p className="text-xs text-muted-foreground">
              Active positions
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Holdings Table */}
      <Card>
        <CardHeader>
          <CardTitle>Holdings</CardTitle>
          <CardDescription>Your current positions</CardDescription>
        </CardHeader>
        <CardContent>
          {holdings.length === 0 ? (
            <div className="text-center py-8 text-[hsl(var(--tv-text-secondary))]">
              No holdings yet. Start trading to build your portfolio!
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[hsl(var(--tv-border))]">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">Symbol</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">Name</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">Quantity</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">Avg Cost</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">Current Price</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">Total Value</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">P&L</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-[hsl(var(--tv-text-secondary))] uppercase">P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((holding) => (
                    <tr key={holding.symbol} className="border-b border-[hsl(var(--tv-border))] hover:bg-[hsl(var(--tv-surface-elevated))] transition-colors">
                      <td className="py-3 px-4 font-semibold text-[hsl(var(--tv-text-primary))]">{holding.symbol}</td>
                      <td className="py-3 px-4 text-[hsl(var(--tv-text-secondary))] text-sm">{holding.name}</td>
                      <td className="py-3 px-4 text-right text-[hsl(var(--tv-text-primary))]">{holding.quantity}</td>
                      <td className="py-3 px-4 text-right text-[hsl(var(--tv-text-primary))]">
                        ${holding.avgCost.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right text-[hsl(var(--tv-text-primary))]">
                        ${holding.currentPrice.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-[hsl(var(--tv-text-primary))]">
                        ${holding.totalValue.toFixed(2)}
                      </td>
                      <td
                        className={`py-3 px-4 text-right font-semibold ${
                          holding.pnl >= 0 ? "text-[hsl(var(--tv-green))]" : "text-[hsl(var(--tv-red))]"
                        }`}
                      >
                        ${holding.pnl >= 0 ? "+" : ""}
                        {holding.pnl.toFixed(2)}
                      </td>
                      <td
                        className={`py-3 px-4 text-right font-semibold ${
                          holding.pnlPercent >= 0 ? "text-[hsl(var(--tv-green))]" : "text-[hsl(var(--tv-red))]"
                        }`}
                      >
                        {holding.pnlPercent >= 0 ? "+" : ""}
                        {holding.pnlPercent.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
