import { Link, createFileRoute, notFound } from "@tanstack/react-router";
import {
  Ambulance,
  ArrowLeft,
  BedDouble,
  Check,
  Clock,
  IndianRupee,
  Info,
  MapPin,
  ShieldCheck,
  Star,
  Stethoscope,
} from "lucide-react";

import { DisclaimerBar } from "@/components/disclaimer-bar";
import { MapPreview, formatInrPrice } from "@/components/hospital-card";
import { SuitabilityMeter } from "@/components/suitability-meter";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchHospitalById } from "@/api/hospitals";
import type { Hospital as APIHospital, TreatmentPrice } from "@/api/types";
import { tierMeta } from "@/lib/charak-data";

export const Route = createFileRoute("/hospital/$id")({
  loader: async ({ params }): Promise<{ hospital: APIHospital }> => {
    try {
      const hospital = await fetchHospitalById(params.id);
      if (!hospital) throw notFound();
      return { hospital };
    } catch {
      throw notFound();
    }
  },
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [{ title: "Hospital unavailable — Charak" }, { name: "robots", content: "noindex" }],
      };
    }
    const { hospital } = loaderData;
    const description = `${hospital.name} in ${hospital.city}, ${hospital.state} — specialties, facilities, insurance, emergency services and published cost information.`;
    return {
      meta: [
        { title: `${hospital.name} — Charak` },
        { name: "description", content: description },
        { property: "og:title", content: `${hospital.name} — Charak` },
        { property: "og:description", content: description },
      ],
    };
  },
  component: HospitalDetail,
});

// ---------------------------------------------------------------------------
// Pricing state helpers
// ---------------------------------------------------------------------------

type PricingState = "verified" | "demo" | "unavailable";

function resolvePricingState(
  pricing: APIHospital["pricing"],
  treatmentPricing: TreatmentPrice[]
): PricingState {
  if (pricing?.status === "VERIFIED" && pricing?.min != null) return "verified";
  if (
    pricing?.status === "DEMO" ||
    treatmentPricing.some((t) => t.source_type === "demo")
  )
    return "demo";
  return "unavailable";
}

// ---------------------------------------------------------------------------
// Detail page
// ---------------------------------------------------------------------------

