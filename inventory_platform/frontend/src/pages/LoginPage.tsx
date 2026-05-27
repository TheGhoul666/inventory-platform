/**
 * Login / Register page — Supabase Auth.
 *
 * Sign-in calls supabase.auth.signInWithPassword() directly from the browser.
 * Sign-up calls supabase.auth.signUp() — no backend route needed.
 * The resulting session is stored by Supabase in localStorage and
 * mirrored into authStore via onAuthStateChange.
 */
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Bus, Eye, EyeOff } from "lucide-react";
import toast from "react-hot-toast";
import { supabase } from "@/lib/supabase";
import { useAuthStore } from "@/store/authStore";
import { useTranslation } from "react-i18next";

type Tab = "signin" | "signup";

export function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("signin");

  useEffect(() => {
    if (isAuthenticated) navigate("/", { replace: true });
  }, [isAuthenticated, navigate]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      navigate("/");
    } catch (err: any) {
      toast.error(err.message ?? t("auth.loginFailed"));
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      toast.error(t("auth.minPassword"));
      return;
    }
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: fullName },
        },
      });
      if (error) throw error;

      if (data.session) {
        // Email confirmation disabled — signed in immediately
        toast.success(t("auth.accountCreated"));
        navigate("/");
      } else {
        // Email confirmation enabled — prompt user to confirm
        toast.success(t("auth.accountCreatedConfirm"));
        setTab("signin");
      }
    } catch (err: any) {
      toast.error(err.message ?? t("auth.registrationFailed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-brand-600 mb-4">
            <Bus className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">{t("auth.welcomeBack")}</h1>
          <p className="text-slate-400 text-sm mt-1">{t("auth.subtitle")}</p>
        </div>

        <div className="bg-surface-800 rounded-2xl border border-surface-700 p-8 shadow-2xl">
          {/* Tabs */}
          <div className="flex rounded-lg bg-surface-700 p-1 mb-6">
            <button
              onClick={() => setTab("signin")}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                tab === "signin"
                  ? "bg-brand-600 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {t("auth.signIn")}
            </button>
            <button
              onClick={() => setTab("signup")}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                tab === "signup"
                  ? "bg-brand-600 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {t("auth.signUp")}
            </button>
          </div>

          {/* Sign In Form */}
          {tab === "signin" && (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="text-sm text-slate-400 block mb-1.5">{t("auth.email")}</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                  placeholder="operator@depot.com"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 block mb-1.5">{t("auth.password")}</label>
                <div className="relative">
                  <input
                    type={showPw ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2.5 pr-10 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  >
                    {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors mt-2"
              >
                {loading ? t("auth.signingIn") : t("auth.signIn")}
              </button>

              <div className="pt-2 border-t border-surface-700">
                <button
                  type="button"
                  onClick={async () => {
                    if (!email) { toast.error(t("auth.enterEmailFirst")); return; }
                    const { error } = await supabase.auth.resetPasswordForEmail(email);
                    if (error) toast.error(error.message);
                    else toast.success(t("auth.passwordResetSent"));
                  }}
                  className="w-full text-sm text-slate-400 hover:text-brand-400 transition-colors"
                >
                  {t("auth.forgotPassword")}
                </button>
              </div>
            </form>
          )}

          {/* Sign Up Form */}
          {tab === "signup" && (
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="text-sm text-slate-400 block mb-1.5">{t("auth.fullName")}</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  autoComplete="name"
                  className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                  placeholder="John Smith"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 block mb-1.5">{t("auth.email")}</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                  placeholder="operator@depot.com"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 block mb-1.5">{t("auth.password")}</label>
                <div className="relative">
                  <input
                    type={showPw ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2.5 pr-10 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                    placeholder="Min 8 characters"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  >
                    {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors mt-2"
              >
                {loading ? t("auth.creatingAccount") : t("auth.signUp")}
              </button>
            </form>
          )}
        </div>

        <p className="text-center text-slate-600 text-xs mt-6">
          Powered by Supabase · Bus Inventory Platform v1.0
        </p>
      </div>
    </div>
  );
}
