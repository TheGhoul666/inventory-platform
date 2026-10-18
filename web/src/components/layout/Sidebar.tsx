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
        "flex flex-col h-full bg-surface-800 border-e border-surface-700 transition-all duration-300",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-surface-700">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 shadow-md shadow-brand-900/50"><Bus className="h-4 w-4 text-white" /></span>
            <span className="font-semibold tracking-tight text-ink text-sm">{t("nav.appName")}</span>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!sidebarCollapsed}
          className="p-1.5 rounded-lg text-slate-400 hover:text-ink hover:bg-surface-700 transition-colors ms-auto"
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
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors group",
                isActive
                  ? "bg-brand-600 text-white shadow-md shadow-brand-900/40"
                  : "text-slate-400 hover:text-ink hover:bg-surface-700"
              )
            }
          >
            <Icon className="h-5 w-5 shrink-0" />
            {!sidebarCollapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Bottom settings */}
      <div className="p-2 border-t border-surface-700">
        <NavLink
          to="/settings"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-ink hover:bg-surface-700 transition-colors"
        >
          <Settings className="h-5 w-5 shrink-0" />
          {!sidebarCollapsed && <span>{t("nav.settings")}</span>}
        </NavLink>
      </div>
    </aside>
  );
}