function HospitalDetail() {
  const { hospital: h } = Route.useLoaderData() as { hospital: APIHospital };
  const tierKey =
    h.data_provenance === "HOSPITAL_INTEGRATION"
      ? "integrated"
      : h.data_provenance === "PUBLISHED_AGGREGATED"
        ? "aggregated"
        : "verified";
  const tier = tierMeta[tierKey];

  const specialties = h.specialties ?? [];
  const insurance = h.insurance_supported ?? [];
  const doctors = h.doctors ?? [];
  const reasons = h.recommendation_reasons ?? [];
  const availability = h.availability;
  const treatmentPricing: TreatmentPrice[] = h.treatment_pricing ?? [];

  // -------------------------------------------------------------------------
  // Canonical suitability score — reads h.suitability which the backend
  // populates from hospitals.suitability_score (the single DB source of truth).
  // The recommendation card reads the same field via the sessionStorage result.
  // Neither view recalculates independently.
  // -------------------------------------------------------------------------
  const suitabilityScore: number | undefined = h.suitability ?? undefined;

  // -------------------------------------------------------------------------
  // Bed capacity — total_beds / total_icu from the availability record.
  // We surface total capacity (not live available count) to match the card.
  // -------------------------------------------------------------------------
  const totalBeds = availability?.total_beds ?? null;
  const totalIcu = availability?.total_icu ?? null;
  const bedStatusAvailable = availability?.status === "AVAILABLE";

  // -------------------------------------------------------------------------
  // Pricing state
  // -------------------------------------------------------------------------
  const pricingState = resolvePricingState(h.pricing, treatmentPricing);

  return (
    <div className="mx-auto max-w-7xl px-5 py-10 lg:px-8">
      <Link
        to="/results"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> Back to recommendations
      </Link>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.55fr_1fr]">
        <div className="min-w-0 space-y-6">
          <section className="surface p-6">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                <span className={`h-1.5 w-1.5 rounded-full ${tier.dot}`} /> {tier.label}
              </span>
              {h.hfr_id && (
                <Badge variant="secondary" className="rounded-full">
                  HFR: {h.hfr_id}
                </Badge>
              )}
            </div>
            <h1 className="mt-4 text-3xl font-extrabold leading-tight">{h.name}</h1>
            <p className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="h-4 w-4" /> {h.address}, {h.city}, {h.state}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Clock className="h-4 w-4" />{" "}
                {h.distance_km != null ? `${h.distance_km} km` : "Distance unavailable"}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Star className="h-4 w-4 text-warning" /> {h.rating}
              </span>
            </p>
            <p className="mt-5 text-sm leading-relaxed text-muted-foreground">
              Verified facility registered under ABDM Health Facility Registry ({h.hfr_id}).
            </p>
          </section>

          <Panel title="Specialties & Departments" icon={<Stethoscope className="h-4 w-4" />}>
            <div className="flex flex-wrap gap-2">
              {specialties.map((d) => (
                <Badge key={d} variant="secondary" className="rounded-full">
                  {d}
                </Badge>
              ))}
            </div>
          </Panel>

          <Panel title="Doctors" icon={<Stethoscope className="h-4 w-4" />}>
            {doctors.length ? (
              <ul className="grid gap-3 sm:grid-cols-2">
                {doctors.map((d) => (
                  <li key={d.name} className="rounded-2xl border border-border bg-background p-4">
                    <p className="text-sm font-semibold">{d.name}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {d.specialty} · {d.qualification} ({d.experience_years} yrs exp)
                    </p>
                    <p className="mt-1 text-xs font-medium text-teal">
                      {d.pricing?.status === "VERIFIED" && d.pricing?.min != null
                        ? `Consultation fee: ₹${d.pricing.min}`
                        : "Consultation fee unavailable from verified source"}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">
                Doctor information is not currently listed for this facility.
              </p>
            )}
          </Panel>

          <Panel title="Insurance Supported" icon={<ShieldCheck className="h-4 w-4" />}>
            <div className="flex flex-wrap gap-2">
              {insurance.length ? (
                insurance.map((i) => (
                  <Badge key={i} variant="secondary" className="rounded-full">
                    {i}
                  </Badge>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">Check with hospital counter.</p>
              )}
            </div>
          </Panel>

          <Panel title="Emergency Services" icon={<Ambulance className="h-4 w-4" />}>
            <p className="text-sm text-muted-foreground">
              {h.emergency_ready
                ? "24×7 Emergency Department operational with acute care readiness."
                : "Emergency department status not listed."}
            </p>
          </Panel>

          <Panel title="Location & Map" icon={<MapPin className="h-4 w-4" />}>
            <MapPreview className="h-56" />
            <p className="mt-3 text-xs text-muted-foreground">
              GPS Coordinates: {h.lat}, {h.lng}
            </p>
          </Panel>
        </div>

        <aside className="space-y-6 lg:sticky lg:top-24 lg:self-start">
          {/* ---------------------------------------------------------------
              Suitability Score Panel
              Reads from h.suitability — same canonical field as the card.
          --------------------------------------------------------------- */}
          <div className="surface p-6">
            <div className="flex items-center gap-4">
              {suitabilityScore != null ? (
                <SuitabilityMeter value={suitabilityScore} />
              ) : (
                <div className="flex h-[92px] w-[92px] shrink-0 items-center justify-center rounded-full border-2 border-dashed border-muted-foreground/30">
                  <span className="text-[10px] text-muted-foreground text-center leading-tight">
                    Score<br />unavailable
                  </span>
                </div>
              )}
              <p className="text-xs leading-relaxed text-muted-foreground">
                Suitability score based on specialty match, emergency readiness, distance, and insurance.
              </p>
            </div>
            {reasons.length > 0 && (
              <ul className="mt-5 space-y-2.5 border-t border-border pt-5">
                {reasons.map((r) => (
                  <li key={r} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" /> {r}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* ---------------------------------------------------------------
              Treatment Cost Panel
              Three states: verified | demo | unavailable
          --------------------------------------------------------------- */}
          <div className="surface p-6">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <IndianRupee className="h-4 w-4 text-teal" /> Treatment Cost
            </h2>

            {pricingState === "verified" && h.pricing?.min != null && (
              <div className="mt-2.5 space-y-1">
                <div className="inline-flex items-center gap-1.5 rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">
                  ✓ Verified pricing
                </div>
                <p className="mt-2 text-sm font-bold text-foreground">
                  {formatInrPrice(h.pricing.min)} – {formatInrPrice(h.pricing.max ?? h.pricing.min)}{" "}
                  {h.pricing.currency}
                </p>
                {h.pricing.source && (
                  <p className="text-xs text-muted-foreground">Source: {h.pricing.source}</p>
                )}
              </div>
            )}

            {pricingState === "demo" && treatmentPricing.length > 0 && (
              <div className="mt-3 space-y-3">
                <ul className="space-y-2">
                  {treatmentPricing.map((t) => (
                    <li key={t.treatment} className="flex items-center justify-between gap-2">
                      <span className="text-sm text-muted-foreground">{t.treatment}</span>
                      <span className="shrink-0 text-sm font-semibold text-foreground">
                        {formatInrPrice(t.min_price)} – {formatInrPrice(t.max_price)}
                      </span>
                    </li>
                  ))}
                </ul>
                {/* Disclaimer — clearly distinguishes demo from verified */}
                <div className="flex items-start gap-2 rounded-xl border border-warning/30 bg-warning/5 px-3 py-2.5 text-[11px] leading-relaxed text-warning-foreground">
                  <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
                  <span>
                    <strong>Indicative demo pricing</strong> — verify final cost directly with the hospital. These figures are representative ranges, not confirmed tariffs.
                  </span>
                </div>
              </div>
            )}

            {pricingState === "unavailable" && (
              <p className="mt-2.5 text-xs text-muted-foreground leading-relaxed">
                Pricing unavailable from verified source. Charak does not display unverified or estimated costs.
              </p>
            )}
          </div>

          {/* ---------------------------------------------------------------
              Bed Availability Panel
              Shows total bed capacity (not live count) — consistent with card.
          --------------------------------------------------------------- */}
          <div className="surface p-6">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <BedDouble className="h-4 w-4 text-teal" /> Bed Availability
            </h2>
            {bedStatusAvailable && totalBeds != null ? (
              <div className="mt-3 grid grid-cols-2 gap-3">
                <Metric label="Total beds" value={String(totalBeds)} />
                {totalIcu != null && <Metric label="ICU beds" value={String(totalIcu)} />}
              </div>
            ) : (
              <p className="mt-2.5 text-sm text-muted-foreground">
                Live bed availability is not currently provided by this facility.
              </p>
            )}
          </div>

          <div className="surface p-6">
            <Button className="w-full rounded-full">Book Appointment</Button>
            <Link to="/compare" className="mt-3 block">
              <Button variant="outline" className="w-full rounded-full bg-card">
                Compare with others
              </Button>
            </Link>
          </div>

          <DisclaimerBar />
        </aside>
      </div>
    </div>
  );
}

function Panel({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="surface p-6">
      <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-widest text-muted-foreground">
        <span className="text-teal">{icon}</span> {title}
      </h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-background p-4">
      <p className="font-display text-xl font-extrabold">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
