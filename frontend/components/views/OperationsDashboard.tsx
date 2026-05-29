"use client";

import Link from "next/link";
import {
  Users,
  AlertTriangle,
  PhoneCall,
  Phone,
  ClipboardList,
} from "lucide-react";
import type {
  Senior,
  DashboardSummary,
  Alert,
  ScheduleItem,
  PriorityItem,
  OperatorAction,
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
  pendingOperatorActions: OperatorAction[];
}

function HeatTrendChart({ data }: { data: HeatTrendPoint[] }) {
  const safeData = data.map((d) => ({
    ...d,
    value: Number.isFinite(Number(d.value)) ? Number(d.value) : 0,
  }));

  const W = 400;
  const H = 110;
  const MAX = 8;
  const pad = { t: 6, b: 0 };
  const chartH = H - pad.t - pad.b;

  const toY = (v: number) => pad.t + chartH - (v / MAX) * chartH;
  const toX = (i: number) =>
    safeData.length <= 1 ? W / 2 : (i / (safeData.length - 1)) * W;

  const points = safeData
    .map((d, i) => `${toX(i)},${toY(d.value)}`)
    .join(" ");

  const areaPoints =
    safeData.length > 0
      ? `0,${toY(0)} ${points} ${W},${toY(0)}`
      : `0,${toY(0)} ${W},${toY(0)}`;

  const zones = [
    {
      y: toY(8),
      h: toY(6) - toY(8),
      fill: "rgba(229,41,32,0.07)",
      label: "Extreme",
    },
    {
      y: toY(6),
      h: toY(4) - toY(6),
      fill: "rgba(245,158,11,0.08)",
      label: "High",
    },
    {
      y: toY(4),
      h: toY(2) - toY(4),
      fill: "rgba(18,103,216,0.06)",
      label: "Moderate",
    },
    {
      y: toY(2),
      h: toY(0) - toY(2),
      fill: "rgba(34,199,201,0.07)",
      label: "Low",
    },
  ];

  return (
    <div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        height={H}
        style={{ display: "block" }}
      >
        {zones.map((z) => (
          <rect
            key={z.label}
            x={0}
            y={z.y}
            width={W}
            height={z.h}
            fill={z.fill}
          />
        ))}

        {[2, 4, 6].map((v) => (
          <line
            key={v}
            x1={0}
            y1={toY(v)}
            x2={W}
            y2={toY(v)}
            stroke="#E2E8F0"
            strokeWidth={0.75}
            strokeDasharray="3 3"
          />
        ))}

        <polygon points={areaPoints} fill="rgba(34,199,201,0.06)" />

        {points && (
          <polyline
            points={points}
            fill="none"
            stroke="#22C7C9"
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        )}

        {safeData.map((d, i) => (
          <g key={i}>
            <circle
              cx={toX(i)}
              cy={toY(d.value)}
              r={4}
              fill="white"
              stroke="#22C7C9"
              strokeWidth={2}
            />
          </g>
        ))}
      </svg>

      <div className="flex justify-between mt-1.5">
        {safeData.map((d) => (
          <span
            key={d.date}
            className="tabular"
            style={{ fontSize: 10, color: "#94A8BC" }}
          >
            {d.date.replace("May ", "")}
          </span>
        ))}
      </div>

      <div className="flex gap-4 mt-2.5">
        {(["Low", "Moderate", "High", "Extreme"] as const).map((lbl) => (
          <div key={lbl} className="flex items-center gap-1.5">
            <span
              className="rounded-full"
              style={{
                width: 6,
                height: 6,
                display: "inline-block",
                background: riskColor(lbl),
              }}
            />
            <span style={{ fontSize: 10.5, color: "#8FA8C8" }}>{lbl}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatOperatorActionTitle(action: OperatorAction): string {
  const type = (action.action_type || "").toLowerCase();

  if (type === "wellness_check") return "Wellness Check";
  if (type === "message_support") return "Support Outreach";
  if (type === "operator_review") return "Operator Review";
  if (type === "call_senior") return "Senior Call";

  return "Operator Action";
}

function formatOperatorActionTime(value?: string | null): string {
  if (!value) return "Unknown time";

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return "Unknown time";
  }

  return parsed.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });
}

const CARD_SHADOW =
  "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

export function OperationsDashboard({
  seniors: _seniors,
  summary,
  alerts,
  schedule,
  priorities,
  trendData,
  pendingOperatorActions = [],
}: Props) {
  return (
    <div className="p-6 overflow-auto h-full">
      {/* Header */}
      <div className="mb-7">
        <h1
          className="font-bold"
          style={{
            fontSize: 22,
            color: "#071D3A",
            letterSpacing: "-0.03em",
          }}
        >
          Operations Dashboard
        </h1>
        <p className="mt-1" style={{ fontSize: 13, color: "#667085" }}>
          Daily outreach and monitoring at a glance.
        </p>
      </div>

      {/* Metric cards */}
      <div className="flex gap-4 mb-7">
        {[
          {
            icon: <Users size={16} style={{ color: "#1267D8" }} />,
            value: summary.seniorsMonitored,
            label: "Seniors Monitored",
            bg: "#EFF6FF",
            border: "#BFDBFE",
            iconBg: "rgba(18,103,216,0.08)",
          },
          {
            icon: <AlertTriangle size={16} style={{ color: "#F59E0B" }} />,
            value: summary.needOutreach,
            label: "Need Outreach",
            bg: "#FFF7ED",
            border: "#FED7AA",
            iconBg: "rgba(245,158,11,0.1)",
          },
          {
            icon: <AlertTriangle size={16} style={{ color: "#E52920" }} />,
            value: summary.criticalAlerts,
            label: "Critical Alerts",
            bg: "#FEF2F2",
            border: "#FECACA",
            iconBg: "rgba(229,41,32,0.08)",
          },
          {
            icon: <ClipboardList size={16} style={{ color: "#1267D8" }} />,
            value: pendingOperatorActions.length,
            label: "Pending Actions",
            bg: "#F8FAFC",
            border: "#E2E8F0",
            iconBg: "rgba(18,103,216,0.08)",
          },
        ].map((card) => (
          <div
            key={card.label}
            className="flex items-center gap-3.5 rounded-xl px-5 py-4"
            style={{
              background: card.bg,
              border: `1px solid ${card.border}`,
              boxShadow: "var(--shadow-xs)",
              minWidth: 186,
            }}
          >
            <div
              className="flex items-center justify-center rounded-lg shrink-0"
              style={{ width: 36, height: 36, background: card.iconBg }}
            >
              {card.icon}
            </div>
            <div>
              <div
                className="font-bold tabular leading-none mb-1"
                style={{
                  fontSize: 26,
                  color: "#071D3A",
                  letterSpacing: "-0.04em",
                }}
              >
                {card.value}
              </div>
              <div className="label-caps">{card.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Main 2-col */}
      <div className="flex gap-5">
        {/* Left */}
        <div className="flex-1 min-w-0 space-y-5">
          {/* Priorities table */}
          <div
            className="rounded-xl overflow-hidden"
            style={{ background: "white", boxShadow: CARD_SHADOW }}
          >
            <div
              className="flex items-center justify-between px-5 py-4"
              style={{ borderBottom: "1px solid #F1F5F9" }}
            >
              <div>
                <h2
                  className="font-semibold"
                  style={{
                    fontSize: 13.5,
                    color: "#071D3A",
                    letterSpacing: "-0.01em",
                  }}
                >
                  Today&apos;s Priorities
                </h2>
                <p
                  className="mt-0.5"
                  style={{ fontSize: 12, color: "#667085" }}
                >
                  Seniors who need attention today.
                </p>
              </div>
              <Link
                href="/seniors"
                className="transition-interactive"
                style={{ fontSize: 12, color: "#1267D8", fontWeight: 500 }}
              >
                View all →
              </Link>
            </div>

            <table className="w-full">
              <thead>
                <tr
                  style={{
                    borderBottom: "1px solid #F1F5F9",
                    background: "#FAFBFC",
                  }}
                >
                  {["#", "Senior", "Location", "Risk", "Next Action"].map(
                    (col) => (
                      <th key={col} className="text-left px-5 py-2.5 label-caps">
                        {col}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {priorities.map((p, i) => (
                  <tr
                    key={p.seniorId}
                    className="transition-interactive"
                    style={{
                      borderBottom:
                        i < priorities.length - 1
                          ? "1px solid #F8FAFC"
                          : undefined,
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLElement).style.background =
                        "#FAFBFC";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.background =
                        "transparent";
                    }}
                  >
                    <td className="px-5 py-3">
                      <span
                        className="inline-flex items-center justify-center rounded-full text-white font-bold tabular"
                        style={{
                          width: 22,
                          height: 22,
                          fontSize: 11,
                          background:
                            p.risk === "High" || p.risk === "Extreme"
                              ? "#F59E0B"
                              : "#1267D8",
                        }}
                      >
                        {p.rank}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <Link
                        href={`/seniors/${p.seniorId}`}
                        className="font-medium transition-interactive hover:text-brand-blue"
                        style={{ fontSize: 13, color: "#071D3A" }}
                      >
                        {p.seniorName}, {p.age}
                      </Link>
                    </td>
                    <td
                      className="px-5 py-3"
                      style={{ fontSize: 13, color: "#667085" }}
                    >
                      {p.location}
                    </td>
                    <td className="px-5 py-3">
                      <RiskBadge risk={p.risk} />
                    </td>
                    <td className="px-5 py-3">
                      <ActionButton
                        variant={
                          p.action === "Dispatch wellness check" ||
                          p.action.includes("wellness")
                            ? "warning"
                            : "outline"
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
            className="rounded-xl p-5"
            style={{ background: "white", boxShadow: CARD_SHADOW }}
          >
            <div className="flex items-baseline justify-between mb-1">
              <h2
                className="font-semibold"
                style={{
                  fontSize: 13.5,
                  color: "#071D3A",
                  letterSpacing: "-0.01em",
                }}
              >
                Heat Risk Trend
              </h2>
              <span className="label-caps">Last 7 days</span>
            </div>
            <p className="mb-4" style={{ fontSize: 12, color: "#667085" }}>
              Daily average risk level across monitored seniors
            </p>
            <HeatTrendChart data={trendData} />
          </div>
        </div>

        {/* Right sidebar */}
        <div className="w-[272px] shrink-0 space-y-4">
          {/* Pending Actions */}
          <div
            className="rounded-xl overflow-hidden"
            style={{ background: "white", boxShadow: CARD_SHADOW }}
          >
            <div
              className="flex items-center justify-between px-4 py-3.5"
              style={{ borderBottom: "1px solid #F1F5F9" }}
            >
              <Link
                href="/actions"
                className="font-semibold flex items-center gap-2 transition-interactive hover:text-brand-blue"
                style={{ fontSize: 13, color: "#071D3A" }}
              >
                <ClipboardList size={14} />
                Pending Actions
              </Link>
              <span className="label-caps">
                {pendingOperatorActions.length}
              </span>
            </div>

            <div className="px-4 py-1">
              {pendingOperatorActions.length === 0 && (
                <div
                  className="py-3"
                  style={{ fontSize: 12, color: "#667085", lineHeight: 1.5 }}
                >
                  No pending operator actions.
                </div>
              )}

              {pendingOperatorActions.slice(0, 5).map((action, i, arr) => (
                <div
                  key={action.id}
                  className="py-2.5 transition-interactive"
                  style={{
                    borderBottom:
                      i < arr.length - 1 ? "1px solid #F8FAFC" : undefined,
                  }}
                >
                  <div className="flex items-center justify-between gap-2 mb-0.5">
                    <span
                      className="font-medium"
                      style={{ fontSize: 12, color: "#071D3A" }}
                    >
                      {formatOperatorActionTitle(action)}
                    </span>
                    <span
                      className="tabular"
                      style={{ fontSize: 10.5, color: "#94A8BC" }}
                    >
                      {formatOperatorActionTime(action.created_at)}
                    </span>
                  </div>

                  <Link
                    href={`/seniors/${action.senior_id}`}
                    className="font-medium transition-interactive hover:text-brand-blue"
                    style={{ fontSize: 11.5, color: "#1267D8" }}
                  >
                    {action.senior_name ?? `Senior ${action.senior_id}`}
                  </Link>

                  <p
                    className="mt-0.5"
                    style={{
                      fontSize: 11.5,
                      color: "#667085",
                      lineHeight: 1.45,
                    }}
                  >
                    {action.reason ?? "No reason provided."}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Schedule */}
          <div
            className="rounded-xl overflow-hidden"
            style={{ background: "white", boxShadow: CARD_SHADOW }}
          >
            <div
              className="flex items-center justify-between px-4 py-3.5"
              style={{ borderBottom: "1px solid #F1F5F9" }}
            >
              <h2
                className="font-semibold"
                style={{ fontSize: 13, color: "#071D3A" }}
              >
                Today&apos;s Schedule
              </h2>
              <Link
                href="/seniors"
                style={{ fontSize: 11.5, color: "#1267D8", fontWeight: 500 }}
              >
                View all
              </Link>
            </div>
            <div className="px-4 py-1">
              {schedule.map((item, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 py-2.5 transition-interactive"
                  style={{
                    borderBottom:
                      i < schedule.length - 1
                        ? "1px solid #F8FAFC"
                        : undefined,
                  }}
                >
                  <div className="shrink-0" style={{ width: 44 }}>
                    <span
                      className="font-semibold tabular block"
                      style={{ fontSize: 11.5, color: "#1267D8" }}
                    >
                      {item.time}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 mb-0.5">
                      {item.type === "Wellness Visit" ? (
                        <Phone size={10} style={{ color: "#22C7C9" }} />
                      ) : (
                        <PhoneCall size={10} style={{ color: "#1267D8" }} />
                      )}
                      <span
                        className="font-medium"
                        style={{ fontSize: 12, color: "#071D3A" }}
                      >
                        {item.type}
                      </span>
                    </div>
                    <p style={{ fontSize: 12, color: "#667085" }}>
                      {item.seniorName}
                    </p>
                    <p style={{ fontSize: 11, color: "#94A8BC" }}>
                      {item.location}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Urgent Alerts */}
          <div
            className="rounded-xl overflow-hidden"
            style={{ background: "white", boxShadow: CARD_SHADOW }}
          >
            <div
              className="flex items-center justify-between px-4 py-3.5"
              style={{ borderBottom: "1px solid #F1F5F9" }}
            >
              <h2
                className="font-semibold"
                style={{ fontSize: 13, color: "#071D3A" }}
              >
                Urgent Alerts
              </h2>
              <Link
                href="/alerts"
                style={{ fontSize: 11.5, color: "#1267D8", fontWeight: 500 }}
              >
                All alerts
              </Link>
            </div>
            <div className="px-4 py-1">
              {alerts
                .filter((a) => !a.acknowledged)
                .slice(0, 3)
                .map((alert, i, arr) => (
                  <div
                    key={alert.id}
                    className="flex items-start gap-2.5 py-2.5"
                    style={{
                      borderBottom:
                        i < arr.length - 1
                          ? "1px solid #F8FAFC"
                          : undefined,
                    }}
                  >
                    <div
                      className="flex items-center justify-center rounded-md shrink-0 mt-0.5"
                      style={{
                        width: 22,
                        height: 22,
                        background: riskColor(alert.severity) + "15",
                      }}
                    >
                      <AlertTriangle
                        size={11}
                        style={{ color: riskColor(alert.severity) }}
                      />
                    </div>
                    <div className="min-w-0">
                      <p
                        className="font-medium truncate"
                        style={{ fontSize: 12, color: "#071D3A" }}
                      >
                        {alert.type}
                      </p>
                      <p
                        className="truncate"
                        style={{ fontSize: 11.5, color: "#667085" }}
                      >
                        {alert.seniorName}
                      </p>
                      <p
                        className="tabular"
                        style={{ fontSize: 10.5, color: "#94A8BC" }}
                      >
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