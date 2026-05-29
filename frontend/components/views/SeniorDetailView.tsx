"use client";

import Link from "next/link";
import {
  ChevronLeft,
  MapPin,
  Clock,
  User,
  Phone,
  Heart,
  CheckCircle,
  XCircle,
  Info,
  ShieldCheck,
  Home,
} from "lucide-react";
import { SupportNetworkEditor } from "@/components/forms/SupportNetworkEditor";
import { HeatSettingsEditor } from "@/components/forms/HeatSettingsEditor";
import { DemographicsEditor } from "@/components/forms/DemographicsEditor";
import { SeniorActionPanel } from "@/components/forms/SeniorActionPanel";
import { OperatorActionQueue } from "@/components/forms/OperatorActionQueue";
import { ConversationInsightPanel } from "@/components/forms/ConversationInsightPanel";
import type { Senior, TimelineItem } from "@/lib/types";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { StatusDot } from "@/components/ui/StatusDot";
import { ActionButton } from "@/components/ui/ActionButton";
import { riskColor } from "@/lib/risk";

interface Props {
  senior: Senior;
  timeline: TimelineItem[];
}

function TimelineItemRow({ item }: { item: TimelineItem }) {
  const iconProps = { size: 14, className: "shrink-0 mt-0.5" };
  const icons = {
    success: <CheckCircle {...iconProps} style={{ color: "#22C55E" }} />,
    missed:  <XCircle    {...iconProps} style={{ color: "#EF4444" }} />,
    info:    <Info       {...iconProps} style={{ color: "#1267D8" }} />,
  };
  const icon = icons[item.status ?? "info"];

  return (
    <div
      className="flex gap-3 py-3 transition-interactive"
      style={{ borderBottom: "1px solid #F8FAFC" }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#FAFBFC"; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}
    >
      <div className="mt-0.5 shrink-0">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2">
          <span className="font-medium" style={{ fontSize: 13, color: "#071D3A" }}>
            {item.title}
          </span>
          <span className="tabular shrink-0" style={{ fontSize: 11.5, color: "#94A8BC" }}>
            {item.time}
          </span>
        </div>
        {item.description && (
          <p className="mt-0.5" style={{ fontSize: 12.5, color: "#667085", lineHeight: 1.5 }}>
            {item.description}
          </p>
        )}
        <span style={{ fontSize: 10.5, color: "#94A8BC" }}>{item.date}</span>
      </div>
    </div>
  );
}

const CARD_SHADOW = "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

function ProfileRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="shrink-0 mt-0.5" style={{ color: "#94A8BC" }}>{icon}</div>
      <div>
        <p className="label-caps mb-0.5">{label}</p>
        <div style={{ fontSize: 13, color: "#071D3A", lineHeight: 1.5 }}>{value}</div>
      </div>
    </div>
  );
}

