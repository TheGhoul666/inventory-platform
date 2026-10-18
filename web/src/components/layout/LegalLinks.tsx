import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { cn } from "@/utils/cn";

export function LegalLinks({ className }: { className?: string }) {
  const { t } = useTranslation();
  const links = [
    { to: "/privacy", label: t("legal.privacy") },
    { to: "/terms", label: t("legal.terms") },
    { to: "/cookies", label: t("legal.cookies") },
    { to: "/accessibility", label: t("legal.accessibility") },
  ];
  return (
    <nav aria-label={t("legal.navLabel")} className={cn("flex flex-wrap justify-center gap-x-5 gap-y-2 text-xs", className)}>
      {links.map((l) => (
        <Link key={l.to} to={l.to} className="text-slate-300 underline underline-offset-2 hover:text-white">
          {l.label}
        </Link>
      ))}
    </nav>
  );
}
