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

export function MapView({ mapData }: Props) {
  const { seniors, summary, urgentOutreach } = mapData;

  const initialSelectedSenior = useMemo(() => {
    if (!seniors.length) return null;

    if (mapData.selectedSeniorId !== undefined && mapData.selectedSeniorId !== null) {
      const selected = seniors.find(
        (senior) => String(senior.id) === String(mapData.selectedSeniorId)
      );

      if (selected) return selected;
    }

    return (
      seniors.find((senior) => senior.status === "Urgent") ??
      seniors.find((senior) => senior.heatRisk === "High") ??
      seniors[0]
    );
  }, [seniors, mapData.selectedSeniorId]);

  const [selectedSenior, setSelectedSenior] = useState<Senior | null>(
    initialSelectedSenior
  );

  const supervisedCount = summary.supervisedSeniors ?? summary.seniorsMonitored ?? seniors.length;

  const needOutreachCount =
    summary.needOutreachToday ??
    summary.needOutreach ??
    seniors.filter((senior) => senior.status === "Urgent" || senior.status === "Watch").length;

  const criticalCount =
    summary.critical ??
    summary.criticalAlerts ??
    seniors.filter((senior) => senior.status === "Urgent").length;

  return (
    <div className="flex h-full" style={{ background: "#F8FAFC" }}>
      <div className="flex flex-col flex-1 min-w-0">
        <div
          className="px-6 py-4 shrink-0 border-b"
          style={{ background: "white", borderColor: "#D8E0EA" }}
        >
          <div className="flex items-start justify-between gap-6">
            <div>
              <h1 className="font-bold text-xl" style={{ color: "#071D3A" }}>
                National Supervision Map
              </h1>
              <p className="text-sm mt-0.5" style={{ color: "#667085" }}>
                Track seniors across the U.S. during elevated heat conditions.
              </p>
            </div>

            <div className="flex items-center gap-3 mt-1">
              <div
                className="flex items-center gap-2 rounded-md px-3 py-1.5"
                style={{ background: "#EFF6FF", border: "1px solid #BFDBFE" }}
              >
                <Users size={13} style={{ color: "#1267D8" }} />
                <span className="text-xs font-medium" style={{ color: "#1267D8" }}>
                  Supervised Seniors
                </span>
                <span className="text-xs font-bold" style={{ color: "#071D3A" }}>
                  {supervisedCount}
                </span>
              </div>

              <div
                className="flex items-center gap-2 rounded-md px-3 py-1.5"
                style={{ background: "#FFF7ED", border: "1px solid #FED7AA" }}
              >
                <Thermometer size={13} style={{ color: "#F59E0B" }} />
                <span className="text-xs font-medium" style={{ color: "#F59E0B" }}>
                  Need Outreach Today
                </span>
                <span className="text-xs font-bold" style={{ color: "#071D3A" }}>
                  {needOutreachCount}
                </span>
              </div>

              <div
                className="flex items-center gap-2 rounded-md px-3 py-1.5"
                style={{ background: "#FEF2F2", border: "1px solid #FECACA" }}
              >
                <AlertTriangle size={13} style={{ color: "#E52920" }} />
                <span className="text-xs font-medium" style={{ color: "#E52920" }}>
                  Critical
                </span>
                <span className="text-xs font-bold" style={{ color: "#071D3A" }}>
                  {criticalCount}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex-1 relative min-h-0 p-4">
          <NationalHeatMap
            seniors={seniors}
            selectedId={selectedSenior?.id}
            onSelectSenior={setSelectedSenior}
          />
        </div>

        <MapLegend />
      </div>

      <SelectedSeniorPanel
        senior={selectedSenior}
        urgentOutreach={urgentOutreach}
      />
    </div>
  );
}