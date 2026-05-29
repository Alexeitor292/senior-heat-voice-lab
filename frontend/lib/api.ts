import type {
  Senior,
  Alert,
  HeatCheck,
  DashboardSummary,
  MapViewData,
  TimelineItem,
  PriorityItem,
  ScheduleItem,
  HeatTrendPoint,
  SupportNetwork,
  EscalationPlanPayload,
  SupportContactPayload,
  HeatSettings,
  HeatSettingsPayload,
  HeatRiskResult,
  SeniorDemographics,
  SeniorDemographicsPayload,
  StartHeatCheckResponse,
  OperatorAction,
  OperatorActionPayload,
  OperatorActionUpdatePayload,
  OperatorActionStatusFilter,
  ConversationInsight,
} from "./types";
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

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }

  return res.json() as Promise<T>;
}

async function apiSend<T>(
  path: string,
  options: {
    method: "POST" | "PUT" | "PATCH" | "DELETE";
    body?: unknown;
  }
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: options.method,
    headers: options.body ? { "Content-Type": "application/json" } : undefined,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!res.ok) {
    const message = await res.text().catch(() => "");
    throw new Error(message || `API error ${res.status}: ${path}`);
  }

  return res.json() as Promise<T>;
}

function fallbackMapView(): MapViewData {
  const urgentOutreach = MOCK_SENIORS
    .filter((senior) => senior.status === "Urgent" || senior.status === "Watch")
    .slice(0, 3)
    .map((senior) => ({
      seniorId: senior.id,
      name: senior.name,
      age: senior.age,
      location: senior.location,
      time: "9:54 AM",
      risk: senior.heatRisk,
      status: senior.status,
    }));

  return {
    summary: {
      ...MOCK_DASHBOARD_SUMMARY,
      supervisedSeniors: MOCK_SENIORS.length,
      needOutreachToday: urgentOutreach.length,
      critical: MOCK_SENIORS.filter((senior) => senior.status === "Urgent").length,
    },
    seniors: MOCK_SENIORS,
    selectedSeniorId: "eleanor-jennings",
    urgentOutreach,
  };
}

// Map --------------------------------------------------------------------

export async function getMapView(): Promise<MapViewData> {
  try {
    return await apiFetch<MapViewData>("/ui-api/map");
  } catch {
    return fallbackMapView();
  }
}

export async function getMapSeniors(): Promise<Senior[]> {
  const mapView = await getMapView();
  return mapView.seniors;
}

// Seniors ----------------------------------------------------------------

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

export async function getSeniorTimeline(
  id: string | number
): Promise<TimelineItem[]> {
  try {
    const data = await apiFetch<{ senior: Senior; timeline: TimelineItem[] }>(
      `/ui-api/seniors/${id}`
    );

    return data.timeline;
  } catch {
    return MOCK_TIMELINE;
  }
}

export async function getConversationInsights(
  seniorId: string | number
): Promise<{ senior_id: number; items: ConversationInsight[] }> {
  return apiFetch<{ senior_id: number; items: ConversationInsight[] }>(
    `/seniors/${seniorId}/conversation-insights`
  );
}
// Support Network --------------------------------------------------------

export async function getSupportNetwork(
  seniorId: string | number
): Promise<SupportNetwork> {
  return apiFetch<SupportNetwork>(`/seniors/${seniorId}/support-network`);
}

export async function updateEscalationPlan(
  seniorId: string | number,
  payload: EscalationPlanPayload
): Promise<{ message: string; plan: SupportNetwork["plan"] }> {
  return apiSend<{ message: string; plan: SupportNetwork["plan"] }>(
    `/seniors/${seniorId}/escalation-plan`,
    {
      method: "PUT",
      body: payload,
    }
  );
}

export async function createSupportContact(
  seniorId: string | number,
  payload: SupportContactPayload
): Promise<{
  message: string;
  support_contact: SupportNetwork["support_contacts"][number];
}> {
  return apiSend<{
    message: string;
    support_contact: SupportNetwork["support_contacts"][number];
  }>(`/seniors/${seniorId}/support-contacts`, {
    method: "POST",
    body: payload,
  });
}

export async function deactivateSupportContact(
  contactId: string | number
): Promise<{
  message: string;
  support_contact: SupportNetwork["support_contacts"][number];
}> {
  return apiSend<{
    message: string;
    support_contact: SupportNetwork["support_contacts"][number];
  }>(`/support-contacts/${contactId}`, {
    method: "DELETE",
  });
}

// Heat Settings ----------------------------------------------------------

export async function getHeatSettings(
  seniorId: string | number
): Promise<{ senior: Senior; heat_settings: HeatSettings }> {
  return apiFetch<{ senior: Senior; heat_settings: HeatSettings }>(
    `/seniors/${seniorId}/heat-settings`
  );
}

export async function updateHeatSettings(
  seniorId: string | number,
  payload: HeatSettingsPayload
): Promise<{ message: string; heat_settings: HeatSettings }> {
  return apiSend<{ message: string; heat_settings: HeatSettings }>(
    `/seniors/${seniorId}/heat-settings`,
    {
      method: "PUT",
      body: payload,
    }
  );
}

