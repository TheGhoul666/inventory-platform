import React, { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider, Navigate } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { LoginPage } from "@/pages/LoginPage";
import { useAuthStore } from "@/store/authStore";

// Lazy-load pages for code splitting
const Dashboard = lazy(() => import("@/pages/Dashboard").then((m) => ({ default: m.Dashboard })));
const InventoryPage = lazy(() => import("@/pages/InventoryPage").then((m) => ({ default: m.InventoryPage })));
const AlertsPage = lazy(() => import("@/pages/AlertsPage").then((m) => ({ default: m.AlertsPage })));
const AnalyticsPage = lazy(() => import("@/pages/AnalyticsPage").then((m) => ({ default: m.AnalyticsPage })));
const WarehousesPage = lazy(() => import("@/pages/WarehousesPage").then((m) => ({ default: m.WarehousesPage })));
const WarehouseDetailPage = lazy(() => import("@/pages/WarehouseDetailPage").then((m) => ({ default: m.WarehouseDetailPage })));
const UsersPage = lazy(() => import("@/pages/UsersPage").then((m) => ({ default: m.UsersPage })));
const PermissionsPage = lazy(() => import("@/pages/PermissionsPage").then((m) => ({ default: m.PermissionsPage })));
const BusesPage = lazy(() => import("@/pages/BusesPage").then((m) => ({ default: m.BusesPage })));
const TransactionsPage = lazy(() => import("@/pages/TransactionsPage").then((m) => ({ default: m.TransactionsPage })));
const AuditLogsPage = lazy(() => import("@/pages/AuditLogsPage").then((m) => ({ default: m.AuditLogsPage })));
const SettingsPage = lazy(() => import("@/pages/SettingsPage").then((m) => ({ default: m.SettingsPage })));

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64 text-slate-400 text-sm">
      טוען…
    </div>
  );
}

/**
 * Unified route guard — holds rendering until auth is resolved, then applies
 * the provided predicate. Both AppLayout (isAuthenticated) and per-route
 * permission checks use this same component to avoid duplicate redirect logic.
 */
function RouteGuard({
  predicate,
  children,
}: {
  predicate: () => boolean;
  children: React.ReactNode;
}) {
  const isLoading = useAuthStore((s) => s.isLoading);
  if (isLoading) return null; // AppLayout spinner covers this window
  if (!predicate()) return <Navigate to="/" replace />;
  return <>{children}</>;
}

const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<PageLoader />}>
            <Dashboard />
          </Suspense>
        ),
      },
      {
        path: "inventory",
        element: (
          <Suspense fallback={<PageLoader />}>
            <InventoryPage />
          </Suspense>
        ),
      },
      {
        path: "alerts",
        element: (
          <Suspense fallback={<PageLoader />}>
            <AlertsPage />
          </Suspense>
        ),
      },
      {
        path: "analytics",
        element: (
          <Suspense fallback={<PageLoader />}>
            <AnalyticsPage />
          </Suspense>
        ),
      },
      {
        path: "warehouses",
        element: (
          <Suspense fallback={<PageLoader />}>
            <WarehousesPage />
          </Suspense>
        ),
      },
      {
        path: "warehouses/:id",
        element: (
          <Suspense fallback={<PageLoader />}>
            <WarehouseDetailPage />
          </Suspense>
        ),
      },
      {
        path: "buses",
        element: (
          <Suspense fallback={<PageLoader />}>
            <BusesPage />
          </Suspense>
        ),
      },
      {
        path: "transactions",
        element: (
          <Suspense fallback={<PageLoader />}>
            <TransactionsPage />
          </Suspense>
        ),
      },
      {
        path: "users",
        element: (
          <RouteGuard predicate={() => useAuthStore.getState().hasPermission("users:manage")}>
            <Suspense fallback={<PageLoader />}>
              <UsersPage />
            </Suspense>
          </RouteGuard>
        ),
      },
      {
        path: "permissions",
        element: (
          <RouteGuard predicate={() => useAuthStore.getState().hasPermission("users:manage")}>
            <Suspense fallback={<PageLoader />}>
              <PermissionsPage />
            </Suspense>
          </RouteGuard>
        ),
      },
      {
        path: "audit",
        element: (
          <RouteGuard predicate={() => useAuthStore.getState().hasPermission("audit:read")}>
            <Suspense fallback={<PageLoader />}>
              <AuditLogsPage />
            </Suspense>
          </RouteGuard>
        ),
      },
      {
        path: "settings",
        element: (
          <Suspense fallback={<PageLoader />}>
            <SettingsPage />
          </Suspense>
        ),
      },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
