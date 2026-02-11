import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router";
import { Button, Input } from "@/components/ui";
import type { Frequency, GoalType, ValueType } from "@/types/goal";
import axios from "axios";

const selectClass =
  "h-10 w-full rounded-lg border px-3 text-sm transition-colors " +
  "border-zinc-300 bg-white text-zinc-900 " +
  "dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 " +
  "focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20";

export interface GoalFormValues {
  title: string;
  description: string;
  goalType: GoalType;
  frequency: Frequency;
  targetCount: number;
  valueType: ValueType;
  valueUnit: string;
  startDate: string;
  endDate: string;
}

interface GoalFormProps {
  initialValues?: Partial<GoalFormValues>;
  onSubmit: (values: GoalFormValues) => Promise<void>;
  submitLabel: string;
}

const defaults: GoalFormValues = {
  title: "",
  description: "",
  goalType: "one_time",
  frequency: "daily",
  targetCount: 1,
  valueType: "none",
  valueUnit: "",
  startDate: new Date().toISOString().split("T")[0],
  endDate: "",
};

export function GoalForm({ initialValues, onSubmit, submitLabel }: GoalFormProps) {
  const navigate = useNavigate();
  const init = { ...defaults, ...initialValues };

  const [title, setTitle] = useState(init.title);
  const [description, setDescription] = useState(init.description);
  const [goalType, setGoalType] = useState<GoalType>(init.goalType);
  const [frequency, setFrequency] = useState<Frequency>(init.frequency);
  const [targetCount, setTargetCount] = useState(init.targetCount);
  const [valueType, setValueType] = useState<ValueType>(init.valueType);
  const [valueUnit, setValueUnit] = useState(init.valueUnit);
  const [startDate, setStartDate] = useState(init.startDate);
  const [endDate, setEndDate] = useState(init.endDate);

  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await onSubmit({
        title,
        description,
        goalType,
        frequency,
        targetCount,
        valueType,
        valueUnit,
        startDate,
        endDate,
      });
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (Array.isArray(detail)) {
          setError(detail.map((d: { msg: string }) => d.msg).join(", "));
        } else {
          setError(detail ?? "Something went wrong");
        }
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Title */}
      <Input
        id="title"
        label="Title"
        placeholder="e.g. Run 3 times a week"
        required
        maxLength={256}
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />

      {/* Description */}
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="description"
          className="text-sm font-medium text-zinc-700 dark:text-zinc-300"
        >
          Description
        </label>
        <textarea
          id="description"
          placeholder="Optional details about this goal..."
          maxLength={1024}
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className={
            "w-full rounded-lg border px-3 py-2 text-sm transition-colors " +
            "border-zinc-300 bg-white text-zinc-900 placeholder:text-zinc-400 " +
            "dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder:text-zinc-500 " +
            "focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          }
        />
      </div>

      {/* Goal type */}
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="goal-type"
          className="text-sm font-medium text-zinc-700 dark:text-zinc-300"
        >
          Goal type
        </label>
        <select
          id="goal-type"
          value={goalType}
          onChange={(e) => setGoalType(e.target.value as GoalType)}
          className={selectClass}
        >
          <option value="one_time">One-time</option>
          <option value="periodic">Periodic (recurring)</option>
        </select>
      </div>

      {/* Periodic-only fields */}
      {goalType === "periodic" && (
        <div className="space-y-4 rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-950">
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="frequency"
              className="text-sm font-medium text-zinc-700 dark:text-zinc-300"
            >
              Frequency
            </label>
            <select
              id="frequency"
              value={frequency}
              onChange={(e) => setFrequency(e.target.value as Frequency)}
              className={selectClass}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
          </div>

          <Input
            id="target-count"
            label="Times per period"
            type="number"
            min={1}
            max={100}
            value={String(targetCount)}
            onChange={(e) => setTargetCount(Number(e.target.value) || 1)}
          />
        </div>
      )}

      {/* Value tracking */}
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="value-type"
          className="text-sm font-medium text-zinc-700 dark:text-zinc-300"
        >
          Completion tracking
        </label>
        <select
          id="value-type"
          value={valueType}
          onChange={(e) => setValueType(e.target.value as ValueType)}
          className={selectClass}
        >
          <option value="none">Simple check-in (just mark done)</option>
          <option value="numeric">Log a number (e.g. miles, pages)</option>
          <option value="text">Log a text note</option>
        </select>
      </div>

      {valueType !== "none" && (
        <Input
          id="value-unit"
          label="Unit label"
          placeholder={
            valueType === "numeric"
              ? "e.g. miles, pages, minutes"
              : "e.g. summary, reflection"
          }
          maxLength={32}
          value={valueUnit}
          onChange={(e) => setValueUnit(e.target.value)}
        />
      )}

      {/* Dates */}
      <div className="grid grid-cols-2 gap-4">
        <Input
          id="start-date"
          label="Start date"
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
        />
        <Input
          id="end-date"
          label="End date (optional)"
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-2">
        <Button type="submit" isLoading={isSubmitting} className="flex-1">
          {submitLabel}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => navigate("/goals")}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}
