import { Link } from "@tanstack/react-router";
import logo from "../../logo.jpeg";

export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/" className="flex min-w-0 items-center gap-2.5" aria-label="Charak home">
      <img
        src={logo}
        alt="Charak"
        className="h-10 w-10 shrink-0 rounded-xl object-cover object-center shadow-soft"
      />
      {!compact && (
        <span className="flex min-w-0 flex-col leading-none">
          <span className="truncate font-display text-base font-extrabold tracking-tight">
            Charak
          </span>
          <span className="truncate text-[11px] font-medium text-muted-foreground">
            By Chanakya · healthcare navigation
          </span>
        </span>
      )}
    </Link>
  );
}
