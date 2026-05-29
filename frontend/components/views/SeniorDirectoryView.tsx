"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, SlidersHorizontal } from "lucide-react";
import type { Senior } from "@/lib/types";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { StatusDot } from "@/components/ui/StatusDot";
import { ActionButton } from "@/components/ui/ActionButton";

interface Props {
  seniors: Senior[];
}

function initials(name: string) {
  return name.split(" ").map((n) => n[0]).join("");
}

const CARD_SHADOW = "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

export function SeniorDirectoryView({ seniors }: Props) {
  const [query, setQuery]           = useState("");
  const [riskFilter, setRiskFilter] = useState<string>("All");

  const filtered = seniors.filter((s) => {
    const matchQuery =
      !query ||
      s.name.toLowerCase().includes(query.toLowerCase()) ||
      s.location.toLowerCase().includes(query.toLowerCase());
    const matchRisk = riskFilter === "All" || s.heatRisk === riskFilter;
    return matchQuery && matchRisk;
  });

  return (
    <div className="p-6 overflow-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1
            className="font-bold"
            style={{ fontSize: 22, color: "#071D3A", letterSpacing: "-0.03em" }}
          >
            Seniors
          </h1>
          <p className="mt-1" style={{ fontSize: 13, color: "#667085" }}>
            {seniors.length} enrolled
          </p>
        </div>
        <ActionButton variant="primary">+ Add Senior</ActionButton>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-5">
        <div className="relative flex-1 max-w-xs">
          <Search
            size={13}
            className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
            style={{ color: "#94A8BC" }}
          />
          <input
            type="text"
            placeholder="Search by name or location…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full rounded-lg pl-8 pr-3 py-2"
            style={{
              border: "1px solid #E2E8F0",
              background: "white",
              color: "#071D3A",
              fontSize: 13,
              fontFamily: "inherit",
              boxShadow: "var(--shadow-xs)",
            }}
          />
        </div>

        <div className="flex items-center gap-1 p-1 rounded-lg" style={{ background: "white", border: "1px solid #E2E8F0", boxShadow: "var(--shadow-xs)" }}>
          <SlidersHorizontal size={12} style={{ color: "#94A8BC", marginLeft: 6 }} />
          {["All", "Extreme", "High", "Moderate", "Low"].map((level) => (
            <button
              key={level}
              onClick={() => setRiskFilter(level)}
              className="px-3 py-1.5 rounded-md font-medium transition-interactive"
              style={{
                background: riskFilter === level ? "#071D3A" : "transparent",
                color: riskFilter === level ? "white" : "#667085",
                fontSize: 12,
              }}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-xl overflow-hidden" style={{ background: "white", boxShadow: CARD_SHADOW }}>
        <table className="w-full">
          <thead>
            <tr style={{ background: "#FAFBFC", borderBottom: "1px solid #F1F5F9" }}>
              {["Senior", "Location", "Heat Risk", "Status", "Support", "Last Check-in", ""].map((col) => (
                <th key={col} className="text-left px-5 py-3 label-caps">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((s, i) => (
              <tr
                key={s.id}
                className="transition-interactive"
                style={{ borderBottom: i < filtered.length - 1 ? "1px solid #F8FAFC" : undefined }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#FAFBFC"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}
              >
                {/* Senior */}
                <td className="px-5 py-3">
                  <div className="flex items-center gap-3">
                    <div
                      className="flex items-center justify-center rounded-full text-white font-semibold shrink-0"
                      style={{
                        width: 32, height: 32,
                        background: s.status === "Urgent"
                          ? "linear-gradient(135deg, #E52920, #C8221A)"
                          : s.status === "Watch"
                          ? "linear-gradient(135deg, #F59E0B, #D97706)"
                          : "linear-gradient(135deg, #1267D8, #0E51B0)",
                        fontSize: 11,
                        boxShadow: "0 1px 3px rgba(0,0,0,0.12)",
                      }}
                    >
                      {initials(s.name)}
                    </div>
                    <div>
                      <Link
                        href={`/seniors/${s.id}`}
                        className="font-medium transition-interactive hover:text-brand-blue"
                        style={{ fontSize: 13, color: "#071D3A" }}
                      >
                        {s.name}
                      </Link>
                      <p style={{ fontSize: 11.5, color: "#8FA8C8" }}>
                        Age {s.age} · {s.gender ?? "—"}
                      </p>
                    </div>
                  </div>
                </td>
                {/* Location */}
                <td className="px-5 py-3" style={{ fontSize: 13, color: "#667085" }}>
                  {s.location}
                </td>
                {/* Heat Risk */}
                <td className="px-5 py-3">
                  <RiskBadge risk={s.heatRisk} />
                </td>
                {/* Status */}
                <td className="px-5 py-3">
                  <div className="flex items-center gap-2">
                    <StatusDot status={s.status} />
                    <span style={{ fontSize: 13, color: "#071D3A" }}>{s.status}</span>
                  </div>
                </td>
                {/* Support */}
                <td className="px-5 py-3">
                  {s.supportMode ? (
                    <div className="flex flex-col gap-1">
                      <span style={{ fontSize: 12, color: "#071D3A" }}>{s.supportMode}</span>
                      {s.hasSupportContact === false && (
                        <span
                          className="inline-flex items-center rounded-full font-semibold"
                          style={{
                            fontSize: 10,
                            padding: "1px 6px",
                            background: "#FEF2F2",
                            color: "#B42318",
                            border: "1px solid #FECACA",
                            width: "fit-content",
                          }}
                        >
                          No contact
                        </span>
                      )}
                    </div>
                  ) : (
                    <span style={{ fontSize: 12, color: "#B0BFC8" }}>—</span>
                  )}
                </td>
                {/* Last check-in */}
                <td className="px-5 py-3 tabular" style={{ fontSize: 12.5, color: "#667085" }}>
                  {s.latestCheckIn ?? "—"}
                </td>
                {/* Action */}
                <td className="px-5 py-3">
                  <Link href={`/seniors/${s.id}`}>
                    <ActionButton variant="secondary" size="sm">View</ActionButton>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <div className="py-14 text-center">
            <p style={{ fontSize: 13, color: "#667085" }}>No seniors match your filters.</p>
          </div>
        )}
      </div>
    </div>
  );
}
