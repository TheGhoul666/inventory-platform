/**
 * Supabase client — singleton for the entire frontend.
 *
 * Uses the ANON key (public — safe to expose in browser).
 * Row Level Security in Supabase enforces data access per user.
 *
 * Session is stored in localStorage so it persists across tab close/reopen
 * and is shared across tabs. sessionStorage would break multi-tab workflows
 * and log users out on every tab close. XSS token theft is mitigated via CSP
 * (nginx) rather than storage choice.
 *
 * The Supabase access_token is attached to API requests via the
 * Axios interceptor (services/api.ts).
 */
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    "Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY environment variables"
  );
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    storage: window.localStorage,
  },
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
});


export type SupabaseClient = typeof supabase;
