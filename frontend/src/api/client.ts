import axios from "axios";
import { storage } from "@/lib/utils";

const TOKEN_KEY = "access_token";

/**
 * Pre-configured Axios instance.
 *
 * In development the Vite proxy forwards `/api` to the backend,
 * so we only need a base URL override in production.
 */
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
  headers: { "Content-Type": "application/json" },
});

// ── Request interceptor: attach JWT ────────────────────────────────────────
client.interceptors.request.use((config) => {
  const token = storage.get(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: handle 401 globally ──────────────────────────────
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      storage.remove(TOKEN_KEY);
      // Redirect to login if not already there
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export { TOKEN_KEY };
export default client;
