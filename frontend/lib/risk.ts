import type { RiskLevel, SeniorStatus } from "./types";

export function riskColor(level: RiskLevel): string {
  switch (level) {
    case "Extreme": return "#E52920";
    case "High":    return "#F59E0B";
    case "Moderate":return "#1267D8";
    case "Low":     return "#22C7C9";
    default:        return "#667085";
  }
}

export function riskBg(level: RiskLevel): string {
  switch (level) {
    case "Extreme": return "bg-red-50 text-brand-red border-red-200";
    case "High":    return "bg-orange-50 text-brand-orange border-orange-200";
    case "Moderate":return "bg-blue-50 text-brand-blue border-blue-200";
    case "Low":     return "bg-teal-50 text-teal-600 border-teal-200";
    default:        return "bg-gray-50 text-muted border-line";
  }
}

export function riskLabel(level: RiskLevel): string {
  return level;
}

export function statusColor(status: SeniorStatus): string {
  switch (status) {
    case "Safe":   return "#22C55E";
    case "Stable": return "#3B82F6";
    case "Watch":  return "#F59E0B";
    case "Urgent": return "#EF4444";
    default:       return "#9CA3AF";
  }
}

export function statusBg(status: SeniorStatus): string {
  switch (status) {
    case "Safe":   return "bg-green-100 text-green-700";
    case "Stable": return "bg-blue-100 text-blue-700";
    case "Watch":  return "bg-orange-100 text-orange-700";
    case "Urgent": return "bg-red-100 text-red-700";
    default:       return "bg-gray-100 text-gray-600";
  }
}
