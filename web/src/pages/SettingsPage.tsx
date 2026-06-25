import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { useAuthStore } from "@/store/authStore";
import { usersService } from "@/services/inventoryService";
import { extractError } from "@/services/api";
import { Shield, User, Mail, Key, LogOut, Phone } from "lucide-react";
import { useTranslation } from "react-i18next";

const ROLE_COLORS: Record<string, string> = {
  SuperAdmin: "bg-purple-500/15 text-purple-400 border border-purple-500/30",
  WarehouseManager: "bg-blue-500/15 text-blue-400 border border-blue-500/30",
  Technician: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
  Viewer: "bg-slate-500/15 text-slate-400 border border-slate-500/30",
};

export function SettingsPage() {
  const { user, roles, permissions, is_superadmin, logout } = useAuthStore();
  const { t } = useTranslation();

  const email = user?.email ?? "—";
  const username = user?.user_metadata?.username ?? user?.email ?? "—";
  const fullName = user?.user_metadata?.full_name ?? "—";

  const [phone, setPhone] = useState<string>(user?.user_metadata?.phone ?? "");
  const phoneMutation = useMutation({
    mutationFn: () => usersService.updateMyProfile({ phone }),
    onSuccess: () => toast.success("Notification phone saved. Refresh your session to see it everywhere."),
    onError: (err) => toast.error(extractError(err)),
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-white">{t("settings.title")}</h1>
        <p className="text-slate-400 text-sm mt-1">Your account and session information</p>
      </div>

      {/* Profile card */}
      <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-surface-700">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">{t("settings.profile")}</h2>
        </div>
        <div className="p-6 space-y-5">
          <div className="flex items-center gap-3">
            <div className="h-14 w-14 rounded-full bg-brand-600/20 border border-brand-500/30 flex items-center justify-center text-xl font-bold text-brand-400">
              {fullName !== "—" ? fullName[0].toUpperCase() : email[0].toUpperCase()}
            </div>
            <div>
              <p className="text-white font-semibold text-lg">{fullName}</p>
              <p className="text-slate-400 text-sm">{email}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            <InfoRow icon={<Mail className="h-4 w-4" />} label="Email" value={email} />
            <InfoRow icon={<User className="h-4 w-4" />} label="Username" value={username} />
            <InfoRow icon={<Key className="h-4 w-4" />} label="User ID" value={user?.id ?? "—"} mono />
          </div>
        </div>
      </div>

      {/* Notification phone */}
      <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-surface-700">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Phone className="h-4 w-4" /> Alert Notifications
          </h2>
        </div>
        <div className="p-6 space-y-3">
          <p className="text-sm text-slate-400">
            {is_superadmin
              ? "As a SuperAdmin you receive SMS alerts for stock shortages and significant inventory changes. Set the phone number that should receive them."
              : "Set the phone number used for inventory notifications. International format recommended (e.g. +972501234567)."}
          </p>
          <div className="flex gap-2">
            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+972501234567"
              className="flex-1 bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 text-sm"
            />
            <button
              onClick={() => phoneMutation.mutate()}
              disabled={phoneMutation.isPending}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
            >
              {phoneMutation.isPending ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      </div>

      {/* Roles & Permissions */}
      <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-surface-700">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Access</h2>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Roles</p>
            <div className="flex flex-wrap gap-2">
              {is_superadmin && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-purple-500/15 text-purple-400 border border-purple-500/30 flex items-center gap-1">
                  <Shield className="h-3 w-3" /> SuperAdmin
                </span>
              )}
              {roles.map((r) => (
                <span key={r} className={`px-3 py-1 rounded-full text-xs font-medium ${ROLE_COLORS[r] ?? "bg-slate-500/15 text-slate-400"}`}>
                  {r}
                </span>
              ))}
              {!is_superadmin && roles.length === 0 && (
                <span className="text-slate-500 text-sm">No roles assigned</span>
              )}
            </div>
          </div>

          {permissions.length > 0 && !permissions.includes("*") && (
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Permissions</p>
              <div className="flex flex-wrap gap-1.5">
                {permissions.map((p) => (
                  <span key={p} className="px-2 py-0.5 rounded bg-surface-700 text-slate-400 text-xs font-mono">
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}

          {permissions.includes("*") && (
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Permissions</p>
              <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 text-xs font-mono">* (all)</span>
            </div>
          )}
        </div>
      </div>

      {/* Sign out */}
      <div className="bg-surface-800 rounded-xl border border-surface-700 overflow-hidden">
        <div className="p-6">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Session</h2>
          <button
            onClick={() => logout()}
            className="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-lg text-sm font-medium transition-colors"
          >
            <LogOut className="h-4 w-4" />
            {t("auth.logout")}
          </button>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ icon, label, value, mono = false }: {
  icon: React.ReactNode; label: string; value: string; mono?: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="text-slate-500 w-4 flex-shrink-0">{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-slate-500 mb-0.5">{label}</p>
        <p className={`text-white text-sm truncate ${mono ? "font-mono text-xs" : ""}`}>{value}</p>
      </div>
    </div>
  );
}
