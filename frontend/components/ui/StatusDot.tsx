import { statusColor } from "@/lib/risk";
import type { SeniorStatus } from "@/lib/types";

interface Props {
  status: SeniorStatus;
  size?: number;
}

export function StatusDot({ status, size = 8 }: Props) {
  return (
    <span
      className="rounded-full inline-block flex-shrink-0"
      style={{ width: size, height: size, background: statusColor(status) }}
    />
  );
}
