"use client";

import { Search, Bell, Calendar } from "lucide-react";

const TODAY = new Date().toLocaleDateString("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
});

export function TopBar() {
  return (
    <header
      className="flex items-center justify-between px-6 shrink-0"
      style={{
        height: 56,
        background: "white",
        borderBottom: "1px solid #E8EDF3",
      }}
    >
      {/* Search */}
      <div className="relative flex-1 max-w-[280px]">
        <Search
          size={13}
          className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
          style={{ color: "#94A8BC" }}
        />
        <input
          type="text"
          placeholder="Search seniors, locations…"
          className="w-full rounded-md pl-8 pr-3 py-[7px]"
          style={{
            border: "1px solid #E2E8F0",
            background: "#F8FAFC",
            color: "#071D3A",
            fontSize: 13,
            fontFamily: "inherit",
          }}
        />
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-2.5">
        {/* Date chip */}
        <div
          className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5"
          style={{ background: "#F1F5F9", border: "1px solid #E2E8F0" }}
        >
          <Calendar size={11} style={{ color: "#667085" }} />
          <span className="font-medium tabular" style={{ fontSize: 11.5, color: "#4A6070" }}>
            {TODAY}
          </span>
        </div>

        {/* Bell */}
        <button
          className="relative flex items-center justify-center rounded-lg transition-interactive"
          style={{
            width: 34,
            height: 34,
            background: "transparent",
            border: "1px solid transparent",
            cursor: "pointer",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.background = "#F1F5F9";
            (e.currentTarget as HTMLElement).style.borderColor = "#E2E8F0";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.background = "transparent";
            (e.currentTarget as HTMLElement).style.borderColor = "transparent";
          }}
        >
          <Bell size={16} style={{ color: "#667085" }} />
          <span
            className="absolute flex items-center justify-center rounded-full text-white font-bold"
            style={{ top: 5, right: 5, width: 13, height: 13, background: "#E52920", fontSize: 8 }}
          >
            3
          </span>
        </button>

        {/* Avatar */}
        <button
          className="flex items-center justify-center rounded-full text-white font-semibold transition-interactive"
          style={{
            width: 32,
            height: 32,
            background: "linear-gradient(135deg, #1267D8 0%, #0E51B0 100%)",
            fontSize: 11,
            letterSpacing: "0.03em",
            boxShadow: "0 1px 3px rgb(18 103 216 / 0.28)",
            cursor: "pointer",
          }}
        >
          JM
        </button>
      </div>
    </header>
  );
}
