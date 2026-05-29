"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, MessageSquare, PhoneCall } from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import { startHeatCheck } from "@/lib/api";
import type { Senior } from "@/lib/types";

const CARD_SHADOW = "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

export function SeniorActionPanel({ senior }: { senior: Senior }) {
  const router = useRouter();

  const [startingCall, setStartingCall] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [detail, setDetail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCallSenior() {
    setStartingCall(true);
    setSuccess(null);
    setDetail(null);
    setError(null);

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
        disabled={startingCall}
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
        disabled
        title="Support messaging will be wired in the next milestone."
      >
        <MessageSquare size={13} />
        Message Support
      </ActionButton>

      <ActionButton
        type="button"
        variant="warning"
        size="sm"
        className="w-full justify-center gap-2"
        disabled
        title="Wellness check dispatch will be wired in the next milestone."
      >
        <FileText size={13} />
        Dispatch Wellness Check
      </ActionButton>
    </div>
  );
}