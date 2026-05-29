import { AppShell } from "@/components/shell/AppShell";
import { OperationsDashboard } from "@/components/views/OperationsDashboard";
import { getSeniors, getDashboardSummary, getAlerts } from "@/lib/api";
import {
  MOCK_PRIORITIES,
  MOCK_SCHEDULE,
  HEAT_TREND_DATA,
} from "@/lib/mock-data";

export const metadata = { title: "Dashboard – Senior Heat Voice Lab" };

export default async function DashboardPage() {
  const [seniors, summary, alerts] = await Promise.all([
    getSeniors(),
    getDashboardSummary(),
    getAlerts(),
  ]);

  return (
    <AppShell>
      <OperationsDashboard
        seniors={seniors}
        summary={summary}
        alerts={alerts}
        schedule={MOCK_SCHEDULE}
        priorities={MOCK_PRIORITIES}
        trendData={HEAT_TREND_DATA}
      />
    </AppShell>
  );
}
