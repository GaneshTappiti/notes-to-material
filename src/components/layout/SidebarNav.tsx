import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Upload, Cog, FileText, Settings, FileClock, Layers, ListChecks, BookOpen, History } from "lucide-react";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/uploads", label: "Uploads", icon: Upload },
  { to: "/queue", label: "Processing Queue", icon: FileClock },
  { to: "/review", label: "Review Center", icon: ListChecks },
  { to: "/templates", label: "Templates & Export", icon: Layers },
  { to: "/exports", label: "Exports", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/logs", label: "Logs / Activity", icon: History },
];

const SidebarNav = () => {
  return (
    <aside className="hidden md:flex md:flex-col md:w-64 border-r bg-card/40 backdrop-blur-sm">
      <div className="h-16 flex items-center px-5 border-b">
        <span className="text-lg font-semibold">Scollab</span>
      </div>
      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-3">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "group flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                      isActive
                        ? "bg-secondary text-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-foreground"
                    )
                  }
                  aria-label={item.label}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  <span>{item.label}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="p-4 text-xs text-muted-foreground border-t">
        v1 • Crafted for colleges
      </div>
    </aside>
  );
};

export default SidebarNav;
