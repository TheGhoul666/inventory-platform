/**
 * Login / Register page — Supabase Auth.
 *
 * Sign-in calls supabase.auth.signInWithPassword() directly from the browser.
 * Sign-up calls supabase.auth.signUp() — no backend route needed.
 * The resulting session is stored by Supabase in localStorage (see supabase.ts)
 * and mirrored into authStore via onAuthStateChange.
 */
import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Bus, Eye, EyeOff } from "lucide-react";
import toast from "react-hot-toast";
import { supabase } from "@/lib/supabase";
import { useAuthStore } from "@/store/authStore";
import { useTranslation } from "react-i18next";
import { LegalLinks } from "@/components/layout/LegalLinks";
import { LEGAL_VERSION } from "@/config/business";

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
  const [agreed, setAgreed] = useState(false);

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
    if (!agreed) {
      toast.error(t("legal.agreeRequired"));
      return;
    }
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
          data: { full_name: fullName, terms_accepted_at: new Date().toISOString(), terms_version: LEGAL_VERSION },
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
          <h1 className="text-2xl font-bold text-ink">{t("auth.welcomeBack")}</h1>
          <p className="text-slate-400 text-sm mt-1">{t("auth.subtitle")}</p>
        </div>

        <div className="bg-surface-800 rounded-2xl border border-surface-700 p-8 shadow-2xl">
          {/* Tabs */}
          <div role="tablist" className="flex rounded-lg bg-surface-700 p-1 mb-6">
            <button
              type="button"
              role="tab"
              id="tab-signin"
              aria-selected={tab === "signin"}
              aria-controls="panel-signin"
              onClick={() => setTab("signin")}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                tab === "signin"
                  ? "bg-brand-600 text-white"
                  : "text-slate-400 hover:text-ink"
              }`}
            >
              {t("auth.signIn")}
            </button>
            <button
              type="button"
              role="tab"
              id="tab-signup"
              aria-selected={tab === "signup"}
              aria-controls="panel-signup"
              onClick={() => setTab("signup")}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                tab === "signup"
                  ? "bg-brand-600 text-white"
                  : "text-slate-400 hover:text-ink"
              }`}
            >
              {t("auth.signUp")}
            </button>
          </div>

          {/* Sign In Form */}
          {tab === "signin" && (
            <form onSubmit={handleLogin} className="space-y-4" role="tabpanel" id="panel-signin" aria-labelledby="tab-signin">
              <div>
                <label htmlFor="si-f0" className="text-sm text-slate-300 block mb-1.5">{t("auth.email")}</label>
                <input
                  id="si-f0"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="w-full bg-white border border-surface-600 rounded-lg px-3 py-2.5 text-ink placeholder-slate-400 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                  placeholder="operator@depot.com"
                />
              </div>
              <div>
                <label htmlFor="si-f1" className="text-sm text-slate-300 block mb-1.5">{t("auth.password")}</label>
                <div className="relative">
                  <input
                  id="si-f1"
                    type={showPw ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    className="w-full bg-white border border-surface-600 rounded-lg px-3 py-2.5 pe-10 text-ink placeholder-slate-400 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    aria-label={showPw ? t("a11y.hidePassword") : t("a11y.showPassword")}
                    aria-pressed={showPw}
                    className="absolute end-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-ink"
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
                {loading ? t("auth.signingIn") : t("auth.submitSignIn")}
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
                  className="w-full text-sm text-slate-300 underline underline-offset-2 hover:text-ink transition-colors"
                >
                  {t("auth.forgotPassword")}
                </button>
              </div>
            </form>
          )}

          {/* Sign Up Form */}
          {tab === "signup" && (
            <form onSubmit={handleRegister} className="space-y-4" role="tabpanel" id="panel-signup" aria-labelledby="tab-signup">
              <div>
                <label htmlFor="su-f0" className="text-sm text-slate-300 block mb-1.5">{t("auth.fullName")}</label>
                <input
                  id="su-f0"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  autoComplete="name"
                  className="w-full bg-white border border-surface-600 rounded-lg px-3 py-2.5 text-ink placeholder-slate-400 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                  placeholder="John Smith"
                />
              </div>
              <div>
                <label htmlFor="su-f1" className="text-sm text-slate-300 block mb-1.5">{t("auth.email")}</label>
                <input
                  id="su-f1"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="w-full bg-white border border-surface-600 rounded-lg px-3 py-2.5 text-ink placeholder-slate-400 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                  placeholder="operator@depot.com"
                />
              </div>
              <div>
                <label htmlFor="su-f2" className="text-sm text-slate-300 block mb-1.5">{t("auth.password")}</label>
                <div className="relative">
                  <input
                  id="su-f2"
                    type={showPw ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    className="w-full bg-white border border-surface-600 rounded-lg px-3 py-2.5 pe-10 text-ink placeholder-slate-400 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
                    placeholder="Min 8 characters"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    aria-label={showPw ? t("a11y.hidePassword") : t("a11y.showPassword")}
                    aria-pressed={showPw}
                    className="absolute end-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-ink"
                  >
                    {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <input
                  id="su-agree"
                  type="checkbox"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                  required
                  className="mt-1 h-4 w-4 shrink-0 rounded border-surface-600 bg-surface-700 accent-brand-600"
                />
                <label htmlFor="su-agree" className="text-sm leading-snug text-slate-300">
                  {t("legal.agreePrefix")}
                  <Link to="/terms" target="_blank" className="text-brand-300 underline underline-offset-2 hover:text-ink">{t("legal.terms")}</Link>
                  {t("legal.agreeAnd")}
                  <Link to="/privacy" target="_blank" className="text-brand-300 underline underline-offset-2 hover:text-ink">{t("legal.privacy")}</Link>
                </label>
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

        <LegalLinks className="mt-6" />
      </div>
    </div>
  );
}
