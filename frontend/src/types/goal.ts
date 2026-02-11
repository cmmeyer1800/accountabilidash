export type GoalType = "periodic" | "one_time";
export type Frequency = "daily" | "weekly" | "monthly" | "yearly";
export type ValueType = "none" | "numeric" | "text";

export interface Goal {
  id: string;
  user_id: string;
  title: string;
  description: string;
  goal_type: GoalType;
  frequency: Frequency | null;
  target_count: number;
  value_type: ValueType;
  value_unit: string | null;
  start_date: string;
  end_date: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GoalCreateRequest {
  title: string;
  description?: string;
  goal_type: GoalType;
  frequency?: Frequency | null;
  target_count?: number;
  value_type?: ValueType;
  value_unit?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export interface GoalWithProgress extends Goal {
  period_completions: number;
  is_completed: boolean;
}

export interface CheckInRequest {
  value?: number | null;
  note?: string | null;
}

export interface GoalCompletion {
  id: string;
  goal_id: string;
  completed_at: string;
  period_start: string;
  value: number | null;
  note: string | null;
  created_at: string;
}

export interface GoalUpdateRequest {
  title?: string;
  description?: string;
  goal_type?: GoalType;
  frequency?: Frequency | null;
  target_count?: number;
  value_type?: ValueType;
  value_unit?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_active?: boolean;
}
