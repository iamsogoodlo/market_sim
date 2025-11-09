"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { useState } from "react";

interface StrategyRating {
  strategy: string;
  rating: number;
  metrics: Record<string, any>;
  rationale: string;
}

interface StockQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

export default function StrategiesPage() {
  const [symbol, setSymbol] = useState("AAPL");
  const [ratings, setRatings] = useState<StrategyRating[]>([]);
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const strategies = [
    {
      name: "Cointegration Pairs Trading",
      description: "Statistical arbitrage based on mean-reversion of cointegrated spreads",
      implemented: true,
    },
    {
      name: "Ornstein-Uhlenbeck Mean Reversion",
      description: "Model price as mean-reverting stochastic process",
      implemented: true,
    },
    {
      name: "Time-Series Momentum (12-1)",
      description: "Past winners continue to outperform with volatility targeting",
      implemented: true,
    },
    {
      name: "Cross-Sectional Value",
      description: "Cheap stocks outperform expensive ones within industries",
      implemented: true,
    },
    {
      name: "Quality/Profitability (QMJ)",
      description: "High-quality firms earn superior risk-adjusted returns",
      implemented: true,
    },
    {
      name: "Earnings Surprise & Revision Drift",
      description: "Post-Earnings Announcement Drift with analyst revisions",
      implemented: true,
    },
    {
      name: "Factor-Neutral Residual Momentum",
      description: "Momentum unexplained by Fama-French factors",
      implemented: true,
    },
  ];

  const analyzeSymbol = async () => {
    setLoading(true);
    setSearched(true);

    try {
      // Fetch real-time quote first
      const quoteResponse = await fetch(`/api/stocks/quote/${symbol}`);
      if (quoteResponse.ok) {
        const quoteData = await quoteResponse.json();
        setQuote({
          symbol: quoteData.symbol || symbol,
          name: quoteData.name || symbol,
          price: quoteData.price || 0,
          change: quoteData.change || 0,
          changePercent: quoteData.changePercent || 0,
        });
      }

      // Call all 7 strategies in parallel
      const strategyEndpoints = [
        { name: "Cointegration Pairs Trading", endpoint: "pairs" },
        { name: "Ornstein-Uhlenbeck Mean Reversion", endpoint: "ou_mean_reversion" },
        { name: "Time-Series Momentum (12-1)", endpoint: "ts_momentum" },
        { name: "Cross-Sectional Value", endpoint: "value" },
        { name: "Quality/Profitability (QMJ)", endpoint: "quality" },
        { name: "Earnings Surprise & Revision Drift", endpoint: "earnings_drift" },
        { name: "Factor-Neutral Residual Momentum", endpoint: "residual_momentum" },
      ];

      const strategyPromises = strategyEndpoints.map(async (strat) => {
        try {
          const response = await fetch(`/api/strategies/${strat.endpoint}/${symbol}`);
          if (response.ok) {
            const data = await response.json();
            return {
              strategy: strat.name,
              rating: data.rating,
              metrics: data.metrics,
              rationale: data.rationale,
            };
          }
          return null;
        } catch (error) {
          console.error(`Error fetching ${strat.name}:`, error);
          return null;
        }
      });

      const results = await Promise.all(strategyPromises);
      const validRatings = results.filter((r) => r !== null) as StrategyRating[];

      if (validRatings.length > 0) {
        setRatings(validRatings);
      } else {
        // Fallback if all strategies fail
        setRatings([
          {
            strategy: "Error",
            rating: 3,
            metrics: {},
            rationale: "Unable to fetch strategy data. Check if backend is running.",
          },
        ]);
      }
    } catch (error) {
      console.error("Error analyzing symbol:", error);
      setRatings([
        {
          strategy: "Error",
          rating: 3,
          metrics: {},
          rationale: "Unable to fetch strategy data. Check if backend is running.",
        },
      ]);
    }

    setLoading(false);
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 4) return "text-[hsl(var(--tv-green))]";
    if (rating <= 2) return "text-[hsl(var(--tv-red))]";
    return "text-[#F5A623]"; // Yellow/orange for neutral
  };

  const getRatingIcon = (rating: number) => {
    if (rating >= 4) return <TrendingUp className="h-5 w-5" />;
    if (rating <= 2) return <TrendingDown className="h-5 w-5" />;
    return <Minus className="h-5 w-5" />;
  };

  const getRatingLabel = (rating: number) => {
    if (rating === 5) return "Strong Buy";
    if (rating === 4) return "Buy";
    if (rating === 3) return "Neutral";
    if (rating === 2) return "Sell";
    return "Strong Sell";
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[hsl(var(--tv-text-primary))]">Quantitative Strategies</h1>
        <p className="text-[hsl(var(--tv-text-secondary))]">
          7 institutional-grade trading strategies with 1-5 rating system
        </p>
      </div>

      {/* Search Bar */}
      <Card>
        <CardHeader>
          <CardTitle>Analyze Stock</CardTitle>
          <CardDescription>
            Get quantitative strategy ratings for any NASDAQ stock
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Enter stock symbol (e.g., AAPL)"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === "Enter" && analyzeSymbol()}
              />
            </div>
            <Button onClick={analyzeSymbol} disabled={loading}>
              <Search className="mr-2 h-4 w-4" />
              {loading ? "Analyzing..." : "Analyze"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stock Quote */}
      {quote && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{quote.name} ({quote.symbol})</span>
              <span className="text-3xl font-bold">${quote.price.toFixed(2)}</span>
            </CardTitle>
            <CardDescription className={quote.change >= 0 ? "text-[hsl(var(--tv-green))]" : "text-[hsl(var(--tv-red))]"}>
              {quote.change >= 0 ? "+" : ""}{quote.change.toFixed(2)} ({quote.changePercent >= 0 ? "+" : ""}{quote.changePercent.toFixed(2)}%)
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {/* Strategy Ratings */}
      {searched && ratings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Strategy Ratings for {symbol}</CardTitle>
            <CardDescription>
              Real-time quantitative analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {ratings.map((rating, idx) => (
                <div
                  key={idx}
                  className="p-4 border border-[hsl(var(--tv-border))] rounded-lg hover:bg-[hsl(var(--tv-surface-elevated))] transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-[hsl(var(--tv-text-primary))]">{rating.strategy}</h3>
                    <div className={`flex items-center gap-2 ${getRatingColor(rating.rating)}`}>
                      {getRatingIcon(rating.rating)}
                      <span className="text-2xl font-bold">{rating.rating}/5</span>
                      <span className="text-sm">({getRatingLabel(rating.rating)})</span>
                    </div>
                  </div>
                  <p className="text-sm text-[hsl(var(--tv-text-secondary))] mb-3">
                    {rating.rationale}
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    {Object.entries(rating.metrics).map(([key, value]) => (
                      <div key={key}>
                        <span className="text-[hsl(var(--tv-text-secondary))] capitalize">
                          {key.replace(/_/g, " ")}:
                        </span>
                        <span className="ml-2 font-medium text-[hsl(var(--tv-text-primary))]">
                          {typeof value === "number" ? value.toFixed(3) : value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* All Strategies */}
      <Card>
        <CardHeader>
          <CardTitle>Available Strategies</CardTitle>
          <CardDescription>
            {strategies.filter(s => s.implemented).length} of {strategies.length} implemented
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {strategies.map((strategy, idx) => (
              <div
                key={idx}
                className={`p-4 border border-[hsl(var(--tv-border))] rounded-lg ${
                  strategy.implemented
                    ? "hover:bg-[hsl(var(--tv-surface-elevated))] cursor-pointer"
                    : "opacity-60"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold flex items-center gap-2 text-[hsl(var(--tv-text-primary))]">
                      {strategy.name}
                      {strategy.implemented && (
                        <span className="text-xs bg-[hsl(var(--tv-green))] bg-opacity-20 text-[hsl(var(--tv-green))] px-2 py-1 rounded border border-[hsl(var(--tv-green))] border-opacity-30">
                          Active
                        </span>
                      )}
                      {!strategy.implemented && (
                        <span className="text-xs bg-[hsl(var(--tv-surface-elevated))] text-[hsl(var(--tv-text-secondary))] px-2 py-1 rounded border border-[hsl(var(--tv-border))]">
                          Coming Soon
                        </span>
                      )}
                    </h3>
                    <p className="text-sm text-[hsl(var(--tv-text-secondary))] mt-1">
                      {strategy.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
