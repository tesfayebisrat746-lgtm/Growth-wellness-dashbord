import datetime as dt
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
st.set_page_config(
    page_title="Growth & Wellness Dashboard",
    page_icon="📈",
    layout="wide",
)

DB_PATH = Path("growth_wellness.db")
ACTIVITIES = [
    "Walking",
    "Running",
    "Cycling",
    "Swimming",
    "Basketball / volleyball",
    "Strength training",
    "Mobility / stretching",
    "Other recreational activity",
]

st.title("📈 Growth & Wellness Dashboard")
st.caption(
    "Track health habits and measured growth. This app supports healthy routines; "
    "it does not predict or guarantee adult height."
)

# ------------------------------------------------------------
# Database: entries persist between app sessions
# ------------------------------------------------------------
def connect_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_logs (
            log_date TEXT PRIMARY KEY,
            height_cm REAL,
            sleep_hours REAL NOT NULL,
            protein_note TEXT NOT NULL,
            meals_note TEXT NOT NULL,
            activity_minutes INTEGER NOT NULL,
            activities TEXT NOT NULL,
            outdoor_minutes INTEGER NOT NULL,
            hydration_note TEXT NOT NULL,
            wellbeing_note TEXT NOT NULL,
            notes TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


conn = connect_db()


def load_logs():
    df = pd.read_sql_query("SELECT * FROM daily_logs ORDER BY log_date", conn)
    if not df.empty:
        df["log_date"] = pd.to_datetime(df["log_date"]).dt.date
    return df


def save_log(row):
    conn.execute(
        """
        INSERT INTO daily_logs (
            log_date, height_cm, sleep_hours, protein_note, meals_note,
            activity_minutes, activities, outdoor_minutes, hydration_note,
            wellbeing_note, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(log_date) DO UPDATE SET
            height_cm=excluded.height_cm,
            sleep_hours=excluded.sleep_hours,
            protein_note=excluded.protein_note,
            meals_note=excluded.meals_note,
            activity_minutes=excluded.activity_minutes,
            activities=excluded.activities,
            outdoor_minutes=excluded.outdoor_minutes,
            hydration_note=excluded.hydration_note,
            wellbeing_note=excluded.wellbeing_note,
            notes=excluded.notes
        """,
        row,
    )
    conn.commit()


logs = load_logs()

# ------------------------------------------------------------
# Sidebar: optional baseline
# ------------------------------------------------------------
st.sidebar.header("📏 Baseline")
st.sidebar.caption("Enter measurements only if you know them. Height changes slowly.")
current_height = st.sidebar.number_input(
    "Most recent measured height (cm)",
    min_value=50.0,
    max_value=250.0,
    value=175.0,
    step=0.1,
    help="Use a real measurement, not a target or estimate.",
)
target_height = st.sidebar.number_input(
    "Personal height goal (cm, optional)",
    min_value=50.0,
    max_value=250.0,
    value=180.0,
    step=0.5,
    help="A goal is not a medical prediction or a guaranteed outcome.",
)
age = st.sidebar.number_input(
    "Age (years)",
    min_value=1,
    max_value=100,
    value=16,
    help="Growth potential depends substantially on age and pubertal development.",
)
st.sidebar.info(
    "A clinician can assess your growth pattern using age, growth charts, "
    "pubertal development, family history, and sometimes bone age."
)

# ------------------------------------------------------------
# Daily entry form
# ------------------------------------------------------------
st.header("🗓️ Daily log")
today = dt.date.today()

existing = None
if not logs.empty:
    match = logs[logs["log_date"] == today]
    if not match.empty:
        existing = match.iloc[0]

def old_value(field, default):
    if existing is None or pd.isna(existing[field]):
        return default
    return existing[field]

with st.form("daily_log", clear_on_submit=False):
    log_date = st.date_input("Date", value=today)

    col1, col2 = st.columns(2)
    with col1:
        measured_height = st.number_input(
            "Measured height today (cm; optional)",
            min_value=50.0,
            max_value=250.0,
            value=float(old_value("height_cm", current_height) or current_height),
            step=0.1,
            help="Measure barefoot on a flat floor against a wall. Daily changes are usually measurement variation, not actual growth.",
        )
        record_height = st.checkbox(
            "Save this height measurement",
            value=not pd.isna(old_value("height_cm", None))
            if existing is not None
            else False,
        )
        sleep_hours = st.number_input(
            "Total sleep (hours)",
            min_value=0.0,
            max_value=24.0,
            value=float(old_value("sleep_hours", 8.0)),
            step=0.25,
        )
        activity_minutes = st.number_input(
            "Total activity (minutes)",
            min_value=0,
            max_value=1440,
            value=int(old_value("activity_minutes", 30)),
            step=5,
        )
        outdoor_minutes = st.number_input(
            "Time outdoors (minutes; optional)",
            min_value=0,
            max_value=1440,
            value=int(old_value("outdoor_minutes", 20)),
            step=5,
        )

    with col2:
        protein_note = st.selectbox(
            "Protein-containing foods",
            ["Not recorded", "Limited today", "Some with meals", "Included regularly"],
            index=[
                "Not recorded", "Limited today", "Some with meals", "Included regularly"
            ].index(str(old_value("protein_note", "Some with meals"))),
            help="This is a simple habit note, not a protein requirement or diagnosis.",
        )
        meals_note = st.selectbox(
            "Overall food intake",
            [
                "Not recorded",
                "Ate regularly and varied foods",
                "Missed meals",
                "Limited variety / appetite issue",
            ],
            index=[
                "Not recorded",
                "Ate regularly and varied foods",
                "Missed meals",
                "Limited variety / appetite issue",
            ].index(str(old_value("meals_note", "Ate regularly and varied foods"))),
        )
        activities = st.multiselect(
            "Activities",
            ACTIVITIES,
            default=[
                item
                for item in str(old_value("activities", "")).split(", ")
                if item in ACTIVITIES
            ],
        )
        hydration_note = st.selectbox(
            "Hydration",
            ["Not recorded", "Drank regularly; thirst was managed", "May not have drunk enough"],
            index=[
                "Not recorded",
                "Drank regularly; thirst was managed",
                "May not have drunk enough",
            ].index(str(old_value("hydration_note", "Drank regularly; thirst was managed"))),
        )
        wellbeing_note = st.selectbox(
            "General wellbeing",
            ["Good", "Okay", "Unwell / unusually tired"],
            index=["Good", "Okay", "Unwell / unusually tired"].index(
                str(old_value("wellbeing_note", "Okay"))
            ),
        )

    notes = st.text_area(
        "Notes (optional)",
        value=str(old_value("notes", "")),
        placeholder="For example: illness, change in routine, or measurement conditions.",
    )
    submitted = st.form_submit_button("💾 Save daily log", type="primary")

    if submitted:
        height_value = float(measured_height) if record_height else None
        save_log(
            (
                log_date.isoformat(),
                height_value,
                float(sleep_hours),
                protein_note,
                meals_note,
                int(activity_minutes),
                ", ".join(activities),
                int(outdoor_minutes),
                hydration_note,
                wellbeing_note,
                notes.strip(),
            )
        )
        st.success(f"Saved entry for {log_date.isoformat()}.")
        st.rerun()

# Refresh after possible save
logs = load_logs()

# ------------------------------------------------------------
# Overview and charts
# ------------------------------------------------------------
st.header("📊 Your tracking history")

if logs.empty:
    st.info("No logs yet. Save your first daily entry to begin tracking.")
else:
    total_days = len(logs)
    avg_sleep = logs["sleep_hours"].mean()
    avg_activity = logs["activity_minutes"].mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("Logged days", f"{total_days}")
    c2.metric("Average sleep", f"{avg_sleep:.1f} h/night")
    c3.metric("Average activity", f"{avg_activity:.0f} min/day")

    tab1, tab2, tab3 = st.tabs(
        ["Sleep & activity", "Measured height", "Daily records"]
    )

    with tab1:
        chart_df = logs.copy()
        chart_df["log_date"] = pd.to_datetime(chart_df["log_date"])
        sleep_fig = px.line(
            chart_df,
            x="log_date",
            y="sleep_hours",
            markers=True,
            title="Sleep duration over time",
            labels={"log_date": "Date", "sleep_hours": "Hours of sleep"},
        )
        sleep_fig.update_layout(yaxis_rangemode="tozero")
        st.plotly_chart(sleep_fig, use_container_width=True)

        activity_fig = px.bar(
            chart_df,
            x="log_date",
            y="activity_minutes",
            title="Daily physical activity",
            labels={"log_date": "Date", "activity_minutes": "Minutes"},
        )
        activity_fig.update_layout(yaxis_rangemode="tozero")
        st.plotly_chart(activity_fig, use_container_width=True)
        st.caption(
            "Charts describe recorded habits. They do not show that a habit caused height growth."
        )

    with tab2:
        height_df = logs.dropna(subset=["height_cm"]).copy()
        if height_df.empty:
            st.info("No height measurements saved yet. Add one occasionally using consistent technique.")
        else:
            height_df["log_date"] = pd.to_datetime(height_df["log_date"])
            height_fig = px.line(
                height_df,
                x="log_date",
                y="height_cm",
                markers=True,
                title="Recorded height measurements",
                labels={"log_date": "Date", "height_cm": "Height (cm)"},
            )
            st.plotly_chart(height_fig, use_container_width=True)
            st.caption(
                "Measure at similar times and under similar conditions. Height can vary during the day. "
                "Look at trends over months, not day-to-day changes."
            )

    with tab3:
        display_df = logs.sort_values("log_date", ascending=False).copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        csv_data = logs.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download logs as CSV",
            data=csv_data,
            file_name="growth_wellness_logs.csv",
            mime="text/csv",
        )

