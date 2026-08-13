import { createFileRoute, useSearch } from "@tanstack/react-router";
import { AlertCircle, Building2, Loader2, RefreshCw, ServerOff, WifiOff } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { DisclaimerBar } from "@/components/disclaimer-bar";
import { HospitalCard } from "@/components/hospital-card";
import { DataSourcesSection } from "@/components/sections/data-sources-section";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchHospitals } from "@/api/hospitals";
import { APIError, getApiErrorMessage } from "@/api/client";
import type { Hospital } from "@/api/types";

// Accept specialty query param for Currado navigation links
type HospitalSearch = { specialty?: string | undefined };

export const Route = createFileRoute("/hospitals")({
  validateSearch: (search: Record<string, unknown>): HospitalSearch => {
    if (typeof search["specialty"] === "string" && search["specialty"].trim()) {
      return { specialty: search["specialty"] };
    }
    return {};
  },
  head: () => ({
    meta: [
      { title: "Hospital network — Charak" },
      {
        name: "description",
        content:
          "Browse hospitals in the Charak network with specialties, emergency readiness, insurance support and verified data provenance for each facility.",
      },
      { property: "og:title", content: "Hospital network — Charak" },
      {
        property: "og:description",
        content:
          "Every facility is labelled by data layer: verified public registry, published information or active hospital integration.",
      },
    ],
  }),
  component: HospitalsPage,
});

type LoadState = "idle" | "loading" | "success" | "empty" | "error" | "offline";

function HospitalCardSkeleton() {
  return (
    <div className="surface p-5 sm:p-6 animate-pulse">
      <div className="flex items-start gap-4">
        <Skeleton className="h-12 w-12 rounded-xl shrink-0" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
          <div className="flex gap-2 mt-2">
            <Skeleton className="h-6 w-24 rounded-full" />
            <Skeleton className="h-6 w-28 rounded-full" />
          </div>
        </div>
        <Skeleton className="h-10 w-10 rounded-full shrink-0" />
      </div>
    </div>
  );
}

function HospitalsPage() {
  const { specialty } = useSearch({ from: "/hospitals" });
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const loadHospitals = useCallback(async () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoadState("loading");
    setErrorMessage("");

    try {
      const data = await fetchHospitals({
        specialty: specialty ?? undefined,
        signal: controller.signal,
      });

      if (controller.signal.aborted) return;

      if (data.length === 0) {
        setLoadState("empty");
      } else {
        setHospitals(data);
        setLoadState("success");
      }
    } catch (err: unknown) {
      if (controller.signal.aborted) return;

      if (err instanceof APIError) {
        if (err.code === "NETWORK_ERROR" || err.code === "REQUEST_TIMEOUT") {
          setLoadState("offline");
          setErrorMessage(getApiErrorMessage(err));
        } else {
          setLoadState("error");
          setErrorMessage(getApiErrorMessage(err));
        }
      } else {
        setLoadState("offline");
        setErrorMessage(getApiErrorMessage(err));
      }
    }
  }, [specialty]);

  useEffect(() => {
    loadHospitals();
    return () => {
      abortRef.current?.abort();
    };
  }, [loadHospitals]);

  return (
    <>
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">
        <header className="max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-widest text-teal">Hospitals</p>
          <h1 className="mt-3 text-3xl font-extrabold sm:text-4xl">
            {specialty && specialty !== "All"
              ? `${specialty} facilities near you`
              : "Facilities Charak can navigate you to"}
          </h1>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">
            Each hospital card shows where its information comes from. Live bed and ICU counts appear
            only where a hospital integration exists.
          </p>
        </header>

        <DisclaimerBar className="mt-6" />

        <div className="mt-6 space-y-5">
          {/* Loading State */}
          {loadState === "loading" && (
            <>
              {[0, 1, 2].map((i) => (
                <HospitalCardSkeleton key={i} />
              ))}
            </>
          )}

          {/* Success State */}
          {loadState === "success" &&
            hospitals.map((h) => (
              <HospitalCard key={h.id} hospital={h as any} />
            ))}

          {/* Empty State */}
          {loadState === "empty" && (
            <div className="surface flex flex-col items-center justify-center py-16 text-center">
              <Building2 className="h-12 w-12 text-muted-foreground/40" />
              <h2 className="mt-4 text-base font-semibold">
                {specialty ? `No ${specialty} hospitals found` : "No hospitals found"}
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {specialty
                  ? `The database does not contain facilities with a ${specialty} department yet.`
                  : "The hospital database is currently empty. Run the HFR importer to seed data."}
              </p>
              <Button
                className="mt-5 rounded-full"
                variant="outline"
                onClick={loadHospitals}
              >
                <RefreshCw className="mr-1.5 h-4 w-4" />
                Retry
              </Button>
            </div>
          )}

          {/* Backend Offline / Timeout State */}
          {loadState === "offline" && (
            <div className="surface flex flex-col items-center justify-center py-16 text-center">
              <WifiOff className="h-12 w-12 text-danger/60" />
              <h2 className="mt-4 text-base font-semibold text-foreground">
                Backend unavailable
              </h2>
              <p className="mt-2 max-w-sm text-sm text-muted-foreground">{errorMessage}</p>
              <code className="mt-3 block rounded-lg bg-muted px-4 py-2 text-xs text-foreground">
                cd backend &amp;&amp; uvicorn app.main:app --port 8000
              </code>
              <Button
                className="mt-5 rounded-full"
                onClick={loadHospitals}
              >
                <RefreshCw className="mr-1.5 h-4 w-4" />
                Try again
              </Button>
            </div>
          )}

          {/* Generic Error State */}
          {loadState === "error" && (
            <div className="surface flex flex-col items-center justify-center py-16 text-center">
              <AlertCircle className="h-12 w-12 text-danger/60" />
              <h2 className="mt-4 text-base font-semibold">Failed to load hospitals</h2>
              <p className="mt-2 max-w-sm text-sm text-muted-foreground">{errorMessage}</p>
              <Button
                className="mt-5 rounded-full"
                variant="outline"
                onClick={loadHospitals}
              >
                <RefreshCw className="mr-1.5 h-4 w-4" />
                Try again
              </Button>
            </div>
          )}
        </div>
      </div>
      <DataSourcesSection />
    </>
  );
}
