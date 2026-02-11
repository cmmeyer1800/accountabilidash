import type { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types";
import client from "./client";

const PREFIX = "/api/v1/auth";

/** Register a new user. */
export async function register(data: RegisterRequest): Promise<User> {
  const res = await client.post<User>(`${PREFIX}/register`, data);
  return res.data;
}

/** Log in and return a JWT. */
export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await client.post<TokenResponse>(`${PREFIX}/login`, data);
  return res.data;
}

/** Fetch the currently authenticated user. */
export async function fetchCurrentUser(): Promise<User> {
  const res = await client.get<User>(`${PREFIX}/me`);
  return res.data;
}
