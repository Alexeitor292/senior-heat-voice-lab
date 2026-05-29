import { riskColor } from "@/lib/risk";
import type { RiskLevel } from "@/lib/types";

interface Props {
  risk: RiskLevel;
  size?: "sm" | "md";
}

export function RiskBadge({ risk, size = "md" }: Props) {
  const color = riskColor(risk);
  return (
    <span
      className="inline-flex items-center rounded-full font-medium"
      style={{
        background: color + "18",
        color,
        border: `1px solid ${color}40`,
        fontSize: size === "sm" ? 11 : 12,
        padding: size === "sm" ? "1px 7px" : "2px 9px",
      }}
    >
      {risk}
    </span>
  );
}
