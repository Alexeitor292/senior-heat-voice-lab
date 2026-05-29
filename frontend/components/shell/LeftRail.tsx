"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  Map,
  PhoneCall,
  Bell,
  Settings,
  Activity,
  Wifi,
} from "lucide-react";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/seniors", label: "Seniors", icon: Users },
  { href: "/map", label: "Map", icon: Map },
  { href: "/heat-checks/live-eleanor", label: "Heat Checks", icon: PhoneCall },
  { href: "/alerts", label: "Alerts", icon: Bell },
];

const BOTTOM_NAV = [
  { href: "/settings", label: "Settings", icon: Settings },
];

export function LeftRail() {
  const pathname = usePathname();

  function isActive(href: string) {
    if (href === "/heat-checks/live-eleanor") {
      return pathname.startsWith("/heat-checks");
    }
    if (href === "/seniors") {
      return pathname.startsWith("/seniors");
    }
    return pathname === href || pathname.startsWith(href + "/");
  }

  return (
    <aside
      className="flex flex-col h-full"
      style={{
        width: 220,
        minWidth: 220,
        background: "#071D3A",
        borderRight: "1px solid #0D3560",
      }}
    >
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b" style={{ borderColor: "#0D3560" }}>
        <div
          className="flex items-center justify-center rounded"
          style={{ width: 28, height: 28 }}
        >
          <Activity size={20} color="#22C7C9" strokeWidth={2} />
        </div>
        <span
          className="text-white font-semibold leading-tight"
          style={{ fontSize: 12.5 }}
        >
          Senior Heat<br />Voice Lab
        </span>
      </div>

      {/* Main nav */}
      <nav className="flex-1 pt-2 px-2">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              className="relative flex items-center gap-3 rounded px-3 py-2.5 mb-0.5 transition-colors group"
              style={{
                color: active ? "#22C7C9" : "#8FA8C8",
                background: active ? "rgba(34,199,201,0.08)" : "transparent",
              }}
            >
              {active && (
                <span
                  className="absolute left-0 top-1 bottom-1 rounded-full"
                  style={{ width: 3, background: "#22C7C9" }}
                />
              )}
              <Icon
                size={16}
                strokeWidth={active ? 2 : 1.75}
                color={active ? "#22C7C9" : "#8FA8C8"}
              />
              <span
                className="text-sm font-medium"
                style={{ color: active ? "#22C7C9" : "#8FA8C8" }}
              >
                {label}
              </span>
              {label === "Alerts" && (
                <span
                  className="ml-auto text-xs font-semibold rounded-full px-1.5 py-0.5 leading-none"
                  style={{ background: "#E52920", color: "white", fontSize: 10 }}
                >
                  3
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom nav */}
      <div className="px-2 pb-2 border-t" style={{ borderColor: "#0D3560" }}>
        <div className="pt-2">
          {BOTTOM_NAV.map(({ href, label, icon: Icon }) => {
            const active = isActive(href);
            return (
              <Link
                key={href}
                href={href}
                className="flex items-center gap-3 rounded px-3 py-2.5 transition-colors"
                style={{
                  color: active ? "#22C7C9" : "#8FA8C8",
                  background: active ? "rgba(34,199,201,0.08)" : "transparent",
                }}
              >
                <Icon size={16} strokeWidth={1.75} />
                <span className="text-sm font-medium">{label}</span>
              </Link>
            );
          })}
        </div>

        {/* Status */}
        <div className="flex items-center gap-2.5 px-3 py-3 mt-1">
          <div
            className="flex items-center justify-center rounded-full"
            style={{ width: 28, height: 28, background: "#09294D" }}
          >
            <Wifi size={13} color="#22C7C9" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span
                className="rounded-full"
                style={{ width: 6, height: 6, background: "#22C55E", display: "inline-block" }}
              />
              <span className="text-xs font-medium" style={{ color: "#E2EAF4" }}>
                Connected
              </span>
            </div>
            <div className="text-xs" style={{ color: "#5A7EA8", lineHeight: "1.3" }}>
              Daily Check
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
