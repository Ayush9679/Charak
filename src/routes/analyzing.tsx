import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AlertCircle, Check, Loader2, RefreshCw } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { DisclaimerBar } from "@/components/disclaimer-bar";
import { Button } from "@/components/ui/button";
import { loadAnalysis, saveRecommendationResult } from "@/lib/analysis-store";
import { pipelineStages } from "@/lib/charak-data";
import { createRecommendation } from "@/api/recommendations";
import { APIError, getApiErrorMessage } from "@/api/client";

export const Route = createFileRoute("/analyzing")({
  head: () => ({
    meta: [
      { title: "AI analysis in progress — charak" },
      {
        name: "description",
        content:
          "charak's medical NLP pipeline identifies likely specialty and urgency category before ranking suitable hospitals.",
      },
      { property: "og:title", content: "AI analysis in progress — charak" },
      {
        property: "og:description",
        content: "Symptom intake, medical NLP, specialty detection, urgency assessment and AI ranking.",
      },
    ],
  }),
  component: AnalyzingPage,
});

function AnalyzingPage() {
  const navigate = useNavigate();
  const input = typeof window === "undefined" ? null : loadAnalysis();

  const [completedStep, setCompletedStep] = useState(0);
  const [status, setStatus] = useState<"loading" | "success" | "error" | "timeout">("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  const abortRef = useRef<AbortController | null>(null);

  const runAnalysis = () => {
    if (submitting) return;
    setSubmitting(true);
    setStatus("loading");
    setCompletedStep(0);
    setErrorMessage("");

    const controller = new AbortController();
    abortRef.current = controller;

    const payload = {
      symptoms: input?.symptoms?.trim() || "General symptoms — no specific description provided",
      location: input?.location || "Current location",
      latitude: input?.latitude ?? null,
      longitude: input?.longitude ?? null,
      distance: input?.distance || 15,
      insurance: input?.insurance || "Ayushman Bharat",
      budget_level: input?.budget || "No preference",
    };

    createRecommendation(payload, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        saveRecommendationResult(result);
        setCompletedStep(pipelineStages.length - 1);
        setStatus("success");
        setSubmitting(false);
        navigate({ to: "/results" });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setSubmitting(false);
        if (err instanceof APIError) {
          if (err.code === "REQUEST_TIMEOUT") {
            setStatus("timeout");
            setErrorMessage("Analysis is taking longer than expected. Please retry.");
          } else if (err.code === "NETWORK_ERROR") {
            setStatus("error");
            setErrorMessage(getApiErrorMessage(err));
          } else {
            setStatus("error");
            setErrorMessage(getApiErrorMessage(err));
          }
        } else {
          setStatus("error");
          setErrorMessage(getApiErrorMessage(err));
        }
      });
  };

  // Start analysis on mount
  useEffect(() => {
    runAnalysis();
    return () => {
      abortRef.current?.abort();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const entities = (input?.symptoms ?? "")
    .split(/[,.;\n]/)
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 4);

  const isError = status === "error" || status === "timeout";

  return (
    <div className="hero-bg">
      <div className="mx-auto max-w-5xl px-5 py-16 lg:px-8">
        <header className="text-center">
          <h1 className="text-3xl font-extrabold sm:text-4xl">Analyzing your information</h1>
          <p className="mx-auto mt-4 max-w-lg text-sm text-muted-foreground sm:text-base">
            AI supports healthcare navigation only. No diagnosis is being made.
          </p>
        </header>

        {/* Error / Timeout State */}
        {isError && (
          <div className="mt-8 mx-auto max-w-lg rounded-2xl border border-danger/30 bg-danger/5 p-6 text-center">
            <AlertCircle className="mx-auto h-10 w-10 text-danger" />
            <h2 className="mt-3 text-base font-bold text-foreground">
              {status === "timeout" ? "Analysis timed out" : "Analysis failed"}
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">{errorMessage}</p>
            <div className="mt-5 flex flex-wrap justify-center gap-3">
              <Button
                onClick={() => {
                  setSubmitting(false);
                  runAnalysis();
                }}
                className="rounded-full"
              >
                <RefreshCw className="mr-1.5 h-4 w-4" />
                Retry analysis
              </Button>
              <Button
                variant="outline"
                className="rounded-full"
                onClick={() => navigate({ to: "/analyze" })}
              >
                Change inputs
              </Button>
            </div>
          </div>
        )}

        {/* Analysis pipeline steps (shown during loading or after success) */}
        {!isError && (
          <div className="mt-12 grid gap-5 lg:grid-cols-[1.1fr_1fr]">
            <ol className="surface p-5 sm:p-6">
              {pipelineStages.map((s, i) => {
                const done = i <= completedStep;
                const active = i === completedStep + 1 && status === "loading";
                return (
                  <li
                    key={s.key}
                    className={`flex items-start gap-4 py-3 transition-opacity ${
                      i > completedStep + 1 ? "opacity-40" : "opacity-100"
                    }`}
                  >
                    <span
                      className={`mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full border transition-colors ${
                        done
                          ? "border-transparent bg-success text-primary-foreground"
                          : active
                            ? "border-teal text-teal"
                            : "border-border text-muted-foreground"
                      }`}
                    >
                      {done ? (
                        <Check className="h-4 w-4" />
                      ) : active ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <span className="text-xs font-semibold">{i + 1}</span>
                      )}
                    </span>
                    <span className="min-w-0">
                      <span className="block text-sm font-semibold">{s.label}</span>
                      <span className="block text-xs text-muted-foreground">{s.detail}</span>
                    </span>
                  </li>
                );
              })}
            </ol>

            <div className="space-y-5">
              <div className="surface p-5 sm:p-6">
                <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
                  Extracted signals
                </h2>
                <div className="mt-4 flex flex-wrap gap-2">
                  {entities.length === 0 ? (
                    <span className="text-xs text-muted-foreground">Awaiting input...</span>
                  ) : (
                    entities.map((e) => (
                      <span
                        key={e}
                        className="rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium"
                      >
                        {e}
                      </span>
                    ))
                  )}
                </div>
              </div>

              <div className="surface p-5 sm:p-6">
                <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
                  AI triage pipeline
                </h2>
                <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                  {status === "loading"
                    ? "Your symptom description is being analyzed by the AI triage engine to identify the most likely medical specialty and urgency classification. No diagnosis is provided."
                    : status === "success"
                      ? "Analysis complete. Redirecting to your results..."
                      : "AI analysis did not complete."}
                </p>
                {status === "loading" && (
                  <div className="mt-4 flex items-center gap-2 text-xs text-teal">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Communicating with CHANAKYA backend...</span>
                  </div>
                )}
              </div>

              <div className="surface p-5 sm:p-6">
                <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
                  Disclaimer
                </h2>
                <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                  CHANAKYA identifies likely medical specialties from user-provided descriptions. It
                  does not diagnose diseases or replace licensed healthcare professionals. If you
                  have severe or life-threatening symptoms, seek immediate emergency medical care.
                </p>
              </div>
            </div>
          </div>
        )}

        <DisclaimerBar className="mt-8" />
      </div>
    </div>
  );
}
