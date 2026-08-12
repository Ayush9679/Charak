import { Brain, Building2, Database, ListOrdered, MessageSquareText } from "lucide-react";

const stages = [
  {
    icon: MessageSquareText,
    title: "User Input",
    body: "Symptoms, existing diagnosis or an uploaded medical report, plus location, budget and insurance preferences.",
  },
  {
    icon: Brain,
    title: "AI Analysis",
    body: "Medical NLP extracts clinical entities, then maps them to a likely specialty and an urgency category.",
  },
  {
    icon: Database,
    title: "Healthcare Data",
    body: "Verified registries, published hospital information and — where they exist — hospital integrations.",
  },
  {
    icon: ListOrdered,
    title: "Ranking Engine",
    body: "Specialty fit, capability, travel time, cost signals, insurance and emergency readiness are weighed together.",
  },
  {
    icon: Building2,
    title: "Hospital Recommendation",
    body: "A transparent shortlist with a suitability score and the reasons behind every recommendation.",
  },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
      <header className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-widest text-teal">How AI works</p>
        <h2 className="mt-3 text-3xl font-extrabold sm:text-4xl">
          Five stages between a symptom and the right hospital
        </h2>
        <p className="mt-4 text-base leading-relaxed text-muted-foreground">
          charak never diagnoses. It interprets what you provide, identifies the specialty and
          urgency most likely required, and navigates you to facilities capable of handling it.
        </p>
      </header>

      <ol className="mt-12 grid gap-4 md:grid-cols-3 xl:grid-cols-5">
        {stages.map((s, i) => (
          <li
            key={s.title}
            className="surface lift group p-5"
            style={{ animationDelay: `${i * 70}ms` }}
          >
            <div className="flex items-center justify-between">
              <span
                className="grid h-11 w-11 place-items-center rounded-2xl text-primary-foreground transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:rotate-3"
                style={{ backgroundImage: "var(--gradient-brand)" }}
              >
                <s.icon className="h-5 w-5" />
              </span>
              <span className="font-display text-sm font-bold text-muted-foreground">
                0{i + 1}
              </span>
            </div>
            <h3 className="mt-4 text-base font-bold">{s.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}