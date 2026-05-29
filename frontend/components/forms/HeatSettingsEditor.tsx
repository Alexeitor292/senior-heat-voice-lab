"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { MapPin, RefreshCw, Save, ThermometerSun } from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import {
  getCurrentHeatRisk,
  getHeatSettings,
  updateHeatSettings,
} from "@/lib/api";
import type {
  HeatRiskResult,
  HeatSettingsPayload,
  Senior,
} from "@/lib/types";

const CARD_SHADOW = "0 0 0 1px #E8EDF3, 0 1px 3px 0 rgb(7 29 58 / 0.05)";

const TIMEZONES = [
  "America/Los_Angeles",
  "America/Phoenix",
  "America/Denver",
  "America/Chicago",
  "America/New_York",
  "America/Anchorage",
  "Pacific/Honolulu",
];

const THRESHOLDS = [
  { value: 0, label: "0 - Little to no risk" },
  { value: 1, label: "1 - Minor" },
  { value: 2, label: "2 - Moderate" },
  { value: 3, label: "3 - Major" },
  { value: 4, label: "4 - Extreme" },
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

function numberOrNull(value: string): number | null {
  if (value.trim() === "") return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function defaultFormFromSenior(senior: Senior): HeatSettingsPayload {
  return {
    enabled: true,
    latitude: senior.lat ?? null,
    longitude: senior.lng ?? null,
    city: senior.city ?? "",
    state: senior.state ?? "",
    zip_code: senior.zipCode ?? "",
    timezone: senior.timezone ?? "America/Los_Angeles",
    trigger_threshold: 2,
  };
}

export function HeatSettingsEditor({ senior }: { senior: Senior }) {
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<HeatSettingsPayload>(
    defaultFormFromSenior(senior)
  );
  const [latestRisk, setLatestRisk] = useState<HeatRiskResult | null>(null);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [checkingRisk, setCheckingRisk] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function loadSettings() {
    setLoading(true);
    setError(null);

    try {
      const data = await getHeatSettings(senior.id);

      setForm({
        enabled: data.heat_settings.enabled,
        latitude: data.heat_settings.latitude ?? null,
        longitude: data.heat_settings.longitude ?? null,
        city: data.heat_settings.city ?? "",
        state: data.heat_settings.state ?? "",
        zip_code: data.heat_settings.zip_code ?? "",
        timezone: data.heat_settings.timezone ?? "America/Los_Angeles",
        trigger_threshold: data.heat_settings.trigger_threshold ?? 2,
      });
    } catch (err) {
      setForm(defaultFormFromSenior(senior));
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load heat settings."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (open && !loading) {
      void loadSettings();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await updateHeatSettings(senior.id, {
        ...form,
        city: form.city?.trim() || null,
        state: form.state?.trim() || null,
        zip_code: form.zip_code?.trim() || null,
      });

      setSuccess("Heat settings saved.");
      await loadSettings();
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save heat settings."
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleCheckRisk() {
    setCheckingRisk(true);
    setError(null);
    setSuccess(null);

    try {
      const data = await getCurrentHeatRisk(senior.id);
      setLatestRisk(data.result);
      setSuccess("Heat risk checked.");
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to check heat risk."
      );
    } finally {
      setCheckingRisk(false);
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
            Manage Location
          </h2>
          <p className="mt-0.5" style={{ fontSize: 11.5, color: "#667085" }}>
            Edit map location and HeatRisk settings.
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
              Loading heat settings...
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
            <p className="label-caps">Location</p>

            <label className="flex items-center gap-2" style={{ fontSize: 12, color: "#374151" }}>
              <input
                type="checkbox"
                checked={form.enabled}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    enabled: event.target.checked,
                  }))
                }
              />
              Enable HeatRisk monitoring
            </label>

            <div>
              <FieldLabel>City</FieldLabel>
              <input
                value={form.city ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    city: event.target.value,
                  }))
                }
                placeholder="Rocklin"
                style={inputStyle}
              />
            </div>

            <div>
              <FieldLabel>State</FieldLabel>
              <input
                value={form.state ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    state: event.target.value.toUpperCase().slice(0, 2),
                  }))
                }
                placeholder="CA"
                style={inputStyle}
              />
            </div>

            <div>
              <FieldLabel>Zip Code</FieldLabel>
              <input
                value={form.zip_code ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    zip_code: event.target.value,
                  }))
                }
                placeholder="95765"
                style={inputStyle}
              />
            </div>

            <div>
              <FieldLabel>Latitude</FieldLabel>
              <input
                type="number"
                step="0.0001"
                value={form.latitude ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    latitude: numberOrNull(event.target.value),
                  }))
                }
                placeholder="38.7907"
                style={inputStyle}
              />
            </div>

            <div>
              <FieldLabel>Longitude</FieldLabel>
              <input
                type="number"
                step="0.0001"
                value={form.longitude ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    longitude: numberOrNull(event.target.value),
                  }))
                }
                placeholder="-121.2358"
                style={inputStyle}
              />
            </div>

            <div>
              <FieldLabel>Timezone</FieldLabel>
              <select
                value={form.timezone}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    timezone: event.target.value,
                  }))
                }
                style={inputStyle}
              >
                {TIMEZONES.map((timezone) => (
                  <option key={timezone} value={timezone}>
                    {timezone}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <FieldLabel>Trigger Threshold</FieldLabel>
              <select
                value={form.trigger_threshold}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    trigger_threshold: Number(event.target.value),
                  }))
                }
                style={inputStyle}
              >
                {THRESHOLDS.map((threshold) => (
                  <option key={threshold.value} value={threshold.value}>
                    {threshold.label}
                  </option>
                ))}
              </select>
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
              {saving ? "Saving..." : "Save Heat Settings"}
            </ActionButton>

            <ActionButton
              type="button"
              variant="secondary"
              size="sm"
              className="w-full justify-center gap-2"
              disabled={checkingRisk}
              onClick={handleCheckRisk}
            >
              <ThermometerSun size={13} />
              {checkingRisk ? "Checking..." : "Check Current HeatRisk"}
            </ActionButton>
          </div>

          {latestRisk && (
            <div
              className="rounded-lg px-3 py-2 space-y-1"
              style={{
                border: "1px solid #E8EDF3",
                background: "#F8FAFC",
                fontSize: 12,
                color: "#667085",
                lineHeight: 1.5,
              }}
            >
              <div className="flex items-center gap-2" style={{ color: "#071D3A", fontWeight: 650 }}>
                <MapPin size={13} />
                Latest HeatRisk Result
              </div>

              <p>{latestRisk.reason}</p>

              {latestRisk.observation && (
                <p>
                  Observed: HeatRisk {latestRisk.observation.heat_risk_value} -{" "}
                  {latestRisk.observation.heat_risk_label}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}