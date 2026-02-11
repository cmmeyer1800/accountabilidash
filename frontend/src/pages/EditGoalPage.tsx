import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { goalsApi } from "@/api";
import { GoalForm, type GoalFormValues } from "@/components/GoalForm";
import { LoadingSpinner } from "@/components/ui";
import type { Goal } from "@/types/goal";
import axios from "axios";

export function EditGoalPage() {
  const { goalId } = useParams<{ goalId: string }>();
  const navigate = useNavigate();

  const [goal, setGoal] = useState<Goal | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!goalId) return;
    goalsApi
      .getGoal(goalId)
      .then(setGoal)
      .catch((err) => {
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          setError("Goal not found.");
        } else {
          setError("Failed to load goal.");
        }
      })
      .finally(() => setIsLoading(false));
  }, [goalId]);

  async function handleSubmit(values: GoalFormValues) {
    if (!goalId) return;
    await goalsApi.updateGoal(goalId, {
      title: values.title,
      description: values.description,
      goal_type: values.goalType,
      frequency: values.goalType === "periodic" ? values.frequency : null,
      target_count: values.goalType === "periodic" ? values.targetCount : 1,
      value_type: values.valueType,
      value_unit:
        values.valueType !== "none" ? values.valueUnit || null : null,
      start_date: values.startDate || null,
      end_date: values.endDate || null,
    });
    navigate("/goals");
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !goal) {
    return (
      <div className="mx-auto max-w-lg py-20 text-center">
        <p className="text-zinc-500 dark:text-zinc-400">
          {error || "Goal not found."}
        </p>
      </div>
    );
  }

  const initialValues: Partial<GoalFormValues> = {
    title: goal.title,
    description: goal.description,
    goalType: goal.goal_type,
    frequency: goal.frequency ?? "daily",
    targetCount: goal.target_count,
    valueType: goal.value_type,
    valueUnit: goal.value_unit ?? "",
    startDate: goal.start_date,
    endDate: goal.end_date ?? "",
  };

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Edit Goal</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Update your goal details
        </p>
      </div>

      <GoalForm
        initialValues={initialValues}
        onSubmit={handleSubmit}
        submitLabel="Save Changes"
      />
    </div>
  );
}
