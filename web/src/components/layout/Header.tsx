import React from "react";
import { useNavigate } from "react-router-dom";
import { Bell, LogOut } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { useQuery } from "@tanstack/react-query";
import { alertService } from "@/services/inventoryService";
import { useTranslation } from "react-i18next";

export function Header() {
  const { logout } = useAuthStore();
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
    <header className="flex h-12 items-center justify-end gap-2">
      {/* Language toggle */}
      <button
        onClick={() => i18n.changeLanguage(isHe ? "en" : "he")}
        className="btn-secondary flex h-9 w-9 items-center justify-center text-xs font-bold"
        title={isHe ? "Switch to English" : "עבור לעברית"}
        aria-label={isHe ? "Switch to English" : "עבור לעברית"}
      >
        {isHe ? "EN" : "עב"}
      </button>

      {/* Alert indicator */}
      <button
        onClick={() => navigate("/alerts")}
        title={t("alerts.title")}
        aria-label={t("alerts.title")}
        className="btn-secondary relative flex h-9 w-9 items-center justify-center"
      >
        <Bell className="h-[18px] w-[18px]" aria-hidden="true" />
        {openAlertCount > 0 && (
          <span className="absolute -end-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-clay px-1 text-xs font-bold text-white">
            {openAlertCount > 9 ? "9+" : openAlertCount}
          </span>
        )}
      </button>

      <button
        onClick={logout}
        className="btn-secondary flex h-9 items-center gap-2 px-4 text-sm"
        title={t("auth.logout")}
      >
        <LogOut className="h-4 w-4" aria-hidden="true" />
        {t("auth.logout")}
      </button>
    </header>
  );
}
