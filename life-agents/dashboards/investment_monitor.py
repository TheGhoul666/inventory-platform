"""📈 Investment Monitor — מעקב תיק השקעות (Streamlit)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from shared.storage import Storage
from shared.claude_client import ClaudeClient
from shared.config import config

st.set_page_config(page_title="Investment Monitor", page_icon="📈", layout="wide")
db = Storage()

INVESTMENT_TYPES = ["📈 מניות", "📊 ETF / קרן מחקה", "🏠 נדל\"ן", "₿ קריפטו",
                     "📋 אג\"ח", "👴 פנסיה / גמל", "🏦 חיסכון / פיקדון", "🔵 אחר"]


def main():
    st.title("📈 Investment Monitor")
    st.caption("מעקב תיק השקעות אישי")

    with st.sidebar:
        st.header("➕ הוסף השקעה")
        with st.form("add_investment"):
            name = st.text_input("שם ההשקעה")
            inv_type = st.selectbox("סוג", INVESTMENT_TYPES)
            purchase_price = st.number_input("ערך רכישה ₪", min_value=0.0, format="%.2f")
            current_value = st.number_input("ערך נוכחי ₪", min_value=0.0, format="%.2f")
            purchase_date = st.date_input("תאריך רכישה")
            notes = st.text_input("הערות")

            if st.form_submit_button("➕ הוסף") and name:
                db.save("investments", {
                    "name": name,
                    "type": inv_type,
                    "purchase_price": purchase_price,
                    "current_value": current_value,
                    "purchase_date": str(purchase_date),
                    "notes": notes,
                    "added_at": datetime.now().strftime("%d/%m/%Y"),
                })
                st.success(f"'{name}' נוסף!")
                st.rerun()

    investments = db.list_all("investments")

    if not investments:
        st.info("🏦 הוסף השקעות בסרגל הצד כדי להתחיל לעקוב אחר תיק ההשקעות שלך.")
        return

    # Portfolio summary
    total_purchase = sum(i.get("purchase_price", 0) for i in investments)
    total_current = sum(i.get("current_value", 0) for i in investments)
    total_gain = total_current - total_purchase
    total_gain_pct = (total_gain / total_purchase * 100) if total_purchase > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 ערך כולל", f"₪{total_current:,.0f}")
    col2.metric("📊 השקעה מקורית", f"₪{total_purchase:,.0f}")
    col3.metric("📈 רווח/הפסד", f"₪{total_gain:,.0f}", delta=f"{total_gain_pct:.1f}%")
    col4.metric("📦 מספר השקעות", len(investments))

    st.divider()

    # Category breakdown
    st.subheader("📊 פיזור לפי קטגוריה")
    type_totals = {}
    for inv in investments:
        t = inv.get("type", "אחר")
        type_totals[t] = type_totals.get(t, 0) + inv.get("current_value", 0)

    if type_totals and total_current > 0:
        chart_data = {k: v / total_current * 100 for k, v in type_totals.items()}
        col1, col2 = st.columns(2)
        with col1:
            for cat, pct in sorted(chart_data.items(), key=lambda x: -x[1]):
                st.write(f"{cat}: **{pct:.1f}%** (₪{type_totals[cat]:,.0f})")
        with col2:
            import pandas as pd
            st.bar_chart(pd.DataFrame.from_dict({"ערך": type_totals}, orient="index"))

    st.divider()

    # Holdings table
    st.subheader("📋 אחזקות")
    for inv in investments:
        purchase = inv.get("purchase_price", 0)
        current = inv.get("current_value", 0)
        gain = current - purchase
        gain_pct = (gain / purchase * 100) if purchase > 0 else 0
        gain_color = "🟢" if gain >= 0 else "🔴"

        with st.expander(f"{inv.get('type', '')} **{inv.get('name', '')}** — ₪{current:,.0f} {gain_color}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("ערך נוכחי", f"₪{current:,.0f}")
            c2.metric("ערך רכישה", f"₪{purchase:,.0f}")
            c3.metric("רווח/הפסד", f"₪{gain:,.0f}", delta=f"{gain_pct:.1f}%")
            st.caption(f"תאריך רכישה: {inv.get('purchase_date', '—')} | הערות: {inv.get('notes', '—')}")

            # Update value
            new_val = st.number_input(f"עדכן ערך נוכחי ₪", value=float(current), key=f"update_{inv['_id']}")
            if st.button("💾 עדכן", key=f"btn_{inv['_id']}"):
                clean = {k: v for k, v in inv.items() if not k.startswith("_")}
                clean["current_value"] = new_val
                db.update("investments", inv["_id"], clean)
                st.success("עודכן!")
                st.rerun()

    # AI Analysis
    st.divider()
    if config.has_api_key():
        if st.button("🤖 ניתוח AI של התיק"):
            with st.spinner("מנתח..."):
                try:
                    alloc = "\n".join(f"- {k}: {v:.0f}% (₪{type_totals[k]:,.0f})"
                                      for k, v in sorted(chart_data.items(), key=lambda x: -x[1]))
                    client = ClaudeClient()
                    response = client.chat(
                        "אתה יועץ השקעות ישראלי מנוסה. ענה בעברית.",
                        f"תיק ההשקעות שלי:\n{alloc}\n\n"
                        f"ערך כולל: ₪{total_current:,.0f}\n"
                        f"רווח/הפסד: {total_gain_pct:.1f}%\n\n"
                        "תן הערכה של הפיזור, סיכונים, והמלצות לשיפור."
                    )
                    st.info(response)
                except Exception as e:
                    st.error(f"שגיאה: {e}")


if __name__ == "__main__":
    main()
