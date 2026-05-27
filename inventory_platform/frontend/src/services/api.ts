/**
 * Axios client — Supabase edition.
 *
 * Attaches the Supabase access_token from the active session.
 * Token refresh is handled automatically by the Supabase client;
 * we just read the current session on each request.
 *
 * On 401 we sign out (token is expired and Supabase couldn't refresh it).
 */
import axios, { AxiosInstance, AxiosError } from "axios";
import { supabase } from "@/lib/supabase";
import { useAuthStore } from "@/store/authStore";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// Inject Supabase access token before each request
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// On 401 — the session has expired; sign out
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      await useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

export function extractError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d: { msg: string }) => d.msg).join(", ");
  }
  return "An unexpected error occurred";
}

export default api;
