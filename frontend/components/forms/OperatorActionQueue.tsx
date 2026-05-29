"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  CheckCircle2,
  ClipboardList,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import {
  getOperatorActions,
  getSupportNetwork,
  updateOperatorAction,
} from "@/lib/api";
import type {
  OperatorAction,
  OperatorActionStatus,
  OperatorActionUpdatePayload,
  Senior,
  SupportContact,
} from "@/lib/types";

const CARD_SHADOW = "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

const PENDING_STATUSES = new Set(["requested", "in_progress"]);

function formatActionTitle(action: OperatorAction): string {
  const type = (action.action_type || "").toLowerCase();

  if (type === "wellness_check") return "Wellness Check";
  if (type === "message_support") return "Support Outreach";
  if (type === "operator_review") return "Operator Review";
  if (type === "call_senior") return "Senior Call";

  return "Operator Action";
}

function formatActionStatus(status: string): string {
  return status
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatCreatedAt(value?: string | null): string {
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

function contactKey(value: string | number | null | undefined): string | null {
  if (value === null || value === undefined) return null;

  return String(value);
}

function buildContactLookup(contacts: SupportContact[]) {
  const lookup = new Map<string, SupportContact>();

  for (const contact of contacts) {
    const key = contactKey(contact.id);

    if (key) {
      lookup.set(key, contact);
    }
  }

  return lookup;
}

function formatContactLabel(contact: SupportContact): string {
  const relationship = contact.relationship || contact.contact_type;

  return `${contact.name}${relationship ? ` (${relationship})` : ""}`;
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

export function OperatorActionQueue({ senior }: { senior: Senior }) {
  const router = useRouter();

  const [actions, setActions] = useState<OperatorAction[]>([]);
  const [contactLookup, setContactLookup] = useState<Map<string, SupportContact>>(
    new Map()
  );

  const [outcomeNotes, setOutcomeNotes] = useState<Record<number, string>>({});

  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadActions() {
    setLoading(true);
    setError(null);

    try {
      const [actionsData, supportNetwork] = await Promise.all([
        getOperatorActions(senior.id),
        getSupportNetwork(senior.id),
      ]);

      setActions(actionsData.items ?? []);
      setContactLookup(
        buildContactLookup(supportNetwork.support_contacts ?? [])
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load pending actions."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadActions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [senior.id]);

  const pendingActions = useMemo(
    () =>
      actions.filter((action) =>
        PENDING_STATUSES.has((action.status || "").toLowerCase())
      ),
    [actions]
  );

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
      await loadActions();
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update action."
      );
    } finally {
      setUpdatingId(null);
    }
  }

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
            <ClipboardList size={15} />
            Pending Actions
          </h2>
          <p
            className="mt-0.5"
            style={{ fontSize: 11.5, color: "#667085" }}
          >
            Track requested outreach and wellness work.
          </p>
        </div>

        <ActionButton
          type="button"
          variant="outline"
          size="sm"
          onClick={loadActions}
          disabled={loading}
        >
          <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
          Refresh
        </ActionButton>
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
            Loading pending actions...
          </div>
        )}

        {!loading && pendingActions.length === 0 && (
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
            No pending operator actions.
          </div>
        )}

        {!loading &&
          pendingActions.map((action) => {
            const isUpdating = updatingId === action.id;
            const targetContact =
              action.target_contact_id !== null &&
              action.target_contact_id !== undefined
                ? contactLookup.get(String(action.target_contact_id))
                : null;

            return (
              <div
                key={action.id}
                className="rounded-lg px-3 py-3 space-y-3"
                style={{
                  background: "#F8FAFC",
                  border: "1px solid #E8EDF3",
                }}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p
                        className="font-semibold"
                        style={{ fontSize: 13, color: "#071D3A" }}
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
                        {formatActionStatus(action.status)}
                      </span>
                    </div>

                    <p
                      className="mt-1"
                      style={{
                        fontSize: 12.5,
                        color: "#667085",
                        lineHeight: 1.5,
                      }}
                    >
                      {action.reason || "No reason provided."}
                    </p>

                    {action.note && (
                      <p
                        className="mt-1 whitespace-pre-line"
                        style={{
                          fontSize: 12,
                          color: "#667085",
                          lineHeight: 1.5,
                        }}
                      >
                        <span className="font-medium">Note: </span>
                        {action.note}
                      </p>
                    )}

                    <p
                      className="mt-1 tabular"
                      style={{ fontSize: 11, color: "#94A8BC" }}
                    >
                      Created {formatCreatedAt(action.created_at)}
                      {targetContact
                        ? ` • Contact ${formatContactLabel(targetContact)}`
                        : action.target_contact_id
                          ? ` • Contact ID ${action.target_contact_id}`
                          : ""}
                    </p>
                  </div>
                </div>

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
              </div>
            );
          })}
      </div>
    </div>
  );
}