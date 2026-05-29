import { statusColor } from "@/lib/risk";
import type { SeniorStatus } from "@/lib/types";

const HEAT_STOPS = [
  { color: "rgba(34,199,201,0.5)" },
  { color: "rgba(18,103,216,0.45)" },
  { color: "rgba(245,158,11,0.55)" },
  { color: "rgba(229,41,32,0.6)" },
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
      className="flex items-center gap-8 px-5 py-2.5 shrink-0"
      style={{ borderTop: "1px solid #E8EDF3", background: "white" }}
    >
      <div>
        <p className="label-caps mb-1.5">Heat Risk (National)</p>
        <div className="flex items-center gap-1">
          <span style={{ fontSize: 11, color: "#667085", marginRight: 4 }}>Low</span>
          {HEAT_STOPS.map((s, i) => (
            <span
              key={i}
              style={{
                display: "inline-block",
                width: 22,
                height: 10,
                background: s.color,
                borderRadius: 3,
              }}
            />
          ))}
          <span style={{ fontSize: 11, color: "#667085", marginLeft: 4 }}>Extreme</span>
        </div>
      </div>

      <div className="w-px self-stretch" style={{ background: "#E8EDF3" }} />

      <div>
        <p className="label-caps mb-1.5">Senior Status</p>
        <div className="flex items-center gap-4">
          {STATUS_ITEMS.map((s) => (
            <div key={s.label} className="flex items-center gap-1.5">
              <span
                className="rounded-full shrink-0"
                style={{ display: "inline-block", width: 7, height: 7, background: statusColor(s.label) }}
              />
              <span style={{ fontSize: 11.5, color: "#667085" }}>{s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
