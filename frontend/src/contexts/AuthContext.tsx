import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { authApi } from "@/api";
import { storage } from "@/lib/utils";
import { TOKEN_KEY } from "@/api/client";
import type { LoginRequest, RegisterRequest, User } from "@/types";
import { AuthContext } from "./auth-context";

/**
 * Provides authentication state & actions to the component tree.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  // If a token is stored we start in a loading state so the initial
  // /auth/me request can resolve before we render protected routes.
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(() => !!storage.get(TOKEN_KEY));

  // Hydrate session from stored token on mount
  useEffect(() => {
    const token = storage.get(TOKEN_KEY);
    if (!token) {
      return;
    }

    let cancelled = false;

    authApi
      .fetchCurrentUser()
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .catch(() => storage.remove(TOKEN_KEY))
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (data: LoginRequest) => {
    const { access_token } = await authApi.login(data);
    storage.set(TOKEN_KEY, access_token);
    const me = await authApi.fetchCurrentUser();
    setUser(me);
  }, []);

  const register = useCallback(
    async (data: RegisterRequest) => {
      await authApi.register(data);
      // Auto-login after successful registration
      await login({ email: data.email, password: data.password });
    },
    [login],
  );

  const logout = useCallback(() => {
    storage.remove(TOKEN_KEY);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      register,
      logout,
    }),
    [user, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
