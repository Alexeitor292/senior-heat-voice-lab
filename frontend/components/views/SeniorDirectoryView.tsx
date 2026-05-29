"use client";

import { useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import type { Senior } from "@/lib/types";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { StatusDot } from "@/components/ui/StatusDot";
import { ActionButton } from "@/components/ui/ActionButton";

interface Props {
  seniors: Senior[];
}

function initials(name: string) {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("");
}

export function SeniorDirectoryView({ seniors }: Props) {
  const [query, setQuery] = useState("");
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
          <h1 className="font-bold text-2xl" style={{ color: "#071D3A" }}>
            Seniors
          </h1>
          <p className="text-sm mt-1" style={{ color: "#667085" }}>
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
            className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: "#667085" }}
          />
          <input
            type="text"
            placeholder="Search by name or location…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full rounded border pl-8 pr-3 py-1.5 text-sm outline-none focus:border-teal transition-colors"
            style={{
              borderColor: "#D8E0EA",
              background: "#F8FAFC",
              color: "#071D3A",
              fontSize: 13,
            }}
          />
        </div>

        <div className="flex gap-1.5">
          {["All", "Extreme", "High", "Moderate", "Low"].map((level) => (
            <button
              key={level}
              onClick={() => setRiskFilter(level)}
              className="px-3 py-1.5 rounded text-xs font-medium transition-colors"
              style={{
                background: riskFilter === level ? "#071D3A" : "white",
                color: riskFilter === level ? "white" : "#667085",
                border: "1px solid #D8E0EA",
              }}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div
        className="rounded-lg overflow-hidden"
        style={{ background: "white", border: "1px solid #D8E0EA" }}
      >
        <table className="w-full">
          <thead>
            <tr style={{ background: "#F8FAFC", borderBottom: "1px solid #D8E0EA" }}>
              {["Senior", "Location", "Heat Risk", "Status", "Last Check-in", ""].map(
                (col) => (
                  <th
                    key={col}
                    className="text-left px-5 py-3 text-xs font-semibold"
                    style={{ color: "#667085" }}
                  >
                    {col}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {filtered.map((s, i) => (
              <tr
                key={s.id}
                className="hover:bg-gray-50 transition-colors"
                style={{
                  borderBottom:
                    i < filtered.length - 1 ? "1px solid #F1F5F9" : undefined,
                }}
              >
                <td className="px-5 py-3">
                  <div className="flex items-center gap-3">
                    <div
                      className="flex items-center justify-center rounded-full text-white text-xs font-semibold shrink-0"
                      style={{ width: 32, height: 32, background: "#1267D8" }}
                    >
                      {initials(s.name)}
                    </div>
                    <div>
                      <Link
                        href={`/seniors/${s.id}`}
                        className="font-medium text-sm hover:underline"
                        style={{ color: "#071D3A" }}
                      >
                        {s.name}
                      </Link>
                      <p className="text-xs" style={{ color: "#667085" }}>
                        Age {s.age} • {s.gender ?? "—"}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="px-5 py-3 text-sm" style={{ color: "#667085" }}>
                  {s.location}
                </td>
                <td className="px-5 py-3">
                  <RiskBadge risk={s.heatRisk} />
                </td>
                <td className="px-5 py-3">
                  <div className="flex items-center gap-2">
                    <StatusDot status={s.status} />
                    <span className="text-sm" style={{ color: "#071D3A" }}>
                      {s.status}
                    </span>
                  </div>
                </td>
                <td className="px-5 py-3 text-sm" style={{ color: "#667085" }}>
                  {s.latestCheckIn ?? "—"}
                </td>
                <td className="px-5 py-3">
                  <Link href={`/seniors/${s.id}`}>
                    <ActionButton variant="secondary" size="sm">
                      View
                    </ActionButton>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <div className="py-12 text-center">
            <p className="text-sm" style={{ color: "#667085" }}>
              No seniors match your filters.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
