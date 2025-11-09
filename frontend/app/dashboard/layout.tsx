"use client";

import React, { useState } from "react";
import { Sidebar, SidebarBody, SidebarLink } from "@/components/ui/sidebar-nav";
import { LayoutDashboard, TrendingUp, LineChart, Code, BarChart3, BookOpen, Settings, ShoppingCart } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const links = [
    {
      label: "Dashboard",
      href: "/dashboard",
      icon: (
        <LayoutDashboard className="h-5 w-5 flex-shrink-0" />
      ),
    },
    {
      label: "Portfolio",
      href: "/dashboard/portfolio",
      icon: (
        <TrendingUp className="h-5 w-5 flex-shrink-0" />
      ),
    },
    {
      label: "Trade",
      href: "/dashboard/trade",
      icon: (
        <ShoppingCart className="h-5 w-5 flex-shrink-0" />
      ),
    },
    {
      label: "Strategies",
      href: "/dashboard/strategies",
      icon: (
        <LineChart className="h-5 w-5 flex-shrink-0" />
      ),
    },
    {
      label: "Backtesting",
      href: "/dashboard/backtest",
      icon: (
        <BarChart3 className="h-5 w-5 flex-shrink-0" />
      ),
    },
    {
      label: "Algorithms",
      href: "/dashboard/algorithms",
      icon: (
        <Code className="h-5 w-5 flex-shrink-0" />
      ),
    },
    {
      label: "Documentation",
      href: "/dashboard/docs",
      icon: (
        <BookOpen className="h-5 w-5 flex-shrink-0" />
      ),
    },
    {
      label: "Settings",
      href: "/dashboard/settings",
      icon: (
        <Settings className="h-5 w-5 flex-shrink-0" />
      ),
    },
  ];

  const [open, setOpen] = useState(false);

  return (
    <div className="flex flex-col md:flex-row bg-[hsl(var(--tv-background))] w-full min-h-screen">
      <Sidebar open={open} setOpen={setOpen}>
        <SidebarBody className="justify-start gap-0">
          <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden w-full">
            <div className="flex flex-col gap-0 w-full">
              {links.map((link, idx) => (
                <SidebarLink key={idx} link={link} />
              ))}
            </div>
          </div>
        </SidebarBody>
      </Sidebar>
      {/* Main content with proper margin to account for fixed sidebar */}
      <main className="flex-1 w-full md:ml-[48px] pt-12 md:pt-0">
        <div className="w-full bg-[hsl(var(--tv-background))] min-h-screen">
          {children}
        </div>
      </main>
    </div>
  );
}

export const Logo = () => {
  return (
    <Link
      href="/"
      className="font-normal flex space-x-2 items-center text-sm text-black py-1 relative z-20"
    >
      <div className="h-5 w-6 bg-gradient-to-br from-purple-600 to-blue-600 rounded-br-lg rounded-tr-sm rounded-tl-lg rounded-bl-sm flex-shrink-0" />
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="font-medium text-black dark:text-white whitespace-pre"
      >
        MarketSim
      </motion.span>
    </Link>
  );
};

export const LogoIcon = () => {
  return (
    <Link
      href="/"
      className="font-normal flex space-x-2 items-center text-sm text-black py-1 relative z-20"
    >
      <div className="h-5 w-6 bg-gradient-to-br from-purple-600 to-blue-600 rounded-br-lg rounded-tr-sm rounded-tl-lg rounded-bl-sm flex-shrink-0" />
    </Link>
  );
};
