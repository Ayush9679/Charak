import { Link, createFileRoute } from "@tanstack/react-router";
import { ArrowRight, FileUp, ShieldCheck, Sparkles, Stethoscope } from "lucide-react";

import heroFlow from "@/assets/hero-flow.png";
import { DisclaimerBar } from "@/components/disclaimer-bar";
import { DataSourcesSection } from "@/components/sections/data-sources-section";
import { ExplainabilitySection } from "@/components/sections/explainability-section";
import { HowItWorksSection } from "@/components/sections/how-it-works-section";
import { TechnologySection } from "@/components/sections/technology-section";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "charak — Finding the right hospital, not just the nearest" },
      {
        name: "description",
        content:
          "AI-powered healthcare navigation that recommends suitable hospitals from symptoms, diagnosis and medical reports — with specialty, distance, cost and insurance context.",
      },
      {
        property: "og:title",
        content: "charak — Finding the right hospital, not just the nearest",
      },
      {
        property: "og:description",
        content:
          "Describe symptoms or upload a report. charak identifies the likely specialty and urgency, then ranks nearby hospitals by suitability.",
      },
    ],
  }),
  component: Index,
});

const stats = [
  { value: "10", label: "Ranking factors per hospital" },
  { value: "3", label: "Layers of healthcare data" },
  { value: "0", label: "Diagnoses made by AI" },
];

function Index() {
  return (
    <>
      <section className="hero-bg relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 grid-dots opacity-[0.18]" />
        <div className="relative mx-auto grid max-w-7xl gap-14 px-5 py-16 lg:grid-cols-[1.05fr_1fr] lg:items-center lg:px-8 lg:py-24">
          <div className="animate-rise">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3.5 py-1.5 text-xs font-semibold text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5 text-teal" />
              AI-assisted healthcare navigation · not diagnosis
            </span>

            <h1 className="mt-6 text-4xl font-extrabold leading-[1.08] sm:text-5xl xl:text-6xl">
              Finding the <span className="text-gradient">RIGHT</span> Hospital, Not Just the
              Nearest One.
            </h1>

            <p className="mt-6 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
              AI-powered healthcare navigation that helps patients discover the most suitable
              hospitals based on their symptoms, diagnosis, specialty requirements, distance,
              hospital capabilities and verified healthcare information.
            </p>

            <div className="mt-9 flex flex-wrap gap-3">
              <Link to="/analyze">
                <Button size="lg" className="rounded-full">
                  <Stethoscope className="mr-1 h-4 w-4" /> Analyze Symptoms
                </Button>
              </Link>
              <Link to="/analyze" search={{ upload: true }}>
                <Button size="lg" variant="outline" className="rounded-full bg-card">
                  <FileUp className="mr-1 h-4 w-4" /> Upload Medical Report
                </Button>
              </Link>
            </div>

            <dl className="mt-12 grid max-w-lg grid-cols-3 gap-4">
              {stats.map((s) => (
                <div key={s.label} className="surface p-4">
                  <dt className="font-display text-2xl font-extrabold">{s.value}</dt>
                  <dd className="mt-1 text-xs leading-snug text-muted-foreground">{s.label}</dd>
                </div>
              ))}
            </dl>

            <DisclaimerBar className="mt-8 max-w-xl" />
          </div>

          <div className="relative animate-rise [animation-delay:120ms]">
            <div
              className="absolute inset-6 rounded-[3rem] opacity-30 blur-3xl"
              style={{ backgroundImage: "var(--gradient-accent)" }}
            />
            <img
              src={heroFlow}
              alt="Illustration of the charak flow: patient to AI analysis to hospital network to recommended hospitals"
              width={1200}
              height={1104}
              className="relative w-full"
            />
          </div>
        </div>
      </section>

      <HowItWorksSection />
      <DataSourcesSection />
      <ExplainabilitySection />
      <TechnologySection />

      <section className="mx-auto max-w-7xl px-5 pb-4 lg:px-8">
        <div
          className="relative overflow-hidden rounded-3xl px-6 py-14 text-center sm:px-12"
          style={{ backgroundImage: "var(--gradient-brand)" }}
        >
          <div className="pointer-events-none absolute inset-0 grid-dots opacity-10" />
          <div className="relative mx-auto max-w-2xl text-primary-foreground">
            <ShieldCheck className="mx-auto h-8 w-8" />
            <h2 className="mt-5 text-3xl font-extrabold sm:text-4xl">
              Start with what you feel. We handle the navigation.
            </h2>
            <p className="mt-4 text-sm leading-relaxed opacity-80 sm:text-base">
              Describe your symptoms or upload a report. charak identifies the likely specialty and
              urgency, then explains exactly why each hospital is recommended.
            </p>
            <Link to="/analyze" className="mt-8 inline-block">
              <Button size="lg" variant="secondary" className="rounded-full">
                Analyze Symptoms <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
