import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { goalsApi } from "@/api";
import { LoadingSpinner } from "@/components/ui";
import type { GoalTrends, PeriodTrendPoint } from "@/types/goal";
import axios from "axios";

type DateRangePreset = "7d" | "30d" | "12w";

function getDateRange(preset: DateRangePreset): { start: string; end: string } {
  const end = new Date();
  const start = new Date();
  switch (preset) {
    case "7d":
      start.setDate(start.getDate() - 7);
      break;
    case "30d":
      start.setDate(start.getDate() - 30);
      break;
    case "12w":
      start.setDate(start.getDate() - 84);
      break;
  }
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

function formatPeriodLabel(
  periodStart: string,
  frequency: string | null | undefined,
): string {
  const d = new Date(periodStart);
  if (frequency === "weekly") {
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  }
  if (frequency === "monthly") {
    return d.toLocaleDateString(undefined, { month: "short", year: "2-digit" });
  }
  if (frequency === "yearly") {
    return d.getFullYear().toString();
  }
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function TrendsPage() {
  const [preset, setPreset] = useState<DateRangePreset>("30d");
  const [trends, setTrends] = useState<GoalTrends[]>([]);
  const [selectedGoalId, setSelectedGoalId] = useState<string | "all">("all");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadTrends = useCallback(async () => {
    const { start, end } = getDateRange(preset);
    setIsLoading(true);
    setError("");
    try {
      const data = await goalsApi.getTrends(start, end);
      setTrends(data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? "Failed to load trends");
      } else {
        setError("Something went wrong.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [preset]);

  useEffect(() => {
    loadTrends();
  }, [loadTrends]);

  const selectedTrends =
    selectedGoalId === "all"
      ? trends
      : trends.filter((t) => t.goal.id === selectedGoalId);

  // Build chart data: for each period, show completion count and target
  const chartData = buildChartData(selectedTrends);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Trends</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          View your goal progress over time
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {trends.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-lg font-medium text-zinc-700 dark:text-zinc-300">
            No active goals
          </p>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Create a goal and start checking in to see your trends here.
          </p>
        </div>
      ) : (
        <>
          {/* Controls */}
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                Date range:
              </span>
              <div className="flex rounded-lg border border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-900">
                {(["7d", "30d", "12w"] as const).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPreset(p)}
                    className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                      preset === p
                        ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                        : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
                    }`}
                  >
                    {p === "7d" ? "7 days" : p === "30d" ? "30 days" : "12 weeks"}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                Goal:
              </span>
              <select
                value={selectedGoalId}
                onChange={(e) =>
                  setSelectedGoalId(e.target.value as string | "all")
                }
                className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
              >
                <option value="all">All goals</option>
                {trends.map((t) => (
                  <option key={t.goal.id} value={t.goal.id}>
                    {t.goal.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Chart */}
          <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            {chartData.length > 0 ? (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={chartData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      className="stroke-zinc-200 dark:stroke-zinc-700"
                    />
                    <XAxis
                      dataKey="periodLabel"
                      angle={-45}
                      textAnchor="end"
                      height={60}
                      tick={{ fontSize: 11 }}
                      className="text-zinc-600 dark:text-zinc-400"
                    />
                    <YAxis
                      tick={{ fontSize: 11 }}
                      className="text-zinc-600 dark:text-zinc-400"
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "var(--tw-bg-opacity)",
                        borderRadius: "0.5rem",
                        border: "1px solid var(--tw-border-color)",
                      }}
                      formatter={(value: number | undefined) =>
                        [value ?? 0, ""]
                      }
                      labelFormatter={(label) => `Period: ${label}`}
                    />
                    <Legend />
                    <Bar
                      dataKey="completions"
                      name="Completions"
                      fill="#6366f1"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="target"
                      name="Target"
                      fill="#a1a1aa"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex h-64 items-center justify-center text-zinc-500 dark:text-zinc-400">
                No data for this period
              </div>
            )}
          </div>

          {/* When showing multiple goals, stacked may not make sense - show completion rate */}
          {selectedTrends.length === 1 && selectedTrends[0].periods.length > 0 && (
            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-zinc-800 dark:text-zinc-200">
                {selectedTrends[0].goal.title} – completion rate
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[400px] text-sm">
                  <thead>
                    <tr className="border-b border-zinc-200 dark:border-zinc-700">
                      <th className="text-left py-2 font-medium text-zinc-600 dark:text-zinc-400">
                        Period
                      </th>
                      <th className="text-right py-2 font-medium text-zinc-600 dark:text-zinc-400">
                        Progress
                      </th>
                      <th className="text-right py-2 font-medium text-zinc-600 dark:text-zinc-400">
                        Status
                      </th>
                      {(selectedTrends[0].goal.value_type === "numeric" ||
                        selectedTrends[0].goal.value_unit) && (
                        <th className="text-right py-2 font-medium text-zinc-600 dark:text-zinc-400">
                          Total
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {selectedTrends[0].periods.map((p) => (
                      <PeriodRow
                        key={p.period_start}
                        point={p}
                        frequency={selectedTrends[0].goal.frequency}
                        showValue={
                          selectedTrends[0].goal.value_type === "numeric" ||
                          selectedTrends[0].goal.value_unit != null
                        }
                        valueUnit={selectedTrends[0].goal.value_unit}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {selectedTrends.length > 1 && (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Select a single goal to see the detailed completion table.
            </p>
          )}
        </>
      )}
    </div>
  );
}

function buildChartData(
  selectedTrends: GoalTrends[],
): Record<string, string | number>[] {
  if (selectedTrends.length === 0) return [];

  // For single goal: one row per period
  if (selectedTrends.length === 1) {
    const t = selectedTrends[0];
    return t.periods.map((p) => ({
      period: p.period_start,
      periodLabel: formatPeriodLabel(p.period_start, t.goal.frequency),
      completions: p.completion_count,
      target: p.target_count,
    }));
  }

  // For multiple goals: aggregate by period, sum completions and targets
  const byPeriod = new Map<
    string,
    { completions: number; target: number; periodLabel: string }
  >();
  for (const t of selectedTrends) {
    for (const p of t.periods) {
      const periodLabel = formatPeriodLabel(
        p.period_start,
        t.goal.frequency ?? undefined,
      );
      const existing = byPeriod.get(p.period_start);
      if (existing) {
        existing.completions += p.completion_count;
        existing.target += p.target_count;
      } else {
        byPeriod.set(p.period_start, {
          completions: p.completion_count,
          target: p.target_count,
          periodLabel,
        });
      }
    }
  }
  return Array.from(byPeriod.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([period, data]) => ({
      period,
      periodLabel: data.periodLabel,
      completions: data.completions,
      target: data.target,
    }));
}

function PeriodRow({
  point,
  frequency,
  showValue,
  valueUnit,
}: {
  point: PeriodTrendPoint;
  frequency: string | null | undefined;
  showValue: boolean;
  valueUnit: string | null;
}) {
  const pct = Math.min(
    Math.round((point.completion_count / point.target_count) * 100),
    100,
  );
  return (
    <tr className="border-b border-zinc-100 dark:border-zinc-800">
      <td className="py-2 text-zinc-700 dark:text-zinc-300">
        {formatPeriodLabel(point.period_start, frequency)}
      </td>
      <td className="py-2 text-right tabular-nums">
        {point.completion_count} / {point.target_count} ({pct}%)
      </td>
      <td className="py-2 text-right">
        <span
          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
            point.is_completed
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
              : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
          }`}
        >
          {point.is_completed ? "Completed" : "Incomplete"}
        </span>
      </td>
      {showValue && (
        <td className="py-2 text-right tabular-nums">
          {point.sum_value != null
            ? `${point.sum_value.toFixed(1)}${valueUnit ? ` ${valueUnit}` : ""}`
            : "—"}
        </td>
      )}
    </tr>
  );
}
