"use client";

import Link from "next/link";
import { MapPin, Clock, ShieldCheck, UserRoundX } from "lucide-react";
import type { Senior, UrgentOutreachItem } from "@/lib/types";
import { statusColor, riskColor } from "@/lib/risk";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { ActionButton } from "@/components/ui/ActionButton";

interface Props {
  senior: Senior | null;
  urgentOutreach: UrgentOutreachItem[];
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
                style={{
                  width: 40,
                  height: 40,
                  background:
                    senior.status === "Urgent"
                      ? "#E52920"
                      : senior.status === "Watch"
                        ? "#F59E0B"
                        : "#1267D8",
                }}
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
                <span className="text-xs" style={{ color: "#667085" }}>
                  Heat Risk
                </span>
                <RiskBadge risk={senior.heatRisk} size="sm" />
              </div>
            </div>

            {/* Support network context */}
            <div
              className="mt-4 pt-4 space-y-2 border-t"
              style={{ borderColor: "#D8E0EA" }}
            >
              <div className="flex items-center gap-2 text-xs" style={{ color: "#667085" }}>
                <ShieldCheck size={12} className="shrink-0" />
                <span>{senior.supportMode ?? "Support mode unknown"}</span>
              </div>
              <div className="flex items-center gap-2 text-xs" style={{ color: "#667085" }}>
                <UserRoundX size={12} className="shrink-0" />
                <span>{senior.livingSituation ?? "Living situation unknown"}</span>
              </div>
              <div
                className="text-xs leading-relaxed rounded-md px-3 py-2"
                style={{
                  background: senior.hasSupportContact === false ? "#FEF2F2" : "#F8FAFC",
                  color: senior.hasSupportContact === false ? "#B42318" : "#667085",
                  border:
                    senior.hasSupportContact === false
                      ? "1px solid #FECACA"
                      : "1px solid #D8E0EA",
                }}
              >
                {senior.hasSupportContact === false
                  ? "No support contact listed. Operator review required for high-risk events."
                  : `${senior.supportContactCount ?? 0} support contact${
                      senior.supportContactCount === 1 ? "" : "s"
                    } on file.`}
              </div>
              {senior.escalationPlanSummary && (
                <p className="text-xs leading-relaxed" style={{ color: "#667085" }}>
                  {senior.escalationPlanSummary}
                </p>
              )}
            </div>

            {senior.recommendedAction && (
              <ActionButton variant="warning" size="sm" className="w-full justify-center mb-2 mt-4">
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

      <div className="px-5 pt-4 pb-5 flex-1">
        <div className="flex items-center justify-between mb-3">
          <p
            className="text-xs font-semibold uppercase tracking-wider"
            style={{ color: "#667085" }}
          >
            Needs Response ({urgentOutreach.length})
          </p>

          <Link href="/alerts" className="text-xs hover:underline" style={{ color: "#1267D8" }}>
            View all alerts
          </Link>
        </div>

        <div className="space-y-2">
          {urgentOutreach.map((item) => {
            const displayStatus = item.status ?? (item.risk === "High" ? "Urgent" : "Watch");
            const color = item.status ? statusColor(item.status) : riskColor(item.risk);

            return (
              <Link
                key={item.seniorId}
                href={`/seniors/${item.seniorId}`}
                className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-gray-50 transition-colors"
                style={{ border: "1px solid #D8E0EA" }}
              >
                <div>
                  <p className="text-xs font-medium" style={{ color: "#071D3A" }}>
                    {item.name}, {item.age}
                  </p>

                  <p className="text-xs" style={{ color: "#667085" }}>
                    {item.location}
                  </p>

                  {item.time && (
                    <p className="text-[10px] mt-0.5" style={{ color: "#8FA8C8" }}>
                      {item.time}
                    </p>
                  )}
                </div>

                <span
                  className="text-xs font-semibold rounded-full px-2 py-0.5 shrink-0"
                  style={{
                    background: color + "18",
                    color,
                    fontSize: 10,
                  }}
                >
                  {displayStatus}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </aside>
  );
}