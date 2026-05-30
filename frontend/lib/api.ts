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
  CheckInReview,
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

const SERVER_API_BASE =
  process.env.INTERNAL_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

const BROWSER_API_BASE = "/api/backend";

const API_BASIC_AUTH_USERNAME = process.env.API_BASIC_AUTH_USERNAME;
const API_BASIC_AUTH_PASSWORD = process.env.API_BASIC_AUTH_PASSWORD;

const ALLOW_MOCK_FALLBACK =
  process.env.NEXT_PUBLIC_ALLOW_MOCK_FALLBACK === "true";

class ApiError extends Error {
  status: number;
  path: string;
  responseBody: string;

  constructor({
    status,
    path,
    responseBody,
  }: {
    status: number;
    path: string;
    responseBody: string;
  }) {
    super(`API error ${status}: ${path}${responseBody ? ` - ${responseBody}` : ""}`);
    this.name = "ApiError";
    this.status = status;
    this.path = path;
    this.responseBody = responseBody;
  }
}

function isBrowserRuntime(): boolean {
  return typeof window !== "undefined";
}

function apiUrl(path: string): string {
  if (isBrowserRuntime()) {
    return `${BROWSER_API_BASE}${path}`;
  }

  return `${SERVER_API_BASE}${path}`;
}

function encodeBasicAuth(username: string, password: string): string {
  return Buffer.from(`${username}:${password}`, "utf-8").toString("base64");
}

function apiAuthHeaders(): HeadersInit {
  if (isBrowserRuntime()) {
    return {};
  }

  if (!API_BASIC_AUTH_USERNAME || !API_BASIC_AUTH_PASSWORD) {
    return {};
  }

  return {
    Authorization: `Basic ${encodeBasicAuth(
      API_BASIC_AUTH_USERNAME,
      API_BASIC_AUTH_PASSWORD
    )}`,
  };
}

function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

