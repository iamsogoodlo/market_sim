"use client";

import { useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import {
  Search,
  ChevronDown,
  BarChart2,
  TrendingUp,
  LineChart,
  Settings,
  Maximize2,
  LayoutGrid,
  Clock,
  Star,
  X,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

// Dynamically import TradingChart to avoid SSR issues
const TradingChart = dynamic(() => import("@/components/TradingChart"), {
  ssr: false,
  loading: () => <div className="h-full bg-card animate-pulse" />,
});

interface StockQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  open?: number;
  high?: number;
  low?: number;
}

export default function TradingViewTradePage() {
  const [currentSymbol, setCurrentSymbol] = useState("AAPL");
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const [interval, setInterval] = useState("1D");
  const [showWatchlist, setShowWatchlist] = useState(false);
  const [showOrderPanel, setShowOrderPanel] = useState(true);
  const [orderType, setOrderType] = useState<"market" | "limit">("market");
  const [quantity, setQuantity] = useState(1);
  const [limitPrice, setLimitPrice] = useState(0);
  const [cashBalance, setCashBalance] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [watchlist, setWatchlist] = useState(["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]);

  const intervals = ["1M", "5M", "15M", "1H", "1D", "1W"];

  useEffect(() => {
    fetchPortfolioData();
  }, []);

  useEffect(() => {
    if (currentSymbol) {
      fetchStockQuote(currentSymbol);
    }
  }, [currentSymbol]);

  const fetchPortfolioData = async () => {
    try {
      const response = await fetch("/api/portfolio/balance");
      if (response.ok) {
        const data = await response.json();
        setCashBalance(data.cashBalance || 100000);
      }
    } catch (error) {
      console.error("Error fetching balance:", error);
    }
  };

  const fetchStockQuote = async (symbol: string) => {
    try {
      const response = await fetch(`/api/stocks/quote/${symbol}`);
      if (response.ok) {
        const data = await response.json();
        const newQuote: StockQuote = {
          symbol: data.symbol || symbol,
          name: data.name || symbol,
          price: data.price || 0,
          change: data.change || 0,
          changePercent: data.changePercent || 0,
          volume: data.volume || 0,
          open: data.open || data.price,
          high: data.high || data.price,
          low: data.low || data.price,
        };
        setQuote(newQuote);
        setLimitPrice(newQuote.price);
      }
    } catch (error) {
      console.error("Error fetching quote:", error);
    }
  };

  const executeTrade = async (action: "buy" | "sell") => {
    if (!quote || quantity <= 0) return;

    const price = orderType === "market" ? quote.price : limitPrice;
    const total = price * quantity;

    if (action === "buy" && total > cashBalance) {
      alert(`Insufficient funds. Need $${total.toFixed(2)}`);
      return;
    }

    try {
      const response = await fetch("/api/portfolio/trade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: quote.symbol,
          action,
          quantity,
          price,
          orderType,
        }),
      });

      if (response.ok) {
        alert(`✓ ${action.toUpperCase()} ${quantity} ${quote.symbol} @ $${price.toFixed(2)}`);
        fetchPortfolioData();
        setQuantity(1);
      } else {
        const error = await response.json();
        alert(`Order failed: ${error.message}`);
      }
    } catch (error) {
      console.error("Error executing trade:", error);
      alert("Error executing order");
    }
  };

  const changeSymbol = (symbol: string) => {
    setCurrentSymbol(symbol.toUpperCase());
    setSearchQuery("");
  };

  return (
    <div className="h-screen w-full flex flex-col bg-background overflow-hidden">
      {/* Top Toolbar */}
      <div className="tv-toolbar flex-shrink-0">
        {/* Symbol Search */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowWatchlist(!showWatchlist)}
            className="tv-button p-2"
            title="Watchlist"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>

          <div className="relative">
            <input
              type="text"
              value={searchQuery || currentSymbol}
              onChange={(e) => setSearchQuery(e.target.value.toUpperCase())}
              onKeyPress={(e) => e.key === "Enter" && searchQuery && changeSymbol(searchQuery)}
              onFocus={(e) => e.target.select()}
              className="tv-input font-bold text-base w-32"
              placeholder="Symbol"
            />
          </div>

          {quote && (
            <>
              <div className="flex items-center gap-1">
                <span className="text-xl font-bold">${quote.price.toFixed(2)}</span>
                <span className={`text-sm font-semibold ${quote.change >= 0 ? "text-[hsl(var(--tv-green))]" : "text-[hsl(var(--tv-red))]"}`}>
                  {quote.change >= 0 ? "+" : ""}{quote.change.toFixed(2)} ({quote.changePercent >= 0 ? "+" : ""}{quote.changePercent.toFixed(2)}%)
                </span>
              </div>
              <div className="tv-separator" />
              <div className="text-xs text-muted-foreground">
                O {quote.open?.toFixed(2)} H {quote.high?.toFixed(2)} L {quote.low?.toFixed(2)}
              </div>
            </>
          )}
        </div>

        <div className="flex-1" />

        {/* Interval Buttons */}
        <div className="flex items-center gap-1">
          {intervals.map((int) => (
            <button
              key={int}
              onClick={() => setInterval(int)}
              className={`tv-button px-3 ${interval === int ? "active" : ""}`}
            >
              {int}
            </button>
          ))}
        </div>

        <div className="tv-separator" />

        {/* Tools */}
        <button className="tv-button p-2" title="Indicators">
          <TrendingUp className="w-4 h-4" />
        </button>
        <button className="tv-button p-2" title="Drawing Tools">
          <LineChart className="w-4 h-4" />
        </button>
        <button
          onClick={() => setShowOrderPanel(!showOrderPanel)}
          className={`tv-button p-2 ${showOrderPanel ? "active" : ""}`}
          title="Trading Panel"
        >
          <BarChart2 className="w-4 h-4" />
        </button>
        <button className="tv-button p-2" title="Settings">
          <Settings className="w-4 h-4" />
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Watchlist Sidebar */}
        {showWatchlist && (
          <div className="w-64 border-r border-border bg-card flex flex-col flex-shrink-0">
            <div className="p-3 border-b border-border">
              <h3 className="font-semibold text-sm flex items-center justify-between">
                Watchlist
                <button
                  onClick={() => setShowWatchlist(false)}
                  className="tv-button p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </h3>
            </div>
            <div className="flex-1 overflow-y-auto">
              {watchlist.map((symbol) => (
                <button
                  key={symbol}
                  onClick={() => changeSymbol(symbol)}
                  className={`w-full px-3 py-2 text-left hover:bg-secondary/50 transition-colors ${
                    currentSymbol === symbol ? "bg-secondary" : ""
                  }`}
                >
                  <div className="font-semibold text-sm">{symbol}</div>
                </button>
              ))}
            </div>
            <div className="p-3 border-t border-border">
              <input
                type="text"
                placeholder="Add symbol..."
                className="tv-input w-full text-sm"
                onKeyPress={(e) => {
                  if (e.key === "Enter") {
                    const symbol = (e.target as HTMLInputElement).value.toUpperCase();
                    if (symbol && !watchlist.includes(symbol)) {
                      setWatchlist([...watchlist, symbol]);
                      (e.target as HTMLInputElement).value = "";
                    }
                  }
                }}
              />
            </div>
          </div>
        )}

        {/* Chart Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 relative">
            {currentSymbol && (
              <TradingChart
                symbol={currentSymbol}
                height={0}
                showVolume={true}
              />
            )}
          </div>
        </div>

        {/* Order Panel */}
        {showOrderPanel && (
          <div className="w-80 border-l border-border bg-card flex flex-col flex-shrink-0">
            <div className="p-4 border-b border-border">
              <h3 className="font-semibold text-sm flex items-center justify-between mb-4">
                Order Panel
                <button
                  onClick={() => setShowOrderPanel(false)}
                  className="tv-button p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </h3>

              {/* Order Type Tabs */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setOrderType("market")}
                  className={`flex-1 tv-button py-2 ${orderType === "market" ? "active" : ""}`}
                >
                  Market
                </button>
                <button
                  onClick={() => setOrderType("limit")}
                  className={`flex-1 tv-button py-2 ${orderType === "limit" ? "active" : ""}`}
                >
                  Limit
                </button>
              </div>

              {/* Price Input (for limit orders) */}
              {orderType === "limit" && (
                <div className="mb-4">
                  <label className="text-xs text-muted-foreground block mb-1">
                    Limit Price
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={limitPrice}
                    onChange={(e) => setLimitPrice(parseFloat(e.target.value) || 0)}
                    className="tv-input w-full"
                  />
                </div>
              )}

              {/* Quantity Input */}
              <div className="mb-4">
                <label className="text-xs text-muted-foreground block mb-1">
                  Quantity
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="tv-button px-3"
                  >
                    -
                  </button>
                  <input
                    type="number"
                    min="1"
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                    className="tv-input flex-1 text-center"
                  />
                  <button
                    onClick={() => setQuantity(quantity + 1)}
                    className="tv-button px-3"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Order Summary */}
              {quote && (
                <div className="mb-4 p-3 bg-secondary rounded">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Price:</span>
                    <span className="font-semibold">
                      ${(orderType === "market" ? quote.price : limitPrice).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-muted-foreground">Total:</span>
                    <span className="font-bold">
                      ${((orderType === "market" ? quote.price : limitPrice) * quantity).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Cash Balance:</span>
                    <span>${cashBalance.toFixed(2)}</span>
                  </div>
                </div>
              )}

              {/* Buy/Sell Buttons */}
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => executeTrade("buy")}
                  className="tv-buy-button py-3 rounded font-bold"
                >
                  Buy
                </button>
                <button
                  onClick={() => executeTrade("sell")}
                  className="tv-sell-button py-3 rounded font-bold"
                >
                  Sell
                </button>
              </div>
            </div>

            {/* Positions Section */}
            <div className="p-4">
              <h4 className="text-xs font-semibold text-muted-foreground mb-2">
                YOUR POSITIONS
              </h4>
              <div className="text-xs text-muted-foreground text-center py-4">
                No open positions
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
