import { createBrowserRouter, Navigate } from "react-router";
import { RootLayout } from "@/components/layout";
import { ProtectedRoute } from "./ProtectedRoute";
import {
  CreateGoalPage,
  DashboardPage,
  EditGoalPage,
  GoalsPage,
  LoginPage,
  NotFoundPage,
  RegisterPage,
} from "@/pages";

/**
 * Centralised route definitions.
 *
 * To add a new page:
 *   1. Create a component in `src/pages/`
 *   2. Add an entry below (inside or outside ProtectedRoute as needed)
 */
export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      // ── Public routes ────────────────────────────────────────────────
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },

      // ── Protected routes ─────────────────────────────────────────────
      {
        element: <ProtectedRoute />,
        children: [
          { path: "/dashboard", element: <DashboardPage /> },
          { path: "/goals", element: <GoalsPage /> },
          { path: "/goals/new", element: <CreateGoalPage /> },
          { path: "/goals/:goalId/edit", element: <EditGoalPage /> },
        ],
      },

      // ── Redirects & fallback ─────────────────────────────────────────
      { path: "/", element: <Navigate to="/dashboard" replace /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