function fallbackOrThrow<T>({
  path,
  error,
  fallback,
  feature,
}: {
  path: string;
  error: unknown;
  fallback: T;
  feature: string;
}): T {
  if (ALLOW_MOCK_FALLBACK) {
    console.warn(
      `[mock-fallback] ${feature} is using mock/fallback data because ${path} failed.`,
      error
    );

    return fallback;
  }

  throw error;
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(apiUrl(path), {
    cache: "no-store",
    headers: {
      ...apiAuthHeaders(),
    },
  });

  if (!res.ok) {
    const responseBody = await res.text().catch(() => "");

    throw new ApiError({
      status: res.status,
      path,
      responseBody,
    });
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
  const res = await fetch(apiUrl(path), {
    method: options.method,
    headers: {
      ...apiAuthHeaders(),
      ...(options.body ? { "Content-Type": "application/json" } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!res.ok) {
    const responseBody = await res.text().catch(() => "");

    throw new ApiError({
      status: res.status,
      path,
      responseBody,
    });
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
  const path = "/ui-api/map";

  try {
    return await apiFetch<MapViewData>(path);
  } catch (error) {
    return fallbackOrThrow({
      path,
      error,
      fallback: fallbackMapView(),
      feature: "Map view",
    });
  }
}

export async function getMapSeniors(): Promise<Senior[]> {
  const mapView = await getMapView();
  return mapView.seniors;
}

// Seniors ----------------------------------------------------------------

export async function getSeniors(): Promise<Senior[]> {
  const path = "/ui-api/seniors";

  try {
    const data = await apiFetch<{ items: Senior[] }>(path);
    return data.items;
  } catch (error) {
    return fallbackOrThrow({
      path,
      error,
      fallback: MOCK_SENIORS,
      feature: "Senior directory",
    });
  }
}

export async function getSenior(id: string | number): Promise<Senior | null> {
  const path = `/ui-api/seniors/${id}`;

  try {
    const data = await apiFetch<{ senior: Senior }>(path);
    return data.senior;
  } catch (error) {
    const fallbackSenior =
      MOCK_SENIORS.find((senior) => String(senior.id) === String(id)) ?? null;

    if (ALLOW_MOCK_FALLBACK && fallbackSenior) {
      return fallbackOrThrow({
        path,
        error,
        fallback: fallbackSenior,
        feature: "Senior detail",
      });
    }

    if (isApiError(error) && error.status === 404) {
      return null;
    }

    return fallbackOrThrow({
      path,
      error,
      fallback: fallbackSenior,
      feature: "Senior detail",
    });
  }
}

export async function getSeniorTimeline(
  id: string | number
): Promise<TimelineItem[]> {
  const path = `/ui-api/seniors/${id}`;

  try {
    const data = await apiFetch<{ senior: Senior; timeline: TimelineItem[] }>(
      path
    );

    return data.timeline;
  } catch (error) {
    return fallbackOrThrow({
      path,
      error,
      fallback: MOCK_TIMELINE,
      feature: "Senior timeline",
    });
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
  const path = "/ui-api/dashboard";

  try {
    const data = await apiFetch<{ summary: DashboardSummary }>(path);
    return data.summary;
  } catch (error) {
    return fallbackOrThrow({
      path,
      error,
      fallback: MOCK_DASHBOARD_SUMMARY,
      feature: "Dashboard summary",
    });
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
  const path = "/ui-api/dashboard";

  try {
    const dashboard = await apiFetch<{
      summary: DashboardSummary;
      priorities: PriorityItem[];
      schedule: ScheduleItem[];
      alerts: Alert[];
      trendData: HeatTrendPoint[];
    }>(path);

    const pending = await getPendingOperatorActions();

    return {
      ...dashboard,
      pendingOperatorActions: pending.items ?? [],
    };
  } catch (error) {
    return fallbackOrThrow({
      path,
      error,
      fallback: {
        summary: MOCK_DASHBOARD_SUMMARY,
        priorities: MOCK_PRIORITIES,
        schedule: MOCK_SCHEDULE,
        alerts: MOCK_ALERTS,
        trendData: HEAT_TREND_DATA,
        pendingOperatorActions: [],
      },
      feature: "Operations dashboard",
    });
  }
}

// Alerts -----------------------------------------------------------------

export async function getAlerts(): Promise<Alert[]> {
  const path = "/ui-api/alerts";

  try {
    const data = await apiFetch<{ items: Alert[] }>(path);
    return data.items;
  } catch (error) {
    return fallbackOrThrow({
      path,
      error,
      fallback: MOCK_ALERTS,
      feature: "Alerts",
    });
  }
}

// Heat Checks ------------------------------------------------------------

export async function getHeatChecks(): Promise<HeatCheck[]> {
  if (ALLOW_MOCK_FALLBACK) {
    console.warn(
      "[mock-fallback] Heat check list is using mock data because no real heat-check list endpoint is wired yet."
    );

    return [MOCK_HEAT_CHECK];
  }

  throw new Error(
    "Heat check list is not wired to a real backend endpoint yet. Set NEXT_PUBLIC_ALLOW_MOCK_FALLBACK=true to use mock data."
  );
}

export async function getHeatCheck(id: string): Promise<HeatCheck | null> {
  const path = `/ui-api/heat-checks/${id}`;

  try {
    return await apiFetch<HeatCheck>(path);
  } catch (error) {
    const mockHeatCheck =
      id === MOCK_HEAT_CHECK.id || id === "live-eleanor"
        ? MOCK_HEAT_CHECK
        : null;

    if (ALLOW_MOCK_FALLBACK && mockHeatCheck) {
      return fallbackOrThrow({
        path,
        error,
        fallback: mockHeatCheck,
        feature: "Heat check detail",
      });
    }

    if (isApiError(error) && error.status === 404) {
      return null;
    }

    return fallbackOrThrow({
      path,
      error,
      fallback: mockHeatCheck,
      feature: "Heat check detail",
    });
  }
}

export async function getCheckInReview(
  checkInId: string | number
): Promise<CheckInReview | null> {
  const path = `/check-ins/${checkInId}/review`;

  try {
    return await apiFetch<CheckInReview>(path);
  } catch (error) {
    if (isApiError(error) && error.status === 404) {
      return null;
    }

    throw error;
  }
}

// Actions ----------------------------------------------------------------

export async function startHeatCheck(
  seniorId: string | number
): Promise<StartHeatCheckResponse> {
  const path = `/seniors/${seniorId}/start-check-in`;

  const res = await fetch(apiUrl(path), {
    method: "POST",
    headers: {
      ...apiAuthHeaders(),
    },
  });

  if (!res.ok) {
    const responseBody = await res.text().catch(() => "");

    throw new ApiError({
      status: res.status,
      path,
      responseBody,
    });
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