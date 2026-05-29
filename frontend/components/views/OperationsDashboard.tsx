"use client";

import Link from "next/link";
import { Users, AlertTriangle, PhoneCall, Phone } from "lucide-react";
import type {
  Senior,
  DashboardSummary,
  Alert,
  ScheduleItem,
  PriorityItem,
} from "@/lib/types";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { ActionButton } from "@/components/ui/ActionButton";
import { riskColor } from "@/lib/risk";

interface HeatTrendPoint {
  date: string;
  value: number;
}

interface Props {
  seniors: Senior[];
  summary: DashboardSummary;
  alerts: Alert[];
  schedule: ScheduleItem[];
  priorities: PriorityItem[];
  trendData: HeatTrendPoint[];
}

function HeatTrendChart({ data }: { data: HeatTrendPoint[] }) {

  const safeData = data.map((d) => ({
    ...d,
    value: Number.isFinite(Number(d.value)) ? Number(d.value) : 0,
  }));

  const W = 400;
  const H = 100;
  const MAX = 8;
  const pad = { l: 0, r: 0, t: 4, b: 0 };
  const chartH = H - pad.t - pad.b;

  const toY = (v: number) => pad.t + chartH - (v / MAX) * chartH;
  const toX = (i: number) => (i / (data.length - 1)) * W;

  const points = safeData.map((d, i) => `${toX(i)},${toY(d.value)}`).join(" ");

  const zones = [
    { y: toY(8), h: toY(6) - toY(8), fill: "rgba(229,41,32,0.12)",  label: "Extreme" },
    { y: toY(6), h: toY(4) - toY(6), fill: "rgba(245,158,11,0.14)", label: "High" },
    { y: toY(4), h: toY(2) - toY(4), fill: "rgba(18,103,216,0.10)", label: "Moderate" },
    { y: toY(2), h: toY(0) - toY(2), fill: "rgba(34,199,201,0.12)", label: "Low" },
  ];


  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} style={{ display: "block" }}>
        {zones.map((z) => (
          <rect key={z.label} x={0} y={z.y} width={W} height={z.h} fill={z.fill} />
        ))}
        <polyline
          points={points}
          fill="none"
          stroke="#22C7C9"
          strokeWidth={2.5}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {safeData.map((d, i) => (
          <circle key={i} cx={toX(i)} cy={toY(d.value)} r={3.5} fill="#22C7C9" />
        ))}
      </svg>
      {/* X-axis labels */}
      <div className="flex justify-between mt-1">
        {safeData.map((d) => (
          <span key={d.date} className="text-xs" style={{ color: "#667085", fontSize: 10 }}>
            {d.date.replace("May ", "")}
          </span>
        ))}
      </div>
      {/* Zone labels */}
      <div className="flex gap-4 mt-2">
        {["Low", "Moderate", "High", "Extreme"].map((lbl) => {
          const risk = lbl as "Low" | "Moderate" | "High" | "Extreme";
          return (
            <div key={lbl} className="flex items-center gap-1">
              <span
                className="rounded-full"
                style={{ width: 7, height: 7, display: "inline-block", background: riskColor(risk) }}
              />
              <span style={{ fontSize: 10, color: "#667085" }}>{lbl}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function OperationsDashboard({
  seniors: _seniors,
  summary,
  alerts,
  schedule,
  priorities,
  trendData,
}: Props) {
  return (
    <div className="p-6 overflow-auto h-full">
      {/* Header */}
      <div className="mb-6">
        <h1 className="font-bold text-2xl" style={{ color: "#071D3A" }}>
          Operations Dashboard
        </h1>
        <p className="text-sm mt-1" style={{ color: "#667085" }}>
          Daily outreach and monitoring at a glance.
        </p>
      </div>

      {/* Metric cards */}
      <div className="flex gap-4 mb-8">
        {[
          {
            icon: <Users size={18} style={{ color: "#1267D8" }} />,
            value: summary.seniorsMonitored,
            label: "Seniors Monitored",
            bg: "#EFF6FF",
            border: "#BFDBFE",
          },
          {
            icon: <AlertTriangle size={18} style={{ color: "#F59E0B" }} />,
            value: summary.needOutreach,
            label: "Need Outreach",
            bg: "#FFF7ED",
            border: "#FED7AA",
          },
          {
            icon: <AlertTriangle size={18} style={{ color: "#E52920" }} />,
            value: summary.criticalAlerts,
            label: "Critical Alerts",
            bg: "#FEF2F2",
            border: "#FECACA",
          },
        ].map((card) => (
          <div
            key={card.label}
            className="flex items-center gap-3 rounded-lg px-5 py-4"
            style={{ background: card.bg, border: `1px solid ${card.border}`, minWidth: 180 }}
          >
            <div
              className="flex items-center justify-center rounded-lg"
              style={{ width: 36, height: 36, background: "white" }}
            >
              {card.icon}
            </div>
            <div>
              <div className="text-2xl font-bold" style={{ color: "#071D3A" }}>
                {card.value}
              </div>
              <div className="text-xs" style={{ color: "#667085" }}>
                {card.label}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Main 2-col layout */}
      <div className="flex gap-6">
        {/* Left column */}
        <div className="flex-1 min-w-0 space-y-6">
          {/* Today's Priorities */}
          <div
            className="rounded-lg"
            style={{ background: "white", border: "1px solid #D8E0EA" }}
          >
            <div
              className="flex items-center justify-between px-5 py-4 border-b"
              style={{ borderColor: "#D8E0EA" }}
            >
              <div>
                <h2 className="font-semibold text-sm" style={{ color: "#071D3A" }}>
                  Today&apos;s Priorities
                </h2>
                <p className="text-xs mt-0.5" style={{ color: "#667085" }}>
                  Seniors who need attention today.
                </p>
              </div>
              <Link href="/seniors" className="text-xs hover:underline" style={{ color: "#1267D8" }}>
                View all seniors
              </Link>
            </div>

            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: "1px solid #D8E0EA" }}>
                  {["#", "Senior", "Location", "Risk", "Next Action"].map((col) => (
                    <th
                      key={col}
                      className="text-left px-5 py-2.5 text-xs font-semibold"
                      style={{ color: "#667085" }}
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {priorities.map((p, i) => (
                  <tr
                    key={p.seniorId}
                    style={{
                      borderBottom: i < priorities.length - 1 ? "1px solid #F1F5F9" : undefined,
                    }}
                  >
                    <td className="px-5 py-3">
                      <span
                        className="inline-flex items-center justify-center rounded-full text-white font-bold"
                        style={{
                          width: 22,
                          height: 22,
                          fontSize: 11,
                          background:
                            p.risk === "High" || p.risk === "Extreme" ? "#F59E0B" : "#1267D8",
                        }}
                      >
                        {p.rank}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <Link
                        href={`/seniors/${p.seniorId}`}
                        className="font-medium text-sm hover:underline"
                        style={{ color: "#071D3A" }}
                      >
                        {p.seniorName}, {p.age}
                      </Link>
                    </td>
                    <td className="px-5 py-3 text-sm" style={{ color: "#667085" }}>
                      {p.location}
                    </td>
                    <td className="px-5 py-3">
                      <RiskBadge risk={p.risk} />
                    </td>
                    <td className="px-5 py-3">
                      <ActionButton
                        variant={
                          p.action === "Dispatch wellness check" ? "warning" : "outline"
                        }
                        size="sm"
                      >
                        {p.action}
                      </ActionButton>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Heat Risk Trend */}
          <div
            className="rounded-lg p-5"
            style={{ background: "white", border: "1px solid #D8E0EA" }}
          >
            <h2 className="font-semibold text-sm mb-0.5" style={{ color: "#071D3A" }}>
              Heat Risk Trend
            </h2>
            <p className="text-xs mb-4" style={{ color: "#667085" }}>
              Daily average risk level (last 9 days)
            </p>
            <HeatTrendChart data={trendData} />
          </div>
        </div>

        {/* Right sidebar */}
        <div className="w-72 shrink-0 space-y-5">
          {/* Today's Schedule */}
          <div
            className="rounded-lg"
            style={{ background: "white", border: "1px solid #D8E0EA" }}
          >
            <div
              className="flex items-center justify-between px-4 py-3 border-b"
              style={{ borderColor: "#D8E0EA" }}
            >
              <h2 className="font-semibold text-sm" style={{ color: "#071D3A" }}>
                Today&apos;s Schedule
              </h2>
              <Link href="/seniors" className="text-xs hover:underline" style={{ color: "#1267D8" }}>
                View all
              </Link>
            </div>
            <div className="px-4 py-2">
              {schedule.map((item, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 py-2.5"
                  style={{
                    borderBottom: i < schedule.length - 1 ? "1px solid #F1F5F9" : undefined,
                  }}
                >
                  <div className="shrink-0 text-center" style={{ width: 42 }}>
                    <span
                      className="text-xs font-semibold block"
                      style={{ color: "#1267D8" }}
                    >
                      {item.time}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 mb-0.5">
                      {item.type === "Wellness Visit" ? (
                        <Phone size={11} style={{ color: "#22C7C9" }} />
                      ) : (
                        <PhoneCall size={11} style={{ color: "#1267D8" }} />
                      )}
                      <span className="text-xs font-medium" style={{ color: "#071D3A" }}>
                        {item.type}
                      </span>
                    </div>
                    <p className="text-xs" style={{ color: "#667085" }}>
                      {item.seniorName}
                    </p>
                    <p className="text-xs" style={{ color: "#8FA8C8", fontSize: 11 }}>
                      {item.location}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Urgent Alerts */}
          <div
            className="rounded-lg"
            style={{ background: "white", border: "1px solid #D8E0EA" }}
          >
            <div
              className="flex items-center justify-between px-4 py-3 border-b"
              style={{ borderColor: "#D8E0EA" }}
            >
              <h2 className="font-semibold text-sm" style={{ color: "#071D3A" }}>
                Urgent Alerts
              </h2>
              <Link href="/alerts" className="text-xs hover:underline" style={{ color: "#1267D8" }}>
                All alerts
              </Link>
            </div>
            <div className="px-4 py-2">
              {alerts
                .filter((a) => !a.acknowledged)
                .slice(0, 3)
                .map((alert, i, arr) => (
                  <div
                    key={alert.id}
                    className="flex items-start gap-2.5 py-2.5"
                    style={{
                      borderBottom: i < arr.length - 1 ? "1px solid #F1F5F9" : undefined,
                    }}
                  >
                    <AlertTriangle
                      size={14}
                      className="shrink-0 mt-0.5"
                      style={{ color: riskColor(alert.severity) }}
                    />
                    <div className="min-w-0">
                      <p className="text-xs font-medium truncate" style={{ color: "#071D3A" }}>
                        {alert.type}
                      </p>
                      <p className="text-xs truncate" style={{ color: "#667085" }}>
                        {alert.seniorName}
                      </p>
                      <p className="text-xs" style={{ color: "#8FA8C8", fontSize: 10 }}>
                        {alert.time}
                      </p>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
