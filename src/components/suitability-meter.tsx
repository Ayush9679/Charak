export function SuitabilityMeter({ value, size = 92 }: { value: number; size?: number }) {
  const r = size / 2 - 7;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth="7"
          className="stroke-muted"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth="7"
          strokeLinecap="round"
          className="stroke-teal transition-[stroke-dashoffset] duration-700 ease-out"
          strokeDasharray={c}
          strokeDashoffset={c - (c * value) / 100}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5">
        <span className="font-display text-lg font-extrabold leading-none">{value}</span>
        <span className="text-[9px] font-medium uppercase tracking-wide text-muted-foreground">
          suitability
        </span>
      </div>
    </div>
  );
}