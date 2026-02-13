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

/** Get the Strava OAuth URL to redirect the user to (requires auth). */
export async function getStravaConnectUrl(): Promise<{ url: string }> {
  const res = await client.get<{ url: string }>(`${PREFIX}/strava/connect-url`);
  return res.data;
}

/** Fetch the linked Strava athlete profile (requires Strava to be connected). */
export async function fetchStravaAthlete(): Promise<StravaAthlete> {
  const res = await client.get<StravaAthlete>(`${PREFIX}/strava/me`);
  return res.data;
}

/** Strava athlete summary from /api/v3/athlete */
export interface StravaAthlete {
  id: number;
  username: string | null;
  firstname: string;
  lastname: string;
  city: string | null;
  state: string | null;
  country: string | null;
  profile: string | null;
  profile_medium: string | null;
  created_at: string;
  updated_at: string;
}

