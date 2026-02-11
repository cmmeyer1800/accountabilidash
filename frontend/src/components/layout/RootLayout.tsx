import { Outlet } from "react-router";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { useAuth } from "@/hooks/useAuth";

/**
 * Top-level shell shared by all pages.
 * Shows header always; sidebar only when authenticated.
 */
export function RootLayout() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="flex min-h-screen flex-col bg-white text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <Header />
      <div className="flex flex-1">
        {isAuthenticated && <Sidebar />}
        <main className="flex flex-1 flex-col p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
