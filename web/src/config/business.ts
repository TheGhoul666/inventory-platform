/**
 * Business / legal contact details shown on the legal pages.
 * Fill in via VITE_BUSINESS_* variables (see web/.env.example) — these are
 * required by Israeli law (privacy, consumer, accessibility regulations) and
 * must be real. Until set, the pages show a visible "[TO COMPLETE]" marker.
 */
const v = (key: string, fallback: string): string =>
  ((import.meta.env as Record<string, string | undefined>)[key] ?? "").trim() || fallback;

export const LEGAL_VERSION = "2026-10-18";

const placeholder = (he: string, en: string, lang: string) => (lang.startsWith("he") ? `[יש להשלים: ${he}]` : `[TO COMPLETE: ${en}]`);

export function getBusiness(lang: string) {
  const ph = (he: string, en: string) => placeholder(he, en, lang);
  const email = v("VITE_BUSINESS_EMAIL", ph("דוא״ל", "email"));
  const phone = v("VITE_BUSINESS_PHONE", ph("טלפון", "phone"));
  return {
    name: v("VITE_BUSINESS_NAME", ph("שם העסק", "business name")),
    registrationNumber: v("VITE_BUSINESS_ID", ph("ח.פ./ע.מ.", "company no.")),
    address: v("VITE_BUSINESS_ADDRESS", ph("כתובת", "address")),
    email,
    phone,
    privacyEmail: v("VITE_PRIVACY_EMAIL", email),
    accessibilityName: v("VITE_ACCESSIBILITY_COORDINATOR", ph("רכז/ת נגישות", "accessibility coordinator")),
    accessibilityEmail: v("VITE_ACCESSIBILITY_EMAIL", email),
    accessibilityPhone: v("VITE_ACCESSIBILITY_PHONE", phone),
    jurisdiction: v("VITE_BUSINESS_JURISDICTION", lang.startsWith("he") ? "תל אביב-יפו" : "Tel Aviv-Yafo"),
  };
}

export type Business = ReturnType<typeof getBusiness>;
