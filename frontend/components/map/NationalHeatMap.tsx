"use client";

import { useEffect, useState } from "react";
import { geoAlbersUsa, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import type { Topology } from "topojson-specification";
import type { Senior } from "@/lib/types";
import { statusColor } from "@/lib/risk";

// FIPS code → ambient heat level for state fill
const STATE_HEAT: Record<string, "Low" | "Moderate" | "High" | "Extreme"> = {
  "01": "High",     // AL
  "02": "Low",      // AK
  "04": "Extreme",  // AZ
  "05": "High",     // AR
  "06": "High",     // CA
  "08": "Moderate", // CO
  "09": "Low",      // CT
  "10": "Moderate", // DE
  "11": "Moderate", // DC
  "12": "Extreme",  // FL
  "13": "High",     // GA
  "15": "High",     // HI
  "16": "Low",      // ID
  "17": "Moderate", // IL
  "18": "Moderate", // IN
  "19": "Low",      // IA
  "20": "High",     // KS
  "21": "Moderate", // KY
  "22": "Extreme",  // LA
  "23": "Low",      // ME
  "24": "Moderate", // MD
  "25": "Low",      // MA
  "26": "Low",      // MI
  "27": "Low",      // MN
  "28": "High",     // MS
  "29": "Moderate", // MO
  "30": "Low",      // MT
  "31": "Moderate", // NE
  "32": "Extreme",  // NV
  "33": "Low",      // NH
  "34": "Moderate", // NJ
  "35": "Extreme",  // NM
  "36": "Low",      // NY
  "37": "High",     // NC
  "38": "Low",      // ND
  "39": "Moderate", // OH
  "40": "Extreme",  // OK
  "41": "Low",      // OR
  "42": "Moderate", // PA
  "44": "Low",      // RI
  "45": "High",     // SC
  "46": "Low",      // SD
  "47": "High",     // TN
  "48": "Extreme",  // TX
  "49": "High",     // UT
  "50": "Low",      // VT
  "51": "Moderate", // VA
  "53": "Low",      // WA
  "54": "Moderate", // WV
  "55": "Low",      // WI
  "56": "Low",      // WY
};

const HEAT_FILLS: Record<string, string> = {
  Low:      "rgba(34,199,201,0.22)",
  Moderate: "rgba(18,103,216,0.18)",
  High:     "rgba(245,158,11,0.35)",
  Extreme:  "rgba(229,41,32,0.38)",
};

const HEAT_STROKES: Record<string, string> = {
  Low:      "rgba(34,199,201,0.45)",
  Moderate: "rgba(18,103,216,0.35)",
  High:     "rgba(245,158,11,0.55)",
  Extreme:  "rgba(229,41,32,0.6)",
};

const projection = geoAlbersUsa();
const pathGen = geoPath(projection);

interface Props {
  seniors: Senior[];
  selectedId?: string | number | null;
  onSelectSenior: (senior: Senior | null) => void;
}

export function NationalHeatMap({ seniors, selectedId, onSelectSenior }: Props) {
  const [topology, setTopology] = useState<Topology | null>(null);

  useEffect(() => {
    fetch("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json")
      .then((r) => r.json())
      .then((t) => setTopology(t as Topology))
      .catch(() => undefined);
  }, []);

  const statePaths = topology
    ? (() => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const geo = feature(topology, (topology as any).objects.states) as unknown as GeoJSON.FeatureCollection;
        return geo.features.map((f) => {
          const fips = String((f as { id?: number }).id ?? "").padStart(2, "0");
          const heat = STATE_HEAT[fips] ?? "Low";
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const d = pathGen(f as any);
          if (!d) return null;
          return (
            <path
              key={fips}
              d={d}
              fill={HEAT_FILLS[heat]}
              stroke={HEAT_STROKES[heat]}
              strokeWidth={0.7}
            />
          );
        });
      })()
    : null;

  return (
    <svg
      viewBox="0 0 960 500"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
      style={{ display: "block" }}
    >
      <rect width={960} height={500} fill="#EBF3F8" />
      {statePaths}
      {seniors.map((s) => {
        const pt = projection([s.lng, s.lat]);
        if (!pt) return null;
        const [x, y] = pt;
        const color = statusColor(s.status);
        const isSelected = String(s.id) === String(selectedId);
        return (
          <g
            key={s.id}
            transform={`translate(${x},${y})`}
            style={{ cursor: "pointer" }}
            onClick={() => onSelectSenior(isSelected ? null : s)}
          >
            {isSelected && (
              <circle r={14} fill={color} opacity={0.22} />
            )}
            <circle r={6} fill={color} stroke="white" strokeWidth={2} />
          </g>
        );
      })}
    </svg>
  );
}
