import { getBusiness, LEGAL_VERSION, type Business } from "@/config/business";

export type LegalKind = "privacy" | "terms" | "cookies" | "accessibility";
export interface LegalDoc {
  title: string;
  intro?: string;
  sections: { h: string; p: string[] }[];
}
type Lang = "he" | "en";

const buildHe = (b: Business): Record<LegalKind, LegalDoc> => ({
  privacy: {
    title: "מדיניות פרטיות",
    intro: `עודכן לאחרונה: ${LEGAL_VERSION}. מדיניות זו מתארת איזה מידע אישי נאסף במערכת BusOps (ניהול מלאי צי אוטובוסים), למה, ומה הזכויות שלך, בהתאם לחוק הגנת הפרטיות, התשמ״א-1981 ותקנותיו.`,
    sections: [
      { h: "1. מי אחראי על המידע", p: [`בעל מאגר המידע: ${b.name} (${b.registrationNumber}), ${b.address}.`, `לפניות בנושאי פרטיות: ${b.privacyEmail}.`] },
      { h: "2. איזה מידע נאסף", p: [
        "פרטי חשבון: שם מלא, כתובת דוא״ל, שם משתמש, תפקיד והרשאות, ומספר טלפון (אופציונלי, לצורך התראות SMS).",
        "מידע תפעולי: פעולות מלאי (ניפוק, חידוש, העברה), מחסנים, אוטובוסים והתראות, כולל זהות המשתמש שביצע כל פעולה.",
        "יומן ביקורת: סוג הפעולה, מועדה וכתובת ה-IP שממנה בוצעה, לצורכי אבטחה ובקרה.",
        "מידע טכני מינימלי בדפדפן: אסימון התחברות והעדפות תצוגה (ראו עמוד \"קבצי Cookie ואחסון מקומי\"). אין מעקב שיווקי או אנליטי של צד שלישי." ] },
      { h: "3. למה אנחנו משתמשים במידע", p: ["הפעלת המערכת וזיהוי משתמשים מורשים; ניהול הרשאות; תיעוד פעולות מלאי ובקרה; שליחת התראות תפעוליות; אבטחת מידע ומניעת שימוש לרעה; עמידה בדרישות החוק.", "איננו מוכרים מידע אישי ואיננו משתמשים בו לפרסום או לשיווק."] },
      { h: "4. העברה לצדדים שלישיים (ספקי משנה)", p: [
        "Supabase – אירוח מסד הנתונים, אימות משתמשים ושידור עדכונים בזמן אמת. מיקום האחסון נקבע בהגדרות הפרויקט [יש לאמת ולהשלים: אזור/מדינה].",
        "Twilio – שליחת הודעות SMS, אם הופעלה התראת SMS. ספק דוא״ל (SMTP) – שליחת הודעות דוא״ל, אם הופעל.",
        "ייתכן שהמידע מועבר מחוץ לישראל. ההעברה נעשית לספקים הכפופים להתחייבויות אבטחה והגנה על מידע בהתאם לתקנות הגנת הפרטיות (העברת מידע אל מאגרי מידע שמחוץ לגבולות המדינה), התשס״א-2001." ] },
      { h: "5. אבטחת מידע ושמירה", p: ["המידע מאובטח בהתאם לתקנות הגנת הפרטיות (אבטחת מידע), התשע״ז-2017: הצפנה בתעבורה, בקרת גישה לפי הרשאות, ויומן ביקורת.", "מידע נשמר כל עוד החשבון פעיל ובהתאם לצורך התפעולי והחוקי [יש להשלים: תקופות שמירה]. ניתן לבקש מחיקת חשבון; רישומי מלאי וביקורת עשויים להישמר באופן מנוטרל זהות כנדרש לצורכי בקרה."] },
      { h: "6. הזכויות שלך", p: ["זכות לעיין במידע שנשמר עליך (סעיף 13), לבקש תיקון מידע שגוי (סעיף 14), ולבקש מחיקה כאשר אין צורך חוקי או תפעולי בשמירתו.", `למימוש הזכויות פנו אל ${b.privacyEmail}. נשיב בתוך זמן סביר ובכל מקרה בהתאם לדין.`, "ניתן להגיש תלונה לרשות להגנת הפרטיות במשרד המשפטים."] },
      { h: "7. חובה למסור מידע", p: ["מסירת פרטי החשבון הבסיסיים היא תנאי לשימוש במערכת. מסירת מספר טלפון היא וולונטרית."] },
      { h: "8. שינויים במדיניות", p: ["נעדכן מדיניות זו מעת לעת. שינוי מהותי יפורסם במערכת, והגרסה העדכנית תפורסם בעמוד זה."] },
    ],
  },
  terms: {
    title: "תנאי שימוש",
    intro: `גרסה: ${LEGAL_VERSION}. השימוש במערכת BusOps כפוף לתנאים אלה. בעת יצירת חשבון תתבקש לאשר שקראת והסכמת להם.`,
    sections: [
      { h: "1. מהות השירות", p: [`המערכת מופעלת על ידי ${b.name} ומיועדת לניהול מלאי חלפים ותחזוקה של צי אוטובוסים על ידי משתמשים מורשים בלבד. אין בה מכירה או רכישה של מוצרים או שירותים לצרכנים.`] },
      { h: "2. חשבון ואבטחה", p: ["המשתמש אחראי לשמירת סודיות פרטי ההתחברות ולכל פעולה שתבוצע בחשבונו. יש לדווח מיד על חשד לגישה בלתי מורשית.", "מסירת פרטים נכונים ועדכניים בעת ההרשמה היא חובה."] },
      { h: "3. שימוש מותר ואסור", p: ["השימוש מותר למטרות תפעוליות לגיטימיות בלבד. אסור לעקוף אמצעי אבטחה, לגשת למידע שאינך מורשה לו, להזין מידע כוזב, לפגוע בפעילות המערכת או להעתיק אותה."] },
      { h: "4. דיוק המידע והסתמכות", p: ["המערכת כוללת חישובי תחזית וזיהוי חריגות המבוססים על נתוני העבר. אלה כלי עזר בלבד ואינם תחליף לשיקול דעת מקצועי או לבדיקות בטיחות של כלי רכב."] },
      { h: "5. קניין רוחני", p: ["כל הזכויות במערכת, בקוד ובעיצוב שמורות לבעליה. המשתמש מקבל רישיון שימוש מוגבל, אישי ולא ייחודי. המידע שהוזן על ידי הארגון נשאר בבעלותו."] },
      { h: "6. זמינות והגבלת אחריות", p: ["השירות ניתן כמות שהוא (As Is). ניתן מאמץ סביר לזמינות ואבטחה, אך לא נתחייב לפעילות רצופה וללא תקלות. במידה המרבית המותרת בדין, האחריות מוגבלת ואיננה כוללת נזקים עקיפים או תוצאתיים. אין באמור כדי לגרוע מזכויות שאינן ניתנות להתניה."] },
      { h: "7. פרטיות", p: ["השימוש במידע אישי מפורט במדיניות הפרטיות, המהווה חלק מתנאים אלה."] },
      { h: "8. הפסקת שירות", p: ["אנו רשאים להשעות או לסגור חשבון שהפר תנאים אלה. משתמש רשאי לבקש סגירת חשבון בכל עת."] },
      { h: "9. החוק החל וסמכות שיפוט", p: [`על תנאים אלה יחול הדין הישראלי. סמכות השיפוט הבלעדית נתונה לבתי המשפט המוסמכים ב${b.jurisdiction}.`] },
      { h: "10. יצירת קשר", p: [`${b.name}, ${b.address}. דוא״ל: ${b.email}. טלפון: ${b.phone}.`] },
    ],
  },
  cookies: {
    title: "קבצי Cookie ואחסון מקומי",
    intro: "המערכת משתמשת באחסון מקומי של הדפדפן (localStorage) אך ורק לצורך תפעול. איננה משתמשת ב-Cookie שיווקיים, באנליטיקס או בפיקסלים של צדדים שלישיים.",
    sections: [
      { h: "מה נשמר בדפדפן", p: [
        "אסימון התחברות (Supabase Auth) – הכרחי לשמירת ההתחברות ולאבטחה. נמחק בהתנתקות.",
        "שפת הממשק (i18nextLng) – שומר את בחירת השפה.",
        "העדפות תצוגה (ui-storage) – למשל מצב סרגל הצד." ] },
      { h: "האם נדרש באנר הסכמה", p: ["פריטי האחסון לעיל הם הכרחיים לפעולת השירות שביקשת ואינם משמשים למעקב או לפרסום, ולכן אינם מחייבים הסכמה מראש. אם בעתיד יתווספו כלי אנליטיקס, פיקסלים או סקריפטים של צד שלישי, יוצג באנר הסכמה (ללא טעינת הכלי לפני אישור), ועמוד זה יעודכן."] },
      { h: "ניהול ומחיקה", p: ["ניתן למחוק את הנתונים בכל עת דרך הגדרות הדפדפן. מחיקתם תנתק אותך מהמערכת ותאפס את העדפותיך."] },
      { h: "צדדים שלישיים", p: ["בקשות הרשת היחידות הן לשירות Supabase (אימות, מסד נתונים ועדכונים בזמן אמת). לא נטענים גופנים או סקריפטים מספקים חיצוניים."] },
    ],
  },
  accessibility: {
    title: "הצהרת נגישות",
    intro: `עודכן לאחרונה: ${LEGAL_VERSION}. ${b.name} רואה חשיבות בהנגשת המערכת לאנשים עם מוגבלות, בהתאם לחוק שוויון זכויות לאנשים עם מוגבלות, התשנ״ח-1998 ולתקנות שוויון זכויות לאנשים עם מוגבלות (התאמות נגישות לשירות), התשע״ג-2013.`,
    sections: [
      { h: "רמת הנגישות", p: ["אנו פועלים להתאים את המערכת לתקן הישראלי ת״י 5568 בהתבסס על הנחיות WCAG 2.1 ברמה AA.", "בוצעה בדיקה פנימית של ניווט מקלדת, תוויות טפסים וניגודיות צבעים. לא בוצעה עדיין בדיקה עם קוראי מסך. [יש להשלים: ביקורת נגישות חיצונית ותאריכה.]"] },
      { h: "התאמות שבוצעו", p: ["ניווט ומילוי טפסים באמצעות מקלדת בלבד, כולל קישור \"דלג לתוכן\" ומחוון מיקוד ברור.", "תוויות לשדות טופס וכפתורי אייקון; חלונות דו-שיח נגישים (כפתור Escape, החזרת מיקוד).", "ניגודיות טקסט של לפחות 4.5:1, ותמיכה בעברית (RTL) ובאנגלית עם הגדרת שפה וכיוון.", "כיבוד העדפת המשתמש להפחתת תנועה."] },
      { h: "מגבלות ידועות", p: ["גרפים (תרשימי אנליטיקה) עשויים שלא להיות נגישים במלואם לקורא מסך; הנתונים זמינים גם בכרטיסי הנתונים שלצדם.", "ייתכנו חלקים שטרם הונגשו במלואם. אנו ממשיכים לשפר."] },
      { h: "רכז/ת נגישות ויצירת קשר", p: [`שם: ${b.accessibilityName}`, `דוא״ל: ${b.accessibilityEmail}`, `טלפון: ${b.accessibilityPhone}`, "נתקלת בבעיית נגישות? פנה אלינו ונטפל בה בהקדם. ציין את כתובת העמוד, תיאור הבעיה והטכנולוגיה המסייעת בה אתה משתמש."] },
    ],
  },
});

