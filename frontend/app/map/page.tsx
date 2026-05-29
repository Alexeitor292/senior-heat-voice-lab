import { AppShell } from "@/components/shell/AppShell";
import { MapView } from "@/components/views/MapView";
import { getMapSeniors } from "@/lib/api";

export const metadata = { title: "Map – Senior Heat Voice Lab" };

export default async function MapPage() {
  const seniors = await getMapSeniors();
  return (
    <AppShell>
      <MapView seniors={seniors} />
    </AppShell>
  );
}
