"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Brain,
  HeartPulse,
  Lightbulb,
  RefreshCw,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import { getConversationInsights } from "@/lib/api";
import type { ConversationInsight, Senior } from "@/lib/types";

const CARD_SHADOW =
  "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

function formatLabel(value?: string | null): string {
  if (!value) return "Unknown";

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatConfidence(value?: number | null): string {
  if (value === null || value === undefined) return "—";

  return `${Math.round(value * 100)}%`;
}

function formatDateTime(value?: string | null): string {
  if (!value) return "Unknown time";

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return "Unknown time";
  }

  return parsed.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function riskStyle(risk: string): React.CSSProperties {
  const normalized = risk.toLowerCase();

  if (normalized === "red" || normalized === "urgent") {
    return {
      background: "#FEF2F2",
      color: "#B42318",
      border: "1px solid #FECACA",
    };
  }

  if (normalized === "orange" || normalized === "high") {
    return {
      background: "#FFF7ED",
      color: "#B45309",
      border: "1px solid #FED7AA",
    };
  }

  if (normalized === "yellow" || normalized === "medium") {
    return {
      background: "#FEFCE8",
      color: "#A16207",
      border: "1px solid #FEF08A",
    };
  }

  if (normalized === "green" || normalized === "low") {
    return {
      background: "#F0FDF4",
      color: "#166534",
      border: "1px solid #BBF7D0",
    };
  }

  return {
    background: "#F8FAFC",
    color: "#667085",
    border: "1px solid #E2E8F0",
  };
}

function moodStyle(value: string): React.CSSProperties {
  const normalized = value.toLowerCase();

  if (normalized === "low" || normalized === "elevated") {
    return {
      background: "#FDF2F8",
      color: "#BE185D",
      border: "1px solid #FBCFE8",
    };
  }

  if (normalized === "tired") {
    return {
      background: "#FFF7ED",
      color: "#B45309",
      border: "1px solid #FED7AA",
    };
  }

  return {
    background: "#EFF6FF",
    color: "#1267D8",
    border: "1px solid #BFDBFE",
  };
}

function Pill({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <span
      className="rounded-full px-2 py-[3px] font-semibold"
      style={{
        fontSize: 10.5,
        lineHeight: 1.2,
        ...style,
      }}
    >
      {children}
    </span>
  );
}

function MiniSection({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        <span style={{ color: "#94A8BC" }}>{icon}</span>
        <h3
          className="font-semibold"
          style={{ fontSize: 12, color: "#071D3A" }}
        >
          {title}
        </h3>
      </div>
      {children}
    </div>
  );
}

export function ConversationInsightPanel({ senior }: { senior: Senior }) {
  const [insights, setInsights] = useState<ConversationInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadInsights() {
    setLoading(true);
    setError(null);

    try {
      const data = await getConversationInsights(senior.id);
      setInsights(data.items ?? []);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load conversation insight."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadInsights();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [senior.id]);

  const latestInsight = insights[0] ?? null;

  const topMemoryCandidates = useMemo(
    () => latestInsight?.memory_candidates?.slice(0, 3) ?? [],
    [latestInsight]
  );

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ background: "white", boxShadow: CARD_SHADOW }}
    >
      <div
        className="px-5 py-4 flex items-center justify-between gap-3"
        style={{ borderBottom: "1px solid #F1F5F9" }}
      >
        <div>
          <h2
            className="font-semibold flex items-center gap-2"
            style={{ fontSize: 13.5, color: "#071D3A" }}
          >
            <Brain size={15} />
            Latest Conversation Insight
          </h2>
          <p className="mt-0.5" style={{ fontSize: 11.5, color: "#667085" }}>
            AI safety and relationship signals from the most recent analyzed call.
          </p>
        </div>

        <ActionButton
          type="button"
          variant="outline"
          size="sm"
          onClick={loadInsights}
          disabled={loading}
        >
          <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
          Refresh
        </ActionButton>
      </div>

      <div className="px-5 py-4 space-y-4">
        {error && (
          <div
            className="rounded-lg px-3 py-2"
            style={{
              background: "#FEF2F2",
              border: "1px solid #FECACA",
              color: "#B42318",
              fontSize: 12,
              lineHeight: 1.5,
            }}
          >
            {error}
          </div>
        )}

        {loading && (
          <div
            className="flex items-center gap-2"
            style={{ fontSize: 12, color: "#667085" }}
          >
            <RefreshCw size={13} className="animate-spin" />
            Loading conversation insight...
          </div>
        )}

        {!loading && !latestInsight && (
          <div
            className="rounded-lg px-3 py-3"
            style={{
              background: "#F8FAFC",
              border: "1px solid #E8EDF3",
              color: "#667085",
              fontSize: 12.5,
              lineHeight: 1.5,
            }}
          >
            No analyzed conversation insights yet.
          </div>
        )}

        {!loading && latestInsight && (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <Pill style={riskStyle(latestInsight.safety_risk_level)}>
                Safety: {formatLabel(latestInsight.safety_risk_level)}
              </Pill>

              <Pill style={moodStyle(latestInsight.mood_label)}>
                Mood: {formatLabel(latestInsight.mood_label)}
              </Pill>

              <Pill style={moodStyle(latestInsight.loneliness_signal)}>
                Loneliness: {formatLabel(latestInsight.loneliness_signal)}
              </Pill>

              <span
                className="tabular ml-auto"
                style={{ fontSize: 11, color: "#94A8BC" }}
              >
                {formatDateTime(latestInsight.created_at)}
              </span>
            </div>

            <div
              className="rounded-lg px-3 py-3"
              style={{
                background: "#F8FAFC",
                border: "1px solid #E8EDF3",
              }}
            >
              <div className="flex items-start gap-2">
                <ShieldAlert
                  size={14}
                  className="shrink-0 mt-0.5"
                  style={{ color: "#F59E0B" }}
                />
                <div>
                  <p
                    className="font-semibold"
                    style={{ fontSize: 12.5, color: "#071D3A" }}
                  >
                    Safety Summary
                  </p>
                  <p
                    className="mt-0.5"
                    style={{
                      fontSize: 12.5,
                      color: "#667085",
                      lineHeight: 1.5,
                    }}
                  >
                    {latestInsight.safety_summary || "No safety summary available."}
                  </p>
                  <p
                    className="mt-1 tabular"
                    style={{ fontSize: 11, color: "#94A8BC" }}
                  >
                    Confidence: {formatConfidence(latestInsight.safety_confidence)}
                    {latestInsight.safety_escalation_needed
                      ? " • Escalation recommended"
                      : " • No escalation recommended"}
                  </p>
                </div>
              </div>
            </div>

            <MiniSection icon={<HeartPulse size={13} />} title="Relationship Signal">
              <p
                style={{
                  fontSize: 12.5,
                  color: "#667085",
                  lineHeight: 1.5,
                }}
              >
                {latestInsight.relationship_summary ||
                  "No relationship summary available."}
              </p>
            </MiniSection>

            {latestInsight.topics_discussed.length > 0 && (
              <MiniSection icon={<Sparkles size={13} />} title="Topics Discussed">
                <div className="flex flex-wrap gap-1.5">
                  {latestInsight.topics_discussed.map((topic) => (
                    <Pill
                      key={topic}
                      style={{
                        background: "#EFF6FF",
                        color: "#1267D8",
                        border: "1px solid #BFDBFE",
                      }}
                    >
                      {topic}
                    </Pill>
                  ))}
                </div>
              </MiniSection>
            )}

            {latestInsight.follow_up_suggestions.length > 0 && (
              <MiniSection icon={<Lightbulb size={13} />} title="Suggested Follow-Up">
                <div className="space-y-1.5">
                  {latestInsight.follow_up_suggestions.slice(0, 3).map((item) => (
                    <p
                      key={item}
                      style={{
                        fontSize: 12.5,
                        color: "#667085",
                        lineHeight: 1.45,
                      }}
                    >
                      • {item}
                    </p>
                  ))}
                </div>
              </MiniSection>
            )}

            {topMemoryCandidates.length > 0 && (
              <MiniSection icon={<Brain size={13} />} title="Memory Candidates">
                <div className="space-y-1.5">
                  {topMemoryCandidates.map((memory) => (
                    <p
                      key={`${memory.type}-${memory.content}`}
                      style={{
                        fontSize: 12.5,
                        color: "#667085",
                        lineHeight: 1.45,
                      }}
                    >
                      <span className="font-medium">
                        {formatLabel(memory.type)}:
                      </span>{" "}
                      {memory.content}
                    </p>
                  ))}
                </div>
              </MiniSection>
            )}

            {latestInsight.recommended_actions.length > 0 && (
              <MiniSection icon={<ShieldAlert size={13} />} title="Recommended Actions">
                <div className="space-y-1.5">
                  {latestInsight.recommended_actions.map((action) => (
                    <p
                      key={`${action.action_type}-${action.reason}`}
                      style={{
                        fontSize: 12.5,
                        color: "#667085",
                        lineHeight: 1.45,
                      }}
                    >
                      <span className="font-medium">
                        {formatLabel(action.action_type)}:
                      </span>{" "}
                      {action.reason}
                    </p>
                  ))}
                </div>
              </MiniSection>
            )}

            <p style={{ fontSize: 10.5, color: "#94A8BC" }}>
              Analyzer: {latestInsight.analyzer ?? "unknown"} • Check-in #
              {latestInsight.check_in_id ?? "—"}
            </p>
          </>
        )}
      </div>
    </div>
  );
}