# ------------------------------------------------------------
# Evidence-informed routine
# ------------------------------------------------------------
st.header("🧭 Healthy routine to support normal growth")

st.subheader("Daily habits")
routine = [
    ("Sleep consistently", "If aged 13–17, aim for 8–10 hours nightly; adults generally need 7–9 hours. Keep a regular sleep and wake time."),
    ("Eat enough and vary foods", "Include regular meals with protein sources, grains or other starchy foods, vegetables, fruit, and sources of healthy fats. Avoid crash diets."),
    ("Get calcium and vitamin D through appropriate sources", "Use foods such as dairy or fortified alternatives and other calcium-rich foods. Vitamin D needs vary; ask a clinician before taking supplements, especially high doses."),
    ("Move regularly", "Choose enjoyable activities such as walking, sports, cycling, dancing, or age-appropriate strength training with good technique."),
    ("Recover", "Include rest days when needed and do not train through pain, illness, or persistent exhaustion."),
    ("Stay hydrated", "Drink regularly, especially during heat and exercise; needs vary with activity and weather."),
    ("Avoid smoking, vaping, alcohol, and unprescribed hormones", "These can harm health. Do not use growth hormone or “height pills” unless prescribed for a diagnosed medical indication."),
    ("Measure sensibly", "If monitoring growth, measure barefoot with consistent technique every few months rather than repeatedly every day."),
]
for heading, detail in routine:
    with st.expander(heading):
        st.write(detail)

st.subheader("What will not reliably increase bone length")
st.write(
    "Hanging, stretching, sprinting, jumping, special foods, and supplements have not been shown "
    "to make a person taller than their biological growth potential. Exercise can improve fitness, "
    "bone health, posture, and wellbeing, but it does not lengthen mature bones."
)

st.subheader("When to seek medical advice")
st.write(
    "If you are concerned about being much shorter than expected, growth slowing, puberty starting "
    "very early or late, persistent digestive symptoms, unexplained weight change, or ongoing fatigue, "
    "talk with a healthcare professional. They can review your growth chart and decide whether any "
    "tests are appropriate. Do not use parental-average height as a guarantee."
)

st.caption(
    "Privacy: entries are stored in a local SQLite database file named growth_wellness.db "
    "in the app's working directory. On hosted platforms, local files may not persist across "
    "restarts unless persistent storage is configured. Keep backups of exported CSV files."
)
