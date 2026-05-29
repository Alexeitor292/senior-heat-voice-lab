"use client";

import { useMemo, useState } from "react";
import { Users, Thermometer, AlertTriangle } from "lucide-react";
import { NationalHeatMap } from "@/components/map/NationalHeatMap";
import { SelectedSeniorPanel } from "@/components/map/SelectedSeniorPanel";
import { MapLegend } from "@/components/map/MapLegend";
import type { Senior, MapViewData } from "@/lib/types";

interface Props {
  mapData: MapViewData;
}

interface StatChipProps {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  bg: string;
  border: string;
  labelColor: string;
}

function StatChip({ icon, label, value, bg, border, labelColor }: StatChipProps) {
  return (
    <div
      className="flex items-center gap-2 rounded-lg px-3 py-2"
      style={{ background: bg, border: `1px solid ${border}` }}
    >
      {icon}
      <span className="font-medium" style={{ fontSize: 12, color: labelColor }}>
        {label}
      </span>
      <span
        className="font-bold tabular"
        style={{ fontSize: 14, color: "#071D3A", marginLeft: 2 }}
      >
        {value}
      </span>
    </div>
  );
}

export function MapView({ mapData }: Props) {
  const { seniors, summary, urgentOutreach } = mapData;

  const initialSelectedSenior = useMemo(() => {
    if (!seniors.length) return null;
    if (mapData.selectedSeniorId !== undefined && mapData.selectedSeniorId !== null) {
      const found = seniors.find((s) => String(s.id) === String(mapData.selectedSeniorId));
      if (found) return found;
    }
    return (
      seniors.find((s) => s.status === "Urgent") ??
      seniors.find((s) => s.heatRisk === "High") ??
      seniors[0]
    );
  }, [seniors, mapData.selectedSeniorId]);

  const [selectedSenior, setSelectedSenior] = useState<Senior | null>(initialSelectedSenior);

  const supervisedCount  = summary.supervisedSeniors ?? summary.seniorsMonitored ?? seniors.length;
  const needOutreachCount = summary.needOutreachToday ?? summary.needOutreach ?? seniors.filter((s) => s.status === "Urgent" || s.status === "Watch").length;
  const criticalCount     = summary.critical ?? summary.criticalAlerts ?? seniors.filter((s) => s.status === "Urgent").length;

  return (
    <div className="flex h-full" style={{ background: "#F0F4F8" }}>
      {/* Map area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <div
          className="px-6 py-4 shrink-0"
          style={{ background: "white", borderBottom: "1px solid #E8EDF3" }}
        >
          <div className="flex items-center justify-between gap-6">
            <div>
              <h1
                className="font-bold"
                style={{ fontSize: 18, color: "#071D3A", letterSpacing: "-0.03em" }}
              >
                National Supervision Map
              </h1>
              <p className="mt-0.5" style={{ fontSize: 13, color: "#667085" }}>
                Track seniors across the U.S. during elevated heat conditions.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <StatChip
                icon={<Users size={12} style={{ color: "#1267D8" }} />}
                label="Supervised"
                value={supervisedCount}
                bg="#EFF6FF"
                border="#BFDBFE"
                labelColor="#1267D8"
              />
              <StatChip
                icon={<Thermometer size={12} style={{ color: "#F59E0B" }} />}
                label="Need Outreach"
                value={needOutreachCount}
                bg="#FFF7ED"
                border="#FED7AA"
                labelColor="#D97706"
              />
              <StatChip
                icon={<AlertTriangle size={12} style={{ color: "#E52920" }} />}
                label="Critical"
                value={criticalCount}
                bg="#FEF2F2"
                border="#FECACA"
                labelColor="#E52920"
              />
            </div>
          </div>
        </div>

        {/* Map */}
        <div className="flex-1 relative min-h-0 p-3">
          <div className="w-full h-full rounded-xl overflow-hidden" style={{ boxShadow: "var(--shadow-sm)" }}>
            <NationalHeatMap
              seniors={seniors}
              selectedId={selectedSenior?.id}
              onSelectSenior={setSelectedSenior}
            />
          </div>
        </div>

        <MapLegend />
      </div>

      {/* Right panel */}
      <SelectedSeniorPanel senior={selectedSenior} urgentOutreach={urgentOutreach} />
    </div>
  );
}
