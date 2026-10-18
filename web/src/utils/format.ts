import i18n from "@/i18n";

const locale = () => (i18n.language?.startsWith("he") ? "he-IL" : "en-GB");

export function fmtDateTime(iso: string | null | undefined, withSeconds = false): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(locale(), {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", ...(withSeconds ? { second: "2-digit" } : {}),
  });
}

export const fmtDate = (iso: string | null | undefined): string =>
  iso ? new Date(iso).toLocaleDateString(locale(), { day: "2-digit", month: "short", year: "numeric" }) : "—";

export const fmtTime = (iso: string): string =>
  new Date(iso).toLocaleTimeString(locale(), { hour: "2-digit", minute: "2-digit" });

export const fmtNumber = (n: number): string => n.toLocaleString(locale());

/** Compact currency (e.g. ₪184K). The currency of `unit_cost` is not stored; ILS is assumed. */
export const fmtMoney = (n: number): string =>
  new Intl.NumberFormat(locale(), { style: "currency", currency: "ILS", notation: "compact", maximumFractionDigits: 1 }).format(n);

/** Short "when": time today, "yesterday" (localised), otherwise the date. */
export function fmtWhen(iso: string, now = new Date()): string {
  const d = new Date(iso);
  const startOfDay = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const days = Math.round((startOfDay(now) - startOfDay(d)) / 86_400_000);
  if (days <= 0) return fmtTime(iso);
  if (days === 1) return new Intl.RelativeTimeFormat(locale(), { numeric: "auto" }).format(-1, "day");
  return fmtDate(iso);
}
