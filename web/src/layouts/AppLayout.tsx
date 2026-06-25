import React from "react";
import { Outlet, Navigate } from "react-router-dom";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { useAuthStore } from "@/store/authStore";
import { useRealtimeInventory } from "@/hooks/useRealtimeInventory";
import { useTranslation } from "react-i18next";

export function AppLayout() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const { t } = useTranslation();

  // Subscribe to live PostgreSQL changes for the entire app
  useRealtimeInventory();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface-900 flex items-center justify-center">
        <div className="text-slate-400 text-sm">{t("loading.session")}</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex h-screen bg-surface-900 text-white overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
