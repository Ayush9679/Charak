import { Link } from "@tanstack/react-router";
import { ShieldCheck } from "lucide-react";

import { Brand } from "./brand";

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-border bg-card">
      <div className="mx-auto max-w-7xl px-5 py-14 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div className="max-w-sm">
            <Brand />
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              AI-powered healthcare navigation for finding the most suitable hospital — built on
              verified public registries, published hospital information and opt-in hospital
              integrations.
            </p>
          </div>
          <FooterCol
            title="Product"
            items={[
              { to: "/analyze", label: "Analyze symptoms" },
              { to: "/hospitals", label: "Hospitals" },
              { to: "/compare", label: "Compare" },
              { to: "/how-it-works", label: "How it works" },
            ]}
          />
          <FooterCol
            title="Company"
            items={[
              { to: "/about", label: "About" },
              { to: "/contact", label: "Contact" },
              { to: "/login", label: "Login" },
              { to: "/signup", label: "Sign up" },
            ]}
          />
          <div>
            <h4 className="text-sm font-semibold">Data posture</h4>
            <ul className="mt-4 space-y-2.5 text-sm text-muted-foreground">
              <li className="flex items-center gap-2">
                <span className="h-2 w-2 shrink-0 rounded-full bg-success" /> Verified public data
              </li>
              <li className="flex items-center gap-2">
                <span className="h-2 w-2 shrink-0 rounded-full bg-warning" /> Aggregated published
                data
              </li>
              <li className="flex items-center gap-2">
                <span className="h-2 w-2 shrink-0 rounded-full bg-teal" /> Hospital integrations
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 rounded-2xl border border-border bg-background p-5">
          <h5 className="flex items-center gap-2 text-sm font-semibold">
            <ShieldCheck className="h-4 w-4 text-teal" /> Medical disclaimer
          </h5>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            Charak assists healthcare navigation by interpreting user-provided information to
            identify appropriate medical specialties and recommend healthcare facilities. It does not
            provide medical diagnoses or replace licensed healthcare professionals. Real-time bed,
            ICU and appointment data is available only through participating hospital integrations.
          </p>
        </div>

        <p className="mt-8 text-xs text-muted-foreground">
          © {new Date().getFullYear()} Chanakya · Charak. Smart India Hackathon 2026 prototype.
        </p>
      </div>
    </footer>
  );
}

function FooterCol({
  title,
  items,
}: {
  title: string;
  items: { to: string; label: string }[];
}) {
  return (
    <div>
      <h4 className="text-sm font-semibold">{title}</h4>
      <ul className="mt-4 space-y-2.5 text-sm">
        {items.map((i) => (
          <li key={i.to}>
            <Link to={i.to} className="text-muted-foreground transition-colors hover:text-foreground">
              {i.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
