import { useNavigate } from "react-router";
import { goalsApi } from "@/api";
import { GoalForm, type GoalFormValues } from "@/components/GoalForm";

export function CreateGoalPage() {
  const navigate = useNavigate();

  async function handleSubmit(values: GoalFormValues) {
    await goalsApi.createGoal({
      title: values.title,
      description: values.description || undefined,
      goal_type: values.goalType,
      frequency: values.goalType === "periodic" ? values.frequency : null,
      target_count: values.goalType === "periodic" ? values.targetCount : 1,
      value_type: values.valueType,
      value_unit:
        values.valueType !== "none" ? values.valueUnit || undefined : undefined,
      start_date: values.startDate || undefined,
      end_date: values.endDate || undefined,
    });
    navigate("/goals");
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">New Goal</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Define a one-time or recurring goal to track
        </p>
      </div>

      <GoalForm onSubmit={handleSubmit} submitLabel="Create Goal" />
    </div>
  );
}
