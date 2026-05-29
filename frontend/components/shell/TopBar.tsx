"use client";

import { Search, Bell, Calendar } from "lucide-react";

export function TopBar() {
  return (
    <header
      className="flex items-center justify-between px-6 shrink-0"
      style={{
        height: 56,
        background: "white",
        borderBottom: "1px solid #D8E0EA",
      }}
    >
      {/* Search */}
      <div className="relative flex-1 max-w-xs">
        <Search
          size={14}
          className="absolute left-3 top-1/2 -translate-y-1/2"
          style={{ color: "#667085" }}
        />
        <input
          type="text"
          placeholder="Search seniors, locations…"
          className="w-full rounded border pl-8 pr-3 py-1.5 text-sm outline-none focus:border-teal transition-colors"
          style={{
            borderColor: "#D8E0EA",
            background: "#F8FAFC",
            color: "#071D3A",
            fontSize: 13,
          }}
        />
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-4">
        {/* Date */}
        <div className="flex items-center gap-1.5 text-sm" style={{ color: "#667085" }}>
          <Calendar size={14} style={{ color: "#667085" }} />
          <span style={{ fontSize: 13 }}>May 29, 2025</span>
        </div>

        {/* Bell */}
        <button className="relative p-1.5 rounded hover:bg-gray-100 transition-colors">
          <Bell size={18} style={{ color: "#667085" }} />
          <span
            className="absolute top-0.5 right-0.5 rounded-full text-white font-bold flex items-center justify-center"
            style={{
              width: 14,
              height: 14,
              background: "#E52920",
              fontSize: 9,
            }}
          >
            3
          </span>
        </button>

        {/* User */}
        <div
          className="flex items-center justify-center rounded-full text-white font-semibold text-xs"
          style={{
            width: 32,
            height: 32,
            background: "#1267D8",
            userSelect: "none",
          }}
        >
          JM
        </div>
      </div>
    </header>
  );
}
