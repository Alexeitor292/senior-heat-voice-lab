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
    name.split(" ").map((n) => n[0]).join("");

  const avatarBg = senior
    ? senior.status === "Urgent"
      ? "linear-gradient(135deg, #E52920, #C8221A)"
      : senior.status === "Watch"
      ? "linear-gradient(135deg, #F59E0B, #D97706)"
      : "linear-gradient(135deg, #1267D8, #0E51B0)"
    : "#1267D8";

  return (
    <aside
      className="flex flex-col h-full overflow-y-auto shrink-0"
      style={{ width: 292, background: "white", borderLeft: "1px solid #E8EDF3" }}
    >
      {/* Selected Senior */}
      <div className="px-5 pt-5 pb-4" style={{ borderBottom: "1px solid #F1F5F9" }}>
        <p className="label-caps mb-3">Selected Senior</p>

        {senior ? (
          <>
            {/* Avatar + name */}
            <div className="flex items-center gap-3 mb-4">
              <div
                className="flex items-center justify-center rounded-full text-white font-semibold shrink-0"
                style={{
                  width: 40, height: 40,
                  background: avatarBg,
                  fontSize: 13,
                  boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
                }}
              >
                {initials(senior.name)}
              </div>
              <div>
                <p className="font-semibold" style={{ fontSize: 14, color: "#071D3A", letterSpacing: "-0.02em" }}>
                  {senior.name}
                </p>
                <p style={{ fontSize: 12, color: "#8FA8C8" }}>
                  Age {senior.age} · {senior.gender ?? "—"}
                </p>
              </div>
            </div>

            {/* Info rows */}
            <div className="space-y-2 mb-4">
              <div className="flex items-center gap-2" style={{ fontSize: 12, color: "#667085" }}>
                <MapPin size={11} className="shrink-0" style={{ color: "#94A8BC" }} />
                <span>{senior.location}</span>
              </div>
              <div className="flex items-center gap-2" style={{ fontSize: 12, color: "#667085" }}>
                <Clock size={11} className="shrink-0" style={{ color: "#94A8BC" }} />
                <span className="tabular">{senior.latestCheckIn ?? "No check-in recorded"}</span>
              </div>
              <div className="flex items-center gap-2">
                <span style={{ fontSize: 11.5, color: "#94A8BC" }}>Heat Risk</span>
                <RiskBadge risk={senior.heatRisk} size="sm" />
              </div>
            </div>

            {/* Support network block */}
            {(senior.supportMode || senior.livingSituation) && (
              <div
                className="mt-3 pt-3 space-y-2"
                style={{ borderTop: "1px solid #F1F5F9" }}
              >
                <div className="flex items-center gap-2" style={{ fontSize: 12, color: "#667085" }}>
                  <ShieldCheck size={11} className="shrink-0" style={{ color: "#94A8BC" }} />
                  <span>{senior.supportMode ?? "Support mode unknown"}</span>
                </div>
                <div className="flex items-center gap-2" style={{ fontSize: 12, color: "#667085" }}>
                  <UserRoundX size={11} className="shrink-0" style={{ color: "#94A8BC" }} />
                  <span>{senior.livingSituation ?? "Living situation unknown"}</span>
                </div>
                <div
                  className="rounded-lg px-3 py-2"
                  style={{
                    background: senior.hasSupportContact === false ? "#FEF2F2" : "#F8FAFC",
                    color:      senior.hasSupportContact === false ? "#B42318" : "#667085",
                    border:     senior.hasSupportContact === false ? "1px solid #FECACA" : "1px solid #E8EDF3",
                    fontSize: 11.5,
                    lineHeight: 1.5,
                  }}
                >
                  {senior.hasSupportContact === false
                    ? "No support contact listed. Operator review required for high-risk events."
                    : `${senior.supportContactCount ?? 0} support contact${senior.supportContactCount === 1 ? "" : "s"} on file.`}
                </div>
                {senior.escalationPlanSummary && (
                  <p style={{ fontSize: 11.5, color: "#8FA8C8", lineHeight: 1.5 }}>
                    {senior.escalationPlanSummary}
                  </p>
                )}
              </div>
            )}

            {senior.recommendedAction && (
              <ActionButton variant="warning" size="sm" className="w-full justify-center mt-4 mb-2">
                {senior.recommendedAction}
              </ActionButton>
            )}
            <Link
              href={`/seniors/${senior.id}`}
              className="transition-interactive"
              style={{ fontSize: 12, color: "#1267D8", fontWeight: 500 }}
            >
              View full profile →
            </Link>
          </>
        ) : (
          <p style={{ fontSize: 12.5, color: "#94A8BC" }}>
            Click a marker on the map to view senior details.
          </p>
        )}
      </div>

      {/* Needs Response */}
      <div className="px-5 pt-4 pb-5 flex-1">
        <div className="flex items-center justify-between mb-3">
          <p className="label-caps">Needs Response ({urgentOutreach.length})</p>
          <Link href="/alerts" style={{ fontSize: 11.5, color: "#1267D8", fontWeight: 500 }}>
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
                className="flex items-center justify-between rounded-lg px-3 py-2.5 transition-interactive"
                style={{ border: "1px solid #F1F5F9", background: "#FAFBFC" }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = "#D8E0EA";
                  (e.currentTarget as HTMLElement).style.background = "white";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = "#F1F5F9";
                  (e.currentTarget as HTMLElement).style.background = "#FAFBFC";
                }}
              >
                <div>
                  <p className="font-medium" style={{ fontSize: 12.5, color: "#071D3A" }}>
                    {item.name}, {item.age}
                  </p>
                  <p style={{ fontSize: 11.5, color: "#8FA8C8" }}>{item.location}</p>
                  {item.time && (
                    <p className="tabular" style={{ fontSize: 10.5, color: "#94A8BC" }}>{item.time}</p>
                  )}
                </div>
                <span
                  className="font-semibold rounded-full px-2 py-0.5 shrink-0"
                  style={{ background: color + "18", color, fontSize: 10.5 }}
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
