import streamlit as st
import pandas as pd
import base64
import os
import plotly.express as px

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
# METRICS
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
# =========================================================
# 📊 TABLEAU BRUT FILTRÉ (TON ORIGINAL)
# =========================================================
# =========================================================

st.title("📊 GPS Dashboard")

st.subheader("📌 Données brutes filtrées")

col1, col2, col3 = st.columns(3)

with col1:
    joueurs = sorted(df["Nom du joueur"].dropna().unique())
    f_joueur = st.multiselect("Joueur", joueurs)

with col2:
    types = sorted(df["Type"].dropna().unique())
    f_type = st.selectbox("Type", [""] + types)

with col3:
    periodes = sorted(df["Période"].dropna().unique())
    f_periode = st.selectbox("Période", [""] + periodes)

col4, col5, col6 = st.columns(3)

with col4:
    md = sorted(df["MD"].dropna().unique())
    f_md = st.selectbox("MD", [""] + md)

with col5:
    postes = sorted(df["Poste"].dropna().unique())
    f_poste = st.selectbox("Poste", [""] + postes)

with col6:
    dates = sorted(df["Date"].dt.date.unique())
    f_date = st.selectbox("Date", [""] + [d.strftime("%d/%m/%Y") for d in dates])

df_base = df.copy()

if f_joueur:
    df_base = df_base[df_base["Nom du joueur"].isin(f_joueur)]

if f_type:
    df_base = df_base[df_base["Type"] == f_type]

if f_periode:
    df_base = df_base[df_base["Période"] == f_periode]

if f_md:
    df_base = df_base[df_base["MD"] == f_md]

if f_poste:
    df_base = df_base[df_base["Poste"] == f_poste]

if f_date:
    d = pd.to_datetime(f_date, format="%d/%m/%Y")
    df_base = df_base[df_base["Date"].dt.date == d.date()]

st.write(f"📊 {len(df_base)} lignes")
st.dataframe(df_base)

# =========================================================
# DATA SPLIT PROPRE
# =========================================================

df_training = df[df["Type"] == "Entrainement"]
df_match = df[df["MD"] == "M"]

# =========================================================
# FUNCTIONS
# =========================================================

def compute_training_week(metric):
    return (
        df_training.groupby("Nom du joueur")[metric]
        .sum()
        .reset_index()
        .rename(columns={metric: "Training Week"})
    )


def compute_match_top3(metric):
    return (
        df_match.groupby("Nom du joueur")[metric]
        .apply(lambda x: x.nlargest(3).mean())
        .reset_index()
        .rename(columns={metric: "Match Top3"})
    )


def build_table(metric, low, high, name):
    training = compute_training_week(metric)
    match = compute_match_top3(metric)

    result = training.merge(match, on="Nom du joueur", how="left")

    result["Match Top3"] = result["Match Top3"].replace(0, pd.NA)

    result["Exposure %"] = (result["Training Week"] / result["Match Top3"]) * 100
    result["Exposure %"] = result["Exposure %"].round(1)

    def status(x):
        if pd.isna(x):
            return "⚪ NA"
        if x < low:
            return "🔴 Sous-exposé"
        if x <= high:
            return "🟢 Optimal"
        return "🟠 Surcharge"

    result["Status"] = result["Exposure %"].apply(status)

    return result

# =========================================================
# METRICS
# =========================================================

SPRINT_COUNT = "# Sprints (>25 km/h)"
SPRINT_DISTANCE = "Sprint Distance"
HSR_DISTANCE = "HSR Distance"

players = sorted(df["Nom du joueur"].dropna().unique())
weeks = sorted(df["Semaine"].dropna().unique())

# =========================================================
# 1️⃣ SPR COUNT
# =========================================================

st.divider()
st.subheader("1️⃣ Sprint Count")

col1, col2 = st.columns(2)

with col1:
    p1 = st.multiselect("Joueurs", players, key="p1")

with col2:
    w1 = st.multiselect("Semaines", weeks, default=[max(weeks)], key="w1")

df1 = df_training.copy()

if p1:
    df1 = df1[df1["Nom du joueur"].isin(p1)]
if w1:
    df1 = df1[df1["Semaine"].isin(w1)]

t1 = build_table(SPRINT_COUNT, 90, 120, "Sprint Count")

st.dataframe(t1)
st.plotly_chart(px.bar(t1, x="Nom du joueur", y="Exposure %"), use_container_width=True)

# =========================================================
# 2️⃣ SPR DISTANCE
# =========================================================

st.divider()
st.subheader("2️⃣ Sprint Distance")

col1, col2 = st.columns(2)

with col1:
    p2 = st.multiselect("Joueurs", players, key="p2")

with col2:
    w2 = st.multiselect("Semaines", weeks, default=[max(weeks)], key="w2")

df2 = df_training.copy()

if p2:
    df2 = df2[df2["Nom du joueur"].isin(p2)]
if w2:
    df2 = df2[df2["Semaine"].isin(w2)]

t2 = build_table(SPRINT_DISTANCE, 80, 120, "Sprint Distance")

st.dataframe(t2)
st.plotly_chart(px.bar(t2, x="Nom du joueur", y="Exposure %"), use_container_width=True)

# =========================================================
# 3️⃣ HSR
# =========================================================

st.divider()
st.subheader("3️⃣ HSR Distance")

col1, col2 = st.columns(2)

with col1:
    p3 = st.multiselect("Joueurs", players, key="p3")

with col2:
    w3 = st.multiselect("Semaines", weeks, default=[max(weeks)], key="w3")

df3 = df_training.copy()

if p3:
    df3 = df3[df3["Nom du joueur"].isin(p3)]
if w3:
    df3 = df3[df3["Semaine"].isin(w3)]

t3 = build_table(HSR_DISTANCE, 70, 100, "HSR Distance")

st.dataframe(t3)
st.plotly_chart(px.bar(t3, x="Nom du joueur", y="Exposure %"), use_container_width=True)