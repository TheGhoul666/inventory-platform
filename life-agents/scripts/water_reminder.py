"""💧 Water Reminder — מעקב שתיית מים."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage

db = Storage()
CATEGORY = "water_logs"

DEFAULT_GOAL_ML = 2000


def get_goal() -> int:
    return int(db.get_setting("water_goal_ml") or DEFAULT_GOAL_ML)


def log_water() -> None:
    UI.rule("💧 רישום שתייה")
    from shared.ui import console

    console.print("[dim]כמות מהירה:[/dim]")
    console.print("  [cyan]1.[/cyan] כוס (250 מ\"ל)")
    console.print("  [cyan]2.[/cyan] בקבוק קטן (500 מ\"ל)")
    console.print("  [cyan]3.[/cyan] בקבוק גדול (750 מ\"ל)")
    console.print("  [cyan]4.[/cyan] כמות מותאמת אישית")

    choice = UI.input("בחר (1-4)", default="1")
    amounts = {"1": 250, "2": 500, "3": 750}

    if choice in amounts:
        ml = amounts[choice]
    else:
        ml_str = UI.input("כמה מ\"ל?", default="250")
        ml = int(ml_str) if ml_str.isdigit() else 250

    today = datetime.now().strftime("%d/%m/%Y")
    db.save(CATEGORY, {
        "date": today,
        "time": datetime.now().strftime("%H:%M"),
        "ml": ml,
    })

    # Show daily progress
    _show_daily_progress(today)


def _show_daily_progress(date: str) -> None:
    from rich.progress import Progress, BarColumn, TextColumn
    from shared.ui import console

    goal = get_goal()
    logs = [l for l in db.list_all(CATEGORY) if l.get("date") == date]
    total = sum(l.get("ml", 0) for l in logs)
    pct = min(total / goal * 100, 100)

    console.print()
    color = "green" if pct >= 100 else "cyan" if pct >= 50 else "yellow"
    bar_filled = int(pct / 5)
    bar = f"[{color}]{'█' * bar_filled}{'░' * (20 - bar_filled)}[/{color}]"
    console.print(f"  💧 {bar} [bold]{total} / {goal} מ\"ל[/bold] ({pct:.0f}%)")

    if pct >= 100:
        UI.success("🎉 הגעת ליעד היום!")
    elif pct >= 50:
        UI.info(f"חצי הדרך! עוד {goal - total} מ\"ל")
    else:
        UI.warning(f"שים לב! עוד {goal - total} מ\"ל ליעד")
    console.print()


def view_today() -> None:
    today = datetime.now().strftime("%d/%m/%Y")
    logs = [l for l in db.list_all(CATEGORY) if l.get("date") == today]

    if not logs:
        UI.info("אין רישומים להיום עדיין.")
        return

    rows = [[l.get("time", "—"), f"{l.get('ml', 0)} מ\"ל"] for l in reversed(logs)]
    UI.table(f"💧 שתייה היום — {today}", ["שעה", "כמות"], rows)
    _show_daily_progress(today)


def set_goal() -> None:
    current = get_goal()
    UI.info(f"יעד נוכחי: {current} מ\"ל")
    new_goal = UI.input("יעד חדש (מ\"ל)", default=str(current))
    if new_goal.isdigit():
        db.set_setting("water_goal_ml", int(new_goal))
        UI.success(f"יעד עודכן: {new_goal} מ\"ל")


def weekly_average() -> None:
    from datetime import timedelta
    today = datetime.now()

    rows = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%d/%m/%Y")
        logs = [l for l in db.list_all(CATEGORY) if l.get("date") == day_str]
        total = sum(l.get("ml", 0) for l in logs)
        goal = get_goal()
        status = "✅" if total >= goal else "❌"
        rows.append([day.strftime("%a %d/%m"), f"{total} מ\"ל", status])

    UI.table("📊 שבוע אחרון", ["תאריך", "שתייה", "יעד"], rows)


def main() -> None:
    UI.header("💧 Water Reminder", "מעקב שתיית מים יומי")

    while True:
        choice = UI.menu("תפריט", [
            "💧 רשום שתייה",
            "📊 ראה היום",
            "📈 ממוצע שבועי",
            "🎯 הגדר יעד",
            "🚪 יציאה",
        ])
        if choice == 0:
            log_water()
        elif choice == 1:
            view_today()
        elif choice == 2:
            weekly_average()
        elif choice == 3:
            set_goal()
        elif choice == 4:
            UI.success("שתה מים! 💧")
            break


if __name__ == "__main__":
    main()
