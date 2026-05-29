import { AppShell } from "@/components/shell/AppShell";
import { MapView } from "@/components/views/MapView";
import { getMapView } from "@/lib/api";

export const metadata = { title: "Map – Senior Heat Voice Lab" };

export default async function MapPage() {
  const mapData = await getMapView();

  return (
    <AppShell>
      <MapView mapData={mapData} />
    </AppShell>
  );
}