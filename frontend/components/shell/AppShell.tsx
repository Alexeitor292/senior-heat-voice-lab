import { LeftRail } from "./LeftRail";
import { TopBar } from "./TopBar";

interface Props {
  children: React.ReactNode;
}

export function AppShell({ children }: Props) {
  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "#F8FAFC" }}>
      <LeftRail />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
