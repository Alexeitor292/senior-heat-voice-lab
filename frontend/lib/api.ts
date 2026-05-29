import type { Senior, Alert, HeatCheck, DashboardSummary } from "./types";
import {
  MOCK_SENIORS,
  MOCK_ALERTS,
  MOCK_HEAT_CHECK,
  MOCK_DASHBOARD_SUMMARY,
  MOCK_PRIORITIES,
  MOCK_SCHEDULE,
  HEAT_TREND_DATA,
  MOCK_TIMELINE,
} from "./mock-data";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export async function getSeniors(): Promise<Senior[]> {
  try {
    const data = await apiFetch<{ items: Senior[] }>("/ui-api/seniors");
    return data.items;
  } catch {
    return MOCK_SENIORS;
  }
}

export async function getSenior(id: string | number): Promise<Senior | null> {
  try {
    const data = await apiFetch<{ senior: Senior }>(`/ui-api/seniors/${id}`);
    return data.senior;
  } catch {
    return MOCK_SENIORS.find((s) => String(s.id) === String(id)) ?? null;
  }
}

export async function getSeniorTimeline(id: string | number) {
  try {
    const data = await apiFetch<{ senior: Senior; timeline: typeof MOCK_TIMELINE }>(
      `/ui-api/seniors/${id}`
    );
    return data.timeline;
  } catch {
    return MOCK_TIMELINE;
  }
}

export async function getMapSeniors(): Promise<Senior[]> {
  try {
    const data = await apiFetch<{ seniors: Senior[] }>("/ui-api/map");
    return data.seniors;
  } catch {
    return MOCK_SENIORS;
  }
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  try {
    const data = await apiFetch<{ summary: DashboardSummary }>("/ui-api/dashboard");
    return data.summary;
  } catch {
    return MOCK_DASHBOARD_SUMMARY;
  }
}

export async function getDashboardView() {
  try {
    return await apiFetch<{
      summary: DashboardSummary;
      priorities: typeof MOCK_PRIORITIES;
      schedule: typeof MOCK_SCHEDULE;
      alerts: Alert[];
      trendData: typeof HEAT_TREND_DATA;
    }>("/ui-api/dashboard");
  } catch {
    return {
      summary: MOCK_DASHBOARD_SUMMARY,
      priorities: MOCK_PRIORITIES,
      schedule: MOCK_SCHEDULE,
      alerts: MOCK_ALERTS,
      trendData: HEAT_TREND_DATA,
    };
  }
}

export async function getAlerts(): Promise<Alert[]> {
  try {
    const data = await apiFetch<{ items: Alert[] }>("/ui-api/alerts");
    return data.items;
  } catch {
    return MOCK_ALERTS;
  }
}

export async function getHeatChecks(): Promise<HeatCheck[]> {
  return [MOCK_HEAT_CHECK];
}

export async function getHeatCheck(id: string): Promise<HeatCheck | null> {
  try {
    return await apiFetch<HeatCheck>(`/ui-api/heat-checks/${id}`);
  } catch {
    if (id === MOCK_HEAT_CHECK.id || id === "live-eleanor") {
      return MOCK_HEAT_CHECK;
    }

    return null;
  }
}

export async function startHeatCheck(
  seniorId: string | number
): Promise<{ callSid: string }> {
  const res = await fetch(`${BASE}/seniors/${seniorId}/start-check-in`, {
    method: "POST",
  });

  if (!res.ok) throw new Error("Failed to start heat check");

  return res.json();
}

export async function dispatchWellnessCheck(
  seniorId: string | number
): Promise<{ message: string }> {
  console.log("[TODO] Dispatch wellness check for senior", seniorId);
  return { message: "Wellness check dispatched (mock)" };
}