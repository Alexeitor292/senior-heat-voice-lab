import { riskColor } from "@/lib/risk";
import type { RiskLevel } from "@/lib/types";

interface Props {
  risk: RiskLevel;
  size?: "sm" | "md";
}

export function RiskBadge({ risk, size = "md" }: Props) {
  const color = riskColor(risk);
  const isSm = size === "sm";
  return (
    <span
      className="inline-flex items-center rounded-full font-semibold transition-interactive"
      style={{
        background: color + "15",
        color,
        border: `1px solid ${color}35`,
        fontSize: isSm ? 10.5 : 11.5,
        padding: isSm ? "1px 6px" : "2px 8px",
        letterSpacing: "0.01em",
        lineHeight: "1.5",
      }}
    >
      {risk}
    </span>
  );
}
