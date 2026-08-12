import { Info } from "lucide-react";

import { DISCLAIMER } from "@/lib/charak-data";
import { cn } from "@/lib/utils";

export function DisclaimerBar({ className }: { className?: string }) {
  return (
    <p
      className={cn(
        "flex items-start gap-2.5 rounded-2xl border border-border bg-card px-4 py-3 text-xs leading-relaxed text-muted-foreground",
        className,
      )}
    >
      <Info className="mt-0.5 h-4 w-4 shrink-0 text-teal" />
      <span>{DISCLAIMER}</span>
    </p>
  );
}