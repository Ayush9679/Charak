import { createFileRoute } from "@tanstack/react-router";
import { Compass, HeartPulse, ScanSearch, ShieldCheck } from "lucide-react";

import { DisclaimerBar } from "@/components/disclaimer-bar";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About Chanakya and Charak" },
      {
        name: "description",
        content:
          "Charak is built by Chanakya to fix healthcare navigation: matching patients to suitable hospitals using verified data and explainable AI.",
      },
      { property: "og:title", content: "About Chanakya and Charak" },
      {
        property: "og:description",
        content:
          "Our principles: navigation over diagnosis, honest data provenance and explainable recommendations.",
      },
    ],
  }),
  component: AboutPage,
});

const principles = [
  {
    icon: Compass,
    title: "Suitability over proximity",
    body: "The nearest hospital is often the wrong hospital. Charak optimises for the specialty and capability a case actually needs.",
  },
  {
    icon: ShieldCheck,
    title: "Honest about data",
    body: "Each fact is labelled by source layer. We never present estimates as verified data or imply universal live hospital access.",
  },
  {
    icon: ScanSearch,
    title: "Explainable by default",
    body: "Every score is accompanied by the reasons behind it, so patients and clinicians can sanity-check the recommendation.",
  },
  {
    icon: HeartPulse,
    title: "Clinicians stay in charge",
    body: "Charak identifies specialty and urgency signals. Diagnosis and treatment remain with licensed healthcare professionals.",
  },
];

function AboutPage() {
  return (
    <>
      <section className="hero-bg">
        <div className="mx-auto max-w-3xl px-5 py-16 lg:px-8">
          <p className="text-sm font-semibold uppercase tracking-widest text-teal">
            Chanakya
          </p>
          <h1 className="mt-3 text-4xl font-extrabold sm:text-5xl">
            Healthcare navigation deserves better than a map pin
          </h1>
          <p className="mt-5 text-base leading-relaxed text-muted-foreground">
            Patients lose critical hours reaching facilities that cannot treat their condition.
            Charak closes that gap by translating symptoms, diagnoses and reports into the specialty
            and urgency a case needs, then ranking hospitals that can genuinely handle it.
          </p>
          <DisclaimerBar className="mt-8" />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
        <div className="grid gap-5 sm:grid-cols-2">
          {principles.map((p) => (
            <div key={p.title} className="surface lift p-6">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-muted text-teal">
                <p.icon className="h-5 w-5" />
              </span>
              <h2 className="mt-4 text-lg font-bold">{p.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{p.body}</p>
            </div>
          ))}
        </div>

        <div className="surface mt-6 grid gap-6 p-6 sm:grid-cols-3">
          <Stat value="Smart India Hackathon 2026" label="Built for" />
          <Stat value="ABDM-aligned" label="Data foundation" />
          <Stat value="Opt-in only" label="Hospital integrations" />
        </div>
      </section>
    </>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        {label}
      </p>
      <p className="mt-2 font-display text-lg font-extrabold">{value}</p>
    </div>
  );
}
