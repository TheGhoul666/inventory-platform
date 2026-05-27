"""📅 Daily Planner — תכנון יום חכם עם AI."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()

SYSTEM = """אתה מאמן פרודוקטיביות אישי. עזור למשתמש לתכנן את היום שלו בצורה אפקטיבית.
ענה בעברית. השתמש בסגנון ברור, מעשי ומעודד."""


def generate_day_plan(mood: str, agenda: str, tasks: list) -> str | None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return None

    pending_tasks = "\n".join(
        f"- [{t.get('priority','medium').upper()}] {t.get('title','')}"
        for t in tasks[:10]
    )

    today = datetime.now().strftime("%A, %d/%m/%Y")
    prompt = (
        f"תאריך: {today}\n"
        f"מצב רוח/אנרגיה: {mood}\n"
        f"מה על הפרק היום: {agenda}\n"
        f"משימות פתוחות מהמערכת:\n{pending_tasks or 'אין משימות רשומות'}\n\n"
        "צור תוכנית יום מפורטת עם:\n"
        "1. 🌅 בלוקי זמן (פורמט: 09:00-10:30: [פעילות])\n"
        "2. ⚡ 3 עדיפויות ראשיות להיום\n"
        "3. 🔋 הפסקות מומלצות\n"
        "4. 💡 טיפ אחד להיום\n"
        "5. 🎯 מה 'ניצחון קטן' שתוכל להשיג היום?"
    )

    UI.rule("📅 תוכנית היום שלך")
    try:
        client = ClaudeClient()
        return UI.stream_print(client.stream_chat(SYSTEM, prompt))
    except Exception as e:
        UI.error(f"שגיאה: {e}")
        return None


def evening_review(plan_id: int) -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    plan = db.load("daily_plans", plan_id)
    if not plan:
        UI.error("תוכנית לא נמצאה")
        return

    UI.rule("🌙 סקירת ערב")
    done = UI.input("מה הצלחת לעשות היום? (תאר בקצרה)")
    not_done = UI.input("מה לא הספקת?")
    energy = UI.input("איך הייתה האנרגיה שלך? (1-10)", default="7")
    notes = UI.input("הערות נוספות", default="")

    prompt = (
        f"תוכנית הבוקר:\n{plan.get('plan_text', '')}\n\n"
        f"מה הושלם: {done}\n"
        f"מה לא הושלם: {not_done}\n"
        f"רמת אנרגיה: {energy}/10\n"
        f"הערות: {notes}\n\n"
        "תן:\n"
        "1. 🏆 הישגי היום\n"
        "2. 📚 לקחים ותובנות\n"
        "3. 🌅 המלצה לפתיחת מחר\n"
        "4. 💬 מילה מעודדת"
    )

    try:
        client = ClaudeClient()
        review_text = UI.stream_print(client.stream_chat(SYSTEM, prompt))

        # Update plan with review
        plan["evening_review"] = {
            "done": done,
            "not_done": not_done,
            "energy": energy,
            "review_text": review_text,
        }
        clean = {k: v for k, v in plan.items() if not k.startswith("_")}
        db.update("daily_plans", plan_id, clean)
        UI.success("סקירת ערב נשמרה!")
    except Exception as e:
        UI.error(f"שגיאה: {e}")


def view_past_plans() -> None:
    plans = db.list_all("daily_plans")
    if not plans:
        UI.info("אין תוכניות יום שמורות.")
        return

    rows = [
        [str(p["_id"]), p.get("date", "—"), "✅" if p.get("evening_review") else "⏳"]
        for p in plans[:10]
    ]
    UI.table("📅 תוכניות יום", ["#", "תאריך", "סקירת ערב"], rows)

    plan_id = UI.input("הזן # לסקירת ערב (Enter לדלג)", default="")
    if plan_id.isdigit():
        evening_review(int(plan_id))


def main() -> None:
    UI.header("📅 Daily Planner", "תכנון יום אפקטיבי עם AI")

    today = datetime.now().strftime("%A, %d/%m/%Y")
    UI.info(f"היום: {today}")

    while True:
        choice = UI.menu("תפריט", [
            "🌅 צור תוכנית יום חדשה",
            "📚 תוכניות יום קודמות + סקירת ערב",
            "🚪 יציאה",
        ])

        if choice == 0:
            UI.rule("🌤️  בוקר טוב!")
            mood = UI.input("איך אתה מרגיש היום? (תאר)")
            agenda = UI.input("מה על הפרק היום? (פגישות, משימות גדולות, מחויבויות)")

            # Load pending tasks
            tasks = db.list_all("tasks")
            pending = [t for t in tasks if t.get("status") != "done"]

            plan_text = generate_day_plan(mood, agenda, pending)
            if plan_text:
                plan_id = db.save("daily_plans", {
                    "date": today,
                    "mood": mood,
                    "agenda": agenda,
                    "plan_text": plan_text,
                    "evening_review": None,
                })
                UI.success(f"תוכנית נשמרה (#{plan_id})")

        elif choice == 1:
            view_past_plans()
        elif choice == 2:
            UI.success("להתראות! 📅")
            break


if __name__ == "__main__":
    main()
