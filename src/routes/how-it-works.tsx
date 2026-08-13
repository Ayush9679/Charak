import { Link, createFileRoute } from "@tanstack/react-router";

import { DisclaimerBar } from "@/components/disclaimer-bar";
import { DataSourcesSection } from "@/components/sections/data-sources-section";
import { ExplainabilitySection } from "@/components/sections/explainability-section";
import { HowItWorksSection } from "@/components/sections/how-it-works-section";
import { TechnologySection } from "@/components/sections/technology-section";
import { Button } from "@/components/ui/button";
import { pipelineStages } from "@/lib/charak-data";

export const Route = createFileRoute("/how-it-works")({
  head: () => ({
    meta: [
      { title: "How Charak's AI navigation works" },
      {
        name: "description",
        content:
          "From symptom intake and medical NLP to specialty detection, urgency assessment, hospital discovery and explainable AI ranking.",
      },
      { property: "og:title", content: "How Charak's AI navigation works" },
      {
        property: "og:description",
        content:
          "A five-stage pipeline that identifies specialty and urgency, then ranks hospitals on ten healthcare factors.",
      },
    ],
  }),
  component: HowItWorksPage,
});

function HowItWorksPage() {
  return (
    <>
      <section className="hero-bg">
        <div className="mx-auto max-w-3xl px-5 py-16 text-center lg:px-8">
          <h1 className="text-4xl font-extrabold sm:text-5xl">
            Navigation, not <span className="text-gradient">diagnosis</span>
          </h1>
          <p className="mt-5 text-base leading-relaxed text-muted-foreground">
            Charak interprets the information you provide to identify the medical specialty and
            urgency category most likely required, then finds facilities capable of handling it.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-2">
            {pipelineStages.map((s) => (
              <span
                key={s.key}
                className="rounded-full border border-border bg-card px-3.5 py-1.5 text-xs font-medium text-muted-foreground"
              >
                {s.label}
              </span>
            ))}
          </div>
          <DisclaimerBar className="mx-auto mt-8 max-w-xl text-left" />
          <Link to="/analyze" className="mt-8 inline-block">
            <Button size="lg" className="rounded-full">
              Analyze Symptoms
            </Button>
          </Link>
        </div>
      </section>

      <HowItWorksSection />
      <DataSourcesSection />
      <ExplainabilitySection />
      <TechnologySection />
    </>
  );
}