export function SeniorDetailView({ senior, timeline }: Props) {
  return (
    <div className="overflow-auto h-full">
      {/* Breadcrumb */}
      <div
        className="px-6 py-3 flex items-center"
        style={{ background: "white", borderBottom: "1px solid #F1F5F9" }}
      >
        <Link
          href="/seniors"
          className="flex items-center gap-1 transition-interactive hover:text-brand-blue"
          style={{ fontSize: 13, color: "#667085", fontWeight: 500 }}
        >
          <ChevronLeft size={14} />
          Back to Seniors
        </Link>
      </div>

      {/* Header */}
      <div className="px-6 pt-5 pb-5" style={{ background: "white", borderBottom: "1px solid #E8EDF3" }}>
        {/* Name + badges */}
        <div className="flex items-center gap-3 mb-5">
          <h1
            className="font-bold"
            style={{ fontSize: 24, color: "#071D3A", letterSpacing: "-0.04em" }}
          >
            {senior.name}
          </h1>
          <RiskBadge risk={senior.heatRisk} />
          <span
            className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-[3px] font-medium"
            style={{
              fontSize: 11.5,
              background: "#EFF6FF",
              color: "#1267D8",
              border: "1px solid #BFDBFE",
            }}
          >
            <StatusDot status={senior.status} size={6} />
            {senior.status}
          </span>
        </div>

        {/* Metric strip */}
        <div className="flex items-stretch divide-x" style={{ borderColor: "#E8EDF3" }}>
          {[
            {
              label: "Current Heat Risk",
              value: (
                <span className="font-semibold" style={{ color: riskColor(senior.heatRisk) }}>
                  {senior.heatRisk}
                </span>
              ),
            },
            {
              label: "Latest Check-In",
              value: <span className="tabular">{senior.latestCheckIn ?? "—"}</span>,
            },
            {
              label: "Assigned Support",
              value: <span>{senior.assignedCaregiver ?? "—"}</span>,
            },
            {
              label: "Recommended Action",
              value: senior.recommendedAction ? (
                <ActionButton variant="warning" size="sm">{senior.recommendedAction}</ActionButton>
              ) : (
                <span style={{ color: "#94A8BC" }}>None</span>
              ),
            },
          ].map(({ label, value }) => (
            <div key={label} className="flex-1 px-5 first:pl-0">
              <p className="label-caps mb-1">{label}</p>
              <div style={{ fontSize: 13, color: "#071D3A" }}>{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Body */}
      <div className="flex gap-5 p-6">
        {/* Left: Timeline */}
        <div className="flex-1 min-w-0 space-y-4">
          <OperatorActionQueue senior={senior} />

          <ConversationInsightPanel senior={senior} />

          <div className="rounded-xl overflow-hidden" style={{ background: "white", boxShadow: CARD_SHADOW }}>
            <div className="px-5 py-4" style={{ borderBottom: "1px solid #F1F5F9" }}>
              <h2 className="font-semibold" style={{ fontSize: 13.5, color: "#071D3A", letterSpacing: "-0.01em" }}>
                Recent Activity
              </h2>
            </div>
            <div className="px-5">
              {timeline.map((item) => (
                <TimelineItemRow key={item.id} item={item} />
              ))}
            </div>
            <div className="px-5 py-3.5">
              <button
                className="transition-interactive hover:text-brand-blue"
                style={{ fontSize: 12.5, color: "#1267D8", fontWeight: 500 }}
              >
                View full activity history →
              </button>
            </div>
          </div>
        </div>

        {/* Right: Profile + Actions */}
        <div className="w-[272px] shrink-0 space-y-4">
          {/* Profile */}
          <div className="rounded-xl overflow-hidden" style={{ background: "white", boxShadow: CARD_SHADOW }}>
            <div className="px-5 py-4" style={{ borderBottom: "1px solid #F1F5F9" }}>
              <h2 className="font-semibold" style={{ fontSize: 13.5, color: "#071D3A" }}>
                Senior Profile
              </h2>
            </div>
            <div className="px-5 py-4 space-y-4">
              {senior.phone && (
                <ProfileRow
                  icon={<Phone size={13} />}
                  label="Phone"
                  value={<span className="font-medium tabular">{senior.phone}</span>}
                />
              )}
              {senior.address && (
                <ProfileRow
                  icon={<MapPin size={13} />}
                  label="Address"
                  value={<span className="font-medium">{senior.address}</span>}
                />
              )}
              {senior.preferredContactTime && (
                <ProfileRow
                  icon={<Clock size={13} />}
                  label="Contact Window"
                  value={<span className="font-medium tabular">{senior.preferredContactTime}</span>}
                />
              )}
              {senior.medicalNotes && (
                <ProfileRow
                  icon={<Heart size={13} />}
                  label="Medical Notes"
                  value={senior.medicalNotes}
                />
              )}
              {senior.emergencyContact && (
                <ProfileRow
                  icon={<User size={13} />}
                  label="Emergency Contact"
                  value={<span className="font-medium">{senior.emergencyContact}</span>}
                />
              )}

              {/* Support Network */}
              {(senior.supportMode || senior.livingSituation) && (
                <div
                  className="pt-4 mt-1 space-y-3"
                  style={{ borderTop: "1px solid #F1F5F9" }}
                >
                  <p className="label-caps">Support Network</p>

                  {senior.livingSituation && (
                    <ProfileRow
                      icon={<Home size={13} />}
                      label="Living Situation"
                      value={<span className="font-medium">{senior.livingSituation}</span>}
                    />
                  )}
                  {senior.supportMode && (
                    <ProfileRow
                      icon={<ShieldCheck size={13} />}
                      label="Support Mode"
                      value={<span className="font-medium">{senior.supportMode}</span>}
                    />
                  )}
                  <div
                    className="rounded-lg px-3 py-2"
                    style={{
                      background: senior.hasSupportContact === false ? "#FEF2F2" : "#F8FAFC",
                      color: senior.hasSupportContact === false ? "#B42318" : "#667085",
                      border: senior.hasSupportContact === false ? "1px solid #FECACA" : "1px solid #E8EDF3",
                      fontSize: 12,
                      lineHeight: 1.5,
                    }}
                  >
                    {senior.hasSupportContact === false
                      ? "No support contact listed."
                      : `${senior.supportContactCount ?? 0} support contact${senior.supportContactCount === 1 ? "" : "s"} on file.`}
                  </div>
                  {senior.escalationPlanSummary && (
                    <p style={{ fontSize: 12, color: "#667085", lineHeight: 1.5 }}>
                      <span className="font-medium">Escalation: </span>
                      {senior.escalationPlanSummary}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
          
          <DemographicsEditor senior={senior} />

          <HeatSettingsEditor senior={senior} />

          <SupportNetworkEditor senior={senior} />

          <SeniorActionPanel senior={senior} />
        </div>
      </div>
    </div>
  );
}
