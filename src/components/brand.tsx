import { Link } from "@tanstack/react-router";

export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/" className="flex min-w-0 items-center gap-2.5">
      <span
        className="grid h-9 w-9 shrink-0 place-items-center rounded-xl text-primary-foreground"
        style={{ backgroundImage: "var(--gradient-brand)" }}
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M3 12h3l2 4 3-9 2.5 7 1.5-3h6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      {!compact && (
        <span className="flex min-w-0 flex-col leading-none">
          <span className="truncate font-display text-base font-extrabold tracking-tight">
            CHANAKYA
          </span>
          <span className="truncate text-[11px] font-medium text-muted-foreground">
            charak · healthcare navigation
          </span>
        </span>
      )}
    </Link>
  );
}