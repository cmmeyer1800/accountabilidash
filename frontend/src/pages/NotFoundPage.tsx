import { Link } from "react-router";
import { Button } from "@/components/ui";

export function NotFoundPage() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-6xl font-bold text-zinc-300 dark:text-zinc-700">
        404
      </h1>
      <p className="text-lg text-zinc-600 dark:text-zinc-400">
        The page you&apos;re looking for doesn&apos;t exist.
      </p>
      <Link to="/">
        <Button variant="secondary">Go home</Button>
      </Link>
    </div>
  );
}
