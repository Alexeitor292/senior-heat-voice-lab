import type { Senior, Alert, HeatCheck, DashboardSummary } from "./types";
import {
  MOCK_SENIORS,
  MOCK_ALERTS,
  MOCK_HEAT_CHECK,
  MOCK_DASHBOARD_SUMMARY,
} from "./mock-data";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

// Seniors ----------------------------------------------------------------

export async function getSeniors(): Promise<Senior[]> {
  try {
    const data = await apiFetch<{ items: Senior[] }>("/seniors");
    return data.items;
  } catch {
    return MOCK_SENIORS;
  }
}

export async function getSenior(id: string | number): Promise<Senior | null> {
  try {
    const data = await apiFetch<{ senior: Senior }>(`/seniors/${id}`);
    return data.senior;
  } catch {
    return MOCK_SENIORS.find((s) => String(s.id) === String(id)) ?? null;
  }
}

// Map --------------------------------------------------------------------

export async function getMapSeniors(): Promise<Senior[]> {
  return getSeniors();
}

// Dashboard --------------------------------------------------------------

export async function getDashboardSummary(): Promise<DashboardSummary> {
  try {
    return await apiFetch<DashboardSummary>("/dashboard/summary");
  } catch {
    return MOCK_DASHBOARD_SUMMARY;
  }
}

// Alerts -----------------------------------------------------------------

export async function getAlerts(): Promise<Alert[]> {
  try {
    const data = await apiFetch<{ items: Alert[] }>("/dashboard/alerts");
    return data.items;
  } catch {
    return MOCK_ALERTS;
  }
}

// Heat Checks ------------------------------------------------------------

export async function getHeatChecks(): Promise<HeatCheck[]> {
  // TODO: wire to /dashboard/check-ins when backend shape matches
  return [MOCK_HEAT_CHECK];
}

export async function getHeatCheck(id: string): Promise<HeatCheck | null> {
  if (id === MOCK_HEAT_CHECK.id) return MOCK_HEAT_CHECK;
  try {
    return await apiFetch<HeatCheck>(`/check-ins/${id}`);
  } catch {
    return null;
  }
}

// Actions ----------------------------------------------------------------

export async function startHeatCheck(seniorId: string | number): Promise<{ callSid: string }> {
  const res = await fetch(`${BASE}/seniors/${seniorId}/start-check-in`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to start heat check");
  return res.json();
}

export async function dispatchWellnessCheck(
  seniorId: string | number
): Promise<{ message: string }> {
  // TODO: wire to real dispatch endpoint
  console.log("[TODO] Dispatch wellness check for senior", seniorId);
  return { message: "Wellness check dispatched (mock)" };
}
