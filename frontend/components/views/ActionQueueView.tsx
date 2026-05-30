"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  CheckCircle2,
  ClipboardList,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import {
  getOperatorActionsByStatus,
  updateOperatorAction,
} from "@/lib/api";
import type {
  OperatorAction,
  OperatorActionStatus,
  OperatorActionStatusFilter,
  OperatorActionUpdatePayload,
} from "@/lib/types";

const CARD_SHADOW =
  "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

const ACTIONABLE_STATUSES = new Set(["requested", "in_progress"]);

const FILTERS: Array<{
  label: string;
  value: OperatorActionStatusFilter;
}> = [
  { label: "Pending", value: "pending" },
  { label: "Completed", value: "completed" },
  { label: "Canceled", value: "canceled" },
  { label: "Failed", value: "failed" },
  { label: "All", value: "all" },
];

function formatActionTitle(action: OperatorAction): string {
  const type = (action.action_type || "").toLowerCase();

  if (type === "wellness_check") return "Wellness Check";
  if (type === "message_support") return "Support Outreach";
  if (type === "operator_review") return "Operator Review";
  if (type === "call_senior") return "Senior Call";

  return "Operator Action";
}

function formatStatus(status: string): string {
  return status
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
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

function statusBadgeStyle(status: string): React.CSSProperties {
  const normalized = status.toLowerCase();

  if (normalized === "completed") {
    return {
      background: "#F0FDF4",
      color: "#166534",
      border: "1px solid #BBF7D0",
    };
  }

  if (normalized === "failed" || normalized === "canceled") {
    return {
      background: "#FEF2F2",
      color: "#B42318",
      border: "1px solid #FECACA",
    };
  }

  return {
    background: "#EFF6FF",
    color: "#1267D8",
    border: "1px solid #BFDBFE",
  };
}

function buildOutcomeNote(
  action: OperatorAction,
  outcomeNote: string
): string | undefined {
  const trimmedOutcome = outcomeNote.trim();

  if (!trimmedOutcome) {
    return undefined;
  }

  const existingNote = action.note?.trim();

  if (!existingNote) {
    return trimmedOutcome;
  }

  return `${existingNote}\nOutcome: ${trimmedOutcome}`;
}

function isLegacyEvidenceNote(note?: string | null): boolean {
  if (!note) return false;

  return (
    note.includes("Created automatically from AI conversation analysis check-in") ||
    note.includes("Also reinforced by AI conversation analysis check-in")
  );
}

function visibleActionNote(action: OperatorAction): string | null {
  const note = action.note?.trim();

  if (!note) return null;

  if ((action.evidence?.length ?? 0) > 0 && isLegacyEvidenceNote(note)) {
    return null;
  }

  return note;
}

function isActionable(action: OperatorAction) {
  return ACTIONABLE_STATUSES.has((action.status || "").toLowerCase());
}

export function ActionQueueView() {
  const [actions, setActions] = useState<OperatorAction[]>([]);
  const [activeFilter, setActiveFilter] =
    useState<OperatorActionStatusFilter>("pending");
  const [outcomeNotes, setOutcomeNotes] = useState<Record<number, string>>({});

  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadActions(filter = activeFilter) {
    setLoading(true);
    setError(null);

    try {
      const data = await getOperatorActionsByStatus(filter);
      setActions(data.items ?? []);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load operator actions."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadActions(activeFilter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeFilter]);

  const counts = useMemo(() => {
    const support = actions.filter(
      (action) => action.action_type === "message_support"
    ).length;

    const wellness = actions.filter(
      (action) => action.action_type === "wellness_check"
    ).length;

    return {
      total: actions.length,
      support,
      wellness,
    };
  }, [actions]);

  function setOutcomeNote(actionId: number, value: string) {
    setOutcomeNotes((current) => ({
      ...current,
      [actionId]: value,
    }));
  }

  function clearOutcomeNote(actionId: number) {
    setOutcomeNotes((current) => {
      const next = { ...current };
      delete next[actionId];
      return next;
    });
  }

  async function handleUpdateStatus(
    action: OperatorAction,
    status: OperatorActionStatus
  ) {
    setUpdatingId(action.id);
    setError(null);

    try {
      const note = buildOutcomeNote(action, outcomeNotes[action.id] ?? "");

      const payload: OperatorActionUpdatePayload = {
        status,
      };

      if (note !== undefined) {
        payload.note = note;
      }

      await updateOperatorAction(action.id, payload);

      clearOutcomeNote(action.id);
      await loadActions(activeFilter);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update action."
      );
    } finally {
      setUpdatingId(null);
    }
  }

  const emptyText =
    activeFilter === "pending"
      ? "No pending operator actions."
      : `No ${activeFilter} operator actions found.`;

  return (
    <div className="p-6 overflow-auto h-full">
      <div className="mb-7 flex items-start justify-between gap-4">
        <div>
          <h1
            className="font-bold"
            style={{
              fontSize: 22,
              color: "#071D3A",
              letterSpacing: "-0.03em",
            }}
          >
            Action Queue
          </h1>
          <p className="mt-1" style={{ fontSize: 13, color: "#667085" }}>
            Resolve pending work and review completed operator actions.
          </p>
        </div>

        <ActionButton
          type="button"
          variant="outline"
          size="sm"
          onClick={() => loadActions(activeFilter)}
          disabled={loading}
        >
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          Refresh
        </ActionButton>
      </div>

      <div className="flex gap-4 mb-6">
        {[
          {
            label:
              activeFilter === "pending"
                ? "Pending Actions"
                : `${formatStatus(activeFilter)} Actions`,
            value: counts.total,
            bg: "#F8FAFC",
            border: "#E2E8F0",
          },
          {
            label: "Support Outreach",
            value: counts.support,
            bg: "#EFF6FF",
            border: "#BFDBFE",
          },
          {
            label: "Wellness Checks",
            value: counts.wellness,
            bg: "#FFF7ED",
            border: "#FED7AA",
          },
        ].map((card) => (
          <div
            key={card.label}
            className="rounded-xl px-5 py-4"
            style={{
              background: card.bg,
              border: `1px solid ${card.border}`,
              boxShadow: "var(--shadow-xs)",
              minWidth: 180,
            }}
          >
            <div
              className="font-bold tabular leading-none mb-1"
              style={{
                fontSize: 28,
                color: "#071D3A",
                letterSpacing: "-0.04em",
              }}
            >
              {card.value}
            </div>
            <div className="label-caps">{card.label}</div>
          </div>
        ))}
      </div>

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
              <ClipboardList size={15} />
              Operator Actions
            </h2>
            <p
              className="mt-0.5"
              style={{ fontSize: 11.5, color: "#667085" }}
            >
              Pending work can be resolved. Historical actions are read-only.
            </p>
          </div>

          <span className="label-caps">{actions.length} shown</span>
        </div>

        <div
          className="px-5 py-3 flex flex-wrap gap-2"
          style={{ borderBottom: "1px solid #F1F5F9", background: "#FAFBFC" }}
        >
          {FILTERS.map((filter) => {
            const active = activeFilter === filter.value;

            return (
              <button
                key={filter.value}
                type="button"
                onClick={() => setActiveFilter(filter.value)}
                className="rounded-full px-3 py-1.5 font-semibold transition-interactive"
                style={{
                  fontSize: 11.5,
                  background: active ? "#071D3A" : "white",
                  color: active ? "white" : "#667085",
                  border: active ? "1px solid #071D3A" : "1px solid #E2E8F0",
                }}
              >
                {filter.label}
              </button>
            );
          })}
        </div>

        <div className="px-5 py-4 space-y-3">
          {error && (
            <div
              className="rounded-lg px-3 py-2 flex gap-2"
              style={{
                background: "#FEF2F2",
                border: "1px solid #FECACA",
                color: "#B42318",
                fontSize: 12,
                lineHeight: 1.5,
              }}
            >
              <AlertCircle size={14} className="shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {loading && (
            <div
              className="flex items-center gap-2"
              style={{ fontSize: 12, color: "#667085" }}
            >
              <RefreshCw size={13} className="animate-spin" />
              Loading operator actions...
            </div>
          )}

          {!loading && actions.length === 0 && (
            <div
              className="rounded-lg px-3 py-4"
              style={{
                background: "#F8FAFC",
                border: "1px solid #E8EDF3",
                color: "#667085",
                fontSize: 12.5,
                lineHeight: 1.5,
              }}
            >
              {emptyText}
            </div>
          )}

          {!loading &&
            actions.map((action) => {
                const isUpdating = updatingId === action.id;
                const actionable = isActionable(action);
                const actionEvidence = action.evidence ?? [];
                const displayNote = visibleActionNote(action);

              return (
                <div
                  key={action.id}
                  className="rounded-lg px-4 py-4 space-y-3"
                  style={{
                    background: "#F8FAFC",
                    border: "1px solid #E8EDF3",
                  }}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p
                          className="font-semibold"
                          style={{ fontSize: 14, color: "#071D3A" }}
                        >
                          {formatActionTitle(action)}
                        </p>

                        <span
                          className="rounded-full px-2 py-[2px]"
                          style={{
                            ...statusBadgeStyle(action.status),
                            fontSize: 10.5,
                            fontWeight: 700,
                            textTransform: "uppercase",
                            letterSpacing: "0.04em",
                          }}
                        >
                          {formatStatus(action.status)}
                        </span>
                      </div>

                      <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
                        <Link
                          href={`/seniors/${action.senior_id}`}
                          className="font-medium transition-interactive hover:text-brand-blue"
                          style={{ fontSize: 12.5, color: "#1267D8" }}
                        >
                          {action.senior_name ?? `Senior ${action.senior_id}`}
                        </Link>

                        <span style={{ fontSize: 11, color: "#94A8BC" }}>
                          Created {formatDateTime(action.created_at)}
                        </span>

                        {action.updated_at && (
                          <span style={{ fontSize: 11, color: "#94A8BC" }}>
                            Updated {formatDateTime(action.updated_at)}
                          </span>
                        )}
                      </div>

                      <p
                        className="mt-2"
                        style={{
                          fontSize: 12.5,
                          color: "#667085",
                          lineHeight: 1.5,
                        }}
                      >
                        {action.reason || "No reason provided."}
                      </p>

                      {displayNote && (
                        <p
                            className="mt-2 whitespace-pre-line"
                            style={{
                            fontSize: 12,
                            color: "#667085",
                            lineHeight: 1.5,
                            }}
                        >
                            <span className="font-medium">Note: </span>
                            {displayNote}
                        </p>
                        )}

                        {actionEvidence.length > 0 && (
                        <div
                            className="mt-3 rounded-lg px-3 py-2"
                            style={{
                            background: "white",
                            border: "1px solid #E8EDF3",
                            }}
                        >
                            <p className="label-caps mb-1">
                            Evidence From {actionEvidence.length} Check-In
                            {actionEvidence.length === 1 ? "" : "s"}
                            </p>

                            <div className="space-y-1">
                            {actionEvidence.slice(0, 4).map((item) => (
                                <div key={item.id} className="flex gap-1.5">
                                <Link
                                    href={`/check-ins/${item.check_in_id}`}
                                    className="shrink-0 transition-interactive hover:text-brand-blue"
                                    style={{
                                    fontSize: 11.5,
                                    color: "#1267D8",
                                    fontWeight: 600,
                                    }}
                                >
                                    Check-in #{item.check_in_id}
                                </Link>

                                <p
                                    style={{
                                    fontSize: 11.5,
                                    color: "#667085",
                                    lineHeight: 1.45,
                                    }}
                                >
                                    {item.reason}
                                </p>
                                </div>
                            ))}
                            </div>

                            {actionEvidence.length > 4 && (
                            <p className="mt-1" style={{ fontSize: 11, color: "#94A8BC" }}>
                                +{actionEvidence.length - 4} more check-in
                                {actionEvidence.length - 4 === 1 ? "" : "s"}
                            </p>
                            )}
                        </div>
                        )}

                      {action.target_contact_id && (
                        <p
                          className="mt-1 tabular"
                          style={{ fontSize: 11, color: "#94A8BC" }}
                        >
                          Target contact ID {action.target_contact_id}
                        </p>
                      )}
                    </div>
                  </div>

                  {actionable ? (
                    <>
                      <div>
                        <label
                          className="block mb-1"
                          style={{
                            fontSize: 10.5,
                            color: "#667085",
                            fontWeight: 700,
                            textTransform: "uppercase",
                            letterSpacing: "0.06em",
                          }}
                        >
                          Outcome Note
                        </label>

                        <textarea
                          value={outcomeNotes[action.id] ?? ""}
                          onChange={(event) =>
                            setOutcomeNote(action.id, event.target.value)
                          }
                          rows={2}
                          placeholder="Example: Ana answered and will check in within 15 minutes."
                          disabled={isUpdating}
                          style={{
                            width: "100%",
                            border: "1px solid #D8E0EA",
                            borderRadius: 8,
                            padding: "8px 9px",
                            fontSize: 12.5,
                            color: "#071D3A",
                            background: "white",
                            outline: "none",
                            resize: "vertical",
                          }}
                        />
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <ActionButton
                          type="button"
                          variant="primary"
                          size="sm"
                          disabled={isUpdating}
                          onClick={() => handleUpdateStatus(action, "completed")}
                        >
                          <CheckCircle2 size={12} />
                          Complete
                        </ActionButton>

                        <ActionButton
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={isUpdating}
                          onClick={() => handleUpdateStatus(action, "canceled")}
                        >
                          <XCircle size={12} />
                          Cancel
                        </ActionButton>

                        <ActionButton
                          type="button"
                          variant="danger"
                          size="sm"
                          disabled={isUpdating}
                          onClick={() => handleUpdateStatus(action, "failed")}
                        >
                          <AlertCircle size={12} />
                          Failed
                        </ActionButton>
                      </div>
                    </>
                  ) : (
                    <div
                      className="rounded-lg px-3 py-2"
                      style={{
                        background: "white",
                        border: "1px solid #E8EDF3",
                        color: "#667085",
                        fontSize: 12,
                        lineHeight: 1.5,
                      }}
                    >
                      This action is resolved and shown for history only.
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
}