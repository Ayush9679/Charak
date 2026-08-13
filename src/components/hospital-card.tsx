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
import type { TreatmentPrice } from "@/api/types";

// Unified hospital shape that works for both old static data and real API data
export type AnyHospital = {
  id: string;
  name: string;
  // Old shape fields (static charak-data.ts)
  area?: string;
  city?: string;
  distanceKm?: number;
  travelMin?: number;
  // Canonical suitability score — single source of truth consumed by both
  // the recommendation card and the detail page.
  suitability?: number;
  specialtyMatch?: number;
  specialties?: string[];
  emergency?: boolean;
  insurance?: string[];
  estimatedCost?: string | null;
  availability?: {
    integrated?: boolean;
    beds?: number;
    icu?: number;
    // API availability fields
    total_beds?: number;
    total_icu?: number;
    status?: string;
  } | null;
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
  // Structured pricing
  pricing?: {
    min?: number | null;
    max?: number | null;
    currency?: string;
    status?: string;
    source_type?: string;
    source?: string | null;
  };
  treatment_pricing?: TreatmentPrice[];
};

function normalizeTier(h: AnyHospital): "verified" | "aggregated" | "integrated" {
  if (h.tier) return h.tier;
  if (h.data_provenance === "HOSPITAL_INTEGRATION") return "integrated";
  if (h.data_provenance === "PUBLISHED_AGGREGATED") return "aggregated";
  return "verified";
}

/**
 * Resolves bed display from both legacy (charak-data.ts) and API shapes.
 * Returns { totalBeds, totalIcu } or nulls when unavailable.
 */
function resolveBedInfo(h: AnyHospital): { totalBeds: number | null; totalIcu: number | null } {
  const avail = h.availability;
  if (!avail) return { totalBeds: null, totalIcu: null };

  // API shape: total_beds / total_icu with status === "AVAILABLE"
  if (avail.status === "AVAILABLE" && avail.total_beds != null) {
    return {
      totalBeds: avail.total_beds,
      totalIcu: avail.total_icu ?? null,
    };
  }

  // Legacy shape: integrated flag + beds / icu
  if (avail.integrated && avail.beds != null) {
    return {
      totalBeds: avail.beds,
      totalIcu: avail.icu ?? null,
    };
  }

  return { totalBeds: null, totalIcu: null };
}

/**
 * Formats a price in INR with lakh shorthand.
 * e.g. 120000 → "₹1.2L", 4000 → "₹4,000"
 */
export function formatInrPrice(amount: number): string {
  if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(1).replace(/\.0$/, "")}L`;
  }
  return `₹${amount.toLocaleString("en-IN")}`;
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

  const specialties = h.specialties ?? [];
  const insurance = h.insurance ?? h.insurance_supported ?? [];
  const rawDist = h.distanceKm ?? h.distance_km;
  const rawTime = h.travelMin ?? h.travel_time_mins;

  const distanceText = rawDist != null ? `${rawDist} km` : "Distance unavailable";
  const travelText = rawTime != null ? `${rawTime} min · ` : "";

  // -------------------------------------------------------------------------
  // Canonical suitability score — single source of truth.
  // Both the SuitabilityMeter circle and the "Charak Match" fact cell read
  // from this one variable. Do NOT use specialtyMatch independently.
  // -------------------------------------------------------------------------
  const suitabilityScore: number | undefined = h.suitability ?? undefined;

  // -------------------------------------------------------------------------
  // Pricing — card summary line
  // -------------------------------------------------------------------------
  const pricing = h.pricing;
  const treatmentPricing = h.treatment_pricing ?? [];

  let pricingText = "Pricing unavailable";
  let pricingOk = false;

  if (pricing?.status === "VERIFIED" && (pricing?.min != null || pricing?.max != null)) {
    pricingText = pricing.min && pricing.max
      ? `${formatInrPrice(pricing.min)} – ${formatInrPrice(pricing.max)}`
      : `${formatInrPrice(pricing.min ?? pricing.max ?? 0)}`;
    pricingOk = true;
  } else if (pricing?.status === "DEMO" || treatmentPricing.some((t) => t.source_type === "demo")) {
    // Show range of first treatment as a representative demo price
    const first = treatmentPricing[0];
    pricingText = first
      ? `${formatInrPrice(first.min_price)} – ${formatInrPrice(first.max_price)} (indicative)`
      : "Indicative demo pricing";
    pricingOk = true;
  } else if (pricing?.status === "STALE" && pricing?.min != null) {
    pricingText = `${formatInrPrice(pricing.min)} – ${formatInrPrice(pricing.max ?? pricing.min)} (outdated)`;
    pricingOk = false;
  }

  // -------------------------------------------------------------------------
  // Bed count — surfaces total_beds from API availability or legacy integrated flag
  // -------------------------------------------------------------------------
  const { totalBeds, totalIcu } = resolveBedInfo(h);
  const bedText =
    totalBeds != null
      ? totalIcu != null
        ? `${totalBeds} Beds · ${totalIcu} ICU`
        : `${totalBeds} Beds`
      : "Not provided by verified source";

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
              <Star className="h-3.5 w-3.5 text-warning" />{" "}
              {rating !== null && rating !== undefined ? rating : "Rating unavailable"}
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
              value={bedText}
              ok={totalBeds != null}
            />
            {/* Charak Match fact — reads from the same suitabilityScore as the meter */}
            <Fact
              icon={<Stethoscope className="h-4 w-4" />}
              label="Charak Match"
              value={suitabilityScore != null ? `${suitabilityScore}%` : "Score unavailable"}
              ok={suitabilityScore != null}
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
            {/* SuitabilityMeter reads from suitabilityScore — same field as the Fact above */}
            {suitabilityScore != null ? (
              <SuitabilityMeter value={suitabilityScore} size={84} />
            ) : (
              <div className="flex h-[84px] w-[84px] shrink-0 items-center justify-center rounded-full border-2 border-dashed border-muted-foreground/30">
                <span className="text-[10px] text-muted-foreground text-center leading-tight">Score<br />unavailable</span>
              </div>
            )}
            <div className="min-w-0 text-xs text-muted-foreground">
              <span className="font-bold block text-foreground">CHARAK MATCH</span>
              Weighted on specialty, distance, capability, cost &amp; insurance.
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
