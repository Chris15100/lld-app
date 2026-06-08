import streamlit as st
import pandas as pd
import base64
import os
import plotly.express as px

# =========================================================
# CONFIG
# =========================================================

saison = st.session_state.get("saison", "2026-2027")

excel_path = f"data/{saison}/DonneesGPSPropres.xlsx"
image_path = "images/logo.png"

# =========================================================
# UTILS
# =========================================================

def get_base64(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def find_col(df, keyword):
    """Trouve une colonne contenant un mot clé"""
    cols = [c for c in df.columns if keyword.lower() in c.lower()]
    return cols[0] if cols else None

# =========================================================
# LOGO
# =========================================================

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
    st.error("Fichier introuvable")
    st.stop()

df = pd.read_excel(excel_path)

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])
df["Semaine"] = df["Date"].dt.isocalendar().week

# =========================================================
# AUTO DETECTION COLONNES IMPORTANTES
# =========================================================

sprint_col = find_col(df, "sprint")
accel_col = find_col(df, "accel")
decel_col = find_col(df, "decel")

# =========================================================
# SAFETY CHECK
# =========================================================

if sprint_col is None:
    st.error("Colonne Sprint introuvable dans le fichier")
    st.stop()

# =========================================================
# DATA SPLIT
# =========================================================

df_training = df[df["Type"] == "Entrainement"]
df_match = df[df["MD"] == "M"]

# =========================================================
# TABLEAU BRUT (FILTRÉ)
# =========================================================

st.title("📊 GPS Dashboard")

st.subheader("📌 Données brutes")

col1, col2, col3 = st.columns(3)

with col1:
    joueurs = sorted(df["Nom du joueur"].dropna().unique())
    f_joueur = st.multiselect("Joueur", joueurs)

with col2:
    types = sorted(df["Type"].dropna().unique())
    f_type = st.selectbox("Type", [""] + types)

with col3:
    md = sorted(df["MD"].dropna().unique())
    f_md = st.selectbox("MD", [""] + md)

df_raw = df.copy()

if f_joueur:
    df_raw = df_raw[df_raw["Nom du joueur"].isin(f_joueur)]

if f_type:
    df_raw = df_raw[df_raw["Type"] == f_type]

if f_md:
    df_raw = df_raw[df_raw["MD"] == f_md]

st.write(f"{len(df_raw)} lignes")
st.dataframe(df_raw)

# =========================================================
# SPR FUNCTIONS
# =========================================================

def training_week(df_input, col):
    return (
        df_input.groupby("Nom du joueur")[col]
        .sum()
        .reset_index(name="Training")
    )

def match_top3(col):
    return (
        df_match.groupby("Nom du joueur")[col]
        .apply(lambda x: x.nlargest(3).mean())
        .reset_index(name="MatchTop3")
    )

def build(df_input, col, low, high):
    train = training_week(df_input, col)
    match = match_top3(col)

    out = train.merge(match, on="Nom du joueur", how="left")

    out["MatchTop3"] = out["MatchTop3"].replace(0, pd.NA)
    out["Ratio %"] = (out["Training"] / out["MatchTop3"]) * 100
    out["Ratio %"] = out["Ratio %"].round(1)

    def status(x):
        if pd.isna(x):
            return "⚪ NA"
        if x < low:
            return "🔴 Sous-exposé"
        if x <= high:
            return "🟢 Optimal"
        return "🟠 Surcharge"

    out["Status"] = out["Ratio %"].apply(status)

    return out

# =========================================================
# SPR DASHBOARD FILTERS
# =========================================================

st.divider()
st.subheader("SPR Dashboard")

col1, col2 = st.columns(2)

with col1:
    players = st.multiselect("Joueurs", sorted(df["Nom du joueur"].unique()))

with col2:
    weeks = st.multiselect("Semaines", sorted(df["Semaine"].unique()))

df_train_f = df_training.copy()

if players:
    df_train_f = df_train_f[df_train_f["Nom du joueur"].isin(players)]

if weeks:
    df_train_f = df_train_f[df_train_f["Semaine"].isin(weeks)]

# =========================================================
# KPI 1 - SPRINT COUNT
# =========================================================

st.subheader("Sprint Count")

t1 = build(df_train_f, sprint_col, 90, 120)

st.dataframe(t1)
st.plotly_chart(px.bar(t1, x="Nom du joueur", y="Ratio %"), use_container_width=True)

# =========================================================
# KPI 2 - ACCELERATIONS (si existe)
# =========================================================

if accel_col:
    st.subheader("Accelerations")

    t2 = build(df_train_f, accel_col, 80, 120)

    st.dataframe(t2)
    st.plotly_chart(px.bar(t2, x="Nom du joueur", y="Ratio %"), use_container_width=True)

# =========================================================
# KPI 3 - DECELERATIONS (si existe)
# =========================================================

if decel_col:
    st.subheader("Decelerations")

    t3 = build(df_train_f, decel_col, 80, 120)

    st.dataframe(t3)
    st.plotly_chart(px.bar(t3, x="Nom du joueur", y="Ratio %"), use_container_width=True)