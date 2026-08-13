import { useState } from "react";
import { Link, createFileRoute } from "@tanstack/react-router";
import {
  AlertCircle,
  ArrowRight,
  Building2,
  Check,
  ChevronDown,
  ChevronUp,
  Clock,
  Columns3,
  HelpCircle,
  Info,
  MapPin,
  RefreshCw,
  Search,
  ShieldAlert,
  SlidersHorizontal,
  Sparkles,
  Stethoscope,
  Zap,
} from "lucide-react";

import { DisclaimerBar } from "@/components/disclaimer-bar";
import { HospitalCard } from "@/components/hospital-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { loadAnalysis, loadRecommendationResult } from "@/lib/analysis-store";
import type { Hospital, PossibleCondition } from "@/api/types";

export const Route = createFileRoute("/results")({
  head: () => ({
    meta: [
      { title: "Clinical assessment & recommendations — Charak" },
      {
        name: "description",
        content:
          "AI healthcare assessment identifying possible clinical patterns, required medical specialties, and verified hospital discovery.",
      },
      { property: "og:title", content: "Clinical assessment & recommendations — Charak" },
      {
        property: "og:description",
        content: "Transparent healthcare assessment with possible conditions and hospital discovery.",
      },
    ],
  }),
  component: ResultsPage,
});

// Map urgency to badge style
function urgencyBadgeClass(urgency: string) {
  switch (urgency) {
    case "EMERGENCY":
      return "bg-danger text-white";
    case "URGENT":
      return "bg-warning text-foreground";
    case "MODERATE":
      return "bg-sky-500 text-white";
    default:
      return "bg-success text-white";
  }
}

// Map confidence label to badge style
function confidenceBadgeVariant(label?: string) {
  switch (label) {
    case "More consistent with":
      return "bg-teal text-teal-foreground font-semibold";
    case "Needs clinical evaluation":
      return "bg-warning/20 text-warning-foreground border border-warning/40 font-medium";
    case "Less consistent with":
      return "bg-muted text-muted-foreground font-normal";
    default:
      return "bg-secondary text-secondary-foreground font-medium";
  }
}

