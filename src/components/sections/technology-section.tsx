import {
  BrainCircuit,
  Database,
  Layers,
  LayoutDashboard,
  ListOrdered,
  Server,
  User,
} from "lucide-react";

const nodes = [
  { icon: User, label: "User", note: "Symptoms, reports, preferences" },
  { icon: LayoutDashboard, label: "Frontend", note: "Guided navigation experience" },
  { icon: Server, label: "FastAPI backend", note: "Orchestration & validation" },
  { icon: BrainCircuit, label: "AI engine", note: "Medical NLP · specialty · urgency" },
  { icon: Database, label: "Healthcare data layer", note: "Registries · published data · APIs" },
  { icon: ListOrdered, label: "Recommendation engine", note: "Multi-factor ranking" },
  { icon: Layers, label: "Hospital results", note: "Explainable shortlist" },
];

export function TechnologySection() {
  return (
    <section className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
      <header className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-widest text-teal">Technology</p>
        <h2 className="mt-3 text-3xl font-extrabold sm:text-4xl">
          A calm architecture behind every recommendation
        </h2>
      </header>

      <div className="mt-12 grid gap-3 lg:grid-cols-7">
        {nodes.map((n, i) => (
          <div key={n.label} className="relative">
            <div className="surface h-full p-5">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-muted text-teal">
                <n.icon className="h-5 w-5" />
              </span>
              <h3 className="mt-4 text-sm font-bold leading-snug">{n.label}</h3>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{n.note}</p>
            </div>
            {i < nodes.length - 1 && (
              <span className="pointer-events-none absolute -right-2.5 top-1/2 hidden h-px w-5 -translate-y-1/2 bg-border lg:block" />
            )}
          </div>
        ))}
      </div>
    </section>
  );
}