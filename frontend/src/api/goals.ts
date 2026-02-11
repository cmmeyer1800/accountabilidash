import client from "./client";
import type {
  CheckInRequest,
  Goal,
  GoalCompletion,
  GoalCreateRequest,
  GoalUpdateRequest,
  GoalWithProgress,
} from "@/types/goal";

export async function createGoal(data: GoalCreateRequest): Promise<Goal> {
  const response = await client.post<Goal>("/api/v1/goals", data);
  return response.data;
}

export async function listGoals(activeOnly = true): Promise<Goal[]> {
  const response = await client.get<Goal[]>("/api/v1/goals", {
    params: { active_only: activeOnly },
  });
  return response.data;
}

export async function getGoal(id: string): Promise<Goal> {
  const response = await client.get<Goal>(`/api/v1/goals/${id}`);
  return response.data;
}

export async function updateGoal(
  id: string,
  data: GoalUpdateRequest,
): Promise<Goal> {
  const response = await client.patch<Goal>(`/api/v1/goals/${id}`, data);
  return response.data;
}

export async function getDashboard(): Promise<GoalWithProgress[]> {
  const response = await client.get<GoalWithProgress[]>(
    "/api/v1/goals/dashboard",
  );
  return response.data;
}

export async function checkIn(
  goalId: string,
  data: CheckInRequest = {},
): Promise<GoalCompletion> {
  const response = await client.post<GoalCompletion>(
    `/api/v1/goals/${goalId}/check-in`,
    data,
  );
  return response.data;
}

export async function getGoalCompletions(
  goalId: string,
): Promise<GoalCompletion[]> {
  const response = await client.get<GoalCompletion[]>(
    `/api/v1/goals/${goalId}/completions`,
  );
  return response.data;
}

export async function deleteGoal(id: string): Promise<void> {
  await client.delete(`/api/v1/goals/${id}`);
}
