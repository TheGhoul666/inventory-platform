"""🥗 Calorie Counter — מעקב קלוריות יומי."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()
CATEGORY = "calorie_logs"

DEFAULT_GOAL = 2000


def get_goal() -> int:
    return int(db.get_setting("calorie_goal") or DEFAULT_GOAL)


def quick_log() -> None:
    """Log food described in natural language — AI estimates calories."""
    if not config.has_api_key():
        UI.warning("ללא API key — הזן קלוריות ידנית.")
        manual_log()
        return

    UI.rule("⚡ רישום מהיר")
    description = UI.input("מה אכלת? (תאר בחופשיות)")
    if not description:
        return

    try:
        client = ClaudeClient()
        estimate = client.quick(
            f"הערך את הקלוריות ב: '{description}'\n"
            "ענה בפורמט JSON בלבד: "
            '{\"calories\": 350, \"protein\": 20, \"carbs\": 40, \"fat\": 10, \"notes\": \"הערה\"}\n'
            "שים לב: מנה בישראלית ממוצעת. ענה בפורמט JSON בלבד ללא טקסט נוסף."
        )
        import json
        data = json.loads(estimate.strip().strip("```json").strip("```").strip())
        cals = int(data.get("calories", 0))
        protein = data.get("protein", 0)
        carbs = data.get("carbs", 0)
        fat = data.get("fat", 0)
        notes = data.get("notes", "")
    except Exception:
        UI.warning("לא הצלחתי לנתח. הזן ידנית.")
        manual_log()
        return

    from shared.ui import console
    console.print(f"\n  🥗 [bold]{description}[/bold]")
    console.print(f"  🔥 קלוריות: [bold green]{cals}[/bold green]")
    console.print(f"  🥩 חלבון: {protein}g  |  🍞 פחמימות: {carbs}g  |  🧈 שומן: {fat}g")
    if notes:
        console.print(f"  📝 {notes}")

    meal_idx = UI.menu("סוג ארוחה", ["🌅 בוקר", "☀️ צהריים", "🌙 ערב", "🍎 חטיף"])
    meal_type = ["breakfast", "lunch", "dinner", "snack"][meal_idx]

    db.save(CATEGORY, {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "time": datetime.now().strftime("%H:%M"),
        "description": description,
        "calories": cals,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "meal_type": meal_type,
    })
    _show_progress()


def manual_log() -> None:
    UI.rule("📝 רישום ידני")
    description = UI.input("תיאור האוכל")
    calories = UI.input("קלוריות", default="0")
    meal_idx = UI.menu("סוג ארוחה", ["🌅 בוקר", "☀️ צהריים", "🌙 ערב", "🍎 חטיף"])
    meal_type = ["breakfast", "lunch", "dinner", "snack"][meal_idx]

    db.save(CATEGORY, {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "time": datetime.now().strftime("%H:%M"),
        "description": description,
        "calories": int(calories) if calories.isdigit() else 0,
        "protein": 0, "carbs": 0, "fat": 0,
        "meal_type": meal_type,
    })
    UI.success(f"נרשם: {description} ({calories} קל')")
    _show_progress()


def _show_progress() -> None:
    today = datetime.now().strftime("%d/%m/%Y")
    logs = [l for l in db.list_all(CATEGORY) if l.get("date") == today]
    total = sum(l.get("calories", 0) for l in logs)
    goal = get_goal()
    remaining = goal - total

    from shared.ui import console
    pct = min(total / goal * 100, 100) if goal > 0 else 0
    color = "green" if remaining > 0 else "red"
    console.print(f"\n  🔥 [{color}]{total} / {goal} קל'[/{color}] ({pct:.0f}%)")
    if remaining > 0:
        UI.info(f"נותר: {remaining} קל' ליעד היום")
    else:
        UI.warning(f"עברת ב-{abs(remaining)} קל'")


def view_today() -> None:
    today = datetime.now().strftime("%d/%m/%Y")
    logs = [l for l in db.list_all(CATEGORY) if l.get("date") == today]

    if not logs:
        UI.info("לא נרשמו ארוחות היום.")
        return

    meal_icons = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙", "snack": "🍎"}
    rows = [
        [meal_icons.get(l.get("meal_type", ""), ""), l.get("time", "—"),
         l.get("description", "—"), str(l.get("calories", 0)),
         f"{l.get('protein',0)}g", f"{l.get('carbs',0)}g"]
        for l in reversed(logs)
    ]
    UI.table(f"🥗 יומן אכילה — {today}", ["", "שעה", "תיאור", "קל'", "חלבון", "פחמימות"], rows)
    _show_progress()


def set_goal() -> None:
    current = get_goal()
    new = UI.input(f"יעד קלוריות יומי (נוכחי: {current})", default=str(current))
    if new.isdigit():
        db.set_setting("calorie_goal", int(new))
        UI.success(f"יעד עודכן: {new} קל'")


def main() -> None:
    UI.header("🥗 Calorie Counter", "מעקב קלוריות יומי")

    while True:
        choice = UI.menu("תפריט", [
            "⚡ רישום מהיר (AI)",
            "📝 רישום ידני",
            "📊 ראה היום",
            "🎯 הגדר יעד קלורי",
            "🚪 יציאה",
        ])
        if choice == 0:
            quick_log()
        elif choice == 1:
            manual_log()
        elif choice == 2:
            view_today()
        elif choice == 3:
            set_goal()
        elif choice == 4:
            break

    UI.success("אכול בריא! 🥗")


if __name__ == "__main__":
    main()
