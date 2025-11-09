(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/market_sim/frontend/components/TradingChart.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>TradingChart
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$market_sim$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/market_sim/frontend/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$market_sim$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/market_sim/frontend/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
function TradingChart({ symbol, height = 400, showVolume = true, interval = '1D' }) {
    _s();
    const chartContainerRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$market_sim$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const chartRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$market_sim$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const candlestickSeriesRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$market_sim$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const volumeSeriesRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$market_sim$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const [loading, setLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$market_sim$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    // Initialize chart
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$market_sim$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "TradingChart.useEffect": ()=>{
            if (!chartContainerRef.current) return;
            __turbopack_context__.A("[project]/market_sim/frontend/node_modules/lightweight-charts/dist/lightweight-charts.development.mjs [app-client] (ecmascript, async loader)").then({
                "TradingChart.useEffect": ({ createChart })=>{
                    if (!chartContainerRef.current || chartRef.current) return;
                    const chart = createChart(chartContainerRef.current, {
                        layout: {
                            background: {
                                color: 'transparent'
                            },
                            textColor: '#D1D4DC'
                        },
                        grid: {
                            vertLines: {
                                color: 'rgba(42, 46, 57, 0.4)'
                            },
                            horzLines: {
                                color: 'rgba(42, 46, 57, 0.4)'
                            }
                        },
                        width: chartContainerRef.current.clientWidth,
                        height: height || chartContainerRef.current.clientHeight,
                        timeScale: {
                            timeVisible: true,
                            secondsVisible: false,
                            borderColor: '#363A45'
                        },
                        crosshair: {
                            mode: 1,
                            vertLine: {
                                color: '#758696',
                                width: 1,
                                style: 3
                            },
                            horzLine: {
                                color: '#758696',
                                width: 1,
                                style: 3
                            }
                        },
                        rightPriceScale: {
                            borderColor: '#363A45',
                            textColor: '#787B86'
                        },
                        leftPriceScale: {
                            visible: showVolume,
                            borderColor: '#363A45',
                            textColor: '#787B86'
                        }
                    });
                    chartRef.current = chart;
                    // Add candlestick series
                    const candlestickSeries = chart.addCandlestickSeries({
                        upColor: '#089981',
                        downColor: '#F23645',
                        borderVisible: false,
                        wickUpColor: '#089981',
                        wickDownColor: '#F23645'
                    });
                    candlestickSeriesRef.current = candlestickSeries;
                    // Add volume series if enabled
                    if (showVolume) {
                        const volumeSeries = chart.addHistogramSeries({
                            color: '#26a69a',
                            priceFormat: {
                                type: 'volume'
                            },
                            priceScaleId: 'left'
                        });
                        volumeSeriesRef.current = volumeSeries;
                    }
                    // Handle resize
                    const handleResize = {
                        "TradingChart.useEffect.handleResize": ()=>{
                            if (chartContainerRef.current && chartRef.current) {
                                chartRef.current.applyOptions({
                                    width: chartContainerRef.current.clientWidth,
                                    height: height || chartContainerRef.current.clientHeight
                                });
                            }
                        }
                    }["TradingChart.useEffect.handleResize"];
                    window.addEventListener('resize', handleResize);
                    // Load initial data
                    fetchChartData(symbol, interval);
                    return ({
                        "TradingChart.useEffect": ()=>{
                            window.removeEventListener('resize', handleResize);
                            if (chartRef.current) {
                                chartRef.current.remove();
                                chartRef.current = null;
                            }
                        }
                    })["TradingChart.useEffect"];
                }
            }["TradingChart.useEffect"]).catch({
                "TradingChart.useEffect": (error)=>{
                    console.error('Error loading chart library:', error);
                }
            }["TradingChart.useEffect"]);
            return ({
                "TradingChart.useEffect": ()=>{
                    if (chartRef.current) {
                        chartRef.current.remove();
                        chartRef.current = null;
                    }
                }
            })["TradingChart.useEffect"];
        }
    }["TradingChart.useEffect"], [
        height,
        showVolume
    ]);
    // Fetch and update chart data when symbol or interval changes
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$market_sim$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "TradingChart.useEffect": ()=>{
            if (!symbol || !chartRef.current) return;
            fetchChartData(symbol, interval);
        }
    }["TradingChart.useEffect"], [
        symbol,
        interval
    ]);
    const fetchChartData = async (sym, int)=>{
        if (!candlestickSeriesRef.current) return;
        setLoading(true);
        try {
            // Map interval to API format
            const intervalMap = {
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
            const candlestickData = data.map((bar)=>({
                    time: new Date(bar.date).getTime() / 1000,
                    open: bar.open,
                    high: bar.high,
                    low: bar.low,
                    close: bar.close
                }));
            const volumeData = data.map((bar)=>({
                    time: new Date(bar.date).getTime() / 1000,
                    value: bar.volume,
                    color: bar.close >= bar.open ? 'rgba(8, 153, 129, 0.5)' : 'rgba(242, 54, 69, 0.5)'
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
        } finally{
            setLoading(false);
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$market_sim$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "w-full h-full relative",
        ref: chartContainerRef,
        children: loading && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$market_sim$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "absolute top-4 right-4 text-xs text-muted-foreground",
            children: "Loading..."
        }, void 0, false, {
            fileName: "[project]/market_sim/frontend/components/TradingChart.tsx",
            lineNumber: 203,
            columnNumber: 9
        }, this)
    }, void 0, false, {
        fileName: "[project]/market_sim/frontend/components/TradingChart.tsx",
        lineNumber: 201,
        columnNumber: 5
    }, this);
}
_s(TradingChart, "e7P3pyn1BPc1xrULAwIYh/aeoK4=");
_c = TradingChart;
var _c;
__turbopack_context__.k.register(_c, "TradingChart");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/market_sim/frontend/components/TradingChart.tsx [app-client] (ecmascript, next/dynamic entry)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/market_sim/frontend/components/TradingChart.tsx [app-client] (ecmascript)"));
}),
]);

//# sourceMappingURL=market_sim_frontend_components_TradingChart_tsx_ee0fc93b._.js.map