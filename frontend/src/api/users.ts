import type { User } from "@/types";
import client from "./client";

const PREFIX = "/api/v1/users";

/** Fetch all users (admin). */
export async function fetchUsers(): Promise<User[]> {
  const res = await client.get<User[]>(PREFIX);
  return res.data;
}

/** Fetch a single user by ID. */
export async function fetchUser(id: string): Promise<User> {
  const res = await client.get<User>(`${PREFIX}/${id}`);
  return res.data;
}
