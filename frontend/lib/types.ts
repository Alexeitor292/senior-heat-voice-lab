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
  dateOfBirth?: string | null;
  pronouns?: string | null;
  primaryLanguage?: string | null;
  hasRealDemographics?: boolean;
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
  occurredAt?: string | null;
  metadata?: Record<string, unknown>;
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

export interface EscalationPlan {
  id: number;
  senior_id: number;
  living_situation: LivingSituation | string;
  support_mode: SupportMode | string;
  allow_operator_review: boolean;
  allow_wellness_check: boolean;
  allow_emergency_escalation: boolean;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface SupportContact {
  id: string | number;
  source?: "support_contact" | "legacy_caregiver";
  senior_id: number;
  name: string;
  phone_number: string;
  relationship?: string | null;
  contact_type: string;
  priority: number;
  can_receive_alerts: boolean;
  is_emergency_contact: boolean;
  is_active: boolean;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface EscalationStep {
  id: number;
  plan_id: number;
  step_order: number;
  trigger_level: string;
  action_type: string;
  target_contact_id?: number | null;
  instructions?: string | null;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface SupportNetwork {
  senior_id: number;
  plan: EscalationPlan | null;
  support_contacts: SupportContact[];
  steps: EscalationStep[];
}

export interface EscalationPlanPayload {
  living_situation: string;
  support_mode: string;
  allow_operator_review: boolean;
  allow_wellness_check: boolean;
  allow_emergency_escalation: boolean;
  notes?: string | null;
}

export interface SupportContactPayload {
  name: string;
  phone_number: string;
  relationship?: string | null;
  contact_type: string;
  priority: number;
  can_receive_alerts: boolean;
  is_emergency_contact: boolean;
  notes?: string | null;
}

export interface HeatSettings {
  id: number;
  senior_id: number;
  enabled: boolean;
  latitude?: number | null;
  longitude?: number | null;
  city?: string | null;
  state?: string | null;
  zip_code?: string | null;
  timezone: string;
  trigger_threshold: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface HeatSettingsPayload {
  enabled: boolean;
  latitude?: number | null;
  longitude?: number | null;
  city?: string | null;
  state?: string | null;
  zip_code?: string | null;
  timezone: string;
  trigger_threshold: number;
}

export interface HeatRiskResult {
  senior_id: number;
  enabled?: boolean;
  heat_settings?: HeatSettings;
  observation?: {
    id?: number;
    senior_id?: number;
    provider?: string;
    latitude?: number | null;
    longitude?: number | null;
    heat_risk_value: number;
    heat_risk_label: string;
    source_url?: string | null;
    observed_at?: string | null;
  };
  trigger_threshold?: number;
  should_trigger_check_in: boolean;
  reason: string;
}

export interface SeniorDemographics {
  id: number;
  senior_id: number;
  date_of_birth?: string | null;
  age_years?: number | null;
  gender?: string | null;
  pronouns?: string | null;
  primary_language?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface SeniorDemographicsPayload {
  date_of_birth?: string | null;
  age_years?: number | null;
  gender?: string | null;
  pronouns?: string | null;
  primary_language?: string | null;
  notes?: string | null;
}