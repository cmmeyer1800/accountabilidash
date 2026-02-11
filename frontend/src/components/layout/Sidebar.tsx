import { NavLink } from "react-router";
import { cn } from "@/lib/utils";

export interface SidebarLink {
  to: string;
  label: string;
}

const navLinks: SidebarLink[] = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/goals", label: "Goals" },
];

export function Sidebar() {
  return (
    <aside className="hidden w-56 shrink-0 border-r border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 lg:block">
      <nav className="flex flex-col gap-1 p-4">
        {navLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              cn(
                "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-100",
              )
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
