import { useEffect, useState } from "react";
import { Link } from "react-router";
import { goalsApi } from "@/api";
import { Button } from "@/components/ui";
import { LoadingSpinner } from "@/components/ui";
import type { Goal } from "@/types/goal";
import axios from "axios";

const FREQUENCY_LABELS: Record<string, string> = {
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
  yearly: "Yearly",
};

const VALUE_TYPE_LABELS: Record<string, string> = {
  none: "Check-in",
  numeric: "Numeric",
  text: "Text",
};

export function GoalsPage() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadGoals();
  }, []);

  async function loadGoals() {
    try {
      const data = await goalsApi.listGoals();
      setGoals(data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? "Failed to load goals");
      } else {
        setError("Something went wrong.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await goalsApi.deleteGoal(id);
      setGoals((prev) => prev.filter((g) => g.id !== id));
    } catch {
      setError("Failed to delete goal.");
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Goals</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Track your periodic and one-time goals
          </p>
        </div>
        <Link to="/goals/new">
          <Button>New Goal</Button>
        </Link>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {goals.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-zinc-500 dark:text-zinc-400">
            No goals yet. Create your first one to get started.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {goals.map((goal) => (
            <div
              key={goal.id}
              className="group relative rounded-xl border border-zinc-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
            >
              <div className="mb-3 flex items-start justify-between gap-2">
                <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
                  {goal.title}
                </h3>
                <span
                  className={
                    goal.goal_type === "periodic"
                      ? "shrink-0 rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                      : "shrink-0 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                  }
                >
                  {goal.goal_type === "periodic"
                    ? FREQUENCY_LABELS[goal.frequency ?? ""]
                    : "One-time"}
                </span>
              </div>

              {goal.description && (
                <p className="mb-3 text-sm text-zinc-500 dark:text-zinc-400 line-clamp-2">
                  {goal.description}
                </p>
              )}

              <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-400 dark:text-zinc-500">
                {goal.goal_type === "periodic" && goal.target_count > 1 && (
                  <span>{goal.target_count}x per period</span>
                )}
                {goal.value_type !== "none" && (
                  <span>
                    {VALUE_TYPE_LABELS[goal.value_type]}
                    {goal.value_unit ? ` (${goal.value_unit})` : ""}
                  </span>
                )}
                <span>
                  Started{" "}
                  {new Date(goal.start_date).toLocaleDateString()}
                </span>
              </div>

              <div className="absolute right-2 top-2 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                <Link
                  to={`/goals/${goal.id}/edit`}
                  className="rounded p-1 text-zinc-400 hover:text-indigo-500 dark:text-zinc-500 dark:hover:text-indigo-400"
                  title="Edit goal"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                </Link>
                <button
                  onClick={() => handleDelete(goal.id)}
                  className="rounded p-1 text-zinc-400 hover:text-red-500 dark:text-zinc-500 dark:hover:text-red-400"
                  title="Delete goal"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
