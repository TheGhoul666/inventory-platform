import React, { useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Bus, ArrowRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import { legalDocs, type LegalKind } from "@/content/legal";
import { LegalLinks } from "@/components/layout/LegalLinks";
import { getBusiness } from "@/config/business";

/** Public (no sign-in) legal page — privacy, terms, cookies, accessibility. */
export function LegalPage({ kind }: { kind: LegalKind }) {
  const { t, i18n } = useTranslation();
  const doc = legalDocs(i18n.language, kind);
  const { pathname } = useLocation();
  const isHe = i18n.language.startsWith("he");

  useEffect(() => {
    document.title = `${doc.title} · BusOps`;
  }, [doc.title]);

  return (
    <div className="min-h-screen bg-surface-900 text-slate-200">
      <a href="#legal-main" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:m-2 focus:rounded-lg focus:bg-brand-600 focus:px-4 focus:py-2 focus:text-white">
        {t("a11y.skip")}
      </a>
      <header className="border-b border-surface-700 bg-surface-800">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
          <Link to="/" className="flex items-center gap-2 font-semibold text-ink">
            <Bus className="h-5 w-5 text-brand-400" aria-hidden="true" />
            {t("nav.appName")}
          </Link>
          <button
            type="button"
            onClick={() => i18n.changeLanguage(isHe ? "en" : "he")}
            className="btn-secondary px-3 py-1.5 text-sm"
            lang={isHe ? "en" : "he"}
          >
            {isHe ? "English" : "עברית"}
          </button>
        </div>
      </header>

      <main id="legal-main" className="mx-auto max-w-3xl px-4 py-10" key={pathname}>
        <Link to="/login" className="mb-6 inline-flex items-center gap-1 text-sm text-brand-300 underline underline-offset-2 hover:text-ink">
          <ArrowRight className="h-4 w-4 rtl:rotate-0 ltr:rotate-180" aria-hidden="true" />
          {t("legal.back")}
        </Link>
        <h1 className="text-3xl font-bold text-ink">{doc.title}</h1>
        {doc.intro && <p className="mt-3 leading-relaxed text-slate-300">{doc.intro}</p>}
        <div className="mt-8 space-y-8">
          {doc.sections.map((s) => (
            <section key={s.h} aria-labelledby={`h-${s.h}`}>
              <h2 id={`h-${s.h}`} className="mb-2 text-lg font-semibold text-ink">{s.h}</h2>
              {s.p.map((para, i) => (
                <p key={i} className="mb-2 leading-relaxed text-slate-300">{para}</p>
              ))}
            </section>
          ))}
        </div>
        <p className="mt-10 border-t border-surface-700 pt-4 text-sm text-slate-400">
          {getBusiness(i18n.language).name} · {getBusiness(i18n.language).address}
        </p>
      </main>

      <footer className="border-t border-surface-700 py-6">
        <LegalLinks />
      </footer>
    </div>
  );
}
