"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, RefreshCw, Save, Trash2 } from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import {
  createSupportContact,
  deactivateSupportContact,
  getSupportNetwork,
  updateEscalationPlan,
} from "@/lib/api";
import type {
  EscalationPlanPayload,
  Senior,
  SupportContactPayload,
  SupportNetwork,
} from "@/lib/types";

const CARD_SHADOW = "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

const LIVING_SITUATIONS = [
  "Lives alone",
  "Lives with family",
  "Senior community",
  "Assisted living",
  "Unknown",
];

const SUPPORT_MODES = [
  "Self-managed",
  "Family supported",
  "Community supported",
  "Facility supported",
  "Operator monitored",
];

const CONTACT_TYPES = [
  "family",
  "friend",
  "neighbor",
  "facility_staff",
  "case_worker",
  "community_volunteer",
  "operator",
  "emergency_contact",
];

const inputStyle: React.CSSProperties = {
  width: "100%",
  border: "1px solid #D8E0EA",
  borderRadius: 8,
  padding: "8px 9px",
  fontSize: 12.5,
  color: "#071D3A",
  background: "white",
  outline: "none",
};

function FieldLabel({ children }: { children: string }) {
  return (
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
      {children}
    </label>
  );
}

function toNumberId(value: string | number): number | null {
  if (typeof value === "number") return value;

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function defaultPlanFromSenior(senior: Senior): EscalationPlanPayload {
  return {
    living_situation: senior.livingSituation ?? "Unknown",
    support_mode: senior.supportMode ?? "Self-managed",
    allow_operator_review: true,
    allow_wellness_check: true,
    allow_emergency_escalation: false,
    notes: senior.escalationPlanSummary ?? "",
  };
}

function defaultContactForm(): SupportContactPayload {
  return {
    name: "",
    phone_number: "",
    relationship: "",
    contact_type: "family",
    priority: 1,
    can_receive_alerts: true,
    is_emergency_contact: false,
    notes: "",
  };
}

export function SupportNetworkEditor({ senior }: { senior: Senior }) {
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [network, setNetwork] = useState<SupportNetwork | null>(null);
  const [planForm, setPlanForm] = useState<EscalationPlanPayload>(
    defaultPlanFromSenior(senior)
  );
  const [contactForm, setContactForm] =
    useState<SupportContactPayload>(defaultContactForm);

  const [loading, setLoading] = useState(false);
  const [savingPlan, setSavingPlan] = useState(false);
  const [addingContact, setAddingContact] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function loadNetwork() {
    setLoading(true);
    setError(null);

    try {
      const data = await getSupportNetwork(senior.id);
      setNetwork(data);

      if (data.plan) {
        setPlanForm({
          living_situation: data.plan.living_situation ?? "Unknown",
          support_mode: data.plan.support_mode ?? "Self-managed",
          allow_operator_review: data.plan.allow_operator_review,
          allow_wellness_check: data.plan.allow_wellness_check,
          allow_emergency_escalation: data.plan.allow_emergency_escalation,
          notes: data.plan.notes ?? "",
        });
      } else {
        setPlanForm(defaultPlanFromSenior(senior));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load support network.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (open && !network && !loading) {
      void loadNetwork();
    }
  }, [open, network, loading]);

  async function handleSavePlan() {
    setSavingPlan(true);
    setError(null);
    setSuccess(null);

    try {
      await updateEscalationPlan(senior.id, planForm);
      setSuccess("Escalation plan saved.");
      await loadNetwork();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save escalation plan.");
    } finally {
      setSavingPlan(false);
    }
  }

  async function handleAddContact() {
    setAddingContact(true);
    setError(null);
    setSuccess(null);

    try {
      if (!contactForm.name.trim()) {
        throw new Error("Support contact name is required.");
      }

      if (!contactForm.phone_number.trim()) {
        throw new Error("Support contact phone number is required.");
      }

      await createSupportContact(senior.id, {
        ...contactForm,
        name: contactForm.name.trim(),
        phone_number: contactForm.phone_number.trim(),
        relationship: contactForm.relationship?.trim() || null,
        notes: contactForm.notes?.trim() || null,
      });

      setContactForm(defaultContactForm());
      setSuccess("Support contact added.");
      await loadNetwork();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add support contact.");
    } finally {
      setAddingContact(false);
    }
  }

  async function handleDeactivateContact(contactId: string | number) {
    const numericId = toNumberId(contactId);

    if (numericId === null) {
      setError("Legacy caregiver contacts cannot be deactivated from this editor yet.");
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      await deactivateSupportContact(numericId);
      setSuccess("Support contact deactivated.");
      await loadNetwork();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to deactivate contact.");
    }
  }

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ background: "white", boxShadow: CARD_SHADOW }}
    >
      <div
        className="px-5 py-4 flex items-center justify-between gap-3"
        style={{ borderBottom: open ? "1px solid #F1F5F9" : "none" }}
      >
        <div>
          <h2 className="font-semibold" style={{ fontSize: 13.5, color: "#071D3A" }}>
            Manage Support
          </h2>
          <p className="mt-0.5" style={{ fontSize: 11.5, color: "#667085" }}>
            Edit escalation and support contacts.
          </p>
        </div>

        <ActionButton
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? "Close" : "Edit"}
        </ActionButton>
      </div>

      {open && (
        <div className="px-5 py-4 space-y-4">
          {loading && (
            <div className="flex items-center gap-2" style={{ fontSize: 12, color: "#667085" }}>
              <RefreshCw size={13} className="animate-spin" />
              Loading support network...
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
              {success}
            </div>
          )}

          <div className="space-y-3">
            <p className="label-caps">Escalation Plan</p>

            <div>
              <FieldLabel>Living Situation</FieldLabel>
              <select
                value={planForm.living_situation}
                onChange={(event) =>
                  setPlanForm((current) => ({
                    ...current,
                    living_situation: event.target.value,
                  }))
                }
                style={inputStyle}
              >
                {LIVING_SITUATIONS.map((option) => (
                  <option key={option}>{option}</option>
                ))}
              </select>
            </div>

            <div>
              <FieldLabel>Support Mode</FieldLabel>
              <select
                value={planForm.support_mode}
                onChange={(event) =>
                  setPlanForm((current) => ({
                    ...current,
                    support_mode: event.target.value,
                  }))
                }
                style={inputStyle}
              >
                {SUPPORT_MODES.map((option) => (
                  <option key={option}>{option}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-2" style={{ fontSize: 12, color: "#374151" }}>
                <input
                  type="checkbox"
                  checked={planForm.allow_operator_review}
                  onChange={(event) =>
                    setPlanForm((current) => ({
                      ...current,
                      allow_operator_review: event.target.checked,
                    }))
                  }
                />
                Allow operator review
              </label>

              <label className="flex items-center gap-2" style={{ fontSize: 12, color: "#374151" }}>
                <input
                  type="checkbox"
                  checked={planForm.allow_wellness_check}
                  onChange={(event) =>
                    setPlanForm((current) => ({
                      ...current,
                      allow_wellness_check: event.target.checked,
                    }))
                  }
                />
                Allow wellness check recommendation
              </label>

              <label className="flex items-center gap-2" style={{ fontSize: 12, color: "#374151" }}>
                <input
                  type="checkbox"
                  checked={planForm.allow_emergency_escalation}
                  onChange={(event) =>
                    setPlanForm((current) => ({
                      ...current,
                      allow_emergency_escalation: event.target.checked,
                    }))
                  }
                />
                Allow emergency escalation
              </label>
            </div>

            <div>
              <FieldLabel>Escalation Notes</FieldLabel>
              <textarea
                value={planForm.notes ?? ""}
                onChange={(event) =>
                  setPlanForm((current) => ({
                    ...current,
                    notes: event.target.value,
                  }))
                }
                rows={4}
                style={{ ...inputStyle, resize: "vertical" }}
              />
            </div>

            <ActionButton
              type="button"
              variant="primary"
              size="sm"
              className="w-full justify-center gap-2"
              disabled={savingPlan}
              onClick={handleSavePlan}
            >
              <Save size={13} />
              {savingPlan ? "Saving..." : "Save Escalation Plan"}
            </ActionButton>
          </div>

          <div className="pt-4 space-y-3" style={{ borderTop: "1px solid #F1F5F9" }}>
            <p className="label-caps">Support Contacts</p>

            <div className="space-y-2">
              {(network?.support_contacts ?? []).length === 0 && (
                <p style={{ fontSize: 12, color: "#667085" }}>
                  No support contacts listed.
                </p>
              )}

              {(network?.support_contacts ?? []).map((contact) => {
                const canDeactivate =
                  typeof contact.id === "number" || Number.isFinite(Number(contact.id));

                return (
                  <div
                    key={`${contact.source ?? "contact"}-${contact.id}`}
                    className="rounded-lg px-3 py-2"
                    style={{
                      border: "1px solid #E8EDF3",
                      background: contact.is_active ? "#F8FAFC" : "#F1F5F9",
                    }}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p style={{ fontSize: 12.5, fontWeight: 650, color: "#071D3A" }}>
                          {contact.name}
                        </p>
                        <p style={{ fontSize: 11.5, color: "#667085" }}>
                          {contact.relationship || contact.contact_type} • Priority {contact.priority}
                        </p>
                        <p className="tabular" style={{ fontSize: 11.5, color: "#667085" }}>
                          {contact.phone_number}
                        </p>
                        {contact.source === "legacy_caregiver" && (
                          <p style={{ fontSize: 10.5, color: "#94A8BC" }}>
                            Legacy caregiver record
                          </p>
                        )}
                      </div>

                      <ActionButton
                        type="button"
                        variant="danger"
                        size="sm"
                        disabled={!canDeactivate || !contact.is_active}
                        onClick={() => handleDeactivateContact(contact.id)}
                      >
                        <Trash2 size={12} />
                      </ActionButton>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="pt-3 space-y-3" style={{ borderTop: "1px solid #F1F5F9" }}>
              <p className="label-caps">Add Contact</p>

              <div>
                <FieldLabel>Name</FieldLabel>
                <input
                  value={contactForm.name}
                  onChange={(event) =>
                    setContactForm((current) => ({
                      ...current,
                      name: event.target.value,
                    }))
                  }
                  placeholder="Maria Support"
                  style={inputStyle}
                />
              </div>

              <div>
                <FieldLabel>Phone</FieldLabel>
                <input
                  value={contactForm.phone_number}
                  onChange={(event) =>
                    setContactForm((current) => ({
                      ...current,
                      phone_number: event.target.value,
                    }))
                  }
                  placeholder="+15550109999"
                  style={inputStyle}
                />
              </div>

              <div>
                <FieldLabel>Relationship</FieldLabel>
                <input
                  value={contactForm.relationship ?? ""}
                  onChange={(event) =>
                    setContactForm((current) => ({
                      ...current,
                      relationship: event.target.value,
                    }))
                  }
                  placeholder="Neighbor, daughter, front desk..."
                  style={inputStyle}
                />
              </div>

              <div>
                <FieldLabel>Contact Type</FieldLabel>
                <select
                  value={contactForm.contact_type}
                  onChange={(event) =>
                    setContactForm((current) => ({
                      ...current,
                      contact_type: event.target.value,
                    }))
                  }
                  style={inputStyle}
                >
                  {CONTACT_TYPES.map((option) => (
                    <option key={option} value={option}>
                      {option.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <FieldLabel>Priority</FieldLabel>
                <input
                  type="number"
                  min={1}
                  value={contactForm.priority}
                  onChange={(event) =>
                    setContactForm((current) => ({
                      ...current,
                      priority: Number(event.target.value),
                    }))
                  }
                  style={inputStyle}
                />
              </div>

              <div className="space-y-2">
                <label className="flex items-center gap-2" style={{ fontSize: 12, color: "#374151" }}>
                  <input
                    type="checkbox"
                    checked={contactForm.can_receive_alerts}
                    onChange={(event) =>
                      setContactForm((current) => ({
                        ...current,
                        can_receive_alerts: event.target.checked,
                      }))
                    }
                  />
                  Can receive alerts
                </label>

                <label className="flex items-center gap-2" style={{ fontSize: 12, color: "#374151" }}>
                  <input
                    type="checkbox"
                    checked={contactForm.is_emergency_contact}
                    onChange={(event) =>
                      setContactForm((current) => ({
                        ...current,
                        is_emergency_contact: event.target.checked,
                      }))
                    }
                  />
                  Emergency contact
                </label>
              </div>

              <div>
                <FieldLabel>Notes</FieldLabel>
                <textarea
                  value={contactForm.notes ?? ""}
                  onChange={(event) =>
                    setContactForm((current) => ({
                      ...current,
                      notes: event.target.value,
                    }))
                  }
                  rows={3}
                  placeholder="Can check in during heat events."
                  style={{ ...inputStyle, resize: "vertical" }}
                />
              </div>

              <ActionButton
                type="button"
                variant="secondary"
                size="sm"
                className="w-full justify-center gap-2"
                disabled={addingContact}
                onClick={handleAddContact}
              >
                <Plus size={13} />
                {addingContact ? "Adding..." : "Add Support Contact"}
              </ActionButton>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}