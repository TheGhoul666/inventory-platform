"""🏦 Financial Advisor — יועץ פיננסי אישי ישראלי."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()
CATEGORY = "finance_advice"

SYSTEM = """אתה יועץ פיננסי אישי מומחה לשוק הישראלי.
אתה בקיא ב:
- מס הכנסה ישראלי, מדרגות מס, נקודות זיכוי
- קרנות פנסיה, קופות גמל, קרנות השתלמות
- ביטוח לאומי ודמי בריאות
- שוק ההון בישראל (ת"א, מדד S&P 500, אג"ח)
- משכנתאות ומימון דיור בישראל
- ביטוחי חיים, בריאות, נכות
- חסכונות, תוכניות חיסכון, פיקדונות

ענה תמיד בעברית. היה ספציפי ומעשי.
אל תתן ייעוץ משפטי מוחלט — המלץ להתייעץ עם יועץ מוסמך לנושאים מורכבים."""

QUICK_TOPICS = [
    ("🆘 קרן חירום", "מה זה קרן חירום ואיך אני בונה אחת? כמה כסף צריך לשים בצד?"),
    ("👴 פנסיה בסיסית", "הסבר לי את יסודות הפנסיה בישראל — קרן פנסיה, קופת גמל, ביטוח מנהלים. מה ההבדלים ומה מומלץ?"),
    ("🏠 קניית דירה ראשונה", "אני מתכנן לקנות דירה ראשונה. מאיפה מתחילים? מה הון עצמי צריך? מה עם מע\"מ ומס רכישה?"),
    ("📈 השקעות למתחילים", "אני רוצה להתחיל להשקיע. מה האפשרויות הבסיסיות בישראל? מה ה-ETF? מה קרן מחקה?"),
    ("💰 חיסכון יעיל", "איך חוסכים כסף בצורה יעילה בישראל? מה כדאי לפתוח — חשבון חיסכון, קרן השתלמות, תיק השקעות?"),
]


def quick_topic_chat() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    options = [t[0] for t in QUICK_TOPICS] + ["🔙 חזור"]
    choice = UI.menu("נושאים מהירים", options)
    if choice >= len(QUICK_TOPICS):
        return

    topic_name, question = QUICK_TOPICS[choice]
    UI.rule(f"💬 {topic_name}")

    client = ClaudeClient()
    history = []
    try:
        response = UI.stream_print(client.stream_chat(SYSTEM, question))
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": response})
        _continue_conversation(client, history, topic_name)
    except Exception as e:
        UI.error(f"שגיאה: {e}")


def free_chat() -> None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return

    UI.rule("💬 שאל את היועץ הפיננסי")
    question = UI.input("שאלתך")
    if not question:
        return

    client = ClaudeClient()
    history = []
    try:
        response = UI.stream_print(client.stream_chat(SYSTEM, question))
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": response})
        _continue_conversation(client, history, "שיחה כללית")
    except Exception as e:
        UI.error(f"שגיאה: {e}")


def _continue_conversation(client: ClaudeClient, history: list, topic: str) -> None:
    UI.info("ממשיך שיחה... (הקלד 'שמור' לשמירה, 'יציאה' לסיום)")
    while True:
        follow_up = UI.input("שאלה נוספת")
        if follow_up.lower() in ("יציאה", "exit", "q"):
            break
        if follow_up.lower() in ("שמור", "save"):
            db.save(CATEGORY, {
                "topic": topic,
                "history": history,
                "turns": len([h for h in history if h["role"] == "assistant"]),
                "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            })
            UI.success("השיחה נשמרה!")
            break
        if not follow_up:
            continue
        try:
            response = UI.stream_print(client.stream_chat(SYSTEM, follow_up, history))
            history.append({"role": "user", "content": follow_up})
            history.append({"role": "assistant", "content": response})
        except Exception as e:
            UI.error(f"שגיאה: {e}")
            break


def view_past_sessions() -> None:
    sessions = db.list_all(CATEGORY)
    if not sessions:
        UI.info("אין שיחות שמורות.")
        return

    rows = [[str(s["_id"]), s.get("topic", "—"), str(s.get("turns", 0)), s.get("saved_at", "—")]
            for s in sessions[:15]]
    UI.table("📚 שיחות שמורות", ["#", "נושא", "סבבים", "תאריך"], rows)


def main() -> None:
    UI.header("🏦 Financial Advisor", "יועץ פיננסי אישי — שוק ישראלי")

    while True:
        choice = UI.menu("תפריט", [
            "⚡ נושאים מהירים (פנסיה, דירה, השקעות...)",
            "💬 שאלה חופשית",
            "📚 שיחות שמורות",
            "🚪 יציאה",
        ])
        if choice == 0:
            quick_topic_chat()
        elif choice == 1:
            free_chat()
        elif choice == 2:
            view_past_sessions()
        elif choice == 3:
            UI.success("להתראות! 🏦")
            break


if __name__ == "__main__":
    main()
