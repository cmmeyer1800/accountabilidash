import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { authApi } from "@/api";
import type { StravaAthlete } from "@/api/auth";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui";

export function AccountPage() {
  const { user, refreshUser } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [stravaMessage, setStravaMessage] = useState<
    "connected" | "denied" | "error" | null
  >(null);
  const [isConnectingStrava, setIsConnectingStrava] = useState(false);
  const [stravaAthlete, setStravaAthlete] = useState<StravaAthlete | null>(
    null,
  );

  // Handle Strava OAuth callback query params
  useEffect(() => {
    const status = searchParams.get("strava");
    if (status === "connected" || status === "denied" || status === "error") {
      setStravaMessage(status);
      refreshUser();
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, refreshUser, setSearchParams]);

  // Fetch Strava athlete when connected
  useEffect(() => {
    if (user?.strava_connected) {
      authApi
        .fetchStravaAthlete()
        .then(setStravaAthlete)
        .catch(() => setStravaAthlete(null));
    } else {
      setStravaAthlete(null);
    }
  }, [user?.strava_connected]);

  async function handleConnectStrava() {
    setIsConnectingStrava(true);
    try {
      const { url } = await authApi.getStravaConnectUrl();
      window.location.href = url;
    } catch {
      setStravaMessage("error");
    } finally {
      setIsConnectingStrava(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Account</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Manage your account and connected services.
        </p>
      </div>

      {stravaMessage && (
        <div
          className={`rounded-lg p-3 text-sm ${
            stravaMessage === "connected"
              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
              : stravaMessage === "denied"
                ? "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
                : "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
          }`}
        >
          {stravaMessage === "connected"
            ? "Strava account linked successfully."
            : stravaMessage === "denied"
              ? "Strava authorization was cancelled."
              : "Failed to link Strava. Please try again."}
        </div>
      )}

      {/* Connections subsection */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Connections
        </h2>
        <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
          Link external services to enhance your experience.
        </p>

        {/* Strava */}
        <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            Strava
          </h3>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Connect your Strava account to sync activities and track your
            fitness goals.
          </p>
          <div className="mt-4">
            {(user?.strava_connected ?? false) ? (
              stravaAthlete ? (
                <div className="flex items-center gap-4">
                  {(stravaAthlete.profile ?? stravaAthlete.profile_medium) ? (
                    <img
                      src={
                        stravaAthlete.profile ?? stravaAthlete.profile_medium ?? ""
                      }
                      alt=""
                      className="h-14 w-14 rounded-full object-cover"
                    />
                  ) : (
                    <div className="flex h-14 w-14 items-center justify-center rounded-full bg-orange-100 text-lg font-semibold text-orange-600 dark:bg-orange-950 dark:text-orange-400">
                      {stravaAthlete.firstname[0]}
                      {stravaAthlete.lastname[0]}
                    </div>
                  )}
                  <div>
                    <p className="font-medium text-zinc-900 dark:text-zinc-100">
                      {stravaAthlete.firstname} {stravaAthlete.lastname}
                    </p>
                    {(stravaAthlete.city ?? stravaAthlete.country) && (
                      <p className="text-sm text-zinc-500 dark:text-zinc-400">
                        {[stravaAthlete.city, stravaAthlete.country]
                          .filter(Boolean)
                          .join(", ")}
                      </p>
                    )}
                    <span className="mt-1 inline-block rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-medium text-orange-700 dark:bg-orange-950 dark:text-orange-300">
                      Connected
                    </span>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-4">
                  <div className="h-14 w-14 animate-pulse rounded-full bg-zinc-200 dark:bg-zinc-700" />
                  <div className="space-y-2">
                    <div className="h-4 w-32 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
                    <div className="h-3 w-24 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
                  </div>
                </div>
              )
            ) : (
              <Button
                variant="secondary"
                onClick={handleConnectStrava}
                isLoading={isConnectingStrava}
              >
                Connect Strava
              </Button>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
