import { notFound } from "next/navigation";
import { AppShell } from "@/components/shell/AppShell";
import { ActiveHeatCheckView } from "@/components/views/ActiveHeatCheckView";
import { getHeatCheck } from "@/lib/api";

interface Props {
  params: Promise<{ callId: string }>;
}

export const metadata = { title: "Heat Check – Senior Heat Voice Lab" };

export default async function HeatCheckPage({ params }: Props) {
  const { callId } = await params;
  const heatCheck = await getHeatCheck(callId);
  if (!heatCheck) notFound();

  return (
    <AppShell>
      <ActiveHeatCheckView heatCheck={heatCheck} />
    </AppShell>
  );
}
