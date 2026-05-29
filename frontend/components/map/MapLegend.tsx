import { statusColor } from "@/lib/risk";
import type { SeniorStatus } from "@/lib/types";

const HEAT_STOPS = [
  { color: "rgba(34,199,201,0.45)", label: "Low" },
  { color: "rgba(18,103,216,0.4)",  label: "" },
  { color: "rgba(245,158,11,0.5)",  label: "" },
  { color: "rgba(229,41,32,0.55)",  label: "Extreme" },
];

const STATUS_ITEMS: { label: SeniorStatus }[] = [
  { label: "Safe" },
  { label: "Stable" },
  { label: "Watch" },
  { label: "Urgent" },
];

export function MapLegend() {
  return (
    <div
      className="flex items-center gap-8 px-5 py-3 shrink-0"
      style={{ borderTop: "1px solid #D8E0EA", background: "white" }}
    >
      {/* Heat Risk */}
      <div>
        <p className="text-xs font-medium mb-1.5" style={{ color: "#667085" }}>
          Heat Risk (National)
        </p>
        <div className="flex items-center gap-1">
          <span className="text-xs mr-1" style={{ color: "#667085" }}>
            Low
          </span>
          {HEAT_STOPS.map((s, i) => (
            <span
              key={i}
              style={{
                display: "inline-block",
                width: 24,
                height: 12,
                background: s.color,
                borderRadius: 2,
              }}
            />
          ))}
          <span className="text-xs ml-1" style={{ color: "#667085" }}>
            Extreme
          </span>
        </div>
      </div>

      {/* Senior Status */}
      <div>
        <p className="text-xs font-medium mb-1.5" style={{ color: "#667085" }}>
          Senior Status
        </p>
        <div className="flex items-center gap-4">
          {STATUS_ITEMS.map((s) => (
            <div key={s.label} className="flex items-center gap-1.5">
              <span
                className="rounded-full"
                style={{
                  display: "inline-block",
                  width: 8,
                  height: 8,
                  background: statusColor(s.label),
                }}
              />
              <span className="text-xs" style={{ color: "#667085" }}>
                {s.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
