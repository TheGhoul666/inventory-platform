import React from "react";
import { Outlet, Navigate } from "react-router-dom";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { useAuthStore } from "@/store/authStore";
import { useRealtimeInventory } from "@/hooks/useRealtimeInventory";
import { useTranslation } from "react-i18next";
import { LegalLinks } from "@/components/layout/LegalLinks";

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
    <div className="flex h-screen bg-surface-900 text-ink overflow-hidden">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:m-2 focus:rounded-lg focus:bg-brand-600 focus:px-4 focus:py-2">Skip to content</a>
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main id="main" className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
        <footer className="border-t border-surface-700 bg-surface-800/60 px-4 py-2">
          <LegalLinks />
        </footer>
      </div>
    </div>
  );
}