const buildEn = (b: Business): Record<LegalKind, LegalDoc> => ({
  privacy: {
    title: "Privacy Policy",
    intro: `Last updated: ${LEGAL_VERSION}. This policy explains what personal data BusOps (bus-fleet inventory management) collects, why, and your rights under the Israeli Privacy Protection Law, 5741-1981 and its regulations.`,
    sections: [
      { h: "1. Data controller", p: [`Database owner: ${b.name} (${b.registrationNumber}), ${b.address}.`, `Privacy contact: ${b.privacyEmail}.`] },
      { h: "2. Data we collect", p: [
        "Account data: full name, email, username, role and permissions, and an optional phone number (for SMS alerts).",
        "Operational data: stock movements (issue, restock, transfer), warehouses, buses and alerts, including which user performed each action.",
        "Audit log: action type, timestamp and the IP address it came from, for security and oversight.",
        "Minimal browser data: a sign-in token and display preferences (see the Cookies & local storage page). There is no third-party marketing or analytics tracking." ] },
      { h: "3. Why we use it", p: ["To run the system and identify authorised users; manage permissions; record stock activity; send operational alerts; secure the system and prevent misuse; and meet legal obligations.", "We do not sell personal data or use it for advertising or marketing."] },
      { h: "4. Sub-processors and transfers", p: [
        "Supabase – database hosting, authentication and real-time updates. Hosting region is set in the project settings [verify and complete: region/country].",
        "Twilio – SMS delivery when SMS alerts are enabled. An email (SMTP) provider – email delivery when enabled.",
        "Data may be transferred outside Israel to providers bound by security and data-protection commitments, in line with the Privacy Protection (Transfer of Data to Databases Abroad) Regulations, 5761-2001." ] },
      { h: "5. Security and retention", p: ["Data is protected in line with the Privacy Protection (Data Security) Regulations, 5777-2017: encryption in transit, permission-based access control and an audit log.", "Data is kept while the account is active and as operationally and legally required [complete: retention periods]. You can ask for account deletion; stock and audit records may be kept de-identified where needed for oversight."] },
      { h: "6. Your rights", p: ["You may inspect the data held about you (section 13), ask for correction of inaccurate data (section 14), and ask for deletion where there is no legal or operational need to keep it.", `To exercise your rights contact ${b.privacyEmail}. We will reply within a reasonable time and as required by law.`, "You may complain to the Privacy Protection Authority at the Ministry of Justice."] },
      { h: "7. Obligation to provide data", p: ["Basic account details are required to use the system. A phone number is voluntary."] },
      { h: "8. Changes", p: ["We may update this policy. Material changes will be announced in the system and the current version is always published on this page."] },
    ],
  },
  terms: {
    title: "Terms of Service",
    intro: `Version: ${LEGAL_VERSION}. Use of BusOps is subject to these terms. When you create an account you are asked to confirm you have read and agree to them.`,
    sections: [
      { h: "1. The service", p: [`The system is operated by ${b.name} and is intended for authorised users managing spare-parts inventory and maintenance for a bus fleet. It does not sell products or services to consumers.`] },
      { h: "2. Account and security", p: ["You are responsible for keeping your credentials confidential and for all activity under your account. Report suspected unauthorised access immediately.", "You must provide accurate, up-to-date details when registering."] },
      { h: "3. Acceptable use", p: ["Use the system only for legitimate operational purposes. Do not bypass security controls, access data you are not authorised to see, enter false information, disrupt the system or copy it."] },
      { h: "4. Accuracy and reliance", p: ["Forecasts and anomaly detection are based on historical data. They are aids only and do not replace professional judgement or vehicle safety checks."] },
      { h: "5. Intellectual property", p: ["All rights in the system, its code and design are reserved. You receive a limited, personal, non-exclusive licence to use it. Data entered by your organisation remains yours."] },
      { h: "6. Availability and liability", p: ["The service is provided “as is”. We make reasonable efforts on availability and security but do not guarantee uninterrupted or error-free operation. To the fullest extent permitted by law our liability is limited and excludes indirect or consequential loss. Nothing here limits rights that cannot be waived by law."] },
      { h: "7. Privacy", p: ["Personal data use is described in the Privacy Policy, which forms part of these terms."] },
      { h: "8. Suspension", p: ["We may suspend or close an account that breaches these terms. You may ask to close your account at any time."] },
      { h: "9. Governing law and jurisdiction", p: [`Israeli law applies. The competent courts in ${b.jurisdiction} have exclusive jurisdiction.`] },
      { h: "10. Contact", p: [`${b.name}, ${b.address}. Email: ${b.email}. Phone: ${b.phone}.`] },
    ],
  },
  cookies: {
    title: "Cookies & Local Storage",
    intro: "The system uses browser local storage (localStorage) strictly for operation. It does not use marketing cookies, analytics or third-party pixels.",
    sections: [
      { h: "What is stored", p: [
        "Sign-in token (Supabase Auth) – necessary to keep you signed in and for security. Removed on sign-out.",
        "Interface language (i18nextLng) – remembers your language choice.",
        "Display preferences (ui-storage) – for example the sidebar state." ] },
      { h: "Is a consent banner required", p: ["The items above are strictly necessary for the service you requested and are not used for tracking or advertising, so they do not require prior consent. If analytics, pixels or third-party scripts are added in future, a consent banner will be shown (the tool will not load before consent) and this page will be updated."] },
      { h: "Managing and deleting", p: ["You can clear this data at any time in your browser settings. Doing so signs you out and resets your preferences."] },
      { h: "Third parties", p: ["The only network requests are to Supabase (authentication, database and real-time updates). No external fonts or scripts are loaded."] },
    ],
  },
  accessibility: {
    title: "Accessibility Statement",
    intro: `Last updated: ${LEGAL_VERSION}. ${b.name} is committed to making the system accessible to people with disabilities, in line with the Equal Rights for Persons with Disabilities Law, 5758-1998 and the Service Accessibility Adjustments Regulations, 5773-2013.`,
    sections: [
      { h: "Accessibility level", p: ["We work towards the Israeli Standard SI 5568 based on WCAG 2.1 level AA.", "An internal review covered keyboard navigation, form labels and colour contrast. Testing with screen readers has not yet been done. [Complete: external accessibility audit and its date.]"] },
      { h: "Adjustments made", p: ["Keyboard-only navigation and forms, a “Skip to content” link and a clear focus indicator.", "Labels on form fields and icon buttons; accessible dialogs (Escape key, focus return).", "Text contrast of at least 4.5:1, plus Hebrew (RTL) and English with language and direction set.", "Respect for the user’s reduced-motion preference."] },
      { h: "Known limitations", p: ["Analytics charts may not be fully accessible to screen readers; the underlying figures are also shown in the summary cards beside them.", "Some parts may not yet be fully accessible. We continue to improve."] },
      { h: "Accessibility coordinator and contact", p: [`Name: ${b.accessibilityName}`, `Email: ${b.accessibilityEmail}`, `Phone: ${b.accessibilityPhone}`, "Hit an accessibility problem? Contact us and we will address it promptly. Include the page address, a description and the assistive technology you use."] },
    ],
  },
});

export const legalDocs = (lang: string, kind: LegalKind): LegalDoc => {
  const b = getBusiness(lang);
  return (lang.startsWith("he") ? buildHe(b) : buildEn(b))[kind];
};
