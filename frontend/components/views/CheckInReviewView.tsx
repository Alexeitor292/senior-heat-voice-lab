import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  Brain,
  CheckCircle2,
  HeartPulse,
  MessageSquare,
  Phone,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import type {
  CheckInReview,
  CheckInTranscriptTurn,
  ConversationInsight,
  OperatorAction,
  OperatorActionEvidence,
} from "@/lib/types";

const CARD_SHADOW =
  "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

function formatLabel(value?: string | null): string {
  if (!value) return "Unknown";

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatDateTime(value?: string | null): string {
  if (!value) return "Unknown time";

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) return "Unknown time";

  return parsed.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatDuration(seconds?: number | null): string {
  if (seconds === null || seconds === undefined) return "—";

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes === 0) {
    return `${remainingSeconds}s`;
  }

  return `${minutes}m ${remainingSeconds}s`;
}

function riskStyle(value?: string | null): React.CSSProperties {
  const normalized = (value || "").toLowerCase();

  if (["red", "urgent", "high", "orange"].includes(normalized)) {
    return {
      background: "#FFF7ED",
      color: "#B45309",
      border: "1px solid #FED7AA",
    };
  }

  if (["yellow", "medium"].includes(normalized)) {
    return {
      background: "#FEFCE8",
      color: "#A16207",
      border: "1px solid #FEF08A",
    };
  }

  if (["green", "low"].includes(normalized)) {
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

function followUpStatusLabel(
  riskLevel?: string | null,
  escalationNeeded?: boolean | null,
): string | null {
  if (!escalationNeeded) return null;

  const normalized = (riskLevel || "").toLowerCase();

  if (normalized === "yellow") {
    return "Follow-Up Recommended";
  }

  return "Escalation Needed";
}

function followUpStatusStyle(riskLevel?: string | null): React.CSSProperties {
  const normalized = (riskLevel || "").toLowerCase();

  if (normalized === "yellow") {
    return {
      background: "#FEFCE8",
      color: "#A16207",
      border: "1px solid #FEF08A",
    };
  }

  if (normalized === "orange") {
    return {
      background: "#FFF7ED",
      color: "#B45309",
      border: "1px solid #FED7AA",
    };
  }

  return {
    background: "#FEF2F2",
    color: "#B42318",
    border: "1px solid #FECACA",
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

function Card({
  title,
  subtitle,
  icon,
  children,
}: {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ background: "white", boxShadow: CARD_SHADOW }}
    >
      <div
        className="px-5 py-4"
        style={{ borderBottom: "1px solid #F1F5F9" }}
      >
        <h2
          className="font-semibold flex items-center gap-2"
          style={{ fontSize: 13.5, color: "#071D3A" }}
        >
          {icon}
          {title}
        </h2>

        {subtitle && (
          <p className="mt-0.5" style={{ fontSize: 11.5, color: "#667085" }}>
            {subtitle}
          </p>
        )}
      </div>

      <div className="px-5 py-4">{children}</div>
    </div>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div>
      <p className="label-caps mb-1">{label}</p>
      <div style={{ fontSize: 13, color: "#071D3A", lineHeight: 1.5 }}>
        {value}
      </div>
    </div>
  );
}

function TranscriptTurnRow({ turn }: { turn: CheckInTranscriptTurn }) {
  const speaker = (turn.speaker || "unknown").toLowerCase();
  const isAssistant = ["assistant", "ai", "agent"].includes(speaker);
  const isSenior = ["senior", "user", "caller"].includes(speaker);

  return (
    <div
      className="rounded-lg px-3 py-3"
      style={{
        background: isAssistant ? "#F8FAFC" : "white",
        border: "1px solid #E8EDF3",
      }}
    >
      <div className="flex items-center justify-between gap-2 mb-1">
        <span
          className="font-semibold"
          style={{
            fontSize: 11.5,
            color: isSenior ? "#1267D8" : "#667085",
            textTransform: "uppercase",
            letterSpacing: "0.04em",
          }}
        >
          {formatLabel(turn.speaker)}
        </span>

        <span className="tabular" style={{ fontSize: 10.5, color: "#94A8BC" }}>
          Turn {turn.turn_index + 1}
        </span>
      </div>

      <p style={{ fontSize: 13, color: "#071D3A", lineHeight: 1.55 }}>
        {turn.text}
      </p>
    </div>
  );
}

function InsightSummary({
  insight,
}: {
  insight: ConversationInsight | null | undefined;
}) {
  if (!insight) {
    return (
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
        No conversation insight is linked to this check-in yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Pill style={riskStyle(insight.safety_risk_level)}>
          Safety: {formatLabel(insight.safety_risk_level)}
        </Pill>

        <Pill
          style={{
            background: "#EFF6FF",
            color: "#1267D8",
            border: "1px solid #BFDBFE",
          }}
        >
          Mood: {formatLabel(insight.mood_label)}
        </Pill>

        <Pill
          style={{
            background: "#FDF2F8",
            color: "#BE185D",
            border: "1px solid #FBCFE8",
          }}
        >
          Loneliness: {formatLabel(insight.loneliness_signal)}
        </Pill>
      </div>

      <div
        className="rounded-lg px-3 py-3"
        style={{ background: "#F8FAFC", border: "1px solid #E8EDF3" }}
      >
        <p className="font-semibold" style={{ fontSize: 12.5, color: "#071D3A" }}>
          Safety Summary
        </p>
        <p
          className="mt-0.5"
          style={{ fontSize: 12.5, color: "#667085", lineHeight: 1.5 }}
        >
          {insight.safety_summary || "No safety summary available."}
        </p>
      </div>

      <div>
        <p
          className="font-semibold mb-1.5"
          style={{ fontSize: 12.5, color: "#071D3A" }}
        >
          Relationship Summary
        </p>
        <p style={{ fontSize: 12.5, color: "#667085", lineHeight: 1.5 }}>
          {insight.relationship_summary || "No relationship summary available."}
        </p>
      </div>

      {insight.topics_discussed.length > 0 && (
        <div>
          <p
            className="font-semibold mb-1.5"
            style={{ fontSize: 12.5, color: "#071D3A" }}
          >
            Topics Discussed
          </p>
          <div className="flex flex-wrap gap-1.5">
            {insight.topics_discussed.map((topic) => (
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
        </div>
      )}

      {insight.follow_up_suggestions.length > 0 && (
        <div>
          <p
            className="font-semibold mb-1.5"
            style={{ fontSize: 12.5, color: "#071D3A" }}
          >
            Suggested Follow-Up
          </p>
          <div className="space-y-1.5">
            {insight.follow_up_suggestions.map((item) => (
              <p
                key={item}
                style={{ fontSize: 12.5, color: "#667085", lineHeight: 1.45 }}
              >
                • {item}
              </p>
            ))}
          </div>
        </div>
      )}

      {insight.memory_candidates.length > 0 && (
        <div>
          <p
            className="font-semibold mb-1.5"
            style={{ fontSize: 12.5, color: "#071D3A" }}
          >
            Memory Candidates
          </p>
          <div className="space-y-1.5">
            {insight.memory_candidates.map((memory) => (
              <p
                key={`${memory.type}-${memory.content}`}
                style={{ fontSize: 12.5, color: "#667085", lineHeight: 1.45 }}
              >
                <span className="font-medium">{formatLabel(memory.type)}:</span>{" "}
                {memory.content}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function RelatedActions({
  actions,
  evidence,
}: {
  actions: OperatorAction[];
  evidence: OperatorActionEvidence[];
}) {
  if (actions.length === 0) {
    return (
      <p style={{ fontSize: 12.5, color: "#667085", lineHeight: 1.5 }}>
        No operator actions were directly linked to this check-in.
      </p>
    );
  }

  const evidenceByActionId = new Map<number, OperatorActionEvidence[]>();

  for (const item of evidence) {
    const current = evidenceByActionId.get(item.operator_action_id) ?? [];
    current.push(item);
    evidenceByActionId.set(item.operator_action_id, current);
  }

  return (
    <div className="space-y-2">
      {actions.map((action) => {
        const actionEvidence = evidenceByActionId.get(action.id) ?? [];

        return (
          <div
            key={action.id}
            className="rounded-lg px-3 py-3"
            style={{ background: "#F8FAFC", border: "1px solid #E8EDF3" }}
          >
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className="font-semibold"
                style={{ fontSize: 12.5, color: "#071D3A" }}
              >
                {formatLabel(action.action_type)}
              </span>

              <Pill style={riskStyle(action.status)}>
                {formatLabel(action.status)}
              </Pill>
            </div>

            <p
              className="mt-1"
              style={{ fontSize: 12.5, color: "#667085", lineHeight: 1.5 }}
            >
              {action.reason || "No reason provided."}
            </p>

            {actionEvidence.length > 0 ? (
              <div className="mt-2 space-y-1">
                <p className="label-caps">Evidence From This Check-In</p>
                {actionEvidence.map((item) => (
                  <p
                    key={item.id}
                    style={{
                      fontSize: 11.5,
                      color: "#667085",
                      lineHeight: 1.45,
                    }}
                  >
                    {item.reason}
                  </p>
                ))}
              </div>
            ) : (
              action.note && (
                <p
                  className="mt-1"
                  style={{
                    fontSize: 11.5,
                    color: "#94A8BC",
                    lineHeight: 1.45,
                  }}
                >
                  {action.note}
                </p>
              )
            )}
          </div>
        );
      })}
    </div>
  );
}

export function CheckInReviewView({ review }: { review: CheckInReview }) {
  const {
    check_in: checkIn,
    senior,
    insight,
    transcript_turns,
    operator_actions,
    operator_action_evidence,
  } = review;

  const followUpLabel = followUpStatusLabel(
    checkIn.risk_level,
    checkIn.escalation_needed,
  );

  return (
    <div className="overflow-auto h-full">
      <div
        className="px-6 py-3 flex items-center"
        style={{ background: "white", borderBottom: "1px solid #F1F5F9" }}
      >
        <Link
          href={senior ? `/seniors/${senior.id}` : "/dashboard"}
          className="flex items-center gap-1 transition-interactive hover:text-brand-blue"
          style={{ fontSize: 13, color: "#667085", fontWeight: 500 }}
        >
          <ArrowLeft size={14} />
          {senior ? `Back to ${senior.name}` : "Back to Dashboard"}
        </Link>
      </div>

      <div
        className="px-6 pt-5 pb-5"
        style={{ background: "white", borderBottom: "1px solid #E8EDF3" }}
      >
        <div className="flex items-center gap-3 mb-5">
          <h1
            className="font-bold"
            style={{ fontSize: 24, color: "#071D3A", letterSpacing: "-0.04em" }}
          >
            Check-In Review #{checkIn.id}
          </h1>

          <Pill style={riskStyle(checkIn.risk_level)}>
            Risk: {formatLabel(checkIn.risk_level)}
          </Pill>

          {followUpLabel && (
            <Pill style={followUpStatusStyle(checkIn.risk_level)}>
              {followUpLabel}
            </Pill>
          )}
        </div>

        <div className="grid grid-cols-4 gap-4">
          <Metric
            label="Senior"
            value={
              senior ? (
                <Link
                  href={`/seniors/${senior.id}`}
                  style={{ color: "#1267D8", fontWeight: 600 }}
                >
                  {senior.name}
                </Link>
              ) : (
                checkIn.senior_phone_number ?? "Unknown"
              )
            }
          />

          <Metric
            label="Created"
            value={
              <span className="tabular">
                {formatDateTime(checkIn.created_at)}
              </span>
            }
          />

          <Metric
            label="Call Status"
            value={formatLabel(checkIn.senior_call_status)}
          />

          <Metric
            label="Duration"
            value={
              <span className="tabular">
                {formatDuration(checkIn.senior_call_duration_seconds)}
              </span>
            }
          />
        </div>
      </div>

      <div className="p-6 grid grid-cols-[1fr_360px] gap-5">
        <div className="space-y-5 min-w-0">
          <Card
            title="Transcript"
            subtitle="Conversation turns captured from the senior check-in."
            icon={<MessageSquare size={15} />}
          >
            {transcript_turns.length === 0 ? (
              <p style={{ fontSize: 12.5, color: "#667085" }}>
                No transcript turns are available.
              </p>
            ) : (
              <div className="space-y-3">
                {transcript_turns.map((turn, index) => (
                  <TranscriptTurnRow
                    key={turn.id ?? `${turn.turn_index}-${index}`}
                    turn={turn}
                  />
                ))}
              </div>
            )}
          </Card>

          <Card
            title="AI Conversation Insight"
            subtitle="Safety, relationship, memory, and follow-up signals."
            icon={<Brain size={15} />}
          >
            <InsightSummary insight={insight} />
          </Card>
        </div>

        <div className="space-y-5">
          <Card title="Call Details" icon={<Phone size={15} />}>
            <div className="space-y-3">
              <Metric
                label="Call SID"
                value={
                  <span className="tabular break-all">
                    {checkIn.senior_call_sid ?? "—"}
                  </span>
                }
              />

              <Metric
                label="Speech Confidence"
                value={checkIn.speech_confidence ?? "—"}
              />

              <Metric label="Analyzer" value={checkIn.analyzer ?? "—"} />

              <Metric label="Source" value={checkIn.source ?? "—"} />
            </div>
          </Card>

          <Card title="Safety Flags" icon={<ShieldAlert size={15} />}>
            <div className="space-y-3">
              <Metric
                label="Orientation Concern"
                value={checkIn.orientation_concern ? "Yes" : "No"}
              />

              <Metric
                label="Caregiver Alert"
                value={
                  checkIn.caregiver_alert_required ? "Required" : "Not required"
                }
              />

              {checkIn.reported_symptoms.length > 0 && (
                <div>
                  <p className="label-caps mb-1.5">Reported Symptoms</p>
                  <div className="flex flex-wrap gap-1.5">
                    {checkIn.reported_symptoms.map((item) => (
                      <Pill key={item} style={riskStyle("yellow")}>
                        {formatLabel(item)}
                      </Pill>
                    ))}
                  </div>
                </div>
              )}

              {checkIn.red_flags.length > 0 && (
                <div>
                  <p className="label-caps mb-1.5">Red Flags</p>
                  <div className="flex flex-wrap gap-1.5">
                    {checkIn.red_flags.map((item) => (
                      <Pill key={item} style={riskStyle("orange")}>
                        {formatLabel(item)}
                      </Pill>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>

          <Card title="Related Operator Actions" icon={<CheckCircle2 size={15} />}>
            <RelatedActions
              actions={operator_actions}
              evidence={operator_action_evidence}
            />
          </Card>

          {insight && (
            <Card title="Insight Metadata" icon={<Sparkles size={15} />}>
              <div className="space-y-3">
                <Metric label="Insight ID" value={insight.id} />

                <Metric
                  label="Safety Confidence"
                  value={
                    insight.safety_confidence !== null &&
                    insight.safety_confidence !== undefined
                      ? `${Math.round(insight.safety_confidence * 100)}%`
                      : "—"
                  }
                />

                <Metric label="Mood" value={formatLabel(insight.mood_label)} />

                <Metric
                  label="Loneliness"
                  value={formatLabel(insight.loneliness_signal)}
                />
              </div>
            </Card>
          )}

          <Card title="Recommended Action" icon={<AlertTriangle size={15} />}>
            <p style={{ fontSize: 12.5, color: "#667085", lineHeight: 1.5 }}>
              {checkIn.recommended_action ||
                "No recommended action was recorded."}
            </p>
          </Card>

          <Card title="Relationship Summary" icon={<HeartPulse size={15} />}>
            <p style={{ fontSize: 12.5, color: "#667085", lineHeight: 1.5 }}>
              {checkIn.caregiver_summary ||
                insight?.relationship_summary ||
                "No relationship summary available."}
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}