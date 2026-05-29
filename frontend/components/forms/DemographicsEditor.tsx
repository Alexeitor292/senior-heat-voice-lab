"use client";

import { useEffect, useState, type CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw, Save, UserRoundPen } from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import {
  getSeniorDemographics,
  updateSeniorDemographics,
} from "@/lib/api";
import type {
  Senior,
  SeniorDemographicsPayload,
} from "@/lib/types";

const CARD_SHADOW = "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

const GENDER_OPTIONS = [
  "",
  "Female",
  "Male",
  "Non-binary",
  "Other",
  "Unknown",
];

const LANGUAGE_OPTIONS = [
  "en-US",
  "es-US",
  "es-MX",
  "ja-JP",
  "zh-CN",
  "vi-VN",
  "tl-PH",
];

const inputStyle: CSSProperties = {
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

function numberOrNull(value: string): number | null {
  if (value.trim() === "") return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function defaultFormFromSenior(senior: Senior): SeniorDemographicsPayload {
  return {
    date_of_birth: senior.dateOfBirth ?? "",
    age_years: senior.age ?? null,
    gender: senior.gender ?? "",
    pronouns: senior.pronouns ?? "",
    primary_language: senior.primaryLanguage ?? "en-US",
    notes: "",
  };
}

export function DemographicsEditor({ senior }: { senior: Senior }) {
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<SeniorDemographicsPayload>(
    defaultFormFromSenior(senior)
  );

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function loadDemographics() {
    setLoading(true);
    setError(null);

    try {
      const data = await getSeniorDemographics(senior.id);

      setForm({
        date_of_birth: data.demographics.date_of_birth ?? "",
        age_years: data.demographics.age_years ?? senior.age ?? null,
        gender: data.demographics.gender ?? "",
        pronouns: data.demographics.pronouns ?? "",
        primary_language:
          data.demographics.primary_language ??
          senior.primaryLanguage ??
          "en-US",
        notes: data.demographics.notes ?? "",
      });
    } catch {
      setForm(defaultFormFromSenior(senior));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (open && !loading) {
      void loadDemographics();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await updateSeniorDemographics(senior.id, {
        date_of_birth: form.date_of_birth?.trim() || null,
        age_years: form.age_years ?? null,
        gender: form.gender?.trim() || null,
        pronouns: form.pronouns?.trim() || null,
        primary_language: form.primary_language?.trim() || null,
        notes: form.notes?.trim() || null,
      });

      setSuccess("Demographics saved.");
      await loadDemographics();
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save demographics."
      );
    } finally {
      setSaving(false);
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
          <h2
            className="font-semibold"
            style={{ fontSize: 13.5, color: "#071D3A" }}
          >
            Manage Demographics
          </h2>
          <p
            className="mt-0.5"
            style={{ fontSize: 11.5, color: "#667085" }}
          >
            Edit age, language, and profile details.
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
            <div
              className="flex items-center gap-2"
              style={{ fontSize: 12, color: "#667085" }}
            >
              <RefreshCw size={13} className="animate-spin" />
              Loading demographics...
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
            <p className="label-caps">Profile Details</p>

            <div>
              <FieldLabel>Date of Birth</FieldLabel>
              <input
                type="date"
                value={form.date_of_birth ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    date_of_birth: event.target.value,
                  }))
                }
                style={inputStyle}
              />
            </div>

            <div>
              <FieldLabel>Age</FieldLabel>
              <input
                type="number"
                min={0}
                max={130}
                value={form.age_years ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    age_years: numberOrNull(event.target.value),
                  }))
                }
                placeholder="78"
                style={inputStyle}
              />
            </div>

            <div>
              <FieldLabel>Gender</FieldLabel>
              <select
                value={form.gender ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    gender: event.target.value,
                  }))
                }
                style={inputStyle}
              >
                {GENDER_OPTIONS.map((option) => (
                  <option key={option || "blank"} value={option}>
                    {option || "Not specified"}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <FieldLabel>Pronouns</FieldLabel>
              <input
                value={form.pronouns ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    pronouns: event.target.value,
                  }))
                }
                placeholder="he/him, she/her, they/them..."
                style={inputStyle}
              />
            </div>

            <div>
              <FieldLabel>Primary Language</FieldLabel>
              <select
                value={form.primary_language ?? "en-US"}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    primary_language: event.target.value,
                  }))
                }
                style={inputStyle}
              >
                {LANGUAGE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <FieldLabel>Demographic Notes</FieldLabel>
              <textarea
                value={form.notes ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    notes: event.target.value,
                  }))
                }
                rows={3}
                placeholder="Optional profile notes."
                style={{ ...inputStyle, resize: "vertical" }}
              />
            </div>

            <ActionButton
              type="button"
              variant="primary"
              size="sm"
              className="w-full justify-center gap-2"
              disabled={saving}
              onClick={handleSave}
            >
              <Save size={13} />
              {saving ? "Saving..." : "Save Demographics"}
            </ActionButton>

            <div
              className="rounded-lg px-3 py-2"
              style={{
                border: "1px solid #E8EDF3",
                background: "#F8FAFC",
                fontSize: 12,
                color: "#667085",
                lineHeight: 1.5,
              }}
            >
              <div
                className="flex items-center gap-2"
                style={{ color: "#071D3A", fontWeight: 650 }}
              >
                <UserRoundPen size={13} />
                Current Profile
              </div>
              <p>
                {senior.age} years old
                {senior.gender ? ` • ${senior.gender}` : ""}
                {senior.pronouns ? ` • ${senior.pronouns}` : ""}
              </p>
              <p>
                Language: {senior.primaryLanguage ?? "en-US"}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}