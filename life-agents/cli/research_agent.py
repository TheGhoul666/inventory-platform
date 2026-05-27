"""🔍 Research Agent — מחקר מעמיק על כל נושא."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()
CATEGORY = "research"

SYSTEM = """אתה עוזר מחקר מומחה. כשמשתמש שואל שאלה מחקרית, תן:

1. **סקירה כללית** — 3-4 משפטים על הנושא
2. **נקודות מפתח** — לפחות 5 נקודות חשובות עם הסברים
3. **יתרונות וחסרונות** (אם רלוונטי)
4. **המלצות מעשיות** — מה ניתן לעשות עם המידע הזה
5. **מקורות מומלצים** — היכן ללמוד עוד (ספרים, אתרים, מומחים)

ענה בעברית, בצורה מקיפה אך ברורה. השתמש בכותרות ורשימות."""


def new_research() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    UI.rule("🔍 מחקר חדש")
    topic = UI.input("מה תרצה לחקור?")
    if not topic:
        return

    depth_idx = UI.menu("עומק המחקר", ["⚡ תקציר מהיר", "📖 מחקר רגיל", "🔬 מחקר מעמיק"])
    depth = ["קצר ותמציתי (300 מילה)", "בינוני (500 מילה)", "מעמיק ומקיף (800+ מילה)"][depth_idx]

    UI.rule(f"📊 מחקר: {topic}")

    client = ClaudeClient()
    history = []
    try:
        prompt = f"נושא: {topic}\n\nאורך תגובה: {depth}"
        response = UI.stream_print(client.stream_chat(SYSTEM, prompt))
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": response})
    except Exception as e:
        UI.error(f"שגיאה: {e}")
        return

    # Follow-up Q&A loop
    UI.rule("💬 שאלות המשך")
    UI.info("כעת תוכל לשאול שאלות המשך. הקלד 'שמור' לשמירה, 'יציאה' לסיום.")

    while True:
        follow_up = UI.input("שאלת המשך (או 'שמור'/'יציאה')")
        if follow_up.lower() in ("יציאה", "exit", "quit", "q"):
            break
        if follow_up.lower() in ("שמור", "save"):
            _save_research(topic, history)
            break
        if not follow_up:
            continue

        try:
            response = UI.stream_print(client.stream_chat(SYSTEM, follow_up, history))
            history.append({"role": "user", "content": follow_up})
            history.append({"role": "assistant", "content": response})
        except Exception as e:
            UI.error(f"שגיאה: {e}")


def _save_research(topic: str, history: list) -> None:
    db.save(CATEGORY, {
        "topic": topic,
        "history": history,
        "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "turns": len([h for h in history if h["role"] == "assistant"]),
    })
    UI.success(f"מחקר '{topic}' נשמר!")


def view_past_research() -> None:
    sessions = db.list_all(CATEGORY)
    if not sessions:
        UI.info("אין מחקרים שמורים.")
        return

    rows = [
        [str(s["_id"]), s.get("topic", "—"), str(s.get("turns", 0)), s.get("saved_at", "—")]
        for s in sessions
    ]
    UI.table("📚 מחקרים שמורים", ["#", "נושא", "סבבים", "תאריך"], rows)

    session_id = UI.input("הזן # להמשך מחקר (Enter לדלג)", default="")
    if session_id.isdigit():
        session = db.load(CATEGORY, int(session_id))
        if session:
            _continue_research(session)


def _continue_research(session: dict) -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    topic = session.get("topic", "")
    history = session.get("history", [])
    UI.info(f"ממשיך מחקר: {topic} ({len(history)//2} סבבים קודמים)")

    client = ClaudeClient()
    while True:
        follow_up = UI.input("שאלה נוספת (או 'יציאה')")
        if follow_up.lower() in ("יציאה", "exit", "q"):
            break
        if not follow_up:
            continue
        try:
            response = UI.stream_print(client.stream_chat(SYSTEM, follow_up, history))
            history.append({"role": "user", "content": follow_up})
            history.append({"role": "assistant", "content": response})
            # Update saved session
            clean = {k: v for k, v in session.items() if not k.startswith("_")}
            clean["history"] = history
            clean["turns"] = len([h for h in history if h["role"] == "assistant"])
            db.update(CATEGORY, session["_id"], clean)
        except Exception as e:
            UI.error(f"שגיאה: {e}")


def main() -> None:
    UI.header("🔍 Research Agent", "מחקר מעמיק על כל נושא")

    while True:
        choice = UI.menu("תפריט מחקר", [
            "🔍 מחקר חדש",
            "📚 הצג מחקרים שמורים",
            "🚪 יציאה",
        ])
        if choice == 0:
            new_research()
        elif choice == 1:
            view_past_research()
        elif choice == 2:
            UI.success("להתראות! 🔍")
            break


if __name__ == "__main__":
    main()
