"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, DollarSign, Activity } from "lucide-react";
import { useEffect, useState } from "react";

interface PortfolioStats {
  totalValue: number;
  cashBalance: number;
  todayPnL: number;
  totalPnL: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<PortfolioStats>({
    totalValue: 100000,
    cashBalance: 100000,
    todayPnL: 0,
    totalPnL: 0,
  });

  const [connected, setConnected] = useState(false);

  // Fetch portfolio data on mount
  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        const [balanceRes, holdingsRes] = await Promise.all([
          fetch("/api/portfolio/balance"),
          fetch("/api/portfolio/holdings"),
        ]);

        if (balanceRes.ok && holdingsRes.ok) {
          const balanceData = await balanceRes.json();
          const holdingsData = await holdingsRes.json();

          const cashBalance = balanceData.cashBalance || 100000;

          // Calculate holdings value
          const holdingsValue = holdingsData.reduce((sum: number, holding: any) => {
            return sum + (holding.currentPrice || 0) * (holding.quantity || 0);
          }, 0);

          const totalValue = cashBalance + holdingsValue;

          setStats({
            totalValue,
            cashBalance,
            todayPnL: 0, // TODO: Calculate from daily changes
            totalPnL: holdingsValue - holdingsData.reduce((sum: number, h: any) => sum + (h.costBasis || 0) * (h.quantity || 0), 0),
          });
        }
      } catch (error) {
        console.error("Error fetching portfolio data:", error);
      }
    };

    fetchPortfolioData();
  }, []);

  // Connect to WebSocket for real-time updates (optional feature)
  useEffect(() => {
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket("ws://localhost:8080/ws");

      ws.onopen = () => {
        console.log("✓ Connected to market simulator");
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("Received market update:", data);
          // Handle real-time updates here
        } catch (e) {
          console.error("Error parsing message:", e);
        }
      };

      ws.onerror = () => {
        // Silently handle WebSocket errors - this is optional functionality
        setConnected(false);
      };

      ws.onclose = () => {
        console.log("Market simulator connection closed");
        setConnected(false);
      };
    } catch (error) {
      console.log("Market simulator real-time updates unavailable");
      setConnected(false);
    }

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[hsl(var(--tv-text-primary))]">Dashboard</h1>
          <p className="text-[hsl(var(--tv-text-secondary))]">
            Welcome to your quantitative trading platform
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div
            className={`h-2 w-2 rounded-full ${
              connected ? "bg-[hsl(var(--tv-green))]" : "bg-[hsl(var(--tv-text-secondary))]"
            }`}
          />
          <span className="text-xs text-[hsl(var(--tv-text-secondary))]">
            {connected ? "Live" : "Offline"}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${stats.totalValue.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Cash + Holdings
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cash Balance</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${stats.cashBalance.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Available for trading
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's P&L</CardTitle>
            {stats.todayPnL >= 0 ? (
              <TrendingUp className="h-4 w-4 text-[hsl(var(--tv-green))]" />
            ) : (
              <TrendingDown className="h-4 w-4 text-[hsl(var(--tv-red))]" />
            )}
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                stats.todayPnL >= 0 ? "text-[hsl(var(--tv-green))]" : "text-[hsl(var(--tv-red))]"
              }`}
            >
              ${stats.todayPnL >= 0 ? "+" : ""}
              {stats.todayPnL.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats.todayPnL >= 0 ? "↑" : "↓"} {Math.abs(stats.todayPnL / stats.totalValue * 100).toFixed(2)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
            {stats.totalPnL >= 0 ? (
              <TrendingUp className="h-4 w-4 text-[hsl(var(--tv-green))]" />
            ) : (
              <TrendingDown className="h-4 w-4 text-[hsl(var(--tv-red))]" />
            )}
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                stats.totalPnL >= 0 ? "text-[hsl(var(--tv-green))]" : "text-[hsl(var(--tv-red))]"
              }`}
            >
              ${stats.totalPnL >= 0 ? "+" : ""}
              {stats.totalPnL.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              All-time performance
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Orders</CardTitle>
            <CardDescription>Your latest trading activity</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                No recent orders. Place your first order to get started!
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Market Overview</CardTitle>
            <CardDescription>Live NASDAQ data</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Connect to view real-time market data
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
