import { useState, useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { Check, Clock, MapPin, Sparkles } from "lucide-react";

import { SuitabilityMeter } from "@/components/suitability-meter";
import { Button } from "@/components/ui/button";
import { fetchHospitals } from "@/api/hospitals";
import type { Hospital } from "@/api/types";

export function ExplainabilitySection() {
  const [exampleHospital, setExampleHospital] = useState<Hospital | null>(null);

  useEffect(() => {
    fetchHospitals({ limit: 1 })
      .then((data) => {
        if (data.length > 0 && data[0]) {
          setExampleHospital(data[0]);
        }
      })
      .catch(() => {
        setExampleHospital(null);
      });
  }, []);

  return (
    <section className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
      <div className="grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
        <header>
          <p className="text-sm font-semibold uppercase tracking-widest text-teal">
            Explainability
          </p>
          <h2 className="mt-3 text-3xl font-extrabold sm:text-4xl">
            Every recommendation answers “why this hospital?”
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            No black-box score. Charak shows the specialty match, travel reality, emergency
            readiness, insurance compatibility and cost signals that produced the ranking — and marks
            clearly what is unavailable.
          </p>
        </header>

        {exampleHospital ? (
          <div className="surface grid gap-6 p-6 lg:grid-cols-[1.1fr_auto_1.2fr] lg:items-center">
            <div className="min-w-0">
              <h3 className="text-base font-bold leading-snug">{exampleHospital.name}</h3>
              <p className="mt-2 space-y-1 text-sm text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <MapPin className="h-3.5 w-3.5" /> {exampleHospital.city}, {exampleHospital.state}
                </span>
                <span className="mt-1 flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5" /> {exampleHospital.distance_km != null ? `${exampleHospital.distance_km} km` : "Distance unavailable"}
                </span>
              </p>
              <Link to="/hospital/$id" params={{ id: exampleHospital.id }} className="mt-5 block">
                <Button size="sm" className="rounded-full">
                  View Details
                </Button>
              </Link>
            </div>

            <div className="justify-self-center">
              <SuitabilityMeter value={exampleHospital.suitability ?? 88} />
            </div>

            <ul className="space-y-2.5">
              {(exampleHospital.recommendation_reasons || [
                "Verified ABDM HFR Record",
                "Specialized department match",
                "Emergency services operational"
              ]).map((r) => (
                <li key={r} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="surface flex flex-col items-center justify-center p-8 text-center">
            <Sparkles className="h-8 w-8 text-teal mb-3" />
            <h3 className="text-base font-bold">Transparent AI Ranking</h3>
            <p className="mt-2 text-sm text-muted-foreground max-w-md">
              Hospital recommendations and suitability score breakdowns appear after you enter your symptoms and location.
            </p>
            <Link to="/analyze" className="mt-4">
              <Button size="sm" className="rounded-full">
                Analyze symptoms
              </Button>
            </Link>
          </div>
        )}
      </div>
    </section>
  );
}
