import { AppShell } from "@/components/shell/AppShell";
import { SeniorDirectoryView } from "@/components/views/SeniorDirectoryView";
import { getSeniors } from "@/lib/api";

export const metadata = { title: "Seniors – Senior Heat Voice Lab" };

export default async function SeniorsPage() {
  const seniors = await getSeniors();
  return (
    <AppShell>
      <SeniorDirectoryView seniors={seniors} />
    </AppShell>
  );
}
