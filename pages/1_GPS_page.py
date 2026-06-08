import streamlit as st
import pandas as pd
import base64
import os
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# CONFIG
# =========================================================

saison = st.session_state.get("saison", "2026-2027")

image_path = "images/logo.png"
excel_path = f"data/{saison}/DonneesGPSPropres.xlsx"

# =========================================================
# LOGO
# =========================================================

def get_base64(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img = get_base64(image_path)

if img:
    st.markdown(f"""
    <style>
    .logo {{
        position: fixed;
        top: 10px;
        right: 10px;
        width: 140px;
        z-index: 9999;
    }}
    </style>
    <div class="logo">
        <img src="data:image/png;base64,{img}">
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# LOAD DATA
# =========================================================

if not os.path.exists(excel_path):
    st.error(f"Fichier introuvable : {excel_path}")
    st.stop()

df = pd.read_excel(excel_path)

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])
df["Semaine"] = df["Date"].dt.isocalendar().week

# =========================================================
# METRICS CREATION (IMPORTANT)
# =========================================================

df["# Sprints (>25 km/h)"] = (
    df["Distance par plage de vitesse (25-30 km/h)"]
    + df["Distance par plage de vitesse (>30 km/h)"]
)

df["Sprint Distance"] = (
    df["Distance par plage de vitesse (25-30 km/h)"]
    + df["Distance par plage de vitesse (>30 km/h)"]
)

df["HSR Distance"] = (
    df["Distance par plage de vitesse (20-25 km/h)"]
    + df["Distance par plage de vitesse (25-30 km/h)"]
    + df["Distance par plage de vitesse (>30 km/h)"]
)

# =========================================================
# FUNCTION CORE
# =========================================================

def compute_week(df_input, metric):
    return (
        df_input.groupby("Nom du joueur")[metric]
        .sum()
        .reset_index()
        .rename(columns={metric: "Week"})
    )


def compute_top3(metric):
    df_match = df[df["MD"] == "M"]

    top3 = (
        df_match.groupby("Nom du joueur")[metric]
        .apply(lambda x: x.nlargest(3).mean())
        .reset_index()
        .rename(columns={metric: "Top3"})
    )

    return top3


def build_table(df_input, metric, low, high, name):
    week = compute_week(df_input, metric)
    top3 = compute_top3(metric)

    result = week.merge(top3, on="Nom du joueur", how="left")

    result["Top3"] = result["Top3"].replace(0, pd.NA)
    result["Exposure %"] = (result["Week"] / result["Top3"]) * 100
    result["Exposure %"] = result["Exposure %"].round(1)

    def status(x):
        if pd.isna(x):
            return "⚪ NA"
        if x < low:
            return "🔴 Sous-exposé"
        if x <= high:
            return "🟢 Optimal"
        return "🟠 Très élevé"

    result["Status"] = result["Exposure %"].apply(status)

    result = result.rename(columns={
        "Week": f"{name} Week",
        "Top3": f"Top3 Match {name}"
    })

    return result

# =========================================================
# UI TITLE
# =========================================================

st.title("📊 GPS Dashboard")

# =========================================================
# METRICS KEYS
# =========================================================

SPRINT_COUNT = "# Sprints (>25 km/h)"
SPRINT_DISTANCE = "Sprint Distance"
HSR_DISTANCE = "HSR Distance"

players = sorted(df["Nom du joueur"].dropna().unique())
weeks = sorted(df["Semaine"].dropna().unique())

# =========================================================
# 1️⃣ SPRINT COUNT
# =========================================================

st.divider()
st.subheader("1️⃣ Sprint Count")

col1, col2 = st.columns(2)

with col1:
    f1_players = st.multiselect("Joueurs", players, key="c1")

with col2:
    f1_weeks = st.multiselect("Semaines", weeks, default=[max(weeks)], key="c2")

df1 = df.copy()

if f1_players:
    df1 = df1[df1["Nom du joueur"].isin(f1_players)]

if f1_weeks:
    df1 = df1[df1["Semaine"].isin(f1_weeks)]

t1 = build_table(df1, SPRINT_COUNT, 90, 120, "Sprint Count")
st.dataframe(t1)

fig1 = px.bar(t1, x="Nom du joueur", y="Exposure %", text="Exposure %")
st.plotly_chart(fig1, use_container_width=True)

# =========================================================
# 2️⃣ SPRINT DISTANCE
# =========================================================

st.divider()
st.subheader("2️⃣ Sprint Distance")

col1, col2 = st.columns(2)

with col1:
    f2_players = st.multiselect("Joueurs", players, key="c3")

with col2:
    f2_weeks = st.multiselect("Semaines", weeks, default=[max(weeks)], key="c4")

df2 = df.copy()

if f2_players:
    df2 = df2[df2["Nom du joueur"].isin(f2_players)]

if f2_weeks:
    df2 = df2[df2["Semaine"].isin(f2_weeks)]

t2 = build_table(df2, SPRINT_DISTANCE, 80, 120, "Sprint Distance")
st.dataframe(t2)

fig2 = px.bar(t2, x="Nom du joueur", y="Exposure %", text="Exposure %")
st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# 3️⃣ HSR
# =========================================================

st.divider()
st.subheader("3️⃣ HSR Distance")

col1, col2 = st.columns(2)

with col1:
    f3_players = st.multiselect("Joueurs", players, key="c5")

with col2:
    f3_weeks = st.multiselect("Semaines", weeks, default=[max(weeks)], key="c6")

df3 = df.copy()

if f3_players:
    df3 = df3[df3["Nom du joueur"].isin(f3_players)]

if f3_weeks:
    df3 = df3[df3["Semaine"].isin(f3_weeks)]

t3 = build_table(df3, HSR_DISTANCE, 70, 100, "HSR Distance")
st.dataframe(t3)

fig3 = px.bar(t3, x="Nom du joueur", y="Exposure %", text="Exposure %")
st.plotly_chart(fig3, use_container_width=True)