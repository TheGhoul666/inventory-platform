import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  Warehouse,
  ArrowLeftRight,
  Bell,
  BarChart3,
  Users,
  Bus,
  ScrollText,
  Settings,
  ChevronLeft,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { useUIStore } from "@/store/uiStore";
import { useAuthStore } from "@/store/authStore";
import { useTranslation } from "react-i18next";

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const { t } = useTranslation();
  const hasPermission = useAuthStore((s) => s.hasPermission);

  const allNavItems = [
    { path: "/",             icon: LayoutDashboard, label: t("nav.dashboard"),  permission: null },
    { path: "/inventory",    icon: Package,          label: t("nav.inventory"),  permission: null },
    { path: "/warehouses",   icon: Warehouse,        label: t("nav.warehouses"), permission: null },
    { path: "/transactions", icon: ArrowLeftRight,   label: t("nav.transactions"), permission: null },
    { path: "/alerts",       icon: Bell,             label: t("nav.alerts"),     permission: null },
    { path: "/analytics",    icon: BarChart3,        label: t("nav.analytics"),  permission: null },
    { path: "/buses",        icon: Bus,              label: t("nav.buses"),      permission: null },
    { path: "/audit",        icon: ScrollText,       label: t("nav.auditLogs"),  permission: "audit:read" },
    { path: "/users",        icon: Users,            label: t("nav.users"),      permission: "users:manage" },
    { path: "/permissions",  icon: ShieldCheck,      label: t("nav.permissions"), permission: "users:manage" },
  ];

  const navItems = allNavItems.filter(
    ({ permission }) => permission === null || hasPermission(permission)
  );

  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-forest text-ivory transition-all duration-300",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-white/15">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2">
            <Bus className="h-6 w-6 text-ivory" aria-hidden="true" />
            <span className="font-serif text-lg tracking-tight text-ivory">{t("nav.appName")}</span>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!sidebarCollapsed}
          className="p-1.5 rounded-lg text-[#d6e2cf] hover:text-white hover:bg-white/10 transition-colors ms-auto"
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform rtl:rotate-180", sidebarCollapsed && "rotate-180")} />
        </button>
      </div>

      {/* Navigation */}
      <nav aria-label="Main" className="flex-1 py-4 space-y-1 px-2 overflow-y-auto">
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            end={path === "/"}
            title={sidebarCollapsed ? label : undefined}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors group",
                isActive
                  ? "bg-ivory text-forest font-semibold"
                  : "text-[#d6e2cf] hover:text-white hover:bg-white/10"
              )
            }
          >
            <Icon className="h-5 w-5 shrink-0" />
            {!sidebarCollapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Bottom settings */}
      <div className="p-2 border-t border-white/15">
        <NavLink
          to="/settings"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[#d6e2cf] hover:text-white hover:bg-white/10 transition-colors"
        >
          <Settings className="h-5 w-5 shrink-0" />
          {!sidebarCollapsed && <span>{t("nav.settings")}</span>}
        </NavLink>
      </div>
    </aside>
  );
}
