"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import Link from "next/link";
import {
  LayoutDashboard,
  TrendingUp,
  LineChart,
  Settings,
  BookOpen,
  Code,
  BarChart3
} from "lucide-react";

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Sidebar({ className }: SidebarProps) {
  return (
    <div className={cn("pb-12 min-h-screen", className)}>
      <div className="space-y-4 py-4">
        <div className="px-3 py-2">
          <div className="mb-2 px-4 text-lg font-semibold tracking-tight">
            MarketSim
          </div>
          <div className="space-y-1">
            <Link
              href="/dashboard"
              className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <LayoutDashboard className="mr-2 h-4 w-4" />
              Dashboard
            </Link>
            <Link
              href="/dashboard/portfolio"
              className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <TrendingUp className="mr-2 h-4 w-4" />
              Portfolio
            </Link>
            <Link
              href="/dashboard/strategies"
              className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <LineChart className="mr-2 h-4 w-4" />
              Strategies
            </Link>
            <Link
              href="/dashboard/backtest"
              className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <BarChart3 className="mr-2 h-4 w-4" />
              Backtesting
            </Link>
            <Link
              href="/dashboard/algorithms"
              className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <Code className="mr-2 h-4 w-4" />
              My Algorithms
            </Link>
          </div>
        </div>
        <div className="px-3 py-2">
          <div className="mb-2 px-4 text-sm font-semibold text-muted-foreground">
            Learn
          </div>
          <div className="space-y-1">
            <Link
              href="/dashboard/docs"
              className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <BookOpen className="mr-2 h-4 w-4" />
              Documentation
            </Link>
            <Link
              href="/dashboard/settings"
              className="flex items-center rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
