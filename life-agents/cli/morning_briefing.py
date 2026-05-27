"""☀️ Morning Briefing — תדריך בוקר אישי."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()

SYSTEM = """אתה עוזר אישי שמפיק תדריכי בוקר מעוררי השראה ומעשיים.
ענה בעברית. היה אנרגטי, חם ומעודד. כלול מידע ספציפי ומועיל."""

DAYS_HE = {
    "Monday": "יום שני", "Tuesday": "יום שלישי", "Wednesday": "יום רביעי",
    "Thursday": "יום חמישי", "Friday": "יום שישי", "Saturday": "שבת", "Sunday": "יום ראשון"
}


def generate_briefing() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        # Still show non-AI summary
        _show_basic_summary()
        return

    now = datetime.now()
    day_he = DAYS_HE.get(now.strftime("%A"), now.strftime("%A"))
    date_str = now.strftime("%d/%m/%Y")

    UI.rule(f"☀️ {day_he}, {date_str}")

    # Gather data
    tasks = [t for t in db.list_all("tasks") if t.get("status") != "done"]
    bills = db.list_all("bills")
    last_mood = db.list_all("mood_logs")
    last_mood = last_mood[0] if last_mood else None

    # Check due bills
    today = now.day
    upcoming_bills = [b for b in bills if abs(int(b.get("due_day", 0)) - today) <= 3]

    # Ask for priorities
    priorities = UI.input("3 עדיפויות לבוקר זה (מופרדות בפסיקים)")
    extra_note = UI.input("משהו חשוב לציין? (אופציונלי)", default="")

    # Build context
    pending_tasks_str = "\n".join(
        f"- [{t.get('priority','').upper()}] {t.get('title','')}"
        for t in tasks[:8]
    ) or "אין משימות ממתינות"

    bills_str = "\n".join(
        f"- {b.get('name','')} — ₪{b.get('amount',0)} (יום {b.get('due_day','')})"
        for b in upcoming_bills
    ) or "אין חשבונות דחופים"

    mood_str = (
        f"מצב רוח אתמול: {last_mood.get('mood',0)}/10, סטרס: {last_mood.get('stress',0)}/10"
        if last_mood else "אין נתוני מצב רוח"
    )

    prompt = (
        f"תאריך: {day_he}, {date_str}, שעה: {now.strftime('%H:%M')}\n\n"
        f"עדיפויות היום: {priorities}\n"
        f"הערה נוספת: {extra_note or 'אין'}\n\n"
        f"משימות ממתינות:\n{pending_tasks_str}\n\n"
        f"חשבונות קרובים:\n{bills_str}\n\n"
        f"נתוני אתמול: {mood_str}\n\n"
        "צור תדריך בוקר אישי הכולל:\n"
        "1. 👋 ברכת בוקר אנרגטית\n"
        "2. 🎯 3 עדיפויות היום (מה שציינתי + המלצות)\n"
        "3. ⏰ הצעת תזמון ליום\n"
        "4. 🔔 תזכורות חשובות\n"
        "5. 💡 טיפ אחד לפרודוקטיביות\n"
        "6. 💬 מילה מעודדת לסיום"
    )

    UI.rule("☀️ תדריך הבוקר שלך")
    try:
        client = ClaudeClient()
        briefing_text = UI.stream_print(client.stream_chat(SYSTEM, prompt))

        db.save("briefings", {
            "date": date_str,
            "day": day_he,
            "priorities": priorities,
            "briefing_text": briefing_text,
        })
        UI.success("תדריך נשמר!")
    except Exception as e:
        UI.error(f"שגיאה: {e}")
        _show_basic_summary()


def _show_basic_summary() -> None:
    """Show basic summary without AI."""
    now = datetime.now()
    UI.rule(f"☀️ {DAYS_HE.get(now.strftime('%A'), '')} {now.strftime('%d/%m/%Y')}")

    tasks = [t for t in db.list_all("tasks") if t.get("status") != "done"]
    if tasks:
        rows = [[t.get("title", "—"), t.get("priority", "—"), t.get("due_date", "—")]
                for t in tasks[:5]]
        UI.table("📋 משימות ממתינות", ["משימה", "עדיפות", "יעד"], rows)

    bills = db.list_all("bills")
    today = now.day
    upcoming = [b for b in bills if abs(int(b.get("due_day", 0)) - today) <= 3]
    if upcoming:
        rows = [[b.get("name", "—"), f"₪{b.get('amount', 0)}", str(b.get("due_day", ""))]
                for b in upcoming]
        UI.table("🔔 חשבונות קרובים", ["שם", "סכום", "יום בחודש"], rows)


def view_past_briefings() -> None:
    briefings = db.list_all("briefings")[:7]
    if not briefings:
        UI.info("אין תדריכים שמורים.")
        return

    rows = [[str(b["_id"]), b.get("date", "—"), b.get("day", "—")] for b in briefings]
    UI.table("📅 תדריכים שמורים", ["#", "תאריך", "יום"], rows)

    bid = UI.input("הזן # להצגה (Enter לדלג)", default="")
    if bid.isdigit():
        b = db.load("briefings", int(bid))
        if b:
            UI.rule(f"☀️ {b.get('date','')} — {b.get('day','')}")
            from shared.ui import console
            console.print(b.get("briefing_text", ""))


def main() -> None:
    UI.header("☀️ Morning Briefing", "התחל את היום בצורה הטובה ביותר")

    while True:
        choice = UI.menu("תפריט", [
            "☀️ צור תדריך בוקר",
            "📅 תדריכים קודמים",
            "🚪 יציאה",
        ])
        if choice == 0:
            generate_briefing()
        elif choice == 1:
            view_past_briefings()
        elif choice == 2:
            UI.success("בוקר טוב! ☀️")
            break


if __name__ == "__main__":
    main()
