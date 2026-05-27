"""😴 Sleep Coach — מעקב ואימון שינה."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()
CATEGORY = "sleep_logs"

SYSTEM = """אתה מאמן שינה מוסמך המתמחה בשיפור איכות השינה.
ענה בעברית. שים דגש על המלצות מבוססות מדע שניתן ליישם בקלות.
היה תומך ולא שיפוטי."""


def log_sleep() -> None:
    UI.rule("😴 רישום שינה")
    bedtime = UI.input("שעת שכיבה לישון (HH:MM)", default="23:00")
    wake_time = UI.input("שעת קימה (HH:MM)", default="07:00")

    # Calculate duration
    try:
        bed_h, bed_m = map(int, bedtime.split(":"))
        wake_h, wake_m = map(int, wake_time.split(":"))
        duration_mins = (wake_h * 60 + wake_m) - (bed_h * 60 + bed_m)
        if duration_mins < 0:
            duration_mins += 24 * 60
        duration_str = f"{duration_mins // 60}:{duration_mins % 60:02d} שעות"
    except Exception:
        duration_str = "לא ידוע"

    quality = UI.input("איכות השינה (1-10)", default="7")
    interruptions = UI.input("כמה פעמים התעוררת?", default="0")
    notes = UI.input("הערות (חלומות, קושי להירדם, וכו')", default="")

    date_today = datetime.now().strftime("%d/%m/%Y")
    db.save(CATEGORY, {
        "date": date_today,
        "bedtime": bedtime,
        "wake_time": wake_time,
        "duration": duration_str,
        "duration_mins": duration_mins if isinstance(duration_mins, int) else 0,
        "quality": int(quality) if quality.isdigit() else 7,
        "interruptions": int(interruptions) if interruptions.isdigit() else 0,
        "notes": notes,
    })

    from shared.ui import console
    console.print(f"\n  😴 נרשם! {bedtime} → {wake_time} = [bold cyan]{duration_str}[/bold cyan]")
    q = int(quality) if quality.isdigit() else 7
    if q >= 8:
        UI.success("שינה מצוינת! ⭐")
    elif q >= 6:
        UI.info("שינה סבירה. יש מקום לשיפור.")
    else:
        UI.warning("שינה ירודה. כדאי לשפר.")


def view_sleep_history() -> None:
    logs = db.list_all(CATEGORY)[:14]
    if not logs:
        UI.info("אין יומן שינה עדיין.")
        return

    rows = []
    for log in logs:
        q = log.get("quality", 0)
        q_emoji = "🟢" if q >= 8 else "🟡" if q >= 6 else "🔴"
        rows.append([
            log.get("date", "—"),
            log.get("bedtime", "—"),
            log.get("wake_time", "—"),
            log.get("duration", "—"),
            f"{q_emoji} {q}/10",
            str(log.get("interruptions", 0)),
        ])

    UI.table("📊 יומן שינה (14 ימים אחרונים)",
             ["תאריך", "שכיבה", "קימה", "משך", "איכות", "התעוררויות"], rows)

    if logs:
        avg_quality = sum(l.get("quality", 0) for l in logs) / len(logs)
        avg_duration = sum(l.get("duration_mins", 0) for l in logs) / len(logs)
        UI.info(f"ממוצע: איכות {avg_quality:.1f}/10 | {avg_duration/60:.1f} שעות")


def get_sleep_tips() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    logs = db.list_all(CATEGORY)[:7]
    if not logs:
        UI.info("רשום לפחות שינה אחת תחילה.")
        return

    avg_q = sum(l.get("quality", 0) for l in logs) / len(logs)
    avg_dur = sum(l.get("duration_mins", 0) for l in logs) / len(logs)
    avg_interruptions = sum(l.get("interruptions", 0) for l in logs) / len(logs)
    bedtimes = [l.get("bedtime", "23:00") for l in logs]

    current_issue = UI.input("מה הבעיה העיקרית שלך עם השינה? (אופציונלי)", default="")

    prompt = (
        f"נתוני שינה (7 ימים אחרונים):\n"
        f"- ממוצע איכות: {avg_q:.1f}/10\n"
        f"- ממוצע משך: {avg_dur/60:.1f} שעות\n"
        f"- ממוצע התעוררויות: {avg_interruptions:.1f}\n"
        f"- שעות שכיבה: {', '.join(bedtimes)}\n"
        f"- בעיה עיקרית: {current_issue or 'לא ציוין'}\n\n"
        "תן:\n"
        "1. 📊 ניתוח דפוס השינה\n"
        "2. 🚨 בעיות שאני מזהה\n"
        "3. 💡 5 טיפים ספציפיים לשיפור מיידי\n"
        "4. 🌙 שגרת לילה מומלצת (שעה לפני שינה)\n"
        "5. 🌅 שגרת בוקר מומלצת"
    )

    UI.rule("🤖 המלצות מאמן השינה")
    try:
        client = ClaudeClient()
        UI.stream_print(client.stream_chat(SYSTEM, prompt))
    except Exception as e:
        UI.error(f"שגיאה: {e}")


def main() -> None:
    UI.header("😴 Sleep Coach", "מעקב ושיפור איכות השינה")

    while True:
        choice = UI.menu("תפריט", [
            "📝 רשום שינה של הלילה",
            "📊 היסטוריית שינה",
            "💡 טיפים לשיפור מ-AI",
            "🚪 יציאה",
        ])
        if choice == 0:
            log_sleep()
        elif choice == 1:
            view_sleep_history()
        elif choice == 2:
            get_sleep_tips()
        elif choice == 3:
            UI.success("לילה טוב! 😴")
            break


if __name__ == "__main__":
    main()
