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

  const { user, roles } = useAuthStore();
  const displayName = (user?.user_metadata?.full_name as string | undefined) ?? user?.email ?? "";

  return (
    <aside
      className={cn(
        "flex h-full flex-col rounded-2xl border border-surface-600 bg-surface-800 transition-all duration-300",
        sidebarCollapsed ? "w-[72px]" : "w-60"
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white" aria-hidden="true">
              <Bus className="h-5 w-5" />
            </span>
            <span className="text-lg font-extrabold tracking-tight text-ink">{t("nav.appName")}</span>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? t("a11y.expandSidebar") : t("a11y.collapseSidebar")}
          aria-expanded={!sidebarCollapsed}
          className="ms-auto rounded-full p-1.5 text-slate-400 transition-colors hover:bg-surface-700 hover:text-ink"
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform rtl:rotate-180", sidebarCollapsed && "rotate-180")} />
        </button>
      </div>

      {/* Navigation */}
      <nav aria-label="Main" className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            end={path === "/"}
            title={sidebarCollapsed ? label : undefined}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-full px-4 py-2.5 text-[15px] font-medium transition-colors",
                isActive ? "bg-brand-600 font-semibold text-white" : "text-slate-400 hover:bg-surface-700 hover:text-ink"
              )
            }
          >
            <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
            {!sidebarCollapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Settings + current user */}
      <div className="space-y-2 p-3">
        <NavLink
          to="/settings"
          title={sidebarCollapsed ? t("nav.settings") : undefined}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-full px-4 py-2.5 text-[15px] font-medium transition-colors",
              isActive ? "bg-brand-600 font-semibold text-white" : "text-slate-400 hover:bg-surface-700 hover:text-ink"
            )
          }
        >
          <Settings className="h-5 w-5 shrink-0" aria-hidden="true" />
          {!sidebarCollapsed && <span>{t("nav.settings")}</span>}
        </NavLink>
        {!sidebarCollapsed && user && (
          <div className="rounded-2xl bg-sage px-4 py-3 text-sm leading-snug text-brand-700">
            <p className="truncate font-bold">{displayName}</p>
            <p>{roles[0] ?? "Viewer"}</p>
          </div>
        )}
      </div>
    </aside>
  );
}
