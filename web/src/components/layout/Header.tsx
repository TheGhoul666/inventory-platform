import React from "react";
import { useNavigate } from "react-router-dom";
import { Bell, Moon, Sun, LogOut } from "lucide-react";
import { useUIStore } from "@/store/uiStore";
import { useAuthStore } from "@/store/authStore";
import { useQuery } from "@tanstack/react-query";
import { alertService } from "@/services/inventoryService";
import { useTranslation } from "react-i18next";

export function Header() {
  const { darkMode, toggleDarkMode } = useUIStore();
  const { user, roles, logout } = useAuthStore();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const isHe = i18n.language === "he";

  const { data: alertsData } = useQuery({
    queryKey: ["alerts", "open"],
    queryFn: () => alertService.listAlerts({ status: "OPEN", limit: 10 }),
    refetchInterval: 30_000,
  });

  const openAlertCount = alertsData?.alerts?.length ?? 0;

  return (
    <header className="h-16 bg-surface-800 border-b border-surface-700 flex items-center justify-between px-6">
      <div className="flex items-center gap-2 text-slate-400 text-sm">
        <span className="text-white font-medium">{t("auth.welcomeBack")}</span>
        <span>/</span>
        <span>{t("auth.subtitle")}</span>
      </div>

      <div className="flex items-center gap-3">
        {/* Language toggle */}
        <button
          onClick={() => i18n.changeLanguage(isHe ? "en" : "he")}
          className="p-2 rounded-lg bg-surface-700 hover:bg-surface-600 text-slate-300 text-xs font-bold w-9 h-9 flex items-center justify-center transition-colors"
          title={isHe ? "Switch to English" : "עבור לעברית"}
        >
          {isHe ? "EN" : "עב"}
        </button>

        {/* Alert indicator */}
        <button
          onClick={() => navigate("/alerts")}
          title={t("alerts.title")}
          className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-surface-700 transition-colors"
        >
          <Bell className="h-5 w-5" />
          {openAlertCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold">
              {openAlertCount > 9 ? "9+" : openAlertCount}
            </span>
          )}
        </button>

        {/* Dark mode toggle */}
        <button
          onClick={toggleDarkMode}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-surface-700 transition-colors"
        >
          {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>

        {/* User menu */}
        <div className="flex items-center gap-2 pl-3 border-l border-surface-700">
          <div className="h-8 w-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-sm font-bold">
            {(user?.email?.[0] ?? "U").toUpperCase()}
          </div>
          {user && (
            <div className="text-sm">
              <p className="text-white font-medium leading-none">
                {user.user_metadata?.full_name ?? user.email}
              </p>
              <p className="text-slate-400 text-xs mt-0.5">{roles[0] ?? "Viewer"}</p>
            </div>
          )}
          <button
            onClick={logout}
            className="p-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-surface-700 transition-colors ml-1"
            title={t("auth.logout")}
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
