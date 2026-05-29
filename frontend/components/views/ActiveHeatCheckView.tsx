"use client";

import { useState } from "react";
import { MapPin, Thermometer, Clock, Mic, Hash, PhoneOff, CheckSquare, AlertTriangle } from "lucide-react";
import type { HeatCheck, TranscriptLine } from "@/lib/types";
import { riskColor } from "@/lib/risk";

interface Props { heatCheck: HeatCheck }

function RiskDots({ level, max = 5, color }: { level: number; max?: number; color: string }) {
  return (
    <div className="flex items-center gap-1.5">
      {Array.from({ length: max }).map((_, i) => (
        <span
          key={i}
          className="rounded-full transition-interactive"
          style={{
            display: "inline-block",
            width: 7, height: 7,
            background: i < level ? color : "#E8EDF3",
          }}
        />
      ))}
    </div>
  );
}

function levelIndex(label: string): number {
  return ({ Normal: 1, Low: 1, Elevated: 3, High: 5 } as Record<string, number>)[label] ?? 1;
}

function mapHydration(v: string) {
  if (v === "High") return "Extreme";
  if (v === "Elevated") return "High";
  return "Low";
}

function TranscriptMessage({ line }: { line: TranscriptLine }) {
  const isAgent = line.speaker === "Agent";
  return (
    <div className={`flex gap-3 mb-4 ${isAgent ? "" : "pl-10"}`}>
      {isAgent && (
        <div
          className="flex items-center justify-center rounded-full text-white font-bold shrink-0"
          style={{
            width: 28, height: 28,
            background: "linear-gradient(135deg, #1267D8, #0E51B0)",
            fontSize: 11,
            boxShadow: "0 1px 3px rgba(18,103,216,0.25)",
          }}
        >
          A
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2 mb-1.5">
          <span className="font-semibold" style={{ fontSize: 12, color: "#071D3A" }}>{line.name}</span>
          <span className="tabular" style={{ fontSize: 11, color: "#94A8BC" }}>{line.time}</span>
        </div>
        <p
          className="rounded-xl"
          style={{
            display: "inline-block",
            padding: "8px 12px",
            background: isAgent ? "#F0F7FF" : "white",
            color: "#071D3A",
            border: isAgent ? "1px solid #BFDBFE" : "1px solid #E8EDF3",
            boxShadow: "0 1px 2px rgba(7,29,58,0.04)",
            fontSize: 13,
            lineHeight: 1.55,
            maxWidth: "88%",
          }}
        >
          {line.text}
        </p>
      </div>
    </div>
  );
}

const TALKING_POINTS = [
  "Encourage water intake now",
  "Ask if A/C is working",
  "Check if they're with others",
  "Offer to stay on the line while they get water",
];

export function ActiveHeatCheckView({ heatCheck }: Props) {
  const [notes, setNotes] = useState("");
  const { riskSummary } = heatCheck;
  const initials = heatCheck.seniorName.split(" ").map((n) => n[0]).join("");

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Call header */}
      <div
        className="flex items-center justify-between px-6 py-4 shrink-0"
        style={{ background: "white", borderBottom: "1px solid #E8EDF3", boxShadow: "0 1px 0 #F1F5F9" }}
      >
        {/* Senior info */}
        <div className="flex items-center gap-3">
          <div
            className="flex items-center justify-center rounded-full text-white font-bold shrink-0"
            style={{
              width: 44, height: 44,
              background: "linear-gradient(135deg, #1267D8, #0E51B0)",
              fontSize: 14,
              boxShadow: "0 2px 6px rgba(18,103,216,0.28)",
            }}
          >
            {initials}
          </div>
          <div>
            <p className="font-semibold" style={{ fontSize: 15, color: "#071D3A", letterSpacing: "-0.02em" }}>
              {heatCheck.seniorName}
            </p>
            <div className="flex items-center gap-3 mt-0.5">
              <span className="tabular" style={{ fontSize: 12, color: "#667085" }}>{heatCheck.phone}</span>
              <span className="text-xs" style={{ color: "#94A8BC" }}>·</span>
              <span style={{ fontSize: 12, color: "#667085" }}>{heatCheck.location}</span>
            </div>
          </div>
        </div>

        {/* Duration */}
        <div className="text-center">
          <p
            className="font-bold tabular font-data"
            style={{ fontSize: 30, color: "#071D3A", letterSpacing: "-0.04em" }}
          >
            {heatCheck.callDuration}
          </p>
          <div className="flex items-center justify-center gap-1.5 mt-1">
            <span
              className="rounded-full animate-pulse"
              style={{ display: "inline-block", width: 6, height: 6, background: "#22C55E" }}
            />
            <span className="font-semibold" style={{ fontSize: 11, color: "#22C55E" }}>Live</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          {[
            { label: "Mute",   icon: <Mic    size={15} /> },
            { label: "Keypad", icon: <Hash   size={15} /> },
          ].map(({ label, icon }) => (
            <button
              key={label}
              className="flex flex-col items-center gap-1 rounded-lg px-4 py-2 transition-interactive"
              style={{
                border: "1px solid #E2E8F0",
                color: "#667085",
                background: "white",
                cursor: "pointer",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#F8FAFC"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "white"; }}
            >
              {icon}
              <span style={{ fontSize: 10, fontWeight: 500 }}>{label}</span>
            </button>
          ))}
          <button
            className="flex flex-col items-center gap-1 rounded-lg px-4 py-2 text-white transition-interactive"
            style={{ background: "#E52920", cursor: "pointer" }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#C8221A"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "#E52920"; }}
          >
            <PhoneOff size={15} />
            <span style={{ fontSize: 10, fontWeight: 500 }}>End Call</span>
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {/* Transcript panel */}
        <div
          className="flex flex-col flex-1 min-w-0"
          style={{ borderRight: "1px solid #E8EDF3" }}
        >
          <div
            className="px-5 py-3 flex items-center gap-2 shrink-0"
            style={{ background: "white", borderBottom: "1px solid #F1F5F9" }}
          >
            <h2 className="font-semibold" style={{ fontSize: 13, color: "#071D3A" }}>
              Live Transcript
            </h2>
            <span
              className="flex items-center gap-1 rounded-full px-2 py-0.5 font-semibold"
              style={{ background: "#DCFCE7", color: "#16A34A", fontSize: 10.5 }}
            >
              <span className="rounded-full animate-pulse" style={{ display: "inline-block", width: 5, height: 5, background: "#22C55E" }} />
              Live
            </span>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-5">
            {heatCheck.transcript.map((line, i) => (
              <TranscriptMessage key={i} line={line} />
            ))}
            <p className="text-center mt-2" style={{ fontSize: 11.5, color: "#94A8BC" }}>
              Transcribing audio…
            </p>
          </div>

          {/* Footer */}
          <div
            className="flex items-center gap-5 px-5 py-3 shrink-0"
            style={{ borderTop: "1px solid #F1F5F9", background: "#FAFBFC" }}
          >
            {[
              { icon: <MapPin size={11} />,      label: heatCheck.location },
              { icon: <Thermometer size={11} />, label: heatCheck.weather ?? "—" },
              { icon: <Clock size={11} />,       label: heatCheck.lastCheckIn ?? "—" },
            ].map(({ icon, label }) => (
              <div key={label} className="flex items-center gap-1.5" style={{ fontSize: 12, color: "#667085" }}>
                {icon}
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel */}
        <div
          className="w-80 shrink-0 flex flex-col overflow-y-auto"
          style={{ background: "#F8FAFC" }}
        >
          {/* Risk Summary */}
          <div className="px-5 pt-5 pb-4" style={{ borderBottom: "1px solid #E8EDF3" }}>
            <p className="label-caps mb-4">Live Risk Summary</p>

            <div className="space-y-4">
              {[
                {
                  label: "Hydration Concern",
                  levelLabel: riskSummary.hydrationConcern,
                  dots: levelIndex(riskSummary.hydrationConcern),
                  color: riskColor(mapHydration(riskSummary.hydrationConcern) as "Low"),
                },
                {
                  label: "Confusion Indicator",
                  levelLabel: riskSummary.confusionIndicator,
                  dots: levelIndex(riskSummary.confusionIndicator),
                  color: riskColor(mapHydration(riskSummary.confusionIndicator) as "Low"),
                },
              ].map(({ label, levelLabel, dots, color }) => (
                <div key={label}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium" style={{ fontSize: 12.5, color: "#071D3A" }}>{label}</span>
                    <span className="font-semibold" style={{ fontSize: 11.5, color }}>{levelLabel}</span>
                  </div>
                  <RiskDots level={dots} color={color} />
                </div>
              ))}

              {/* Heat Risk Score */}
              <div>
                <p className="label-caps mb-2.5">Current Heat Risk Score</p>
                <div className="flex items-center gap-3">
                  <div
                    className="flex items-center justify-center rounded-full font-bold text-white shrink-0"
                    style={{
                      width: 52, height: 52,
                      background: riskColor(riskSummary.currentHeatRisk),
                      fontSize: 18,
                      fontFamily: '"DM Mono", monospace',
                      boxShadow: `0 2px 8px ${riskColor(riskSummary.currentHeatRisk)}50`,
                    }}
                  >
                    {riskSummary.score}
                  </div>
                  <div>
                    <div
                      className="font-bold"
                      style={{ fontSize: 18, color: riskColor(riskSummary.currentHeatRisk), letterSpacing: "-0.02em" }}
                    >
                      {riskSummary.currentHeatRisk}
                    </div>
                    <p style={{ fontSize: 11, color: "#94A8BC" }}>out of 10</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Recommended Action */}
          <div className="px-5 py-4" style={{ borderBottom: "1px solid #E8EDF3" }}>
            <p className="label-caps mb-3">Recommended Next Action</p>
            <div
              className="rounded-xl p-3 flex items-start gap-2.5"
              style={{ background: "#FFF7ED", border: "1px solid #FED7AA" }}
            >
              <AlertTriangle size={14} className="shrink-0 mt-0.5" style={{ color: "#F59E0B" }} />
              <div>
                <p className="font-semibold" style={{ fontSize: 12.5, color: "#92400E" }}>
                  {heatCheck.recommendedAction ?? "Dispatch wellness check"}
                </p>
                <p className="mt-0.5" style={{ fontSize: 11.5, color: "#B45309" }}>
                  High hydration concern with elevated heat conditions.
                </p>
              </div>
            </div>
          </div>

          {/* Talking Points */}
          <div className="px-5 py-4" style={{ borderBottom: "1px solid #E8EDF3" }}>
            <p className="label-caps mb-3">Suggested Talking Points</p>
            <ul className="space-y-2.5">
              {TALKING_POINTS.map((pt) => (
                <li key={pt} className="flex items-start gap-2" style={{ fontSize: 12.5, color: "#374151" }}>
                  <CheckSquare size={13} className="shrink-0 mt-0.5" style={{ color: "#22C7C9" }} />
                  {pt}
                </li>
              ))}
            </ul>
          </div>

          {/* Notes */}
          <div className="px-5 py-4">
            <p className="label-caps mb-2">Notes</p>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about this call…"
              rows={4}
              className="w-full rounded-lg px-3 py-2 resize-none"
              style={{
                border: "1px solid #E2E8F0",
                background: "white",
                color: "#071D3A",
                fontSize: 12.5,
                fontFamily: "inherit",
                boxShadow: "var(--shadow-xs)",
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
