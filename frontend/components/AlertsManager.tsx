"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Bell, BellOff, Trash2, Clock, CheckCircle2, XCircle } from "lucide-react";
import { Alert, AlertCreate, AlertCondition, AlertChannel, AlertHistory } from "@/types/api";

interface AlertsManagerProps {
  alerts: Alert[];
  history: AlertHistory[];
  onCreateAlert: (alert: AlertCreate) => Promise<void>;
  onDeleteAlert: (alertId: string) => Promise<void>;
  onDisableAlert: (alertId: string) => Promise<void>;
}

export default function AlertsManager({
  alerts,
  history,
  onCreateAlert,
  onDeleteAlert,
  onDisableAlert,
}: AlertsManagerProps) {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newAlert, setNewAlert] = useState<Partial<AlertCreate>>({
    condition: AlertCondition.PRICE_ABOVE,
    channels: [AlertChannel.IN_APP],
  });

  const handleCreateAlert = async () => {
    if (!newAlert.symbol || newAlert.value === undefined) {
      alert("Please fill in all required fields");
      return;
    }

    await onCreateAlert(newAlert as AlertCreate);
    setShowCreateDialog(false);
    setNewAlert({
      condition: AlertCondition.PRICE_ABOVE,
      channels: [AlertChannel.IN_APP],
    });
  };

  const getConditionLabel = (condition: AlertCondition): string => {
    const labels = {
      [AlertCondition.PRICE_ABOVE]: "Price Above",
      [AlertCondition.PRICE_BELOW]: "Price Below",
      [AlertCondition.PRICE_CROSSES_ABOVE]: "Crosses Above",
      [AlertCondition.PRICE_CROSSES_BELOW]: "Crosses Below",
      [AlertCondition.PERCENT_CHANGE]: "% Change",
    };
    return labels[condition];
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <Clock className="h-4 w-4 text-[hsl(var(--tv-blue))]" />;
      case "triggered":
        return <CheckCircle2 className="h-4 w-4 text-[hsl(var(--tv-green))]" />;
      case "expired":
        return <XCircle className="h-4 w-4 text-[hsl(var(--tv-text-secondary))]" />;
      case "disabled":
        return <BellOff className="h-4 w-4 text-[hsl(var(--tv-text-secondary))]" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[hsl(var(--tv-text-primary))]">Alerts</h2>
          <p className="text-sm text-[hsl(var(--tv-text-secondary))]">
            Get notified when price conditions are met
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Alert
        </Button>
      </div>

      {/* Active Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Active Alerts</CardTitle>
          <CardDescription>
            {alerts.filter((a) => a.status === "active").length} active
          </CardDescription>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <p className="text-sm text-[hsl(var(--tv-text-secondary))] text-center py-8">
              No alerts configured. Create one to get started.
            </p>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-4 border border-[hsl(var(--tv-border))] rounded hover:bg-[hsl(var(--tv-surface-elevated))] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {getStatusIcon(alert.status)}
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-[hsl(var(--tv-text-primary))]">
                          {alert.symbol}
                        </p>
                        <span className="text-xs px-2 py-0.5 rounded bg-[hsl(var(--tv-surface-elevated))] text-[hsl(var(--tv-text-secondary))]">
                          {getConditionLabel(alert.condition)}
                        </span>
                      </div>
                      <p className="text-sm text-[hsl(var(--tv-text-secondary))] mt-1">
                        {alert.condition === AlertCondition.PERCENT_CHANGE
                          ? `${alert.value}% change`
                          : `$${alert.value.toFixed(2)}`}
                        {alert.message && ` • ${alert.message}`}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        {alert.channels.map((channel) => (
                          <span
                            key={channel}
                            className="text-xs text-[hsl(var(--tv-blue))]"
                          >
                            {channel}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {alert.status === "active" && (
                      <button
                        onClick={() => onDisableAlert(alert.id)}
                        className="tv-button p-2"
                        title="Disable alert"
                      >
                        <BellOff className="h-4 w-4" />
                      </button>
                    )}
                    <button
                      onClick={() => onDeleteAlert(alert.id)}
                      className="tv-button p-2 hover:text-[hsl(var(--tv-red))]"
                      title="Delete alert"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Alert History */}
      {history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Triggers</CardTitle>
            <CardDescription>Last {history.length} triggered alerts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 border border-[hsl(var(--tv-border))] rounded"
                >
                  <div>
                    <p className="text-sm font-semibold text-[hsl(var(--tv-text-primary))]">
                      {item.symbol} • {item.message}
                    </p>
                    <p className="text-xs text-[hsl(var(--tv-text-secondary))] mt-1">
                      Triggered at ${item.trigger_price.toFixed(2)} •{" "}
                      {new Date(item.timestamp * 1000).toLocaleString()}
                    </p>
                  </div>
                  <Bell className="h-4 w-4 text-[hsl(var(--tv-green))]" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create Alert Dialog */}
      {showCreateDialog && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle>Create Alert</CardTitle>
            <button onClick={() => setShowCreateDialog(false)} className="tv-button p-1">
              <XCircle className="h-5 w-5" />
            </button>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Symbol */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-[hsl(var(--tv-text-primary))]">
                Symbol
              </label>
              <Input
                placeholder="AAPL"
                value={newAlert.symbol || ""}
                onChange={(e) =>
                  setNewAlert({ ...newAlert, symbol: e.target.value.toUpperCase() })
                }
                className="tv-input"
              />
            </div>

            {/* Condition */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-[hsl(var(--tv-text-primary))]">
                Condition
              </label>
              <select
                value={newAlert.condition}
                onChange={(e) =>
                  setNewAlert({ ...newAlert, condition: e.target.value as AlertCondition })
                }
                className="tv-input w-full"
              >
                {Object.values(AlertCondition).map((cond) => (
                  <option key={cond} value={cond}>
                    {getConditionLabel(cond)}
                  </option>
                ))}
              </select>
            </div>

            {/* Value */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-[hsl(var(--tv-text-primary))]">
                {newAlert.condition === AlertCondition.PERCENT_CHANGE
                  ? "Percent Change"
                  : "Price"}
              </label>
              <Input
                type="number"
                step="0.01"
                placeholder={newAlert.condition === AlertCondition.PERCENT_CHANGE ? "5.0" : "150.00"}
                value={newAlert.value || ""}
                onChange={(e) =>
                  setNewAlert({ ...newAlert, value: parseFloat(e.target.value) })
                }
                className="tv-input"
              />
            </div>

            {/* Message (optional) */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-[hsl(var(--tv-text-primary))]">
                Message (optional)
              </label>
              <Input
                placeholder="Custom alert message"
                value={newAlert.message || ""}
                onChange={(e) => setNewAlert({ ...newAlert, message: e.target.value })}
                className="tv-input"
              />
            </div>

            {/* Channels */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-[hsl(var(--tv-text-primary))]">
                Notification Channels
              </label>
              <div className="space-y-2">
                {Object.values(AlertChannel).map((channel) => (
                  <label key={channel} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={newAlert.channels?.includes(channel)}
                      onChange={(e) => {
                        const channels = newAlert.channels || [];
                        if (e.target.checked) {
                          setNewAlert({ ...newAlert, channels: [...channels, channel] });
                        } else {
                          setNewAlert({
                            ...newAlert,
                            channels: channels.filter((c) => c !== channel),
                          });
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm text-[hsl(var(--tv-text-primary))]">
                      {channel}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Webhook URL (if WEBHOOK selected) */}
            {newAlert.channels?.includes(AlertChannel.WEBHOOK) && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-[hsl(var(--tv-text-primary))]">
                  Webhook URL
                </label>
                <Input
                  type="url"
                  placeholder="https://..."
                  value={newAlert.webhook_url || ""}
                  onChange={(e) =>
                    setNewAlert({ ...newAlert, webhook_url: e.target.value })
                  }
                  className="tv-input"
                />
              </div>
            )}

            <Button onClick={handleCreateAlert} className="w-full">
              Create Alert
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
