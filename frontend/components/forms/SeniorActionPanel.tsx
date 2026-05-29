"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, MessageSquare, PhoneCall } from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import {
  createOperatorAction,
  getSupportNetwork,
  startHeatCheck,
} from "@/lib/api";
import type { Senior, SupportContact } from "@/lib/types";

const CARD_SHADOW = "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

function numericContactId(contact: SupportContact | null): number | null {
  if (!contact) return null;

  const parsed = Number(contact.id);
  return Number.isFinite(parsed) ? parsed : null;
}

function selectPrimarySupportContact(
  contacts: SupportContact[]
): SupportContact | null {
  const activeContacts = contacts.filter((contact) => contact.is_active);

  const alertableContacts = activeContacts.filter(
    (contact) => contact.can_receive_alerts
  );

  const candidates =
    alertableContacts.length > 0 ? alertableContacts : activeContacts;

  if (candidates.length === 0) return null;

  return [...candidates].sort((a, b) => a.priority - b.priority)[0];
}

export function SeniorActionPanel({ senior }: { senior: Senior }) {
  const router = useRouter();

  const [startingCall, setStartingCall] = useState(false);
  const [messagingSupport, setMessagingSupport] = useState(false);
  const [dispatchingWellness, setDispatchingWellness] = useState(false);

  const [actionNote, setActionNote] = useState("");

  const [success, setSuccess] = useState<string | null>(null);
  const [detail, setDetail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function resetFeedback() {
    setSuccess(null);
    setDetail(null);
    setError(null);
  }

  function defaultReason() {
    return (
      senior.recommendedAction ||
      `${senior.status} status with ${senior.heatRisk} heat risk`
    );
  }

  async function handleCallSenior() {
    setStartingCall(true);
    resetFeedback();

    try {
      const result = await startHeatCheck(senior.id);

      setSuccess("Check-in call started.");
      setDetail(
        result.callSid
          ? `Call SID: ${result.callSid}`
          : result.nextStep ?? "The check-in workflow has started."
      );

      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start check-in call."
      );
    } finally {
      setStartingCall(false);
    }
  }

  async function handleMessageSupport() {
    setMessagingSupport(true);
    resetFeedback();

    try {
      const network = await getSupportNetwork(senior.id);
      const primaryContact = selectPrimarySupportContact(
        network.support_contacts ?? []
      );

      const targetContactId = numericContactId(primaryContact);

      const result = await createOperatorAction(senior.id, {
        action_type: "message_support",
        status: "requested",
        reason: defaultReason(),
        note: actionNote.trim() || null,
        target_contact_id: targetContactId,
        created_by: "operator",
      });

      setSuccess("Support outreach requested.");
      setDetail(
        primaryContact
          ? `Target: ${primaryContact.name} (${primaryContact.relationship || primaryContact.contact_type}) • Action ID: ${result.action.id}`
          : `No active support contact found. Action ID: ${result.action.id}`
      );

      setActionNote("");
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to request support outreach."
      );
    } finally {
      setMessagingSupport(false);
    }
  }

  async function handleDispatchWellnessCheck() {
    setDispatchingWellness(true);
    resetFeedback();

    try {
      const result = await createOperatorAction(senior.id, {
        action_type: "wellness_check",
        status: "requested",
        reason: defaultReason(),
        note: actionNote.trim() || null,
        created_by: "operator",
      });

      setSuccess("Wellness check requested.");
      setDetail(`Action ID: ${result.action.id}`);

      setActionNote("");
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to request wellness check."
      );
    } finally {
      setDispatchingWellness(false);
    }
  }

  const busy = startingCall || messagingSupport || dispatchingWellness;

  return (
    <div
      className="rounded-xl p-5 space-y-3"
      style={{ background: "white", boxShadow: CARD_SHADOW }}
    >
      <div>
        <h2
          className="font-semibold"
          style={{ fontSize: 13.5, color: "#071D3A" }}
        >
          Take Action
        </h2>
        <p className="mt-0.5" style={{ fontSize: 11.5, color: "#667085" }}>
          Start a call or record an escalation step.
        </p>
      </div>

      {success && (
        <div
          className="rounded-lg px-3 py-2"
          style={{
            background: "#F0FDF4",
            border: "1px solid #BBF7D0",
            color: "#166534",
            fontSize: 12,
            lineHeight: 1.5,
          }}
        >
          <div className="font-semibold">{success}</div>
          {detail && <div>{detail}</div>}
        </div>
      )}

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

      <ActionButton
        type="button"
        variant="secondary"
        size="sm"
        className="w-full justify-center gap-2"
        disabled={busy}
        onClick={handleCallSenior}
      >
        <PhoneCall size={13} />
        {startingCall ? "Starting Call..." : "Call Senior"}
      </ActionButton>

      <ActionButton
        type="button"
        variant="secondary"
        size="sm"
        className="w-full justify-center gap-2"
        disabled={busy}
        onClick={handleMessageSupport}
      >
        <MessageSquare size={13} />
        {messagingSupport ? "Requesting..." : "Message Support"}
      </ActionButton>

      <div className="space-y-2">
        <textarea
          value={actionNote}
          onChange={(event) => setActionNote(event.target.value)}
          rows={3}
          placeholder="Optional note for support outreach or wellness check..."
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

        <ActionButton
          type="button"
          variant="warning"
          size="sm"
          className="w-full justify-center gap-2"
          disabled={busy}
          onClick={handleDispatchWellnessCheck}
        >
          <FileText size={13} />
          {dispatchingWellness
            ? "Requesting..."
            : "Dispatch Wellness Check"}
        </ActionButton>
      </div>
    </div>
  );
}