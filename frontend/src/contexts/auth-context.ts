import { createContext } from "react";
import type { LoginRequest, RegisterRequest, User } from "@/types";

export interface AuthContextValue {
  /** The currently authenticated user, or null when logged out / loading. */
  user: User | null;
  /** True while the initial auth check is in flight. */
  isLoading: boolean;
  /** True when a user is authenticated. */
  isAuthenticated: boolean;
  /** Log in with email & password. */
  login: (data: LoginRequest) => Promise<void>;
  /** Register a new account and log in automatically. */
  register: (data: RegisterRequest) => Promise<void>;
  /** Clear local state and redirect to login. */
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | undefined>(
  undefined,
);
