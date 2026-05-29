import { statusColor } from "@/lib/risk";
import type { SeniorStatus } from "@/lib/types";

interface Props {
  status: SeniorStatus;
  size?: number;
}

export function StatusDot({ status, size = 8 }: Props) {
  const color = statusColor(status);
  const isUrgent = status === "Urgent";

  return (
    <span className="relative inline-flex shrink-0" style={{ width: size, height: size }}>
      {isUrgent && (
        <span
          className="absolute inset-0 rounded-full animate-pulse-ring"
          style={{ background: color, borderRadius: "50%" }}
        />
      )}
      <span
        className="relative rounded-full"
        style={{ width: size, height: size, background: color, display: "inline-block" }}
      />
    </span>
  );
}
