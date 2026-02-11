import { Link } from "react-router";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui";

export function Header() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center border-b border-zinc-200 bg-white/80 px-6 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
      <Link to="/" className="text-lg font-semibold tracking-tight">
        Accountabilidash
      </Link>

      <div className="ml-auto flex items-center gap-4">
        {isAuthenticated ? (
          <>
            <span className="text-sm text-zinc-600 dark:text-zinc-400">
              {user?.full_name ?? user?.email}
            </span>
            <Button variant="ghost" size="sm" onClick={logout}>
              Log out
            </Button>
          </>
        ) : (
          <>
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Log in
              </Button>
            </Link>
            <Link to="/register">
              <Button size="sm">Sign up</Button>
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
