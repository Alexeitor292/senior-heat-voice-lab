"use client";

import Link from "next/link";
import {
  ChevronLeft,
  MapPin,
  Clock,
  User,
  Phone,
  FileText,
  Heart,
  PhoneCall,
  MessageSquare,
  CheckCircle,
  XCircle,
  Info,
} from "lucide-react";
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
    missed: <XCircle {...iconProps} style={{ color: "#EF4444" }} />,
    info: <Info {...iconProps} style={{ color: "#1267D8" }} />,
  };
  const icon = icons[item.status ?? "info"];

  return (
    <div className="flex gap-3 py-3" style={{ borderBottom: "1px solid #F1F5F9" }}>
      <div className="mt-0.5">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2">
          <span className="font-medium text-sm" style={{ color: "#071D3A" }}>
            {item.title}
          </span>
          <span className="text-xs shrink-0" style={{ color: "#8FA8C8" }}>
            {item.time}
          </span>
        </div>
        {item.description && (
          <p className="text-xs mt-0.5" style={{ color: "#667085" }}>
            {item.description}
          </p>
        )}
        <span className="text-xs" style={{ color: "#8FA8C8", fontSize: 10 }}>
          {item.date}
        </span>
      </div>
    </div>
  );
}

export function SeniorDetailView({ senior, timeline }: Props) {
  return (
    <div className="overflow-auto h-full">
      {/* Back breadcrumb */}
      <div
        className="px-6 py-3 border-b flex items-center"
        style={{ background: "white", borderColor: "#D8E0EA" }}
      >
        <Link
          href="/seniors"
          className="flex items-center gap-1 text-sm hover:underline"
          style={{ color: "#1267D8" }}
        >
          <ChevronLeft size={14} />
          Back to Seniors
        </Link>
      </div>

      {/* Header */}
      <div
        className="px-6 py-5 border-b"
        style={{ background: "white", borderColor: "#D8E0EA" }}
      >
        {/* Name + badges */}
        <div className="flex items-center gap-3 mb-4">
          <h1 className="font-bold text-2xl" style={{ color: "#071D3A" }}>
            {senior.name}
          </h1>
          <RiskBadge risk={senior.heatRisk} />
          <span
            className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium"
            style={{ background: "#EFF6FF", color: "#1267D8", border: "1px solid #BFDBFE" }}
          >
            <StatusDot status={senior.status} size={6} />
            {senior.status}
          </span>
        </div>

        {/* Sub-header metrics */}
        <div className="flex items-stretch gap-0 divide-x" style={{ borderColor: "#D8E0EA" }}>
          {[
            {
              label: "Current Heat Risk",
              value: (
                <span style={{ color: riskColor(senior.heatRisk), fontWeight: 600 }}>
                  {senior.heatRisk}
                </span>
              ),
            },
            {
              label: "Latest Check-In",
              value: <span style={{ color: "#071D3A" }}>{senior.latestCheckIn ?? "—"}</span>,
            },
            {
              label: "Assigned Caregiver",
              value: (
                <span style={{ color: "#071D3A" }}>{senior.assignedCaregiver ?? "—"}</span>
              ),
            },
            {
              label: "Recommended Action",
              value: senior.recommendedAction ? (
                <ActionButton variant="warning" size="sm">
                  {senior.recommendedAction}
                </ActionButton>
              ) : (
                <span style={{ color: "#667085" }}>None</span>
              ),
            },
          ].map(({ label, value }) => (
            <div key={label} className="flex-1 px-5 py-0 first:pl-0">
              <p className="text-xs mb-1" style={{ color: "#667085" }}>
                {label}
              </p>
              <div className="text-sm">{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Main 2-col layout */}
      <div className="flex gap-6 p-6">
        {/* Left: Recent Activity */}
        <div className="flex-1 min-w-0">
          <div
            className="rounded-lg"
            style={{ background: "white", border: "1px solid #D8E0EA" }}
          >
            <div
              className="px-5 py-4 border-b"
              style={{ borderColor: "#D8E0EA" }}
            >
              <h2 className="font-semibold text-sm" style={{ color: "#071D3A" }}>
                Recent Activity
              </h2>
            </div>
            <div className="px-5">
              {timeline.map((item) => (
                <TimelineItemRow key={item.id} item={item} />
              ))}
            </div>
            <div className="px-5 py-3">
              <button
                className="text-xs hover:underline"
                style={{ color: "#1267D8" }}
              >
                View full activity history →
              </button>
            </div>
          </div>
        </div>

        {/* Right: Profile + Actions */}
        <div className="w-72 shrink-0 space-y-4">
          {/* Senior Profile */}
          <div
            className="rounded-lg"
            style={{ background: "white", border: "1px solid #D8E0EA" }}
          >
            <div
              className="px-5 py-4 border-b"
              style={{ borderColor: "#D8E0EA" }}
            >
              <h2 className="font-semibold text-sm" style={{ color: "#071D3A" }}>
                Senior Profile
              </h2>
            </div>
            <div className="px-5 py-4 space-y-3">
              {senior.phone && (
                <div className="flex items-start gap-3">
                  <Phone size={13} className="shrink-0 mt-0.5" style={{ color: "#667085" }} />
                  <div>
                    <p className="text-xs" style={{ color: "#667085" }}>
                      Phone
                    </p>
                    <p className="text-sm font-medium" style={{ color: "#071D3A" }}>
                      {senior.phone}
                    </p>
                  </div>
                </div>
              )}
              {senior.address && (
                <div className="flex items-start gap-3">
                  <MapPin size={13} className="shrink-0 mt-0.5" style={{ color: "#667085" }} />
                  <div>
                    <p className="text-xs" style={{ color: "#667085" }}>
                      Address
                    </p>
                    <p className="text-sm font-medium" style={{ color: "#071D3A" }}>
                      {senior.address}
                    </p>
                  </div>
                </div>
              )}
              {senior.preferredContactTime && (
                <div className="flex items-start gap-3">
                  <Clock size={13} className="shrink-0 mt-0.5" style={{ color: "#667085" }} />
                  <div>
                    <p className="text-xs" style={{ color: "#667085" }}>
                      Preferred Contact Time
                    </p>
                    <p className="text-sm font-medium" style={{ color: "#071D3A" }}>
                      {senior.preferredContactTime}
                    </p>
                  </div>
                </div>
              )}
              {senior.medicalNotes && (
                <div className="flex items-start gap-3">
                  <Heart size={13} className="shrink-0 mt-0.5" style={{ color: "#667085" }} />
                  <div>
                    <p className="text-xs" style={{ color: "#667085" }}>
                      Medical Notes
                    </p>
                    <p className="text-sm" style={{ color: "#071D3A" }}>
                      {senior.medicalNotes}
                    </p>
                  </div>
                </div>
              )}
              {senior.emergencyContact && (
                <div className="flex items-start gap-3">
                  <User size={13} className="shrink-0 mt-0.5" style={{ color: "#667085" }} />
                  <div>
                    <p className="text-xs" style={{ color: "#667085" }}>
                      Emergency Contact
                    </p>
                    <p className="text-sm" style={{ color: "#071D3A" }}>
                      {senior.emergencyContact}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Take Action */}
          <div
            className="rounded-lg p-5 space-y-2.5"
            style={{ background: "white", border: "1px solid #D8E0EA" }}
          >
            <h2 className="font-semibold text-sm mb-3" style={{ color: "#071D3A" }}>
              Take Action
            </h2>
            <ActionButton variant="secondary" size="sm" className="w-full justify-center gap-2">
              <PhoneCall size={13} />
              Call Senior
            </ActionButton>
            <ActionButton variant="secondary" size="sm" className="w-full justify-center gap-2">
              <MessageSquare size={13} />
              Message Caregiver
            </ActionButton>
            <ActionButton variant="warning" size="sm" className="w-full justify-center gap-2">
              <FileText size={13} />
              Dispatch Wellness Check
            </ActionButton>
          </div>
        </div>
      </div>
    </div>
  );
}
