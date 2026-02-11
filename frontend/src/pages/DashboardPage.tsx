import { type FormEvent, useEffect, useState } from "react";
import { Link } from "react-router";
import { goalsApi } from "@/api";
import { useAuth } from "@/hooks/useAuth";
import { Button, Input } from "@/components/ui";
import { LoadingSpinner } from "@/components/ui";
import type { GoalCompletion, GoalWithProgress } from "@/types/goal";
import axios from "axios";

const FREQUENCY_LABELS: Record<string, string> = {
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
  yearly: "Yearly",
};

export function DashboardPage() {
  const { user } = useAuth();
  const [goals, setGoals] = useState<GoalWithProgress[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      const data = await goalsApi.getDashboard();
      setGoals(data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? "Failed to load dashboard");
      } else {
        setError("Something went wrong.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  // Separate goals into actionable (not yet completed) and done.
  const pending = goals.filter((g) => !g.is_completed);
  const completed = goals.filter((g) => g.is_completed);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Welcome back, {user?.full_name ?? user?.email}
          </p>
        </div>
        <Link to="/goals/new">
          <Button size="sm">New Goal</Button>
        </Link>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {goals.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-lg font-medium text-zinc-700 dark:text-zinc-300">
            No active goals
          </p>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Create a goal to start tracking your progress.
          </p>
          <Link to="/goals/new">
            <Button className="mt-4">Create your first goal</Button>
          </Link>
        </div>
      ) : (
        <>
          {/* Summary bar */}
          <div className="grid gap-4 sm:grid-cols-3">
            <SummaryCard label="Active Goals" value={goals.length} />
            <SummaryCard
              label="Completed Today"
              value={completed.length}
            />
            <SummaryCard label="Remaining" value={pending.length} />
          </div>

          {/* Pending goals */}
          {pending.length > 0 && (
            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-zinc-800 dark:text-zinc-200">
                Ready to check in
              </h2>
              <div className="space-y-3">
                {pending.map((goal) => (
                  <GoalCheckInCard
                    key={goal.id}
                    goal={goal}
                    onCheckIn={loadDashboard}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Completed goals */}
          {completed.length > 0 && (
            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-zinc-800 dark:text-zinc-200">
                Completed this period
              </h2>
              <div className="space-y-3">
                {completed.map((goal) => (
                  <GoalCheckInCard
                    key={goal.id}
                    goal={goal}
                    onCheckIn={loadDashboard}
                  />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

/* ─── Sub-components ──────────────────────────────────────────────────────── */

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
        {label}
      </p>
      <p className="mt-1 text-3xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function GoalCheckInCard({
  goal,
  onCheckIn,
}: {
  goal: GoalWithProgress;
  onCheckIn: () => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [checkInError, setCheckInError] = useState("");

  // Submissions dropdown
  const [isSubmissionsOpen, setIsSubmissionsOpen] = useState(false);
  const [completions, setCompletions] = useState<GoalCompletion[]>([]);
  const [isLoadingCompletions, setIsLoadingCompletions] = useState(false);

  // Value fields for numeric / text goals.
  const [value, setValue] = useState("");
  const [note, setNote] = useState("");

  const needsInput = goal.value_type !== "none";
  const progress = goal.period_completions;
  const target = goal.target_count;
  const pct = Math.min(Math.round((progress / target) * 100), 100);

  async function toggleSubmissions() {
    if (!isSubmissionsOpen && completions.length === 0) {
      setIsLoadingCompletions(true);
      try {
        const data = await goalsApi.getGoalCompletions(goal.id);
        setCompletions(data);
      } finally {
        setIsLoadingCompletions(false);
      }
    }
    setIsSubmissionsOpen((prev) => !prev);
  }

  async function handleQuickCheckIn() {
    setCheckInError("");
    setIsSubmitting(true);
    try {
      await goalsApi.checkIn(goal.id, {});
      onCheckIn();
      if (isSubmissionsOpen) {
        const data = await goalsApi.getGoalCompletions(goal.id);
        setCompletions(data);
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setCheckInError(err.response?.data?.detail ?? "Check-in failed");
      } else {
        setCheckInError("Something went wrong.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDetailedCheckIn(e: FormEvent) {
    e.preventDefault();
    setCheckInError("");
    setIsSubmitting(true);
    try {
      await goalsApi.checkIn(goal.id, {
        value: goal.value_type === "numeric" && value ? Number(value) : null,
        note: note || null,
      });
      setValue("");
      setNote("");
      setIsOpen(false);
      onCheckIn();
      if (isSubmissionsOpen) {
        const data = await goalsApi.getGoalCompletions(goal.id);
        setCompletions(data);
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setCheckInError(err.response?.data?.detail ?? "Check-in failed");
      } else {
        setCheckInError("Something went wrong.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div
      className={`rounded-xl border bg-white p-4 shadow-sm transition dark:bg-zinc-900 ${
        goal.is_completed
          ? "border-emerald-200 dark:border-emerald-900"
          : "border-zinc-200 dark:border-zinc-800"
      }`}
    >
      <div className="flex items-center gap-4">
        {/* Progress ring / check */}
        <div className="flex shrink-0 items-center justify-center">
          {goal.is_completed ? (
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          ) : (
            <div
              className="relative flex h-10 w-10 items-center justify-center"
              title={`${progress}/${target}`}
            >
              <svg className="h-10 w-10 -rotate-90" viewBox="0 0 36 36">
                <circle
                  cx="18"
                  cy="18"
                  r="15.5"
                  fill="none"
                  className="stroke-zinc-200 dark:stroke-zinc-700"
                  strokeWidth="3"
                />
                <circle
                  cx="18"
                  cy="18"
                  r="15.5"
                  fill="none"
                  className="stroke-indigo-500"
                  strokeWidth="3"
                  strokeDasharray={`${pct} ${100 - pct}`}
                  strokeLinecap="round"
                />
              </svg>
              <span className="absolute text-[10px] font-bold tabular-nums text-zinc-600 dark:text-zinc-300">
                {progress}/{target}
              </span>
            </div>
          )}
        </div>

        {/* Goal info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate font-medium text-zinc-900 dark:text-zinc-100">
              {goal.title}
            </h3>
            <span
              className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                goal.goal_type === "periodic"
                  ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                  : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
              }`}
            >
              {goal.goal_type === "periodic"
                ? FREQUENCY_LABELS[goal.frequency ?? ""]
                : "One-time"}
            </span>
          </div>
          {goal.description && (
            <p className="mt-0.5 truncate text-sm text-zinc-500 dark:text-zinc-400">
              {goal.description}
            </p>
          )}
        </div>

        {/* Action */}
        {!goal.is_completed && (
          <div className="shrink-0">
            {needsInput ? (
              <Button
                size="sm"
                variant={isOpen ? "secondary" : "primary"}
                onClick={() => setIsOpen(!isOpen)}
              >
                {isOpen ? "Cancel" : "Check in"}
              </Button>
            ) : (
              <Button
                size="sm"
                isLoading={isSubmitting}
                onClick={handleQuickCheckIn}
              >
                Check in
              </Button>
            )}
          </div>
        )}

        {/* Dropdown arrow */}
        <button
          type="button"
          onClick={toggleSubmissions}
          className={`shrink-0 rounded p-1.5 text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 ${
            isSubmissionsOpen ? "rotate-180" : ""
          }`}
          title="View submissions"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
      </div>

      {/* Error */}
      {checkInError && (
        <div className="mt-2 rounded-lg bg-red-50 p-2 text-xs text-red-700 dark:bg-red-950 dark:text-red-300">
          {checkInError}
        </div>
      )}

      {/* Expandable input form */}
      {isOpen && !goal.is_completed && (
        <form
          onSubmit={handleDetailedCheckIn}
          className="mt-3 space-y-3 border-t border-zinc-100 pt-3 dark:border-zinc-800"
        >
          {goal.value_type === "numeric" && (
            <Input
              id={`value-${goal.id}`}
              label={`Value${goal.value_unit ? ` (${goal.value_unit})` : ""}`}
              type="number"
              step="any"
              placeholder="0"
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
          )}
          <Input
            id={`note-${goal.id}`}
            label="Note (optional)"
            placeholder="How did it go?"
            maxLength={512}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <Button size="sm" type="submit" isLoading={isSubmitting}>
            Submit
          </Button>
        </form>
      )}

      {/* Submissions from this period */}
      {isSubmissionsOpen && (
        <div className="mt-3 border-t border-zinc-100 pt-3 dark:border-zinc-800">
          <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Submissions this period
          </h4>
          {isLoadingCompletions ? (
            <div className="flex items-center justify-center py-6">
              <LoadingSpinner size="sm" />
            </div>
          ) : completions.length === 0 ? (
            <p className="py-2 text-sm text-zinc-500 dark:text-zinc-400">
              No submissions yet.
            </p>
          ) : (
            <ul className="space-y-2">
              {completions.map((c) => (
                <li
                  key={c.id}
                  className="flex items-start gap-3 rounded-lg bg-zinc-50 px-3 py-2 text-sm dark:bg-zinc-950"
                >
                  <span className="shrink-0 text-zinc-500 dark:text-zinc-400">
                    {new Date(c.completed_at).toLocaleString()}
                  </span>
                  <div className="min-w-0 flex-1">
                    {c.value != null && (
                      <span className="font-medium tabular-nums">
                        {c.value}
                        {goal.value_unit ? ` ${goal.value_unit}` : ""}
                      </span>
                    )}
                    {c.note && (
                      <p
                        className={`text-zinc-600 dark:text-zinc-300 ${
                          c.value != null ? "mt-0.5" : ""
                        }`}
                      >
                        {c.note}
                      </p>
                    )}
                    {c.value == null && !c.note && (
                      <span className="text-zinc-600 dark:text-zinc-300">
                        Checked in
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
