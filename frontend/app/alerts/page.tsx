import Link from "next/link";
import { AlertTriangle, CheckCircle } from "lucide-react";
import { AppShell } from "@/components/shell/AppShell";
import { getAlerts } from "@/lib/api";
import { riskColor } from "@/lib/risk";

export const metadata = { title: "Alerts – Senior Heat Voice Lab" };

export default async function AlertsPage() {
  const alerts = await getAlerts();
  const unacked = alerts.filter((a) => !a.acknowledged);
  const acked = alerts.filter((a) => a.acknowledged);

  return (
    <AppShell>
      <div className="p-6 overflow-auto h-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-bold text-2xl" style={{ color: "#071D3A" }}>
              Alerts
            </h1>
            <p className="text-sm mt-1" style={{ color: "#667085" }}>
              {unacked.length} unacknowledged alert{unacked.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>

        {/* Alert list */}
        <div className="max-w-3xl space-y-6">
          {unacked.length > 0 && (
            <section>
              <h2 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: "#667085" }}>
                Needs Attention
              </h2>
              <div className="space-y-2">
                {unacked.map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-start gap-4 rounded-lg px-5 py-4"
                    style={{
                      background: "white",
                      border: `1px solid ${riskColor(alert.severity)}40`,
                    }}
                  >
                    <AlertTriangle
                      size={16}
                      className="shrink-0 mt-0.5"
                      style={{ color: riskColor(alert.severity) }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline justify-between gap-4 mb-1">
                        <span className="font-semibold text-sm" style={{ color: "#071D3A" }}>
                          {alert.type}
                        </span>
                        <span className="text-xs shrink-0" style={{ color: "#8FA8C8" }}>
                          {alert.time}
                        </span>
                      </div>
                      <p className="text-sm mb-1" style={{ color: "#667085" }}>
                        {alert.message}
                      </p>
                      <Link
                        href={`/seniors/${alert.seniorId}`}
                        className="text-xs hover:underline"
                        style={{ color: "#1267D8" }}
                      >
                        {alert.seniorName}
                        {alert.seniorAge ? `, ${alert.seniorAge}` : ""}
                        {alert.location ? ` · ${alert.location}` : ""}
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {acked.length > 0 && (
            <section>
              <h2 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: "#667085" }}>
                Acknowledged
              </h2>
              <div className="space-y-2">
                {acked.map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-start gap-4 rounded-lg px-5 py-4"
                    style={{ background: "white", border: "1px solid #D8E0EA" }}
                  >
                    <CheckCircle size={16} className="shrink-0 mt-0.5" style={{ color: "#22C55E" }} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline justify-between gap-4 mb-1">
                        <span className="font-semibold text-sm" style={{ color: "#667085" }}>
                          {alert.type}
                        </span>
                        <span className="text-xs shrink-0" style={{ color: "#8FA8C8" }}>
                          {alert.time}
                        </span>
                      </div>
                      <p className="text-sm" style={{ color: "#8FA8C8" }}>
                        {alert.message}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    </AppShell>
  );
}
