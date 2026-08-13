import { Building2, FileCheck2, Plug } from "lucide-react";

const layers = [
  {
    icon: FileCheck2,
    level: "Level 1",
    title: "Verified public data",
    badge: { label: "Available now", dot: "bg-success" },
    items: [
      "ABDM Health Facility Registry",
      "Healthcare Professionals Registry",
      "Facility information",
      "Maps, distance and travel time",
    ],
  },
  {
    icon: Building2,
    level: "Level 2",
    title: "Verified aggregated data",
    badge: { label: "Available through publication", dot: "bg-warning" },
    items: [
      "Hospital websites",
      "Published treatment information",
      "Doctor profiles",
      "Appointment information",
    ],
  },
  {
    icon: Plug,
    level: "Level 3",
    title: "Hospital integrations",
    badge: { label: "Available through integration", dot: "bg-teal" },
    items: [
      "Hospital APIs and HMS",
      "Bed availability",
      "ICU availability",
      "Doctor schedules and appointment slots",
    ],
  },
];

export function DataSourcesSection() {
  return (
    <section className="border-y border-border bg-card py-20">
      <div className="mx-auto max-w-7xl px-5 lg:px-8">
        <header className="max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-widest text-teal">
            Healthcare data sources
          </p>
          <h2 className="mt-3 text-3xl font-extrabold sm:text-4xl">
            Three honest layers of healthcare data
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            Charak is explicit about where each fact comes from. Live bed, ICU and appointment data
            exists only where a hospital has chosen to integrate — we never imply universal access to
            live hospital systems.
          </p>
        </header>

        <div className="mt-12 grid gap-5 lg:grid-cols-3">
          {layers.map((l) => (
            <div key={l.level} className="surface lift p-6">
              <div className="flex items-center justify-between gap-3">
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-muted text-foreground">
                  <l.icon className="h-5 w-5" />
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                  <span className={`h-1.5 w-1.5 rounded-full ${l.badge.dot}`} />
                  {l.badge.label}
                </span>
              </div>
              <p className="mt-5 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                {l.level}
              </p>
              <h3 className="mt-1.5 text-lg font-bold">{l.title}</h3>
              <ul className="mt-4 space-y-2.5">
                {l.items.map((i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    {i}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-8 flex flex-wrap gap-3 text-xs text-muted-foreground">
          <Legend dot="bg-success" label="Available now" />
          <Legend dot="bg-warning" label="Available through integration" />
          <Legend dot="bg-muted-foreground" label="Future expansion" />
        </div>
      </div>
    </section>
  );
}

function Legend({ dot, label }: { dot: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1.5">
      <span className={`h-2 w-2 rounded-full ${dot}`} /> {label}
    </span>
  );
}
