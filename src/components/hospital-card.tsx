import { Link } from "@tanstack/react-router";
import {
  Ambulance,
  BedDouble,
  Check,
  Clock,
  IndianRupee,
  MapPin,
  ShieldCheck,
  Star,
  Stethoscope,
} from "lucide-react";

import { SuitabilityMeter } from "./suitability-meter";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { tierMeta } from "@/lib/charak-data";

// Unified hospital shape that works for both old static data and real API data
export type AnyHospital = {
  id: string;
  name: string;
  // Old shape fields (static charak-data.ts)
  area?: string;
  city?: string;
  distanceKm?: number;
  travelMin?: number;
  suitability?: number;
  specialtyMatch?: number;
  specialties?: string[];
  emergency?: boolean;
  insurance?: string[];
  estimatedCost?: string | null;
  availability?: { integrated?: boolean; beds?: number; icu?: number } | null;
  doctors?: { name: string; specialty?: string; experience?: string }[];
  rating?: number;
  reviews?: number;
  tier?: "verified" | "aggregated" | "integrated";
  reasons?: string[];
  // API shape fields (backend response)
  hfr_id?: string;
  address?: string;
  state?: string;
  lat?: number;
  lng?: number;
  distance_km?: number;
  travel_time_mins?: number;
  emergency_ready?: boolean;
  insurance_supported?: string[];
  estimated_cost_range?: string;
  data_provenance?: "PUBLIC_REGISTRY" | "PUBLISHED_AGGREGATED" | "HOSPITAL_INTEGRATION" | "EXTERNAL_DISCOVERY" | string;
  recommendation_reasons?: string[];
};

function normalizeTier(h: AnyHospital): "verified" | "aggregated" | "integrated" {
  if (h.tier) return h.tier;
  if (h.data_provenance === "HOSPITAL_INTEGRATION") return "integrated";
  if (h.data_provenance === "PUBLISHED_AGGREGATED") return "aggregated";
  return "verified";
}

function normalizeAvailability(h: AnyHospital) {
  if (h.availability) {
    return {
      integrated: h.availability.integrated ?? false,
      beds: h.availability.beds,
      icu: h.availability.icu,
    };
  }
  return { integrated: false };
}

