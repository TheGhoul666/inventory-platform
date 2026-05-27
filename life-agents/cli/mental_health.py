"""🧠 Mental Health Check-in — בדיקת מצב רוח יומי."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()
CATEGORY = "mood_logs"

SYSTEM = """אתה מאמן רווחה נפשית מוסמך ואמפתי.
תגיב בצורה חמה, תומכת ולא שיפוטית. אל תאבחן מחלות — הפנה לאיש מקצוע במקרה הצורך.
ענה בעברית. שים דגש על כלים מעשיים מ-CBT, מיינדפולנס, וטכניקות הרפיה."""


def daily_checkin() -> None:
    UI.rule("🧠 בדיקת מצב רוח יומי")
    from shared.ui import console
    console.print("[dim]דרג מ-1 (נמוך מאוד) עד 10 (מצוין)[/dim]\n")

    mood = UI.input("😊 מצב רוח כללי (1-10)", default="7")
    energy = UI.input("⚡ רמת אנרגיה (1-10)", default="7")
    stress = UI.input("😤 רמת מתח/סטרס (1-10)", default="5")
    one_word = UI.input("מילה אחת שמתארת את היום שלך")
    notes = UI.input("רצה לשתף משהו? (אופציונלי)", default="")

    log_data = {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "time": datetime.now().strftime("%H:%M"),
        "mood": int(mood) if mood.isdigit() else 7,
        "energy": int(energy) if energy.isdigit() else 7,
        "stress": int(stress) if stress.isdigit() else 5,
        "one_word": one_word,
        "notes": notes,
    }
    log_id = db.save(CATEGORY, log_data)

    if config.has_api_key():
        prompt = (
            f"המשתמש עשה צ'ק-אין יומי:\n"
            f"- מצב רוח: {mood}/10\n"
            f"- אנרגיה: {energy}/10\n"
            f"- סטרס: {stress}/10\n"
            f"- מילת תיאור: {one_word}\n"
            f"- הערות: {notes or 'ללא'}\n\n"
            "תגיב:\n"
            "1. תגובה אמפתית קצרה למצב הנוכחי\n"
            "2. כלי/טכניקה אחת מעשית שיכולה לעזור היום\n"
            "3. מילה מעודדת קצרה"
        )
        UI.rule("💬 תגובה")
        try:
            client = ClaudeClient()
            UI.stream_print(client.stream_chat(SYSTEM, prompt))
        except Exception as e:
            UI.error(f"שגיאה: {e}")
    else:
        UI.success("צ'ק-אין נשמר! להוסיף API key לקבלת משוב אישי.")


def journaling_mode() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    UI.rule("📓 מצב יומן")
    UI.info("כתוב מה שעל ליבך. Claude יגיב בצורה תומכת.")
    UI.info("הקלד 'יציאה' לסיום.")

    client = ClaudeClient()
    history = []

    entry = UI.input("📓")
    if not entry or entry.lower() == "יציאה":
        return

    try:
        response = UI.stream_print(client.stream_chat(SYSTEM, entry))
        history.append({"role": "user", "content": entry})
        history.append({"role": "assistant", "content": response})

        while True:
            follow = UI.input("המשך...")
            if follow.lower() in ("יציאה", "exit"):
                break
            if not follow:
                continue
            response = UI.stream_print(client.stream_chat(SYSTEM, follow, history))
            history.append({"role": "user", "content": follow})
            history.append({"role": "assistant", "content": response})
    except Exception as e:
        UI.error(f"שגיאה: {e}")


def mood_chart() -> None:
    logs = db.list_all(CATEGORY)[:14]
    if not logs:
        UI.info("אין נתוני מצב רוח.")
        return

    logs_reversed = list(reversed(logs))
    from shared.ui import console
    UI.rule("📊 מפת מצב רוח (14 ימים)")

    for log in logs_reversed:
        mood = log.get("mood", 0)
        bar = "█" * mood + "░" * (10 - mood)
        color = "green" if mood >= 7 else "yellow" if mood >= 5 else "red"
        console.print(
            f"  {log.get('date', '—')}  [{color}]{bar}[/{color}]  "
            f"[dim]{mood}/10 — {log.get('one_word', '')}[/dim]"
        )

    avg_mood = sum(l.get("mood", 0) for l in logs) / len(logs)
    avg_stress = sum(l.get("stress", 0) for l in logs) / len(logs)
    console.print(f"\n  [bold]ממוצע:[/bold] מצב רוח {avg_mood:.1f}/10 | סטרס {avg_stress:.1f}/10")


def coping_strategies() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    UI.rule("🧰 כלים להתמודדות")
    situation = UI.input("מה מציק לך עכשיו? (תאר בקצרה)")
    if not situation:
        return

    prompt = (
        f"המצב: {situation}\n\n"
        "תן 5 טכניקות ספציפיות להתמודדות עם המצב הזה:\n"
        "- 2 טכניקות מיידיות (ניתן לעשות עכשיו, ב-5 דקות)\n"
        "- 2 טכניקות קצרות טווח (לשעות הקרובות)\n"
        "- 1 טיפ ארוך טווח\n\n"
        "בסוף: מתי כדאי לפנות לעזרה מקצועית?"
    )

    UI.rule("🧰 אסטרטגיות התמודדות")
    try:
        client = ClaudeClient()
        UI.stream_print(client.stream_chat(SYSTEM, prompt))
    except Exception as e:
        UI.error(f"שגיאה: {e}")


def main() -> None:
    UI.header("🧠 Mental Health Check-in", "טיפול ברווחה נפשית יומית")

    while True:
        choice = UI.menu("תפריט", [
            "📝 צ'ק-אין יומי",
            "📓 מצב יומן חופשי",
            "📊 מפת מצב רוח (14 ימים)",
            "🧰 כלים להתמודדות",
            "🚪 יציאה",
        ])
        if choice == 0:
            daily_checkin()
        elif choice == 1:
            journaling_mode()
        elif choice == 2:
            mood_chart()
        elif choice == 3:
            coping_strategies()
        elif choice == 4:
            UI.success("שמור על עצמך! 🧠💙")
            break


if __name__ == "__main__":
    main()
