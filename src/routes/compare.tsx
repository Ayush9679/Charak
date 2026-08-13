import { useState, useEffect } from "react";
import { Link, createFileRoute } from "@tanstack/react-router";
import { Check, Minus, Building2, Loader2 } from "lucide-react";

import { DisclaimerBar } from "@/components/disclaimer-bar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchHospitals } from "@/api/hospitals";
import { loadRecommendationResult } from "@/lib/analysis-store";
import type { Hospital } from "@/api/types";

export const Route = createFileRoute("/compare")({
  head: () => ({
    meta: [
      { title: "Compare hospitals side by side — Charak" },
      {
        name: "description",
        content:
          "Compare hospitals on specialty, distance, travel time, estimated cost, insurance, facilities, emergency services, availability, doctor match and suitability.",
      },
      { property: "og:title", content: "Compare hospitals side by side — Charak" },
      {
        property: "og:description",
        content: "A transparent comparison table across ten healthcare navigation factors.",
      },
    ],
  }),
  component: ComparePage,
});

const rows: { label: string; render: (h: Hospital) => React.ReactNode }[] = [
  { label: "Specialty", render: (h) => (h.specialties || []).slice(0, 2).join(", ") || "General" },
  { label: "Distance", render: (h) => (h.distance_km != null ? `${h.distance_km} km` : <Muted>Unavailable</Muted>) },
  { label: "Travel time", render: (h) => (h.travel_time_mins != null ? `${h.travel_time_mins} min` : <Muted>Unavailable</Muted>) },
  {
    label: "Treatment cost",
    render: (h) =>
      h.pricing?.status === "VERIFIED" && h.pricing?.min != null
        ? `₹${h.pricing.min} – ₹${h.pricing.max ?? h.pricing.min}`
        : <Muted>Not available from verified source</Muted>
  },
  { label: "Insurance", render: (h) => (h.insurance_supported || []).join(", ") || <Muted>Check with hospital</Muted> },
  {
    label: "Emergency",
    render: (h) =>
      h.emergency_ready ? (
        <span className="inline-flex items-center gap-1.5 text-success">
          <Check className="h-4 w-4" /> 24×7
        </span>
      ) : (
        <Muted>Not listed</Muted>
      ),
  },
  {
    label: "Availability",
    render: (h) =>
      h.availability && h.availability.status === "AVAILABLE" ? (
        `${h.availability.beds_available} beds · ${h.availability.icu_available} ICU`
      ) : (
        <Muted>Live bed availability not provided</Muted>
      ),
  },
  {
    label: "Doctor match",
    render: (h) => (h.doctors && h.doctors[0]?.specialty) ? h.doctors[0].specialty : <Muted>Not listed</Muted>,
  },
  {
    label: "Suitability",
    render: (h) =>
      h.suitability != null ? (
        <span className="font-display text-base font-extrabold">{h.suitability}</span>
      ) : (
        <Muted>Unavailable</Muted>
      ),
  },
];

function Muted({ children }: { children: React.ReactNode }) {
  return <span className="text-muted-foreground">{children}</span>;
}

function ComparePage() {
  const [list, setList] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const recResult = loadRecommendationResult();
    if (recResult && recResult.hospitals && recResult.hospitals.length > 0) {
      setList(recResult.hospitals.slice(0, 4));
      setLoading(false);
    } else {
      fetchHospitals({ limit: 4 })
        .then((data) => {
          setList(data);
        })
        .catch(() => {
          setList([]);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, []);

  const best = list[0];

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">
      <header className="max-w-2xl">
        <h1 className="text-3xl font-extrabold sm:text-4xl">Compare hospitals</h1>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground sm:text-base">
          The same ten factors Charak uses to rank, side by side. Missing data is shown as missing —
          never estimated.
        </p>
      </header>

      <DisclaimerBar className="mt-6" />

      {loading ? (
        <div className="surface mt-6 p-12 flex flex-col items-center justify-center text-center">
          <Loader2 className="h-8 w-8 animate-spin text-teal" />
          <p className="mt-3 text-sm text-muted-foreground">Loading hospital comparison...</p>
        </div>
      ) : list.length === 0 ? (
        <div className="surface mt-6 p-12 flex flex-col items-center justify-center text-center">
          <Building2 className="h-10 w-10 text-muted-foreground/40" />
          <h2 className="mt-3 text-base font-semibold">No hospitals to compare</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Run an analysis or browse the hospital network to view recommendations.
          </p>
          <Link to="/analyze" className="mt-4">
            <Button size="sm" className="rounded-full">Start analysis</Button>
          </Link>
        </div>
      ) : (
        <div className="surface mt-6 overflow-x-auto">
          <table className="w-full min-w-[860px] border-collapse text-sm">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 bg-card px-5 py-5 text-left text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                  Factor
                </th>
                {list.map((h) => (
                  <th
                    key={h.id}
                    className={`min-w-56 border-l border-border px-5 py-5 text-left align-top ${
                      h.id === best?.id ? "bg-muted" : ""
                    }`}
                  >
                    {h.id === best?.id && (
                      <Badge className="mb-2 rounded-full bg-teal text-teal-foreground">
                        Recommended
                      </Badge>
                    )}
                    <span className="block text-sm font-bold leading-snug">{h.name}</span>
                    <span className="mt-1 block text-xs font-normal text-muted-foreground">
                      {h.city}, {h.state}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.label} className="border-t border-border">
                  <th className="sticky left-0 z-10 bg-card px-5 py-4 text-left align-top text-sm font-semibold">
                    {r.label}
                  </th>
                  {list.map((h) => (
                    <td
                      key={h.id}
                      className={`border-l border-border px-5 py-4 align-top leading-snug ${
                        h.id === best?.id ? "bg-muted" : ""
                      }`}
                    >
                      {r.render(h)}
                    </td>
                  ))}
                </tr>
              ))}
              <tr className="border-t border-border">
                <th className="sticky left-0 z-10 bg-card px-5 py-4" aria-label="Actions">
                  <Minus className="h-4 w-4 text-muted-foreground" />
                </th>
                {list.map((h) => (
                  <td
                    key={h.id}
                    className={`border-l border-border px-5 py-4 ${h.id === best?.id ? "bg-muted" : ""}`}
                  >
                    <Link to="/hospital/$id" params={{ id: h.id }}>
                      <Button size="sm" variant="outline" className="rounded-full bg-card">
                        View Details
                      </Button>
                    </Link>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
