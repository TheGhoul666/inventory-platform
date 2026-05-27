"""📧 Email Composer — כתיבת מיילים מקצועיים עם AI."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()
CATEGORY = "emails"


def compose_email() -> str | None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return None

    UI.rule("✉️  פרטי המייל")
    recipient = UI.input("שם הנמען")
    rel_idx = UI.menu("מערכת יחסים", ["👔 עמית/ה לעבודה", "👑 בוס/מנהל", "💼 לקוח/ה", "🤝 שותף עסקי", "👥 חבר/ה"])
    relationship = ["colleague", "manager", "client", "business_partner", "friend"][rel_idx]

    purpose = UI.input("מה מטרת המייל? (תאר בקצרה)")
    tone_idx = UI.menu("טון", ["📌 פורמלי", "🤝 ידידותי-מקצועי", "😊 קז'ואל", "⚡ דחוף"])
    tone = ["formal", "friendly-professional", "casual", "urgent"][tone_idx]

    lang_idx = UI.menu("שפה", ["🇮🇱 עברית", "🇬🇧 אנגלית", "🌐 שתיהן (עברית + אנגלית)"])
    language = ["Hebrew", "English", "both Hebrew and English"][lang_idx]

    key_points = UI.input("נקודות עיקריות לכלול (אופציונלי)", default="")

    system = (
        "אתה מומחה לכתיבת מיילים עסקיים ומקצועיים. "
        "כתוב מיילים ברורים, ממוקדים ואפקטיביים."
    )

    prompt = (
        f"כתוב מייל עסקי:\n"
        f"- נמען: {recipient}\n"
        f"- מערכת יחסים: {relationship}\n"
        f"- מטרה: {purpose}\n"
        f"- טון: {tone}\n"
        f"- שפה: {language}\n"
        f"- נקודות לכלול: {key_points or 'ללא'}\n\n"
        "כלול: שורת נושא (Subject:), גוף המייל, חתימה מקצועית."
    )

    UI.rule("📝 המייל שנוצר")
    try:
        client = ClaudeClient()
        email_text = UI.stream_print(client.stream_chat(system, prompt))
        return email_text
    except Exception as e:
        UI.error(f"שגיאה ביצירת המייל: {e}")
        return None


def refine_email(original: str, instruction: str) -> str | None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return None

    system = "אתה מומחה לכתיבת מיילים. שפר את המייל לפי ההוראה."
    prompt = f"המייל המקורי:\n\n{original}\n\nהוראה לשיפור: {instruction}\n\nכתוב את המייל המשופר:"

    UI.rule("✏️  מייל משופר")
    try:
        client = ClaudeClient()
        return UI.stream_print(client.stream_chat(system, prompt))
    except Exception as e:
        UI.error(f"שגיאה: {e}")
        return None


def save_email(email_text: str) -> None:
    subject = ""
    for line in email_text.split("\n"):
        if line.lower().startswith("subject:") or line.lower().startswith("נושא:"):
            subject = line.split(":", 1)[-1].strip()
            break

    db.save(CATEGORY, {
        "subject": subject or "ללא נושא",
        "content": email_text,
        "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    UI.success("המייל נשמר!")


def view_saved_emails() -> None:
    emails = db.list_all(CATEGORY)
    if not emails:
        UI.info("אין מיילים שמורים.")
        return

    rows = [[str(e["_id"]), e.get("subject", "—"), e.get("saved_at", "—")] for e in emails]
    UI.table("📬 מיילים שמורים", ["#", "נושא", "תאריך שמירה"], rows)

    view_id = UI.input("הזן # להצגת מייל מלא (Enter לדלג)", default="")
    if view_id.isdigit():
        email = db.load(CATEGORY, int(view_id))
        if email:
            UI.rule(f"📧 {email.get('subject', '')}")
            from shared.ui import console
            console.print(email.get("content", ""))


def main() -> None:
    UI.header("📧 Email Composer", "כתיבת מיילים מקצועיים עם AI")

    current_email: str | None = None

    while True:
        options = [
            "✍️  כתוב מייל חדש",
            "📬 הצג מיילים שמורים",
            "🚪 יציאה",
        ]
        if current_email:
            options.insert(1, "✂️  קצר את המייל")
            options.insert(2, "🎩 הפוך לפורמלי יותר")
            options.insert(3, "😊 הפוך לקז'ואל יותר")
            options.insert(4, "💾 שמור מייל נוכחי")

        choice = UI.menu("תפריט", options)

        if not current_email:
            if choice == 0:
                current_email = compose_email()
            elif choice == 1:
                view_saved_emails()
            elif choice == 2:
                break
        else:
            if choice == 0:
                current_email = compose_email()
            elif choice == 1:
                new = refine_email(current_email, "קצר את המייל, השאר רק העיקר")
                if new:
                    current_email = new
            elif choice == 2:
                new = refine_email(current_email, "הפוך לפורמלי ומקצועי יותר")
                if new:
                    current_email = new
            elif choice == 3:
                new = refine_email(current_email, "הפוך לקז'ואל וידידותי יותר")
                if new:
                    current_email = new
            elif choice == 4:
                save_email(current_email)
            elif choice == 5:
                view_saved_emails()
            elif choice == 6:
                break

    UI.success("להתראות! 📧")


if __name__ == "__main__":
    main()
