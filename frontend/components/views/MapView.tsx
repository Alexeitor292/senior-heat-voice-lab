"use client";

import { useState } from "react";
import { Users, Thermometer, AlertTriangle } from "lucide-react";
import { NationalHeatMap } from "@/components/map/NationalHeatMap";
import { SelectedSeniorPanel } from "@/components/map/SelectedSeniorPanel";
import { MapLegend } from "@/components/map/MapLegend";
import type { Senior } from "@/lib/types";
import { URGENT_OUTREACH } from "@/lib/mock-data";

interface Props {
  seniors: Senior[];
}

export function MapView({ seniors }: Props) {
  const [selectedSenior, setSelectedSenior] = useState<Senior | null>(
    seniors.find((s) => s.id === "eleanor-jennings") ?? null
  );

  const urgentCount = seniors.filter(
    (s) => s.status === "Urgent" || s.status === "Watch"
  ).length;

  return (
    <div className="flex h-full" style={{ background: "#F8FAFC" }}>
      {/* Map area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header strip */}
        <div
          className="px-6 py-4 shrink-0 border-b"
          style={{ background: "white", borderColor: "#D8E0EA" }}
        >
          <div className="flex items-start justify-between">
            <div>
              <h1 className="font-bold text-xl" style={{ color: "#071D3A" }}>
                National Supervision Map
              </h1>
              <p className="text-sm mt-0.5" style={{ color: "#667085" }}>
                Track seniors across the U.S. during elevated heat conditions.
              </p>
            </div>

            {/* Metric badges */}
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
                  {seniors.length}
                </span>
              </div>

              <div
                className="flex items-center gap-2 rounded-md px-3 py-1.5"
                style={{ background: "#FFF7ED", border: "1px solid #FED7AA" }}
              >
                <Thermometer size={13} style={{ color: "#F59E0B" }} />
                <span className="text-xs font-medium" style={{ color: "#F59E0B" }}>
                  Heat Outreach Today
                </span>
                <span className="text-xs font-bold" style={{ color: "#071D3A" }}>
                  {urgentCount}
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
                  3
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Map canvas */}
        <div className="flex-1 relative min-h-0 p-4">
          <NationalHeatMap
            seniors={seniors}
            selectedId={selectedSenior?.id}
            onSelectSenior={setSelectedSenior}
          />
        </div>

        {/* Legend */}
        <MapLegend />
      </div>

      {/* Right panel */}
      <SelectedSeniorPanel
        senior={selectedSenior}
        urgentOutreach={URGENT_OUTREACH}
      />
    </div>
  );
}
