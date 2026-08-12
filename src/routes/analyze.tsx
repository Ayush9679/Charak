import { createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  FileText,
  IndianRupee,
  MapPin,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Upload,
  X,
  AlertCircle,
  Loader2,
  Navigation,
  Check,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { DisclaimerBar } from "@/components/disclaimer-bar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { defaultInput, saveAnalysis, clearRecommendationResult } from "@/lib/analysis-store";
import { checkHealth } from "@/api/health";
import { useGeolocation } from "@/hooks/use-geolocation";

export const Route = createFileRoute("/analyze")({
  validateSearch: (search: Record<string, unknown>): { upload?: boolean } => {
    if (search["upload"] === true || search["upload"] === "true") {
      return { upload: true };
    }
    return {};
  },
  head: () => ({
    meta: [
      { title: "Analyze symptoms or a medical report — charak" },
      {
        name: "description",
        content:
          "Describe your symptoms or upload a medical report, set location, budget, insurance and travel distance to get suitable hospital recommendations.",
      },
      { property: "og:title", content: "Analyze symptoms or a medical report — charak" },
      {
        property: "og:description",
        content:
          "charak identifies the likely medical specialty and urgency category from what you provide, then ranks suitable hospitals nearby.",
      },
    ],
  }),
  component: AnalyzePage,
});

const EXAMPLE = "Chest pain, dizziness and breathlessness";

function AnalyzePage() {
  const { upload } = Route.useSearch();
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const geo = useGeolocation();
  const [state, setState] = useState({ ...defaultInput });
  const [dragging, setDragging] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [backendError, setBackendError] = useState<string | null>(null);

  const set = <K extends keyof typeof state>(key: K, value: (typeof state)[K]) =>
    setState((s) => ({ ...s, [key]: value }));

  const handleDetectLocation = () => {
    geo.requestLocation();
  };

  // Sync detected geolocation coordinates with state
  useEffect(() => {
    if (geo.status === "success" && geo.latitude !== null && geo.longitude !== null) {
      setState((prev) => ({
        ...prev,
        location: prev.location || "Current location detected",
        latitude: geo.latitude,
        longitude: geo.longitude,
      }));
    }
  }, [geo.status, geo.latitude, geo.longitude]);

  const submit = async () => {
    if (submitting) return;
    setBackendError(null);
    setSubmitting(true);

    // Quick health check before expensive AI call
    try {
      await checkHealth();
    } catch {
      setSubmitting(false);
      setBackendError(
        "Backend server is unreachable. Please start the CHANAKYA backend on port 8000 and try again."
      );
      return;
    }

    clearRecommendationResult();
    saveAnalysis({
      ...state,
      symptoms: state.symptoms.trim() || (state.reportName ? "Uploaded medical report" : EXAMPLE),
      latitude: state.latitude ?? geo.latitude,
      longitude: state.longitude ?? geo.longitude,
    });
    navigate({ to: "/analyzing" });
  };

  return (
    <div className="hero-bg">
      <div className="mx-auto max-w-4xl px-5 py-14 lg:px-8">
        <header className="text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3.5 py-1.5 text-xs font-semibold text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-teal" /> Step 1 of 3 · Intake
          </span>
          <h1 className="mt-5 text-3xl font-extrabold sm:text-4xl">
            Tell charak what you're experiencing
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground sm:text-base">
            Your description is used to identify a likely specialty and urgency category — never to
            diagnose.
          </p>
        </header>

        <div className="surface mt-10 p-5 sm:p-7">
          <Label htmlFor="symptoms" className="text-sm font-semibold">
            Symptoms
          </Label>
          <div className="relative mt-2.5">
            <Stethoscope className="absolute left-4 top-4 h-5 w-5 text-teal" />
            <Textarea
              id="symptoms"
              value={state.symptoms}
              onChange={(e) => set("symptoms", e.target.value)}
              placeholder="Describe your symptoms..."
              className="min-h-32 rounded-2xl border-border bg-background pl-12 text-base"
            />
          </div>
          <button
            type="button"
            onClick={() => set("symptoms", EXAMPLE)}
            className="mt-3 rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            Try example: {EXAMPLE}
          </button>

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="diagnosis" className="text-sm font-semibold">
                Existing diagnosis (optional)
              </Label>
              <Input
                id="diagnosis"
                value={state.diagnosis}
                onChange={(e) => set("diagnosis", e.target.value)}
                placeholder="e.g. Hypertension, Type 2 diabetes"
                className="mt-2.5 h-11 rounded-xl bg-background"
              />
            </div>
            <div>
              <Label htmlFor="location" className="text-sm font-semibold">
                Location & Discovery Radius
              </Label>

              <div className="relative mt-2">
                <MapPin className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="location"
                  value={state.location}
                  onChange={(e) => set("location", e.target.value)}
                  placeholder="e.g. Sector 62, Noida"
                  className="h-11 rounded-xl bg-background pl-10 text-xs"
                />
              </div>

              {/* Location Gate Card */}
              <div className="mt-4 surface p-4 border border-teal/30 rounded-2xl bg-card">
                <div className="flex items-start gap-3">
                  <Navigation className="h-4 w-4 text-teal shrink-0 mt-1" />
                  <div className="flex-1">
                    <h4 className="text-xs font-bold">📍 Find hospitals near you</h4>
                    <p className="mt-0.5 text-[11px] text-muted-foreground leading-relaxed">
                      CHANAKYA uses device GPS to calculate real hospital distances and discover nearby facilities.
                    </p>

                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <Button
                        type="button"
                        size="sm"
                        onClick={handleDetectLocation}
                        disabled={geo.status === "requesting"}
                        className="h-8 rounded-full bg-teal text-white hover:bg-teal/90 text-xs font-semibold px-3"
                      >
                        {geo.status === "requesting" ? (
                          <><Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> Detecting...</>
                        ) : (
                          <><Navigation className="mr-1 h-3.5 w-3.5" /> Detect My Location</>
                        )}
                      </Button>

                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setState((prev) => ({
                            ...prev,
                            location: "Location not specified",
                            latitude: null,
                            longitude: null,
                          }));
                        }}
                        className="h-8 rounded-full text-xs px-3"
                      >
                        Continue without location
                      </Button>
                    </div>

                    {/* Geolocation Status Feedback */}
                    {geo.status === "success" && (state.latitude !== null || geo.latitude !== null) && (
                      <div className="mt-2.5 flex items-center gap-1.5 text-xs text-teal font-semibold">
                        <Check className="h-3.5 w-3.5" />
                        <span>📍 Device GPS active ({(state.latitude ?? geo.latitude)?.toFixed(4)}, {(state.longitude ?? geo.longitude)?.toFixed(4)})</span>
                      </div>
                    )}

                    {(geo.status === "denied" || geo.status === "error" || geo.status === "unavailable") && (
                      <div className="mt-2.5 flex flex-wrap items-center justify-between gap-2 text-[11px] text-warning rounded-xl bg-warning/10 p-2">
                        <span>Location permission denied. Distances will show as unavailable.</span>
                        <button
                          type="button"
                          onClick={handleDetectLocation}
                          className="font-bold underline hover:text-warning/80"
                        >
                          Try Again
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-7">
            <Label className="text-sm font-semibold">Medical report (optional)</Label>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                const f = e.dataTransfer.files?.[0];
                if (f) set("reportName", f.name);
              }}
              className={`mt-2.5 rounded-2xl border-2 border-dashed p-7 text-center transition-colors ${
                dragging || upload ? "border-teal bg-muted" : "border-border bg-background"
              }`}
            >
              {state.reportName ? (
                <div className="flex items-center justify-center gap-3">
                  <FileText className="h-5 w-5 text-teal" />
                  <span className="truncate text-sm font-medium">{state.reportName}</span>
                  <button
                    type="button"
                    aria-label="Remove file"
                    onClick={() => set("reportName", null)}
                    className="grid h-7 w-7 place-items-center rounded-full border border-border"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ) : (
                <>
                  <Upload className="mx-auto h-6 w-6 text-teal" />
                  <p className="mt-3 text-sm font-medium">Drag & drop your report here</p>
                  <p className="mt-1 text-xs text-muted-foreground">PDF or image, up to 10 MB</p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="mt-4 rounded-full"
                    onClick={() => fileRef.current?.click()}
                  >
                    Browse files
                  </Button>
                </>
              )}
              <input
                ref={fileRef}
                type="file"
                accept="application/pdf,image/*"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) set("reportName", f.name);
                }}
              />
            </div>
          </div>

          <div className="mt-7 grid gap-4 sm:grid-cols-2">
            <div>
              <Label className="flex items-center gap-1.5 text-sm font-semibold">
                <IndianRupee className="h-3.5 w-3.5 text-teal" /> Budget preference
              </Label>
              <Select value={state.budget} onValueChange={(v) => set("budget", v)}>
                <SelectTrigger className="mt-2.5 h-11 rounded-xl bg-background">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["No preference", "Public / subsidised", "Up to ₹1,000", "₹1,000 – ₹5,000", "Premium care"].map(
                    (b) => (
                      <SelectItem key={b} value={b}>
                        {b}
                      </SelectItem>
                    ),
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="flex items-center gap-1.5 text-sm font-semibold">
                <ShieldCheck className="h-3.5 w-3.5 text-teal" /> Insurance
              </Label>
              <Select value={state.insurance} onValueChange={(v) => set("insurance", v)}>
                <SelectTrigger className="mt-2.5 h-11 rounded-xl bg-background">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {["Ayushman Bharat", "CGHS", "Star Health", "Niva Bupa", "HDFC ERGO", "None"].map(
                    (i) => (
                      <SelectItem key={i} value={i}>
                        {i}
                      </SelectItem>
                    ),
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="mt-7">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-semibold">Preferred travel distance</Label>
              <span className="text-sm font-semibold text-teal">{state.distance} km</span>
            </div>
            <Slider
              value={[state.distance]}
              onValueChange={([v]) => set("distance", v ?? 15)}
              min={2}
              max={50}
              step={1}
              className="mt-4"
            />
          </div>

          {backendError && (
            <div className="mt-4 flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/5 px-4 py-3 text-xs text-danger">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{backendError}</span>
            </div>
          )}

          <Button
            size="lg"
            className="mt-8 w-full rounded-full"
            onClick={submit}
            disabled={submitting}
          >
            {submitting ? (
              <><Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> Checking backend...</>
            ) : (
              <><Sparkles className="mr-1 h-4 w-4" /> Analyze</>
            )}
          </Button>
        </div>

        <DisclaimerBar className="mt-6" />
      </div>
    </div>
  );
}