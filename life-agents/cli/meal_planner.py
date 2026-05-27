"""🗓️ Meal Planner — תכנון תפריט שבועי עם AI."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()
CATEGORY = "meal_plans"

SYSTEM = """אתה תזונאי ושף מנוסה. עזור למשתמש לתכנן תפריט שבועי מאוזן, טעים ומעשי.
ענה בעברית. כלול מגוון ארוחות ומתחשב בהעדפות המשתמש."""


def create_meal_plan() -> str | None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return None

    UI.rule("🥗 פרטים לתכנון התפריט")
    restrictions = UI.input("הגבלות תזונתיות / אלרגיות (Enter לדלג)", default="ללא")
    people = UI.input("כמה אנשים?", default="2")
    budget_idx = UI.menu("תקציב לשבוע", ["💰 חסכוני (עד 300₪)", "💰💰 בינוני (300-600₪)", "💰💰💰 נדיב (600₪+)"])
    budget = ["חסכוני (עד 300₪)", "בינוני (300-600₪)", "נדיב (600₪+)"][budget_idx]

    likes = UI.input("מאכלים אהובים (אופציונלי)", default="")
    dislikes = UI.input("מאכלים שלא אוהב (אופציונלי)", default="")
    cooking_time = UI.input("זמן בישול מקסימלי ביום (דקות)", default="45")

    prompt = (
        f"צור תפריט שבועי מלא (ראשון עד שבת) עבור {people} אנשים:\n"
        f"- הגבלות: {restrictions}\n"
        f"- תקציב שבועי: {budget}\n"
        f"- אוהב: {likes or 'הכל'}\n"
        f"- לא אוהב: {dislikes or 'ללא'}\n"
        f"- זמן בישול: עד {cooking_time} דקות\n\n"
        "פורמט:\n"
        "**יום ראשון:**\n"
        "🌅 ארוחת בוקר: ...\n"
        "☀️ ארוחת צהריים: ...\n"
        "🌙 ארוחת ערב: ...\n"
        "(חזור לכל 6 ימים)\n\n"
        "בסוף הוסף:\n"
        "**💡 טיפים להכנה מראש (meal prep)**\n"
        "**🛒 רשימת קניות כוללת לשבוע** (מקובצת לפי קטגוריה)"
    )

    UI.rule("🗓️ התפריט השבועי שלך")
    try:
        client = ClaudeClient()
        return UI.stream_print(client.stream_chat(SYSTEM, prompt))
    except Exception as e:
        UI.error(f"שגיאה: {e}")
        return None


def view_plans() -> None:
    plans = db.list_all(CATEGORY)
    if not plans:
        UI.info("אין תוכניות ארוחות שמורות.")
        return

    rows = [
        [str(p["_id"]), p.get("week_start", "—"), p.get("people", "—"), p.get("saved_at", "—")]
        for p in plans
    ]
    UI.table("🗓️ תוכניות ארוחות", ["#", "שבוע", "אנשים", "תאריך"], rows)

    plan_id = UI.input("הזן # להצגה (Enter לדלג)", default="")
    if plan_id.isdigit():
        plan = db.load(CATEGORY, int(plan_id))
        if plan:
            UI.rule("🗓️ תפריט שבועי")
            from shared.ui import console
            console.print(plan.get("content", ""))


def main() -> None:
    UI.header("🗓️ Meal Planner", "תכנון תפריט שבועי חכם")

    current_plan: str | None = None

    while True:
        options = ["📅 צור תפריט שבועי חדש", "📚 תוכניות שמורות", "🚪 יציאה"]
        if current_plan:
            options.insert(1, "💾 שמור תפריט נוכחי")

        choice = UI.menu("תפריט", options)

        if not current_plan:
            if choice == 0:
                current_plan = create_meal_plan()
            elif choice == 1:
                view_plans()
            else:
                break
        else:
            if choice == 0:
                current_plan = create_meal_plan()
            elif choice == 1:
                week_start = datetime.now().strftime("%d/%m/%Y")
                db.save(CATEGORY, {
                    "week_start": week_start,
                    "content": current_plan,
                    "people": "2",
                    "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                })
                UI.success("תפריט נשמר!")
                current_plan = None
            elif choice == 2:
                view_plans()
            else:
                break

    UI.success("להתראות! 🗓️")


if __name__ == "__main__":
    main()
