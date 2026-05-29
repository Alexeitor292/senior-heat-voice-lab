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
  ClipboardList,
} from "lucide-react";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/seniors",   label: "Seniors",   icon: Users },
  { href: "/map",       label: "Map",        icon: Map },
  { href: "/actions",   label: "Actions",    icon: ClipboardList },
  { href: "/heat-checks/live-eleanor", label: "Heat Checks", icon: PhoneCall },
  { href: "/alerts",    label: "Alerts",     icon: Bell },
];

const BOTTOM_NAV = [{ href: "/settings", label: "Settings", icon: Settings }];

export function LeftRail() {
  const pathname = usePathname();

  function isActive(href: string) {
    if (href === "/heat-checks/live-eleanor") return pathname.startsWith("/heat-checks");
    if (href === "/seniors") return pathname.startsWith("/seniors");
    return pathname === href || pathname.startsWith(href + "/");
  }

  return (
    <aside
      className="flex flex-col h-full shrink-0"
      style={{ width: 220, minWidth: 220, background: "#071D3A", borderRight: "1px solid #0C2E52" }}
    >
      {/* Brand */}
      <div
        className="flex items-center gap-2.5 px-5 py-[18px]"
        style={{ borderBottom: "1px solid #0C2E52" }}
      >
        <div className="flex items-center justify-center rounded-lg" style={{ width: 28, height: 28 }}>
          <Activity size={19} color="#22C7C9" strokeWidth={2.25} />
        </div>
        <span
          className="text-white font-semibold leading-snug"
          style={{ fontSize: 12.5, letterSpacing: "-0.01em" }}
        >
          Senior Heat<br />Voice Lab
        </span>
      </div>

      {/* Main nav */}
      <nav className="flex-1 pt-2 px-2 space-y-px">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              className="relative flex items-center gap-2.5 rounded-md px-3 py-[9px] group transition-interactive"
              style={{
                color: active ? "#22C7C9" : "#6D90B0",
                background: active ? "rgba(34,199,201,0.09)" : "transparent",
              }}
              onMouseEnter={(e) => {
                if (!active) {
                  (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)";
                  (e.currentTarget as HTMLElement).style.color = "#9ABCD4";
                }
              }}
              onMouseLeave={(e) => {
                if (!active) {
                  (e.currentTarget as HTMLElement).style.background = "transparent";
                  (e.currentTarget as HTMLElement).style.color = "#6D90B0";
                }
              }}
            >
              {active && (
                <span
                  className="absolute left-0 top-[7px] bottom-[7px] rounded-full"
                  style={{ width: 3, background: "#22C7C9" }}
                />
              )}
              <Icon
                size={15}
                strokeWidth={active ? 2.25 : 1.75}
                color="currentColor"
              />
              <span
                className="font-medium"
                style={{ fontSize: 13, letterSpacing: "-0.005em" }}
              >
                {label}
              </span>
              {label === "Alerts" && (
                <span
                  className="ml-auto flex items-center justify-center rounded-full font-bold text-white"
                  style={{ width: 18, height: 18, background: "#E52920", fontSize: 9 }}
                >
                  3
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="px-2 pb-2" style={{ borderTop: "1px solid #0C2E52" }}>
        <div className="pt-2 space-y-px">
          {BOTTOM_NAV.map(({ href, label, icon: Icon }) => {
            const active = isActive(href);
            return (
              <Link
                key={href}
                href={href}
                className="flex items-center gap-2.5 rounded-md px-3 py-[9px] transition-interactive"
                style={{
                  color: active ? "#22C7C9" : "#6D90B0",
                  background: active ? "rgba(34,199,201,0.09)" : "transparent",
                }}
                onMouseEnter={(e) => {
                  if (!active) {
                    (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)";
                    (e.currentTarget as HTMLElement).style.color = "#9ABCD4";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!active) {
                    (e.currentTarget as HTMLElement).style.background = "transparent";
                    (e.currentTarget as HTMLElement).style.color = "#6D90B0";
                  }
                }}
              >
                <Icon size={15} strokeWidth={1.75} color="currentColor" />
                <span className="font-medium" style={{ fontSize: 13 }}>{label}</span>
              </Link>
            );
          })}
        </div>

        <div className="flex items-center gap-2.5 px-3 py-3 mt-1">
          <div
            className="flex items-center justify-center rounded-full shrink-0"
            style={{ width: 28, height: 28, background: "#09294D" }}
          >
            <Wifi size={13} color="#22C7C9" strokeWidth={2} />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="rounded-full" style={{ width: 6, height: 6, background: "#22C55E", display: "inline-block" }} />
              <span className="font-semibold" style={{ fontSize: 11.5, color: "#D4E4F0" }}>Connected</span>
            </div>
            <div style={{ fontSize: 11, color: "#3D607E", lineHeight: 1.4 }}>Daily Check</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
