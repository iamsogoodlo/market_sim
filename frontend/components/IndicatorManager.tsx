"use client";

import { useState } from "react";
import { Plus, X, Eye, EyeOff, Settings2, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { IndicatorConfig, IndicatorDefinition, IndicatorParam } from "@/types/api";

// Indicator catalog - expand with all MVP indicators
const INDICATOR_CATALOG: IndicatorDefinition[] = [
  {
    type: "SMA",
    display_name: "Simple Moving Average",
    description: "Arithmetic mean of prices over N periods",
    category: "trend",
    params: [
      { name: "period", type: "int", default: 20, min: 1, max: 500 },
      { name: "source", type: "string", default: "close", options: ["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"] },
    ],
    default_style: {
      color: "#2962FF",
      lineWidth: 2,
      lineStyle: "solid",
    },
  },
  {
    type: "EMA",
    display_name: "Exponential Moving Average",
    description: "Exponentially weighted moving average",
    category: "trend",
    params: [
      { name: "period", type: "int", default: 20, min: 1, max: 500 },
      { name: "source", type: "string", default: "close", options: ["close", "open", "high", "low"] },
    ],
    default_style: {
      color: "#FF6D00",
      lineWidth: 2,
      lineStyle: "solid",
    },
  },
  {
    type: "RSI",
    display_name: "Relative Strength Index",
    description: "Momentum oscillator (0-100)",
    category: "momentum",
    params: [
      { name: "period", type: "int", default: 14, min: 2, max: 100 },
      { name: "overbought", type: "int", default: 70, min: 50, max: 100 },
      { name: "oversold", type: "int", default: 30, min: 0, max: 50 },
    ],
    default_style: {
      color: "#9C27B0",
      lineWidth: 2,
      overboughtColor: "#F23645",
      oversoldColor: "#089981",
    },
  },
  {
    type: "MACD",
    display_name: "MACD",
    description: "Moving Average Convergence Divergence",
    category: "momentum",
    params: [
      { name: "fast", type: "int", default: 12, min: 2, max: 100 },
      { name: "slow", type: "int", default: 26, min: 2, max: 200 },
      { name: "signal", type: "int", default: 9, min: 2, max: 50 },
    ],
    default_style: {
      macdColor: "#2962FF",
      signalColor: "#FF6D00",
      histogramColor: "#26a69a",
    },
  },
  {
    type: "BB",
    display_name: "Bollinger Bands",
    description: "Volatility bands around moving average",
    category: "volatility",
    params: [
      { name: "period", type: "int", default: 20, min: 2, max: 200 },
      { name: "std_dev", type: "float", default: 2.0, min: 0.5, max: 5.0 },
    ],
    default_style: {
      upperColor: "#F23645",
      lowerColor: "#089981",
      middleColor: "#787B86",
      fillOpacity: 0.1,
    },
  },
  {
    type: "ATR",
    display_name: "Average True Range",
    description: "Volatility indicator",
    category: "volatility",
    params: [
      { name: "period", type: "int", default: 14, min: 1, max: 100 },
    ],
    default_style: {
      color: "#9C27B0",
      lineWidth: 2,
    },
  },
  {
    type: "VWAP",
    display_name: "Volume Weighted Average Price",
    description: "Intraday price benchmark",
    category: "volume",
    params: [],
    default_style: {
      color: "#FF6D00",
      lineWidth: 2,
    },
  },
  {
    type: "Volume",
    display_name: "Volume",
    description: "Trading volume bars",
    category: "volume",
    params: [
      { name: "show_ma", type: "bool", default: false },
      { name: "ma_period", type: "int", default: 20, min: 1, max: 200 },
    ],
    default_style: {
      upColor: "rgba(8, 153, 129, 0.5)",
      downColor: "rgba(242, 54, 69, 0.5)",
    },
  },
];

interface IndicatorManagerProps {
  indicators: IndicatorConfig[];
  onAdd: (indicator: IndicatorConfig) => void;
  onRemove: (id: string) => void;
  onUpdate: (id: string, updates: Partial<IndicatorConfig>) => void;
  onToggleVisibility: (id: string) => void;
}

export default function IndicatorManager({
  indicators,
  onAdd,
  onRemove,
  onUpdate,
  onToggleVisibility,
}: IndicatorManagerProps) {
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [params, setParams] = useState<Record<string, any>>({});

  const handleAddIndicator = () => {
    if (!selectedType) return;

    const definition = INDICATOR_CATALOG.find((d) => d.type === selectedType);
    if (!definition) return;

    const newIndicator: IndicatorConfig = {
      id: `${selectedType}_${Date.now()}`,
      type: selectedType,
      params: params,
      visible: true,
      pane: definition.category === "overlay" || definition.type === "VWAP" ? 0 : 1,
      style: definition.default_style,
    };

    onAdd(newIndicator);
    setShowAddDialog(false);
    setSelectedType(null);
    setParams({});
  };

  const handleSelectType = (type: string) => {
    setSelectedType(type);
    const definition = INDICATOR_CATALOG.find((d) => d.type === type);
    if (definition) {
      const defaultParams: Record<string, any> = {};
      definition.params.forEach((p) => {
        defaultParams[p.name] = p.default;
      });
      setParams(defaultParams);
    }
  };

  const selectedDefinition = INDICATOR_CATALOG.find((d) => d.type === selectedType);

  return (
    <div className="space-y-4">
      {/* Active Indicators List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
          <CardTitle className="text-sm font-semibold">Active Indicators</CardTitle>
          <Button
            size="sm"
            onClick={() => setShowAddDialog(!showAddDialog)}
            className="h-8"
          >
            <Plus className="h-4 w-4 mr-1" />
            Add
          </Button>
        </CardHeader>
        <CardContent>
          {indicators.length === 0 ? (
            <p className="text-sm text-[hsl(var(--tv-text-secondary))] text-center py-4">
              No indicators added. Click "Add" to get started.
            </p>
          ) : (
            <div className="space-y-2">
              {indicators.map((indicator) => {
                const definition = INDICATOR_CATALOG.find((d) => d.type === indicator.type);
                return (
                  <div
                    key={indicator.id}
                    className="flex items-center justify-between p-3 border border-[hsl(var(--tv-border))] rounded hover:bg-[hsl(var(--tv-surface-elevated))] transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => onToggleVisibility(indicator.id)}
                        className="tv-button p-1"
                      >
                        {indicator.visible ? (
                          <Eye className="h-4 w-4" />
                        ) : (
                          <EyeOff className="h-4 w-4 opacity-50" />
                        )}
                      </button>

                      <div>
                        <p className="text-sm font-semibold text-[hsl(var(--tv-text-primary))]">
                          {definition?.display_name || indicator.type}
                        </p>
                        <p className="text-xs text-[hsl(var(--tv-text-secondary))]">
                          {Object.entries(indicator.params)
                            .map(([key, val]) => `${key}: ${val}`)
                            .join(", ")}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setEditingId(indicator.id)}
                        className="tv-button p-1"
                        title="Edit parameters"
                      >
                        <Settings2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onRemove(indicator.id)}
                        className="tv-button p-1 hover:text-[hsl(var(--tv-red))]"
                        title="Remove indicator"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Indicator Dialog */}
      {showAddDialog && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-semibold">Add Indicator</CardTitle>
            <button onClick={() => setShowAddDialog(false)} className="tv-button p-1">
              <X className="h-4 w-4" />
            </button>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Category Tabs */}
            <div className="flex gap-2 border-b border-[hsl(var(--tv-border))] pb-2">
              {["all", "trend", "momentum", "volatility", "volume"].map((cat) => (
                <button
                  key={cat}
                  className="tv-button text-xs px-3 py-1"
                  onClick={() => {
                    /* Filter by category */
                  }}
                >
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </button>
              ))}
            </div>

            {/* Indicator List */}
            <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
              {INDICATOR_CATALOG.map((def) => (
                <button
                  key={def.type}
                  onClick={() => handleSelectType(def.type)}
                  className={`p-3 text-left border rounded transition-colors ${
                    selectedType === def.type
                      ? "border-[hsl(var(--tv-blue))] bg-[hsl(var(--tv-surface-elevated))]"
                      : "border-[hsl(var(--tv-border))] hover:bg-[hsl(var(--tv-surface-elevated))]"
                  }`}
                >
                  <p className="text-sm font-semibold text-[hsl(var(--tv-text-primary))]">
                    {def.display_name}
                  </p>
                  <p className="text-xs text-[hsl(var(--tv-text-secondary))] mt-1 line-clamp-2">
                    {def.description}
                  </p>
                </button>
              ))}
            </div>

            {/* Parameters */}
            {selectedDefinition && (
              <div className="space-y-3 border-t border-[hsl(var(--tv-border))] pt-4">
                <p className="text-sm font-semibold text-[hsl(var(--tv-text-primary))]">
                  Parameters
                </p>
                {selectedDefinition.params.map((param) => (
                  <div key={param.name} className="space-y-1">
                    <label className="text-xs text-[hsl(var(--tv-text-secondary))] capitalize">
                      {param.name.replace(/_/g, " ")}
                    </label>
                    {param.type === "bool" ? (
                      <input
                        type="checkbox"
                        checked={params[param.name] ?? param.default}
                        onChange={(e) =>
                          setParams({ ...params, [param.name]: e.target.checked })
                        }
                        className="tv-input"
                      />
                    ) : param.options ? (
                      <select
                        value={params[param.name] ?? param.default}
                        onChange={(e) =>
                          setParams({ ...params, [param.name]: e.target.value })
                        }
                        className="tv-input w-full"
                      >
                        {param.options.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <Input
                        type={param.type === "int" || param.type === "float" ? "number" : "text"}
                        value={params[param.name] ?? param.default}
                        onChange={(e) =>
                          setParams({
                            ...params,
                            [param.name]:
                              param.type === "int"
                                ? parseInt(e.target.value)
                                : param.type === "float"
                                ? parseFloat(e.target.value)
                                : e.target.value,
                          })
                        }
                        min={param.min}
                        max={param.max}
                        step={param.type === "float" ? 0.1 : 1}
                        className="tv-input w-full"
                      />
                    )}
                  </div>
                ))}
                <Button onClick={handleAddIndicator} className="w-full mt-4">
                  Add {selectedDefinition.display_name}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
