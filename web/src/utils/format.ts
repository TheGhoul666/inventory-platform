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
