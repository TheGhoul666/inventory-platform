/**
 * Auth state store — Supabase edition.
 *
 * Supabase handles token storage, refresh, and session persistence
 * in localStorage automatically. We only mirror the resolved user
 * into Zustand so components can reactively access it.
 *
 * The Supabase access_token is attached to API requests via the
 * Axios interceptor (services/api.ts).
 */
import { create } from "zustand";
import type { Session, User } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";

interface AuthState {
  session: Session | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Derived from app_metadata (set by backend admin API)
  roles: string[];
  permissions: string[];
  is_superadmin: boolean;

  setSession: (session: Session | null) => void;
  logout: () => Promise<void>;
  hasPermission: (p: string) => boolean;
  hasRole: (r: string) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  session: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,
  roles: [],
  permissions: [],
  is_superadmin: false,

  setSession: (session) => {
    const user = session?.user ?? null;
    const appMeta = user?.app_metadata ?? {};

    set({
      session,
      user,
      isAuthenticated: !!session,
      isLoading: false,
      roles: appMeta.roles ?? [],
      permissions: appMeta.permissions ?? [],
      is_superadmin: appMeta.is_superadmin ?? false,
    });
  },

  logout: async () => {
    await supabase.auth.signOut();
    set({
      session: null,
      user: null,
      isAuthenticated: false,
      roles: [],
      permissions: [],
      is_superadmin: false,
    });
  },

  hasPermission: (p) => {
    const { is_superadmin, permissions } = get();
    return is_superadmin || permissions.includes("*") || permissions.includes(p);
  },

  hasRole: (r) => {
    return get().roles.includes(r);
  },
}));

// Bootstrap: restore session on page load and listen for auth changes
export async function initAuth() {
  const { data: { session } } = await supabase.auth.getSession();
  useAuthStore.getState().setSession(session);

  supabase.auth.onAuthStateChange((_event, session) => {
    useAuthStore.getState().setSession(session);
  });
}