function ResultsPage() {
  const input = typeof window === "undefined" ? null : loadAnalysis();
  const result = typeof window === "undefined" ? null : loadRecommendationResult();

  const [viewMode, setViewMode] = useState<"clinical" | "hospitals">("clinical");
  const [showExplainability, setShowExplainability] = useState(false);

  // If no real result, show fallback message and send user back to analyze
  if (!result) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-24 lg:px-8 flex flex-col items-center text-center">
        <AlertCircle className="h-14 w-14 text-muted-foreground/50" />
        <h1 className="mt-5 text-2xl font-bold">No recommendation results yet</h1>
        <p className="mt-3 max-w-md text-sm text-muted-foreground">
          Please describe your symptoms on the intake form first. Charak will analyze your symptoms
          and present possible clinical patterns followed by real hospital discovery.
        </p>
        <Link to="/analyze" className="mt-6">
          <Button className="rounded-full">
            <Sparkles className="mr-1.5 h-4 w-4" />
            Start analysis
          </Button>
        </Link>
      </div>
    );
  }

  const ranked = [...(result.hospitals || [])].sort(
    (a, b) => (b.suitability ?? 0) - (a.suitability ?? 0)
  );

  const possibleConditions: PossibleCondition[] = result.possible_conditions || [];
  const isEmergency = result.urgency_category === "EMERGENCY" || (result.red_flags && result.red_flags.length > 0);

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">
      {/* Navigation View Switcher Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3.5 py-1.5 text-xs font-semibold text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-teal" /> Step 3 of 3 · {viewMode === "clinical" ? "Clinical Assessment" : "Hospital Discovery"}
          </span>
          <h1 className="mt-3 text-2xl font-extrabold sm:text-3xl">
            {viewMode === "clinical" ? "AI Healthcare Assessment" : `Hospital Recommendations (${ranked.length})`}
          </h1>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {viewMode === "hospitals" ? (
            <Button
              variant="outline"
              size="sm"
              className="rounded-full bg-card"
              onClick={() => {
                setViewMode("clinical");
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
            >
              <Stethoscope className="mr-1.5 h-4 w-4 text-teal" />
              View Clinical Assessment
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              className="rounded-full bg-card"
              onClick={() => {
                setViewMode("hospitals");
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
            >
              <Building2 className="mr-1.5 h-4 w-4 text-teal" />
              Explore Hospitals ({ranked.length})
            </Button>
          )}

          <Link to="/compare">
            <Button variant="outline" size="sm" className="rounded-full bg-card">
              <Columns3 className="mr-1.5 h-4 w-4" /> Compare
            </Button>
          </Link>
          <Link to="/analyze">
            <Button variant="ghost" size="sm" className="rounded-full">
              <SlidersHorizontal className="mr-1.5 h-4 w-4" /> Refine
            </Button>
          </Link>
        </div>
      </div>

      <DisclaimerBar className="mt-6" />

      {/* =========================================================================
          PHASE 1: CLINICAL ASSESSMENT VIEW
         ========================================================================= */}
      {viewMode === "clinical" && (
        <div className="mt-8 space-y-8">
          {/* Emergency Warning Banner if applicable */}
          {isEmergency && (
            <div className="rounded-2xl border border-danger/40 bg-danger/10 p-6 text-danger">
              <div className="flex items-start gap-3">
                <ShieldAlert className="h-6 w-6 shrink-0 mt-1" />
                <div className="flex-1">
                  <h3 className="text-lg font-bold">Urgent Medical Warning Detected</h3>
                  <p className="mt-1 text-sm leading-relaxed opacity-90">
                    Your reported symptoms include emergency indicators that may require prompt medical evaluation.
                    {result.red_flags && result.red_flags.length > 0 && (
                      <span className="block mt-1 font-semibold">
                        Warning signals: {result.red_flags.join(" · ")}
                      </span>
                    )}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <Button
                      size="sm"
                      className="rounded-full bg-danger text-white hover:bg-danger/90 font-bold"
                      onClick={() => {
                        setViewMode("hospitals");
                        window.scrollTo({ top: 0, behavior: "smooth" });
                      }}
                    >
                      <Zap className="mr-1.5 h-4 w-4" />
                      🚨 Find Emergency Hospitals Now
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Clinical Assessment Summary */}
          <div className="surface p-6 sm:p-8">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-teal">
                  Clinical Triage Summary
                </span>
                <h2 className="mt-1 text-xl font-bold">Educational Symptom Assessment</h2>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary" className="rounded-full text-xs font-semibold px-3 py-1">
                  Specialty: {result.primary_specialty}
                </Badge>
                <Badge className={`rounded-full text-xs font-semibold px-3 py-1 ${urgencyBadgeClass(result.urgency_category)}`}>
                  {result.urgency_category} Urgency
                </Badge>
              </div>
            </div>

            <p className="mt-4 text-base leading-relaxed text-muted-foreground">
              {result.clinical_summary || result.urgency_summary}
            </p>

            {result.extracted_signals && result.extracted_signals.length > 0 && (
              <div className="mt-4 flex flex-wrap items-center gap-2 pt-4 border-t border-border">
                <span className="text-xs font-medium text-muted-foreground">Identified symptom signals:</span>
                {result.extracted_signals.map((sig) => (
                  <Badge key={sig} variant="outline" className="rounded-full text-xs">
                    {sig}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Possible Conditions Cards Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold">Possible Conditions to Discuss with a Clinician</h2>
                <p className="text-xs text-muted-foreground mt-1">
                  Potential explanations identified from reported symptoms. These are for educational discussion, not diagnoses.
                </p>
              </div>
            </div>

            {possibleConditions.length === 0 ? (
              <div className="surface p-8 text-center">
                <Info className="mx-auto h-8 w-8 text-teal mb-3" />
                <h3 className="text-base font-bold">Additional Information Recommended</h3>
                <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
                  Reported symptoms are broad or non-specific. Further clinical evaluation and physical examination by a medical provider is recommended.
                </p>
              </div>
            ) : (
              <div className="grid gap-5 md:grid-cols-2">
                {possibleConditions.map((cond, idx) => (
                  <div key={idx} className="surface p-6 flex flex-col justify-between lift">
                    <div>
                      <div className="flex items-start justify-between gap-3">
                        <h3 className="text-base font-bold leading-snug">{cond.name}</h3>
                        <span className={`inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-[11px] ${confidenceBadgeVariant(cond.confidence_label || cond.relevance)}`}>
                          {cond.confidence_label || cond.relevance || "Possible"}
                        </span>
                      </div>

                      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                        {cond.explanation}
                      </p>

                      {cond.supporting_symptoms && cond.supporting_symptoms.length > 0 && (
                        <div className="mt-4">
                          <span className="text-xs font-semibold text-muted-foreground block mb-1.5">
                            Supporting symptoms noted:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {cond.supporting_symptoms.map((s, sIdx) => (
                              <span key={sIdx} className="inline-flex items-center gap-1 rounded-full bg-teal/10 px-2.5 py-0.5 text-xs text-teal font-medium">
                                <Check className="h-3 w-3" /> {s}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {cond.missing_information && cond.missing_information.length > 0 && (
                        <div className="mt-3">
                          <span className="text-xs font-semibold text-muted-foreground block mb-1.5">
                            Details to clarify with doctor:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {cond.missing_information.map((m, mIdx) => (
                              <span key={mIdx} className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-0.5 text-xs text-muted-foreground">
                                <HelpCircle className="h-3 w-3" /> {m}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Specialty & Care Path Summary Panel */}
          <div className="surface p-6 bg-muted/40">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Recommended Specialty
                </span>
                <p className="mt-1 text-lg font-extrabold text-foreground">
                  {result.primary_specialty}
                </p>
                {result.secondary_specialties && result.secondary_specialties.length > 0 && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Secondary: {result.secondary_specialties.join(", ")}
                  </p>
                )}
              </div>
              <div>
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Care Urgency Assessment
                </span>
                <p className="mt-1 text-lg font-extrabold text-foreground flex items-center gap-2">
                  <span className={`h-2.5 w-2.5 rounded-full ${isEmergency ? "bg-danger animate-ping" : "bg-teal"}`} />
                  {result.urgency_category}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {result.urgency_summary}
                </p>
              </div>
            </div>
          </div>

          {/* =========================================================================
              CRITICAL ACTION BUTTON: "LOOK FOR HOSPITALS"
             ========================================================================= */}
          <div className="surface p-8 text-center bg-card border-2 border-teal/30 shadow-lg rounded-3xl">
            <h3 className="text-xl font-extrabold">Ready to explore relevant medical facilities?</h3>
            <p className="mt-2 text-sm text-muted-foreground max-w-lg mx-auto">
              Charak will match your required specialty ({result.primary_specialty}), coordinates, and urgency level against verified ABDM hospitals nearby.
            </p>

            <Button
              size="lg"
              className="mt-6 rounded-full px-8 py-6 text-base font-extrabold shadow-md transition-all lift bg-teal text-teal-foreground hover:bg-teal/90"
              onClick={() => {
                setViewMode("hospitals");
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
            >
              <Search className="mr-2 h-5 w-5" />
              🔍 LOOK FOR HOSPITALS
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      )}

      {/* =========================================================================
          PHASE 2: HOSPITAL DISCOVERY VIEW
         ========================================================================= */}
      {viewMode === "hospitals" && (
        <div className="mt-8 space-y-6">
          {/* Location Status & Active Search Context Banner */}
          <div className="surface p-5 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-3 text-sm">
                {input?.latitude !== null && input?.longitude !== null ? (
                  <span className="inline-flex items-center gap-1.5 font-bold text-teal">
                    <MapPin className="h-4 w-4 text-teal" /> 📍 Using your device location
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 font-semibold text-warning">
                    <AlertCircle className="h-4 w-4 text-warning" /> 📍 Location unavailable — Distances unavailable
                  </span>
                )}
                <span className="text-border">·</span>
                <span className="text-muted-foreground">Specialty: <strong>{result.primary_specialty}</strong></span>
                <span className="text-border">·</span>
                <span className="text-muted-foreground">Insurance: <strong>{input?.insurance || "Ayushman Bharat"}</strong></span>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="rounded-full text-xs"
                  onClick={() => setShowExplainability(!showExplainability)}
                >
                  {showExplainability ? (
                    <>Hide ranking details <ChevronUp className="ml-1 h-3.5 w-3.5" /></>
                  ) : (
                    <>Why am I seeing these results? <ChevronDown className="ml-1 h-3.5 w-3.5" /></>
                  )}
                </Button>
              </div>
            </div>

            {/* Location Unavailable Alert Banner if no coordinates */}
            {input?.latitude === null && (
              <div className="rounded-xl bg-warning/10 border border-warning/30 p-3 text-xs text-warning leading-relaxed flex items-center justify-between gap-3">
                <span>Location was not detected or permitted. Hospital cards display "Distance unavailable" and are ranked strictly by specialty & emergency match.</span>
                <Link to="/analyze">
                  <Button variant="outline" size="sm" className="h-7 text-xs rounded-full border-warning/40 text-warning hover:bg-warning/20">
                    Enable Location
                  </Button>
                </Link>
              </div>
            )}
          </div>

          {/* Explainability Accordion Panel */}
          {showExplainability && (
            <div className="surface p-6 bg-muted/30 border-l-4 border-l-teal space-y-3 text-xs leading-relaxed text-muted-foreground">
              <h4 className="font-bold text-foreground text-sm flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-teal" /> Recommendation Explainability Breakdown
              </h4>
              <p>
                Facilities are combined dynamically from ABDM Health Facility Registry (HFR) and OpenStreetMap local network:
              </p>
              <ul className="grid gap-2 sm:grid-cols-2 pt-2 text-foreground font-medium">
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-teal" /> Verified specialty match for <strong>{result.primary_specialty}</strong> (+20 pts)
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-teal" /> Haversine GPS distance calculation
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-teal" /> 24x7 Emergency Department operational readiness
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-teal" /> ABDM HFR Registry vs OpenStreetMap provenance labeling
                </li>
              </ul>
            </div>
          )}

          {/* Hospital Cards List */}
          <div className="space-y-5">
            {ranked.length === 0 ? (
              <div className="surface flex flex-col items-center justify-center py-16 text-center">
                <AlertCircle className="h-10 w-10 text-muted-foreground/40" />
                <h2 className="mt-4 text-base font-semibold">
                  No verified hospitals matched the current criteria
                </h2>
                <p className="mt-2 max-w-sm text-sm text-muted-foreground">
                  No facilities in the verified registry match your specialty and location radius. Try expanding your search distance.
                </p>
                <Link to="/analyze" className="mt-5">
                  <Button className="rounded-full" variant="outline">
                    <RefreshCw className="mr-1.5 h-4 w-4" />
                    Modify location or distance
                  </Button>
                </Link>
              </div>
            ) : (
              ranked.map((h: Hospital, i: number) => (
                <HospitalCard key={h.id} hospital={h as any} rank={i + 1} />
              ))
            )}
          </div>
        </div>
      )}

      <p className="mt-8 text-xs leading-relaxed text-muted-foreground">
        Bed availability and doctor schedules are displayed for facilities integrated with Charak telemetry.
        All other facilities display verified public data registered under ABDM Health Facility Registry.
      </p>
    </div>
  );
}
