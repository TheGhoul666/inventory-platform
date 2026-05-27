"""🍳 Recipe Finder — מציאת מתכונים לפי מרכיבים."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

db = Storage()
CATEGORY = "recipes"

SYSTEM = """אתה שף מקצועי ומומחה מתכונים.
כשמשתמש נותן לך מרכיבים, הצע מתכונים טעימים ומעשיים.
ענה בעברית. כלול: שם המתכון, זמן הכנה, רמת קושי, מצרכים מלאים, הוראות שלב-אחר-שלב."""


def find_recipes() -> str | None:
    if not config.has_api_key():
        UI.print_api_key_error()
        return None

    UI.rule("🥬 מה יש לך במטבח?")
    ingredients = UI.input("מרכיבים זמינים (מופרדים בפסיקים)")
    if not ingredients:
        return None

    restrictions = UI.input("הגבלות תזונתיות (צמחוני/טבעוני/ללא גלוטן וכו', Enter לדלג)", default="ללא")
    cuisine_idx = UI.menu("סגנון בישול מועדף", [
        "🌍 כל סגנון", "🇮🇱 ישראלי/מזרח תיכוני", "🇮🇹 איטלקי",
        "🇦🇸 אסייתי", "🇺🇸 אמריקאי", "🇲🇦 מרוקאי"
    ])
    cuisines = ["כל סגנון", "ישראלי/מזרח תיכוני", "איטלקי", "אסייתי", "אמריקאי", "מרוקאי"]
    cuisine = cuisines[cuisine_idx]

    servings = UI.input("כמה סועדים?", default="2")
    time_idx = UI.menu("זמן הכנה מקסימלי", ["⚡ עד 20 דקות", "🕐 עד 45 דקות", "🍲 שעה+"])
    max_time = ["20 דקות", "45 דקות", "שעה ומעלה"][time_idx]

    prompt = (
        f"מרכיבים זמינים: {ingredients}\n"
        f"הגבלות תזונתיות: {restrictions}\n"
        f"סגנון: {cuisine}\n"
        f"מספר סועדים: {servings}\n"
        f"זמן מקסימלי: {max_time}\n\n"
        "הצע 3 מתכונים שונים. לכל מתכון כלול:\n"
        "- שם המתכון + emoji\n"
        "- זמן הכנה וקושי (קל/בינוני/מאתגר)\n"
        "- מצרכים מלאים (כולל כמויות)\n"
        "- הוראות הכנה שלב-אחר-שלב\n"
        "- טיפ מהשף"
    )

    UI.rule("👨‍🍳 מתכונים מומלצים")
    try:
        client = ClaudeClient()
        return UI.stream_print(client.stream_chat(SYSTEM, prompt))
    except Exception as e:
        UI.error(f"שגיאה: {e}")
        return None


def save_recipe(recipe_text: str) -> None:
    name = UI.input("שם המתכון לשמירה")
    db.save(CATEGORY, {
        "name": name or "מתכון ללא שם",
        "content": recipe_text,
        "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "favorite": False,
    })
    UI.success(f"מתכון '{name}' נשמר!")


def view_saved_recipes() -> None:
    recipes = db.list_all(CATEGORY)
    if not recipes:
        UI.info("אין מתכונים שמורים עדיין.")
        return

    rows = [
        [str(r["_id"]), r.get("name", "—"), "⭐" if r.get("favorite") else "", r.get("saved_at", "—")]
        for r in recipes
    ]
    UI.table("📖 מתכונים שמורים", ["#", "שם", "מועדף", "תאריך"], rows)

    recipe_id = UI.input("הזן # להצגה (Enter לדלג)", default="")
    if recipe_id.isdigit():
        recipe = db.load(CATEGORY, int(recipe_id))
        if recipe:
            UI.rule(f"🍳 {recipe.get('name', '')}")
            from shared.ui import console
            console.print(recipe.get("content", ""))

            if UI.confirm("סמן כמועדף?"):
                clean = {k: v for k, v in recipe.items() if not k.startswith("_")}
                clean["favorite"] = True
                db.update(CATEGORY, recipe["_id"], clean)
                UI.success("סומן כמועדף! ⭐")


def main() -> None:
    UI.header("🍳 Recipe Finder", "מציאת מתכונים מרכיבים שיש לך")

    current_result: str | None = None

    while True:
        base_options = ["🔍 מצא מתכונים לפי מרכיבים", "📖 מתכונים שמורים", "🚪 יציאה"]
        if current_result:
            base_options.insert(1, "💾 שמור את המתכון הנוכחי")

        choice = UI.menu("תפריט", base_options)

        if not current_result:
            if choice == 0:
                current_result = find_recipes()
            elif choice == 1:
                view_saved_recipes()
            else:
                break
        else:
            if choice == 0:
                current_result = find_recipes()
            elif choice == 1:
                save_recipe(current_result)
                current_result = None
            elif choice == 2:
                view_saved_recipes()
            else:
                break

    UI.success("להתראות! 🍳")


if __name__ == "__main__":
    main()
