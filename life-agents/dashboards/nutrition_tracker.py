"""🥦 Nutrition Tracker — מעקב תזונה (Streamlit)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime, timedelta
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

st.set_page_config(page_title="Nutrition Tracker", page_icon="🥦", layout="wide")
db = Storage()


def get_goals() -> dict:
    return db.get_setting("nutrition_goals") or {
        "calories": 2000, "protein": 120, "carbs": 250, "fat": 65
    }


def main():
    st.title("🥦 Nutrition Tracker")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ יעדים יומיים")
        goals = get_goals()
        with st.form("goals_form"):
            cal_goal = st.number_input("קלוריות", value=goals.get("calories", 2000))
            protein_goal = st.number_input("חלבון (g)", value=goals.get("protein", 120))
            carbs_goal = st.number_input("פחמימות (g)", value=goals.get("carbs", 250))
            fat_goal = st.number_input("שומן (g)", value=goals.get("fat", 65))
            if st.form_submit_button("💾 שמור יעדים"):
                db.set_setting("nutrition_goals", {
                    "calories": cal_goal, "protein": protein_goal,
                    "carbs": carbs_goal, "fat": fat_goal
                })
                st.success("יעדים עודכנו!")
                st.rerun()

    goals = get_goals()
    today = datetime.now().strftime("%d/%m/%Y")

    tab1, tab2, tab3 = st.tabs(["📝 רשום ארוחה", "📊 היום", "📈 שבוע"])

    with tab1:
        st.subheader("➕ רשום ארוחה")
        meal_type = st.selectbox("סוג ארוחה", ["🌅 בוקר", "☀️ צהריים", "🌙 ערב", "🍎 חטיף"])

        col1, col2 = st.columns([3, 1])
        with col1:
            food_desc = st.text_area("מה אכלת?", height=80, placeholder="לדוגמה: 2 ביצים קשות, פרוסת לחם, כוס קפה עם חלב")
        with col2:
            use_ai = st.checkbox("🤖 AI יעריך", value=config.has_api_key())

        if use_ai and config.has_api_key():
            if st.button("📊 הערך ערכים תזונתיים") and food_desc:
                with st.spinner("מעריך..."):
                    try:
                        client = ClaudeClient()
                        import json
                        result = client.quick(
                            f"הערך ערכים תזונתיים של: '{food_desc}'\n"
                            "ענה בפורמט JSON בלבד:\n"
                            '{"calories": 400, "protein": 25, "carbs": 30, "fat": 15}'
                        )
                        parsed = json.loads(result.strip().strip("```json").strip("```").strip())
                        st.session_state["estimated"] = parsed
                        st.success(f"קלוריות: {parsed.get('calories')} | חלבון: {parsed.get('protein')}g | פחמימות: {parsed.get('carbs')}g | שומן: {parsed.get('fat')}g")
                    except Exception as e:
                        st.error(f"שגיאה: {e}")

        estimated = st.session_state.get("estimated", {})
        col1, col2, col3, col4 = st.columns(4)
        calories = col1.number_input("קלוריות", value=int(estimated.get("calories", 0)), min_value=0)
        protein = col2.number_input("חלבון g", value=int(estimated.get("protein", 0)), min_value=0)
        carbs = col3.number_input("פחמימות g", value=int(estimated.get("carbs", 0)), min_value=0)
        fat = col4.number_input("שומן g", value=int(estimated.get("fat", 0)), min_value=0)

        if st.button("💾 שמור ארוחה") and food_desc:
            db.save("nutrition_logs", {
                "date": today,
                "time": datetime.now().strftime("%H:%M"),
                "meal_type": meal_type,
                "description": food_desc,
                "calories": calories, "protein": protein, "carbs": carbs, "fat": fat,
            })
            st.success("ארוחה נרשמה! 🎉")
            if "estimated" in st.session_state:
                del st.session_state["estimated"]
            st.rerun()

    with tab2:
        today_logs = [l for l in db.list_all("nutrition_logs") if l.get("date") == today]

        if not today_logs:
            st.info("טרם נרשמו ארוחות היום.")
        else:
            total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
            for l in today_logs:
                for k in total:
                    total[k] += l.get(k, 0)

            st.subheader("📊 סיכום יומי")
            c1, c2, c3, c4 = st.columns(4)
            for col, key, label, unit in [
                (c1, "calories", "🔥 קלוריות", "קל'"),
                (c2, "protein", "🥩 חלבון", "g"),
                (c3, "carbs", "🍞 פחמימות", "g"),
                (c4, "fat", "🧈 שומן", "g"),
            ]:
                val = total[key]
                goal = goals.get(key, 1)
                pct = val / goal * 100 if goal > 0 else 0
                col.metric(label, f"{val}{unit}", delta=f"{pct:.0f}% מיעד")
                col.progress(min(pct / 100, 1.0))

            st.subheader("📋 יומן ארוחות")
            for l in today_logs:
                st.write(f"{l.get('meal_type','')} | {l.get('time','—')} | {l.get('description','')[:60]} | 🔥{l.get('calories',0)} קל'")

    with tab3:
        import pandas as pd
        cal_by_day = {}
        for i in range(6, -1, -1):
            day = (datetime.now() - timedelta(days=i)).strftime("%d/%m/%Y")
            day_logs = [l for l in db.list_all("nutrition_logs") if l.get("date") == day]
            cal_by_day[day[-5:]] = sum(l.get("calories", 0) for l in day_logs)

        if any(v > 0 for v in cal_by_day.values()):
            st.subheader("📈 קלוריות השבוע")
            st.bar_chart(pd.Series(cal_by_day))

            # AI Nutritionist
            if config.has_api_key() and st.button("🤖 קבל המלצות תזונה"):
                with st.spinner("מנתח..."):
                    try:
                        client = ClaudeClient()
                        week_summary = "\n".join(f"- {day}: {cal} קל'" for day, cal in cal_by_day.items())
                        resp = client.chat(
                            "אתה תזונאי קליני ישראלי מנוסה. ענה בעברית.",
                            f"נתוני תזונה שבועיים:\n{week_summary}\n\nיעדים: {goals}\n\nמה חסר לי ומה לשפר?"
                        )
                        st.info(resp)
                    except Exception as e:
                        st.error(f"שגיאה: {e}")
        else:
            st.info("אין מספיק נתונים לתצוגה שבועית.")


if __name__ == "__main__":
    main()
