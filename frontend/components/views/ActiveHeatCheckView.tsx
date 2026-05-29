"use client";

import { useState } from "react";
import { MapPin, Thermometer, Clock, Mic, Hash, PhoneOff, CheckSquare } from "lucide-react";
import type { HeatCheck, TranscriptLine } from "@/lib/types";
import { riskColor } from "@/lib/risk";

interface Props {
  heatCheck: HeatCheck;
}

function RiskDots({
  level,
  max = 5,
  color,
}: {
  level: number;
  max?: number;
  color: string;
}) {
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: max }).map((_, i) => (
        <span
          key={i}
          className="rounded-full"
          style={{
            display: "inline-block",
            width: 8,
            height: 8,
            background: i < level ? color : "#D8E0EA",
          }}
        />
      ))}
    </div>
  );
}

function levelIndex(label: string): number {
  const map: Record<string, number> = {
    Normal: 1,
    Low: 1,
    Elevated: 3,
    High: 5,
  };
  return map[label] ?? 1;
}

function TranscriptMessage({ line }: { line: TranscriptLine }) {
  const isAgent = line.speaker === "Agent";
  return (
    <div className={`flex gap-3 mb-3 ${isAgent ? "" : "pl-8"}`}>
      {isAgent && (
        <div
          className="flex items-center justify-center rounded-full text-white text-xs font-bold shrink-0"
          style={{ width: 28, height: 28, background: "#1267D8" }}
        >
          A
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-xs font-semibold" style={{ color: "#071D3A" }}>
            {line.name}
          </span>
          <span className="text-xs" style={{ color: "#8FA8C8" }}>
            {line.time}
          </span>
        </div>
        <p
          className="text-sm rounded-lg px-3 py-2 inline-block"
          style={{
            background: isAgent ? "#F0F7FF" : "#F8FAFC",
            color: "#071D3A",
            border: isAgent ? "1px solid #BFDBFE" : "1px solid #E8EDF3",
            lineHeight: 1.5,
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

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Call header */}
      <div
        className="flex items-center justify-between px-6 py-4 shrink-0 border-b"
        style={{ background: "white", borderColor: "#D8E0EA" }}
      >
        {/* Senior info */}
        <div className="flex items-center gap-3">
          <div
            className="flex items-center justify-center rounded-full text-white font-bold text-sm shrink-0"
            style={{ width: 44, height: 44, background: "#1267D8" }}
          >
            {heatCheck.seniorName
              .split(" ")
              .map((n) => n[0])
              .join("")}
          </div>
          <div>
            <p className="font-semibold text-base" style={{ color: "#071D3A" }}>
              {heatCheck.seniorName}
            </p>
            <div className="flex items-center gap-3 mt-0.5">
              <span className="text-xs" style={{ color: "#667085" }}>
                {heatCheck.phone}
              </span>
              <span className="text-xs" style={{ color: "#667085" }}>
                {heatCheck.location}
              </span>
            </div>
          </div>
        </div>

        {/* Call duration */}
        <div className="text-center">
          <p className="text-3xl font-bold font-mono" style={{ color: "#071D3A" }}>
            {heatCheck.callDuration}
          </p>
          <div className="flex items-center justify-center gap-1.5 mt-0.5">
            <span
              className="rounded-full"
              style={{
                display: "inline-block",
                width: 6,
                height: 6,
                background: "#22C55E",
                animation: "pulse 2s infinite",
              }}
            />
            <span className="text-xs font-medium" style={{ color: "#22C55E" }}>
              Live
            </span>
          </div>
        </div>

        {/* Call controls */}
        <div className="flex items-center gap-2">
          {[
            { label: "Mute", icon: <Mic size={16} /> },
            { label: "Keypad", icon: <Hash size={16} /> },
          ].map(({ label, icon }) => (
            <button
              key={label}
              className="flex flex-col items-center gap-1 rounded-lg px-4 py-2 transition-colors hover:bg-gray-100"
              style={{ border: "1px solid #D8E0EA", color: "#667085" }}
            >
              {icon}
              <span style={{ fontSize: 10 }}>{label}</span>
            </button>
          ))}
          <button
            className="flex flex-col items-center gap-1 rounded-lg px-4 py-2 text-white transition-colors"
            style={{ background: "#E52920" }}
          >
            <PhoneOff size={16} />
            <span style={{ fontSize: 10 }}>End Call</span>
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-1 min-h-0 gap-0">
        {/* Live Transcript */}
        <div className="flex flex-col flex-1 min-w-0 border-r" style={{ borderColor: "#D8E0EA" }}>
          <div
            className="px-5 py-3 border-b flex items-center gap-2 shrink-0"
            style={{ borderColor: "#D8E0EA", background: "white" }}
          >
            <h2 className="font-semibold text-sm" style={{ color: "#071D3A" }}>
              Live Transcript
            </h2>
            <span
              className="flex items-center gap-1 text-xs font-medium rounded-full px-2 py-0.5"
              style={{ background: "#DCFCE7", color: "#16A34A" }}
            >
              <span
                className="rounded-full"
                style={{ width: 5, height: 5, background: "#22C55E", display: "inline-block" }}
              />
              Live
            </span>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-4">
            {heatCheck.transcript.map((line, i) => (
              <TranscriptMessage key={i} line={line} />
            ))}
            <p className="text-xs mt-4 text-center" style={{ color: "#8FA8C8" }}>
              Transcribing audio...
            </p>
          </div>

          {/* Footer metrics */}
          <div
            className="flex items-center gap-6 px-5 py-3 shrink-0 border-t"
            style={{ borderColor: "#D8E0EA", background: "#F8FAFC" }}
          >
            {[
              { icon: <MapPin size={12} />, label: heatCheck.location },
              { icon: <Thermometer size={12} />, label: heatCheck.weather ?? "—" },
              { icon: <Clock size={12} />, label: heatCheck.lastCheckIn ?? "—" },
            ].map(({ icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-1.5 text-xs"
                style={{ color: "#667085" }}
              >
                {icon}
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel */}
        <div className="w-80 shrink-0 flex flex-col overflow-y-auto" style={{ background: "#F8FAFC" }}>
          {/* Live Risk Summary */}
          <div className="px-5 pt-5 pb-4 border-b" style={{ borderColor: "#D8E0EA" }}>
            <h2
              className="font-semibold text-xs uppercase tracking-wider mb-4"
              style={{ color: "#667085" }}
            >
              Live Risk Summary
            </h2>

            <div className="space-y-4">
              {/* Hydration */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium" style={{ color: "#071D3A" }}>
                    Hydration Concern
                  </span>
                  <span
                    className="text-xs font-semibold"
                    style={{ color: riskColor(riskSummary.hydrationConcern as "Low") }}
                  >
                    {riskSummary.hydrationConcern}
                  </span>
                </div>
                <RiskDots
                  level={levelIndex(riskSummary.hydrationConcern)}
                  color={riskColor(
                    riskSummary.hydrationConcern === "High"
                      ? "Extreme"
                      : riskSummary.hydrationConcern === "Elevated"
                      ? "High"
                      : "Low"
                  )}
                />
              </div>

              {/* Confusion */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium" style={{ color: "#071D3A" }}>
                    Confusion Indicator
                  </span>
                  <span
                    className="text-xs font-semibold"
                    style={{ color: riskColor(riskSummary.confusionIndicator as "Low") }}
                  >
                    {riskSummary.confusionIndicator}
                  </span>
                </div>
                <RiskDots
                  level={levelIndex(riskSummary.confusionIndicator)}
                  color={riskColor(
                    riskSummary.confusionIndicator === "High"
                      ? "Extreme"
                      : riskSummary.confusionIndicator === "Elevated"
                      ? "High"
                      : "Low"
                  )}
                />
              </div>

              {/* Heat Risk Score */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium" style={{ color: "#071D3A" }}>
                    Current Heat Risk Score
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div
                    className="flex items-center justify-center rounded-full font-bold text-white"
                    style={{
                      width: 52,
                      height: 52,
                      background: riskColor(riskSummary.currentHeatRisk),
                      fontSize: 18,
                    }}
                  >
                    {riskSummary.score}
                  </div>
                  <div>
                    <span
                      className="text-lg font-bold"
                      style={{ color: riskColor(riskSummary.currentHeatRisk) }}
                    >
                      {riskSummary.currentHeatRisk}
                    </span>
                    <p className="text-xs" style={{ color: "#667085" }}>
                      out of 10
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Recommended Next Action */}
          <div className="px-5 py-4 border-b" style={{ borderColor: "#D8E0EA" }}>
            <h2
              className="font-semibold text-xs uppercase tracking-wider mb-3"
              style={{ color: "#667085" }}
            >
              Recommended Next Action
            </h2>
            <div
              className="rounded-lg p-3 flex items-start gap-2"
              style={{
                background: "#FFF7ED",
                border: "1px solid #FED7AA",
              }}
            >
              <span style={{ fontSize: 16 }}>⚠️</span>
              <div>
                <p className="text-sm font-semibold" style={{ color: "#92400E" }}>
                  {heatCheck.recommendedAction ?? "Dispatch wellness check"}
                </p>
                <p className="text-xs mt-0.5" style={{ color: "#B45309" }}>
                  High hydration concern with elevated heat conditions.
                </p>
              </div>
            </div>
          </div>

          {/* Suggested Talking Points */}
          <div className="px-5 py-4 border-b" style={{ borderColor: "#D8E0EA" }}>
            <h2
              className="font-semibold text-xs uppercase tracking-wider mb-3"
              style={{ color: "#667085" }}
            >
              Suggested Talking Points
            </h2>
            <ul className="space-y-2">
              {TALKING_POINTS.map((pt) => (
                <li key={pt} className="flex items-start gap-2 text-xs" style={{ color: "#071D3A" }}>
                  <CheckSquare size={13} className="shrink-0 mt-0.5" style={{ color: "#22C7C9" }} />
                  {pt}
                </li>
              ))}
            </ul>
          </div>

          {/* Notes */}
          <div className="px-5 py-4">
            <h2
              className="font-semibold text-xs uppercase tracking-wider mb-2"
              style={{ color: "#667085" }}
            >
              Notes
            </h2>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about this call…"
              rows={4}
              className="w-full rounded border text-sm px-3 py-2 outline-none resize-none focus:border-teal transition-colors"
              style={{
                borderColor: "#D8E0EA",
                background: "white",
                color: "#071D3A",
                fontSize: 13,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