export function MapPreview({ className = "" }: { className?: string }) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-border bg-muted ${className}`}
    >
      <div className="absolute inset-0 grid-dots opacity-60" />
      <svg viewBox="0 0 200 120" className="relative h-full w-full">
        <path d="M-10 90 L60 70 L120 96 L210 74" className="stroke-border" strokeWidth="8" fill="none" />
        <path d="M30 -10 L52 60 L44 130" className="stroke-border" strokeWidth="6" fill="none" />
        <path d="M150 -10 L138 130" className="stroke-border" strokeWidth="6" fill="none" />
        <path
          d="M40 100 C70 96 88 78 120 74"
          className="stroke-teal"
          strokeWidth="3"
          fill="none"
          strokeDasharray="7 6"
          strokeLinecap="round"
        />
        <circle cx="40" cy="100" r="5" className="fill-sky" />
        <circle cx="120" cy="74" r="6" className="fill-teal" />
      </svg>
    </div>
  );
}

export function HospitalCard({ hospital: h, rank }: { hospital: AnyHospital; rank?: number }) {
  const tierKey = normalizeTier(h);
  const tier = tierMeta[tierKey];
  const avail = normalizeAvailability(h);

  const specialties = h.specialties ?? [];
  const insurance = h.insurance ?? h.insurance_supported ?? [];
  const rawDist = h.distanceKm ?? h.distance_km;
  const rawTime = h.travelMin ?? h.travel_time_mins;
  
  const distanceText = rawDist != null ? `${rawDist} km` : "Distance unavailable";
  const travelText = rawTime != null ? `${rawTime} min · ` : "";

  const pricing = (h as any).pricing;
  let pricingText = "Pricing unavailable from verified source";
  let pricingOk = false;

  if (pricing?.status === "VERIFIED" && (pricing?.min != null || pricing?.max != null)) {
    pricingText = pricing.min && pricing.max ? `₹${pricing.min} – ₹${pricing.max}` : `₹${pricing.min ?? pricing.max}`;
    pricingOk = true;
  } else if (pricing?.status === "STALE" && pricing?.min != null) {
    pricingText = `₹${pricing.min} – ₹${pricing.max} (Outdated)`;
    pricingOk = false;
  }

  const suitability = h.suitability ?? 85;
  const specialtyMatch = h.specialtyMatch ?? suitability;
  const emergency = h.emergency ?? h.emergency_ready ?? false;
  const rating = h.rating ?? 4.5;
  const reviews = h.reviews ?? 0;
  const doctors = h.doctors ?? [];
  const location = h.area
    ? `${h.area}, ${h.city ?? ""}`
    : h.address
      ? h.address.split(",").slice(0, 2).join(",")
      : h.city ?? "";
  const reasons = h.reasons ?? h.recommendation_reasons ?? [];

  return (
    <article className="surface lift overflow-hidden">
      <div className="grid gap-5 p-5 md:grid-cols-[1.6fr_auto] md:p-6">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            {rank === 1 && (
              <Badge className="rounded-full bg-teal text-teal-foreground font-bold">Best match</Badge>
            )}
            
            {/* Provenance Badge */}
            {((h as any).source === "OpenStreetMap" || h.data_provenance === "EXTERNAL_DISCOVERY") ? (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-sky/40 bg-sky/10 px-2.5 py-1 text-[11px] font-bold text-sky-600 dark:text-sky-400">
                🌐 OpenStreetMap Discovery
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-teal/40 bg-teal/10 px-2.5 py-1 text-[11px] font-bold text-teal">
                🛡 ABDM HFR Verified
              </span>
            )}

            {h.hfr_id && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                ID: {h.hfr_id}
              </span>
            )}
          </div>

          <h3 className="mt-3 text-lg font-bold leading-snug md:text-xl">{h.name}</h3>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 text-teal" /> {location}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" /> {travelText}{distanceText}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Star className="h-3.5 w-3.5 text-warning" /> {rating !== null && rating !== undefined ? rating : "Rating unavailable"}
              {reviews > 0 ? ` (${reviews})` : ""}
            </span>
          </p>

          <div className="mt-4 flex flex-wrap gap-2">
            {specialties.slice(0, 3).map((s) => (
              <Badge key={s} variant="secondary" className="rounded-full font-medium">
                <Stethoscope className="mr-1 h-3 w-3" /> {s}
              </Badge>
            ))}
          </div>

          <dl className="mt-5 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            <Fact
              icon={<Ambulance className="h-4 w-4" />}
              label="Emergency"
              value={emergency ? "24×7 available" : "Not listed"}
              ok={emergency}
            />
            <Fact
              icon={<ShieldCheck className="h-4 w-4" />}
              label="Insurance"
              value={insurance.slice(0, 2).join(", ") || "Direct consultation"}
              ok={insurance.length > 0}
            />
            <Fact
              icon={<IndianRupee className="h-4 w-4" />}
              label="Treatment cost"
              value={pricingText}
              ok={pricingOk}
            />
            <Fact
              icon={<BedDouble className="h-4 w-4" />}
              label="Bed / ICU"
              value={
                avail.integrated && avail.beds != null
                  ? `${avail.beds} beds · ${avail.icu ?? 0} ICU`
                  : "Not provided by discovery source"
              }
              ok={avail.integrated && avail.beds != null}
            />
            <Fact
              icon={<Stethoscope className="h-4 w-4" />}
              label="CHANAKYA Match"
              value={`${specialtyMatch}%`}
              ok
            />
            {doctors[0] && (
              <Fact
                icon={<Stethoscope className="h-4 w-4" />}
                label="Doctor"
                value={
                  (doctors[0] as any).pricing?.status === "VERIFIED" && (doctors[0] as any).pricing?.min != null
                    ? `${(doctors[0] as any).name} (₹${(doctors[0] as any).pricing.min})`
                    : `${(doctors[0] as any).name} (Fee unavailable)`
                }
                ok
              />
            )}
          </dl>

          {/* Action links for external Discovery */}
          {((h as any).phone || (h as any).website) && (
            <div className="mt-4 flex flex-wrap gap-2 pt-3 border-t border-border">
              {(h as any).phone && (
                <a
                  href={`tel:${(h as any).phone}`}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-teal hover:underline"
                >
                  📞 Call {(h as any).phone}
                </a>
              )}
              {(h as any).website && (
                <a
                  href={(h as any).website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-teal hover:underline ml-3"
                >
                  🌐 Visit Website
                </a>
              )}
            </div>
          )}
        </div>

        <div className="flex flex-col items-stretch gap-4 md:w-64">
          <div className="flex items-center gap-4 rounded-2xl border border-border bg-background p-4">
            <SuitabilityMeter value={suitability} size={84} />
            <div className="min-w-0 text-xs text-muted-foreground">
              <span className="font-bold block text-foreground">CHANAKYA MATCH</span>
              Weighted on specialty, distance, capability, cost & insurance.
            </div>
          </div>
          <MapPreview className="h-24" />
          <Link to="/hospital/$id" params={{ id: h.id }}>
            <Button className="w-full rounded-full">View Details</Button>
          </Link>
        </div>
      </div>

      {reasons.length > 0 && (
        <div className="border-t border-border bg-background px-5 py-4 md:px-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Why this hospital?
          </p>
          <ul className="mt-2.5 grid gap-2 sm:grid-cols-2">
            {reasons.map((r) => (
              <li key={r} className="flex items-start gap-2 text-sm text-muted-foreground">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}

function Fact({
  icon,
  label,
  value,
  ok,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  ok?: boolean;
}) {
  return (
    <div className="min-w-0">
      <dt className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        <span className={ok ? "text-teal" : "text-muted-foreground"}>{icon}</span>
        {label}
      </dt>
      <dd className="mt-1 text-sm font-medium leading-snug">{value}</dd>
    </div>
  );
}