import { AppShell } from "@/components/shell/AppShell";
import { OperationsDashboard } from "@/components/views/OperationsDashboard";
import { getDashboardView } from "@/lib/api";

export const metadata = { title: "Dashboard – Senior Heat Voice Lab" };

export default async function DashboardPage() {
  const dashboard = await getDashboardView();

  return (
    <AppShell>
      <OperationsDashboard
        seniors={[]}
        summary={dashboard.summary}
        alerts={dashboard.alerts}
        schedule={dashboard.schedule}
        priorities={dashboard.priorities}
        trendData={dashboard.trendData}
        pendingOperatorActions={dashboard.pendingOperatorActions}
      />
    </AppShell>
  );
}