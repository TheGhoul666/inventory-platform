"""🏋️ Workout Planner — תכנון אימונים אישי."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()

SYSTEM = """אתה מאמן כושר אישי מוסמך ומנוסה.
תכנן אימונים מותאמים אישית, מציאותיים ובטוחים.
ענה בעברית. כלול: שמות התרגילים בעברית ואנגלית, מספר סטים/חזרות, זמני מנוחה, טיפים לביצוע."""


def setup_profile() -> None:
    UI.rule("👤 פרופיל כושר")
    level_idx = UI.menu("רמת כושר", ["🌱 מתחיל", "💪 בינוני", "🔥 מתקדם"])
    level = ["beginner", "intermediate", "advanced"][level_idx]

    goal_idx = UI.menu("מטרה עיקרית", ["⬇️ ירידה במשקל", "💪 בניית שרירים", "🏃 סיבולת", "🧘 פעילות ושמירה על בריאות"])
    goal = ["weight_loss", "muscle_gain", "endurance", "maintenance"][goal_idx]

    days = UI.input("כמה ימי אימון בשבוע?", default="3")
    equipment_idx = UI.menu("ציוד זמין", ["🏠 ללא ציוד (בית)", "🏋️ ציוד בסיסי (משקולות/גומיות)", "🏢 חדר כושר מלא"])
    equipment = ["no_equipment", "basic_equipment", "full_gym"][equipment_idx]

    injuries = UI.input("פציעות / הגבלות רפואיות (Enter לדלג)", default="ללא")

    db.set_setting("fitness_profile", {
        "level": level,
        "goal": goal,
        "days_per_week": days,
        "equipment": equipment,
        "injuries": injuries,
        "updated": datetime.now().strftime("%d/%m/%Y"),
    })
    UI.success("פרופיל כושר נשמר!")


def generate_workout_plan() -> str | None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return None

    profile = db.get_setting("fitness_profile")
    if not profile:
        UI.warning("לא נמצא פרופיל כושר. ממלא ברירת מחדל.")
        profile = {"level": "beginner", "goal": "maintenance", "days_per_week": "3",
                   "equipment": "no_equipment", "injuries": "ללא"}

    levels = {"beginner": "מתחיל", "intermediate": "בינוני", "advanced": "מתקדם"}
    goals = {"weight_loss": "ירידה במשקל", "muscle_gain": "בניית שרירים",
              "endurance": "סיבולת", "maintenance": "שמירה על כושר"}
    equip = {"no_equipment": "ללא ציוד (ביתי)", "basic_equipment": "ציוד בסיסי", "full_gym": "חדר כושר"}

    prompt = (
        f"צור תוכנית אימונים שבועית:\n"
        f"- רמה: {levels.get(profile.get('level'), 'מתחיל')}\n"
        f"- מטרה: {goals.get(profile.get('goal'), 'כושר כללי')}\n"
        f"- ימי אימון: {profile.get('days_per_week', '3')} ימים בשבוע\n"
        f"- ציוד: {equip.get(profile.get('equipment'), 'ללא')}\n"
        f"- פציעות: {profile.get('injuries', 'ללא')}\n\n"
        "לכל יום אימון כלול:\n"
        "- שם האימון (למשל: 'יום עליון' / 'יום רגליים' / 'קרדיו')\n"
        "- חימום (5 דקות)\n"
        "- תרגילים עיקריים (שם, סטים × חזרות, זמן מנוחה)\n"
        "- שחרור (5 דקות)\n"
        "- זמן כולל משוער\n\n"
        "בסוף: טיפים כלליים לתוכנית זו"
    )

    UI.rule("🏋️ תוכנית האימונים שלך")
    try:
        client = ClaudeClient()
        return UI.stream_print(client.stream_chat(SYSTEM, prompt))
    except Exception as e:
        UI.error(f"שגיאה: {e}")
        return None


def log_workout() -> None:
    UI.rule("📝 רישום אימון")
    workout_type = UI.input("סוג האימון (למשל: כוח רגליים, ריצה, יוגה)")
    duration = UI.input("משך (דקות)", default="45")
    intensity_idx = UI.menu("עצימות", ["😌 קלה", "💪 בינונית", "🔥 קשה"])
    intensity = ["low", "medium", "high"][intensity_idx]
    exercises = UI.input("תרגילים עיקריים שעשית")
    feeling = UI.input("איך הרגשת? (1-10)", default="7")
    notes = UI.input("הערות (אופציונלי)", default="")

    db.save("workouts", {
        "type": workout_type,
        "duration": int(duration),
        "intensity": intensity,
        "exercises": exercises,
        "feeling": feeling,
        "notes": notes,
        "date": datetime.now().strftime("%d/%m/%Y"),
    })
    UI.success(f"אימון נרשם! {duration} דקות של {workout_type} 💪")


def view_history() -> None:
    workouts = db.list_all("workouts")
    if not workouts:
        UI.info("אין אימונים רשומים עדיין.")
        return

    intensities = {"low": "😌", "medium": "💪", "high": "🔥"}
    rows = [
        [w.get("date", "—"), w.get("type", "—"), f"{w.get('duration', 0)} דק'",
         intensities.get(w.get("intensity", ""), ""), w.get("feeling", "—")]
        for w in workouts[:15]
    ]
    UI.table("💪 היסטוריית אימונים", ["תאריך", "סוג", "משך", "עצימות", "תחושה/10"], rows)

    total_time = sum(w.get("duration", 0) for w in workouts)
    UI.info(f"סה\"כ: {len(workouts)} אימונים | {total_time} דקות")


def ai_feedback() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    workouts = db.list_all("workouts")[:7]  # Last 7
    if not workouts:
        UI.info("אין אימונים לניתוח.")
        return

    summary = "\n".join(
        f"- {w.get('date')}: {w.get('type')} ({w.get('duration')} דק', עצימות: {w.get('intensity')}, תחושה: {w.get('feeling')}/10)"
        for w in workouts
    )

    profile = db.get_setting("fitness_profile") or {}
    prompt = (
        f"פרופיל: {profile}\n\n"
        f"אימונים האחרונים:\n{summary}\n\n"
        "תן:\n"
        "1. 📊 ניתוח השבוע — מה עשיתי טוב?\n"
        "2. ⚠️ מה לשפר?\n"
        "3. 🎯 המלצה לשבוע הבא\n"
        "4. 💡 טיפ אחד לשיפור הביצועים"
    )

    UI.rule("🤖 משוב מהמאמן")
    try:
        client = ClaudeClient()
        UI.stream_print(client.stream_chat(SYSTEM, prompt))
    except Exception as e:
        UI.error(f"שגיאה: {e}")


def main() -> None:
    UI.header("🏋️ Workout Planner", "תכנון כושר אישי עם AI")

    while True:
        choice = UI.menu("תפריט", [
            "👤 הגדר/עדכן פרופיל כושר",
            "📅 צור תוכנית אימונים שבועית",
            "📝 רשום אימון של היום",
            "📊 היסטוריית אימונים",
            "🤖 משוב AI מהמאמן",
            "🚪 יציאה",
        ])
        if choice == 0:
            setup_profile()
        elif choice == 1:
            plan = generate_workout_plan()
            if plan and UI.confirm("שמור תוכנית?"):
                db.save("workout_plans", {"content": plan, "date": datetime.now().strftime("%d/%m/%Y %H:%M")})
                UI.success("תוכנית נשמרה!")
        elif choice == 2:
            log_workout()
        elif choice == 3:
            view_history()
        elif choice == 4:
            ai_feedback()
        elif choice == 5:
            UI.success("להתראות! 🏋️")
            break


if __name__ == "__main__":
    main()
