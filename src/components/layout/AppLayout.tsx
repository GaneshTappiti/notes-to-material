import { PropsWithChildren, useCallback } from "react";
import SidebarNav from "./SidebarNav";
import Topbar from "./Topbar";

const AppLayout = ({ children }: PropsWithChildren) => {
  const handlePointer = useCallback((e: React.MouseEvent) => {
    const root = document.documentElement;
    root.style.setProperty("--glow-x", `${e.clientX}px`);
    root.style.setProperty("--glow-y", `${e.clientY}px`);
  }, []);

  return (
    <div className="min-h-screen bg-hero-glow" onMouseMove={handlePointer}>
      <div className="flex">
        <SidebarNav />
        <div className="flex-1 min-w-0">
          <Topbar />
          <main className="px-4 py-6">{children}</main>
        </div>
      </div>
    </div>
  );
};

export default AppLayout;
