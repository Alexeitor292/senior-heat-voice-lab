import { AppShell } from "@/components/shell/AppShell";
import { ActionQueueView } from "@/components/views/ActionQueueView";

export const metadata = { title: "Action Queue – Senior Heat Voice Lab" };

export default function ActionsPage() {
  return (
    <AppShell>
      <ActionQueueView />
    </AppShell>
  );
}