"use client";

import Link from "next/link";
import { MapPin, Clock } from "lucide-react";
import type { Senior } from "@/lib/types";
import { statusColor } from "@/lib/risk";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { ActionButton } from "@/components/ui/ActionButton";

interface UrgentItem {
  id: string | number;
  name: string;
  age: number;
  location: string;
  status: Senior["status"];
}

interface Props {
  senior: Senior | null;
  urgentOutreach: UrgentItem[];
}

export function SelectedSeniorPanel({ senior, urgentOutreach }: Props) {
  const initials = (name: string) =>
    name
      .split(" ")
      .map((n) => n[0])
      .join("");

  return (
    <aside
      className="flex flex-col h-full overflow-y-auto shrink-0"
      style={{
        width: 292,
        background: "white",
        borderLeft: "1px solid #D8E0EA",
      }}
    >
      {/* Selected Senior */}
      <div className="px-5 pt-5 pb-4 border-b" style={{ borderColor: "#D8E0EA" }}>
        <p
          className="text-xs font-semibold uppercase tracking-wider mb-3"
          style={{ color: "#667085" }}
        >
          Selected Senior
        </p>

        {senior ? (
          <>
            <div className="flex items-center gap-3 mb-4">
              <div
                className="flex items-center justify-center rounded-full text-white font-semibold text-sm shrink-0"
                style={{ width: 40, height: 40, background: "#1267D8" }}
              >
                {initials(senior.name)}
              </div>
              <div>
                <p className="font-semibold text-sm" style={{ color: "#071D3A" }}>
                  {senior.name}
                </p>
                <p className="text-xs" style={{ color: "#667085" }}>
                  Age {senior.age} • {senior.gender ?? "—"}
                </p>
              </div>
            </div>

            <div className="space-y-2 mb-4">
              <div className="flex items-center gap-2 text-xs" style={{ color: "#667085" }}>
                <MapPin size={12} className="shrink-0" />
                <span>{senior.location}</span>
              </div>
              <div className="flex items-center gap-2 text-xs" style={{ color: "#667085" }}>
                <Clock size={12} className="shrink-0" />
                <span>{senior.latestCheckIn ?? "No check-in recorded"}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs" style={{ color: "#667085" }}>Heat Risk</span>
                <RiskBadge risk={senior.heatRisk} size="sm" />
              </div>
            </div>

            {senior.recommendedAction && (
              <ActionButton variant="warning" size="sm" className="w-full justify-center mb-2">
                {senior.recommendedAction}
              </ActionButton>
            )}
            <Link
              href={`/seniors/${senior.id}`}
              className="text-xs hover:underline"
              style={{ color: "#1267D8" }}
            >
              View full profile →
            </Link>
          </>
        ) : (
          <p className="text-xs" style={{ color: "#667085" }}>
            Click a marker on the map to view senior details.
          </p>
        )}
      </div>

      {/* Urgent Outreach */}
      <div className="px-5 pt-4 pb-5 flex-1">
        <div className="flex items-center justify-between mb-3">
          <p
            className="text-xs font-semibold uppercase tracking-wider"
            style={{ color: "#667085" }}
          >
            Urgent Outreach ({urgentOutreach.length})
          </p>
          <Link href="/alerts" className="text-xs hover:underline" style={{ color: "#1267D8" }}>
            View all alerts
          </Link>
        </div>

        <div className="space-y-2">
          {urgentOutreach.map((s) => (
            <Link
              key={s.id}
              href={`/seniors/${s.id}`}
              className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-gray-50 transition-colors"
              style={{ border: "1px solid #D8E0EA" }}
            >
              <div>
                <p className="text-xs font-medium" style={{ color: "#071D3A" }}>
                  {s.name}, {s.age}
                </p>
                <p className="text-xs" style={{ color: "#667085" }}>
                  {s.location}
                </p>
              </div>
              <span
                className="text-xs font-semibold rounded-full px-2 py-0.5 shrink-0"
                style={{
                  background: statusColor(s.status) + "18",
                  color: statusColor(s.status),
                  fontSize: 10,
                }}
              >
                {s.status}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </aside>
  );
}
