"use client";

import { useEffect, useRef, useState } from 'react';

interface TradingChartProps {
  symbol: string;
  height?: number;
  showVolume?: boolean;
  interval?: string;
}

export default function TradingChart({ symbol, height = 400, showVolume = true, interval = '1D' }: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const candlestickSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);
  const [loading, setLoading] = useState(false);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    import('lightweight-charts').then(({ createChart }) => {
      if (!chartContainerRef.current || chartRef.current) return;

      const chart = createChart(chartContainerRef.current, {
        layout: {
          background: { color: 'transparent' },
          textColor: '#D1D4DC',
        },
        grid: {
          vertLines: { color: 'rgba(42, 46, 57, 0.4)' },
          horzLines: { color: 'rgba(42, 46, 57, 0.4)' },
        },
        width: chartContainerRef.current.clientWidth,
        height: height || chartContainerRef.current.clientHeight,
        timeScale: {
          timeVisible: true,
          secondsVisible: false,
          borderColor: '#363A45',
        },
        crosshair: {
          mode: 1,
          vertLine: {
            color: '#758696',
            width: 1,
            style: 3,
          },
          horzLine: {
            color: '#758696',
            width: 1,
            style: 3,
          },
        },
        rightPriceScale: {
          borderColor: '#363A45',
          textColor: '#787B86',
        },
        leftPriceScale: {
          visible: showVolume,
          borderColor: '#363A45',
          textColor: '#787B86',
        },
      });

      chartRef.current = chart;

      // Add candlestick series
      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#089981',
        downColor: '#F23645',
        borderVisible: false,
        wickUpColor: '#089981',
        wickDownColor: '#F23645',
      });

      candlestickSeriesRef.current = candlestickSeries;

      // Add volume series if enabled
      if (showVolume) {
        const volumeSeries = chart.addHistogramSeries({
          color: '#26a69a',
          priceFormat: {
            type: 'volume',
          },
          priceScaleId: 'left',
        });

        volumeSeriesRef.current = volumeSeries;
      }

      // Handle resize
      const handleResize = () => {
        if (chartContainerRef.current && chartRef.current) {
          chartRef.current.applyOptions({
            width: chartContainerRef.current.clientWidth,
            height: height || chartContainerRef.current.clientHeight,
          });
        }
      };

      window.addEventListener('resize', handleResize);

      // Load initial data
      fetchChartData(symbol, interval);

      return () => {
        window.removeEventListener('resize', handleResize);
        if (chartRef.current) {
          chartRef.current.remove();
          chartRef.current = null;
        }
      };
    }).catch(error => {
      console.error('Error loading chart library:', error);
    });

    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [height, showVolume]);

  // Fetch and update chart data when symbol or interval changes
  useEffect(() => {
    if (!symbol || !chartRef.current) return;
    fetchChartData(symbol, interval);
  }, [symbol, interval]);

  const fetchChartData = async (sym: string, int: string) => {
    if (!candlestickSeriesRef.current) return;

    setLoading(true);
    try {
      // Map interval to API format
      const intervalMap: Record<string, string> = {
        '1M': '1m',
        '5M': '5m',
        '15M': '15m',
        '1H': '1h',
        '1D': '1d',
        '1W': '1d'
      };

      const apiInterval = intervalMap[int] || '1d';
      const period = int === '1D' ? '1y' : int === '1W' ? '2y' : int === '1H' ? '1mo' : '5d';

      const response = await fetch(`/api/stocks/historical/${sym}/${period}?interval=${apiInterval}`);

      if (!response.ok) {
        console.error('Failed to fetch chart data');
        return;
      }

      const data = await response.json();

      if (!data || data.length === 0) {
        console.error('No data received');
        return;
      }

      // Transform data to Lightweight Charts format
      const candlestickData = data.map((bar: any) => ({
        time: (new Date(bar.date).getTime() / 1000) as any,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
      }));

      const volumeData = data.map((bar: any) => ({
        time: (new Date(bar.date).getTime() / 1000) as any,
        value: bar.volume,
        color: bar.close >= bar.open ? 'rgba(8, 153, 129, 0.5)' : 'rgba(242, 54, 69, 0.5)',
      }));

      // Update series
      if (candlestickSeriesRef.current) {
        candlestickSeriesRef.current.setData(candlestickData);
      }

      if (volumeSeriesRef.current && showVolume) {
        volumeSeriesRef.current.setData(volumeData);
      }

      // Fit content
      if (chartRef.current) {
        chartRef.current.timeScale().fitContent();
      }

    } catch (error) {
      console.error('Error fetching chart data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full h-full relative" ref={chartContainerRef}>
      {loading && (
        <div className="absolute top-4 right-4 text-xs text-muted-foreground">
          Loading...
        </div>
      )}
    </div>
  );
}
