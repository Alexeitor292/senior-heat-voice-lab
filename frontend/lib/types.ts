export type RiskLevel = "Low" | "Moderate" | "High" | "Extreme" | "Unknown";
export type SeniorStatus = "Safe" | "Stable" | "Watch" | "Urgent";
export type HydrationLevel = "Normal" | "Elevated" | "High";
export type ConfusionLevel = "Low" | "Elevated" | "High";

export type LivingSituation =
  | "Lives alone"
  | "Lives with family"
  | "Senior community"
  | "Assisted living"
  | "Unknown";

export type SupportMode =
  | "Self-managed"
  | "Family supported"
  | "Community supported"
  | "Facility supported"
  | "Operator monitored";

export interface Senior {
  id: string | number;
  name: string;
  age: number;
  gender?: string;
  location: string;
  city: string;
  state: string;
  lat: number;
  lng: number;
  zipCode?: string | null;
  timezone?: string;
  hasRealHeatSettings?: boolean;
  phone?: string;
  address?: string;
  preferredContactTime?: string;
  medicalNotes?: string;
  emergencyContact?: string;
  heatRisk: RiskLevel;
  status: SeniorStatus;
  heatRiskValue?: number | null;
  heatRiskSource?: string | null;
  latestCheckInRisk?: RiskLevel | string;
  latestCheckInAt?: string | null;
  escalationNeeded?: boolean;
  orientationConcern?: boolean;
  latestCheckIn?: string;
  assignedCaregiver?: string;
  recommendedAction?: string;
  isActive?: boolean;
  livingSituation?: LivingSituation;
  supportMode?: SupportMode;
  supportContactCount?: number;
  hasSupportContact?: boolean;
  escalationPlanSummary?: string;
}

export interface Alert {
  id: string | number;
  seniorId: string | number;
  seniorName: string;
  seniorAge?: number;
  location?: string;
  type: string;
  severity: RiskLevel;
  message: string;
  time: string;
  acknowledged: boolean;
}

export interface TranscriptLine {
  speaker: "Agent" | "Senior";
  name: string;
  text: string;
  time: string;
}

export interface RiskSummary {
  hydrationConcern: HydrationLevel;
  confusionIndicator: ConfusionLevel;
  currentHeatRisk: RiskLevel;
  score: number;
}

export interface HeatCheck {
  id: string;
  seniorId: string | number;
  seniorName: string;
  phone: string;
  location: string;
  callDuration: string;
  status: "active" | "completed" | "missed";
  transcript: TranscriptLine[];
  riskSummary: RiskSummary;
  recommendedAction?: string;
  weather?: string;
  lastCheckIn?: string;
}

export interface ScheduleItem {
  time: string;
  type: "Check-in Call" | "Wellness Visit" | "Follow-up";
  seniorName: string;
  location: string;
}

export interface TimelineItem {
  id: string;
  type: "check-in" | "call-attempt" | "note" | "alert";
  title: string;
  description?: string;
  time: string;
  date: string;
  status?: "success" | "missed" | "info";
}

export interface DashboardSummary {
  seniorsMonitored: number;
  needOutreach: number;
  criticalAlerts: number;

  // Map-specific aliases returned by /ui-api/map.
  supervisedSeniors?: number;
  needOutreachToday?: number;
  critical?: number;
}

export interface PriorityItem {
  rank: number;
  seniorId: string | number;
  seniorName: string;
  age: number;
  location: string;
  risk: RiskLevel;
  action: string;
}

export interface HeatTrendPoint {
  date: string;
  value: number;
}

export interface UrgentOutreachItem {
  seniorId: string | number;
  name: string;
  age: number;
  location: string;
  time?: string;
  risk: RiskLevel;
  status?: SeniorStatus;
  supportMode?: SupportMode;
  hasSupportContact?: boolean;
}

export interface MapViewData {
  summary: DashboardSummary;
  seniors: Senior[];
  selectedSeniorId?: string | number | null;
  urgentOutreach: UrgentOutreachItem[];
}