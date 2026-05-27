"""🏥 Medical Tracker — ניהול תורים, תרופות ובריאות."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from shared.ui import UI
from shared.storage import Storage

db = Storage()


def add_appointment() -> None:
    UI.rule("📅 הוספת תור")
    doctor = UI.input("שם הרופא / מומחה")
    specialty = UI.input("התמחות (רופא משפחה/קרדיולוג/עור/...)", default="רופא משפחה")
    date_str = UI.input("תאריך הפגישה (DD/MM/YYYY)")
    time_str = UI.input("שעה (HH:MM)", default="")
    reason = UI.input("סיבת הביקור")
    hmo_idx = UI.menu("קופת חולים", ["🔵 כללית", "🟠 מכבי", "🟡 מאוחדת", "🟢 לאומית", "🔴 פרטי"])
    hmo = ["כללית", "מכבי", "מאוחדת", "לאומית", "פרטי"][hmo_idx]
    notes = UI.input("הערות (אופציונלי)", default="")
    follow_up = UI.confirm("נדרש מעקב?")
    next_appt = UI.input("תאריך תור הבא (אם ידוע)", default="") if follow_up else ""

    db.save("appointments", {
        "doctor": doctor,
        "specialty": specialty,
        "date": date_str,
        "time": time_str,
        "reason": reason,
        "hmo": hmo,
        "notes": notes,
        "follow_up_needed": follow_up,
        "next_appointment": next_appt,
        "status": "upcoming",
    })
    UI.success(f"תור אצל {doctor} ב-{date_str} נוסף!")


def view_appointments() -> None:
    appointments = db.list_all("appointments")
    if not appointments:
        UI.info("אין תורים רשומים.")
        return

    rows = [
        [a.get("date", "—"), a.get("time", "—"), a.get("doctor", "—"),
         a.get("specialty", "—"), a.get("reason", "—")[:30], a.get("hmo", "—")]
        for a in appointments[:20]
    ]
    UI.table("🏥 תורים רפואיים", ["תאריך", "שעה", "רופא", "התמחות", "סיבה", "קופ\"ח"], rows)


def add_medication() -> None:
    UI.rule("💊 הוספת תרופה")
    name = UI.input("שם התרופה")
    dosage = UI.input("מינון (למשל: 10מג)", default="")
    freq_idx = UI.menu("תדירות", ["בוקר", "ערב", "בוקר+ערב", "3x ביום", "לפי הצורך"])
    frequency = ["בוקר", "ערב", "בוקר וערב", "3 פעמים ביום", "לפי הצורך"][freq_idx]
    start_date = UI.input("תאריך התחלה", default=datetime.now().strftime("%d/%m/%Y"))
    end_date = UI.input("תאריך סיום (Enter לקבוע)", default="")
    doctor = UI.input("רשם: (שם רופא)", default="")
    instructions = UI.input("הוראות מיוחדות", default="")

    db.save("medications", {
        "name": name,
        "dosage": dosage,
        "frequency": frequency,
        "start_date": start_date,
        "end_date": end_date,
        "prescribed_by": doctor,
        "instructions": instructions,
        "active": True,
    })
    UI.success(f"תרופה '{name}' נוספה!")


def view_medications() -> None:
    meds = [m for m in db.list_all("medications") if m.get("active")]
    if not meds:
        UI.info("אין תרופות פעילות.")
        return

    rows = [
        [m.get("name", "—"), m.get("dosage", "—"), m.get("frequency", "—"),
         m.get("start_date", "—"), m.get("end_date", "ללא הגבלה")]
        for m in meds
    ]
    UI.table("💊 תרופות פעילות", ["שם", "מינון", "תדירות", "מתאריך", "עד תאריך"], rows)


def log_health_note() -> None:
    UI.rule("📋 רישום בריאותי")
    note_type_idx = UI.menu("סוג", ["📊 ויטלים", "😷 תסמינים", "📝 הערה כללית"])
    note_type = ["vitals", "symptoms", "general"][note_type_idx]

    data = {"date": datetime.now().strftime("%d/%m/%Y %H:%M"), "type": note_type}

    if note_type == "vitals":
        bp = UI.input("לחץ דם (סיסטולי/דיאסטולי, למשל 120/80)", default="")
        weight = UI.input("משקל (ק\"ג)", default="")
        pulse = UI.input("דופק (בדק')", default="")
        data.update({"blood_pressure": bp, "weight": weight, "pulse": pulse})
    elif note_type == "symptoms":
        symptoms = UI.input("תסמינים (תאר)")
        severity = UI.input("חומרה (1-10)", default="5")
        data.update({"symptoms": symptoms, "severity": severity})
    else:
        note = UI.input("הערה")
        data["note"] = note

    db.save("health_notes", data)
    UI.success("רישום בריאותי נשמר!")


def main() -> None:
    UI.header("🏥 Medical Tracker", "ניהול בריאות — תורים, תרופות, ויטלים")

    while True:
        choice = UI.menu("תפריט", [
            "📅 הוסף תור רפואי",
            "📋 הצג תורים",
            "💊 הוסף תרופה",
            "💊 הצג תרופות פעילות",
            "📊 רשום ויטלים/תסמינים",
            "🚪 יציאה",
        ])
        if choice == 0:
            add_appointment()
        elif choice == 1:
            view_appointments()
        elif choice == 2:
            add_medication()
        elif choice == 3:
            view_medications()
        elif choice == 4:
            log_health_note()
        elif choice == 5:
            break

    UI.success("שמור על בריאותך! 🏥")


if __name__ == "__main__":
    main()
