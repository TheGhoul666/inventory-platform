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
} from "lucide-react";
import { cn } from "@/utils/cn";
import { useUIStore } from "@/store/uiStore";
import { useTranslation } from "react-i18next";

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const { t } = useTranslation();

  const navItems = [
    { path: "/", icon: LayoutDashboard, label: t("nav.dashboard") },
    { path: "/inventory", icon: Package, label: t("nav.inventory") },
    { path: "/warehouses", icon: Warehouse, label: t("nav.warehouses") },
    { path: "/transactions", icon: ArrowLeftRight, label: t("nav.transactions") },
    { path: "/alerts", icon: Bell, label: t("nav.alerts") },
    { path: "/analytics", icon: BarChart3, label: t("nav.analytics") },
    { path: "/buses", icon: Bus, label: t("nav.buses") },
    { path: "/audit", icon: ScrollText, label: t("nav.auditLogs") },
    { path: "/users", icon: Users, label: t("nav.users") },
  ];

  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-surface-800 border-r border-surface-700 transition-all duration-300 rtl:border-r-0 rtl:border-l",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-surface-700">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2">
            <Bus className="h-6 w-6 text-brand-500" />
            <span className="font-bold text-white text-sm">{t("nav.appName")}</span>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-surface-700 transition-colors ml-auto rtl:ml-0 rtl:mr-auto"
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform", sidebarCollapsed && "rotate-180")} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1 px-2 overflow-y-auto">
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            end={path === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group",
                isActive
                  ? "bg-brand-600 text-white"
                  : "text-slate-400 hover:text-white hover:bg-surface-700"
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
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-surface-700 transition-colors"
        >
          <Settings className="h-5 w-5 shrink-0" />
          {!sidebarCollapsed && <span>{t("nav.settings")}</span>}
        </NavLink>
      </div>
    </aside>
  );
}
