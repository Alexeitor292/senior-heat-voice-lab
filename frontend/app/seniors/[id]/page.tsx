import { notFound } from "next/navigation";
import { AppShell } from "@/components/shell/AppShell";
import { SeniorDetailView } from "@/components/views/SeniorDetailView";
import { getSenior, getSeniorTimeline } from "@/lib/api";

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props) {
  const { id } = await params;
  const senior = await getSenior(id);

  return {
    title: senior ? `${senior.name} – Senior Heat Voice Lab` : "Senior Not Found",
  };
}

export default async function SeniorDetailPage({ params }: Props) {
  const { id } = await params;
  const senior = await getSenior(id);

  if (!senior) notFound();

  const timeline = await getSeniorTimeline(id);

  return (
    <AppShell>
      <SeniorDetailView senior={senior} timeline={timeline} />
    </AppShell>
  );
}