export async function getCurrentHeatRisk(
  seniorId: string | number
): Promise<{ senior: Senior; result: HeatRiskResult }> {
  return apiFetch<{ senior: Senior; result: HeatRiskResult }>(
    `/seniors/${seniorId}/heat-risk`
  );
}

// Demographics -----------------------------------------------------------

export async function getSeniorDemographics(
  seniorId: string | number
): Promise<{ senior_id: number; demographics: SeniorDemographics }> {
  return apiFetch<{ senior_id: number; demographics: SeniorDemographics }>(
    `/seniors/${seniorId}/demographics`
  );
}

export async function updateSeniorDemographics(
  seniorId: string | number,
  payload: SeniorDemographicsPayload
): Promise<{ message: string; demographics: SeniorDemographics }> {
  return apiSend<{ message: string; demographics: SeniorDemographics }>(
    `/seniors/${seniorId}/demographics`,
    {
      method: "PUT",
      body: payload,
    }
  );
}

// Dashboard --------------------------------------------------------------

export async function getDashboardSummary(): Promise<DashboardSummary> {
  try {
    const data = await apiFetch<{ summary: DashboardSummary }>("/ui-api/dashboard");
    return data.summary;
  } catch {
    return MOCK_DASHBOARD_SUMMARY;
  }
}

export async function getDashboardView(): Promise<{
  summary: DashboardSummary;
  priorities: PriorityItem[];
  schedule: ScheduleItem[];
  alerts: Alert[];
  trendData: HeatTrendPoint[];
  pendingOperatorActions: OperatorAction[];
}> {
  try {
    const dashboard = await apiFetch<{
      summary: DashboardSummary;
      priorities: PriorityItem[];
      schedule: ScheduleItem[];
      alerts: Alert[];
      trendData: HeatTrendPoint[];
    }>("/ui-api/dashboard");

    let pendingOperatorActions: OperatorAction[] = [];

    try {
      const pending = await getPendingOperatorActions();
      pendingOperatorActions = pending.items ?? [];
    } catch {
      pendingOperatorActions = [];
    }

    return {
      ...dashboard,
      pendingOperatorActions,
    };
  } catch {
    return {
      summary: MOCK_DASHBOARD_SUMMARY,
      priorities: MOCK_PRIORITIES,
      schedule: MOCK_SCHEDULE,
      alerts: MOCK_ALERTS,
      trendData: HEAT_TREND_DATA,
      pendingOperatorActions: [],
    };
  }
}

// Alerts -----------------------------------------------------------------

export async function getAlerts(): Promise<Alert[]> {
  try {
    const data = await apiFetch<{ items: Alert[] }>("/ui-api/alerts");
    return data.items;
  } catch {
    return MOCK_ALERTS;
  }
}

// Heat Checks ------------------------------------------------------------

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

// Actions ----------------------------------------------------------------

export async function startHeatCheck(
  seniorId: string | number
): Promise<StartHeatCheckResponse> {
  const res = await fetch(`${BASE}/seniors/${seniorId}/start-check-in`, {
    method: "POST",
  });

  if (!res.ok) {
    const message = await res.text().catch(() => "");
    throw new Error(message || "Failed to start heat check");
  }

  const data = await res.json();

  return {
    ...data,
    callSid: data.callSid ?? data.call_sid,
    nextStep: data.nextStep ?? data.next_step,
  };
}

export async function createOperatorAction(
  seniorId: string | number,
  payload: OperatorActionPayload
): Promise<{ message: string; action: OperatorAction }> {
  return apiSend<{ message: string; action: OperatorAction }>(
    `/seniors/${seniorId}/operator-actions`,
    {
      method: "POST",
      body: payload,
    }
  );
}

export async function getOperatorActions(
  seniorId: string | number
): Promise<{ senior_id: number; items: OperatorAction[] }> {
  return apiFetch<{ senior_id: number; items: OperatorAction[] }>(
    `/seniors/${seniorId}/operator-actions`
  );
}

export async function updateOperatorAction(
  actionId: string | number,
  payload: OperatorActionUpdatePayload
): Promise<{ message: string; action: OperatorAction }> {
  return apiSend<{ message: string; action: OperatorAction }>(
    `/operator-actions/${actionId}`,
    {
      method: "PATCH",
      body: payload,
    }
  );
}

export async function getPendingOperatorActions(): Promise<{
  items: OperatorAction[];
}> {
  return apiFetch<{ items: OperatorAction[] }>("/operator-actions/pending");
}

export async function getOperatorActionsByStatus(
  status: OperatorActionStatusFilter = "pending"
): Promise<{ items: OperatorAction[] }> {
  const query = status === "all" ? "" : `?status=${encodeURIComponent(status)}`;

  return apiFetch<{ items: OperatorAction[] }>(
    `/operator-actions${query}`
  );
}