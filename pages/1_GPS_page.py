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
# DATA LOAD
# =========================================================

if not os.path.exists(excel_path):
    st.error("Fichier introuvable")
    st.stop()

df = pd.read_excel(excel_path)

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])
df["Semaine"] = df["Date"].dt.isocalendar().week

# =========================================================
# METRICS (IMPORTANT : BRUTES)
# =========================================================

df["Sprint Count"] = df["Nb Sprint 25-30"] + df["Nb Sprint >30"]

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
# 1️⃣ TABLEAU BRUT (FILTRÉ)
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
# 2️⃣ DATA SPLIT (IMPORTANT)
# =========================================================

df_training = df[df["Type"] == "Entrainement"]
df_match = df[df["MD"] == "M"]

# =========================================================
# FUNCTIONS (CORRECTES + FILTRES PRIS EN COMPTE)
# =========================================================

def training_week(df_input, metric):
    return (
        df_input.groupby("Nom du joueur")[metric]
        .sum()
        .reset_index(name="Training")
    )

def match_top3(metric):
    return (
        df_match.groupby("Nom du joueur")[metric]
        .apply(lambda x: x.nlargest(3).mean())
        .reset_index(name="MatchTop3")
    )

def build(df_input, metric):
    train = training_week(df_input, metric)
    match = match_top3(metric)

    out = train.merge(match, on="Nom du joueur", how="left")

    out["Ratio %"] = (out["Training"] / out["MatchTop3"]) * 100
    out["Ratio %"] = out["Ratio %"].round(1)

    return out

# =========================================================
# FILTRES SPR (IMPORTANT : APPLIQUÉS AVANT CALCUL)
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
# 1. Sprint Count
# =========================================================

st.subheader("Sprint Count")

t1 = build(df_train_f, "Sprint Count")

st.dataframe(t1)
st.plotly_chart(px.bar(t1, x="Nom du joueur", y="Ratio %"), use_container_width=True)

# =========================================================
# 2. Sprint Distance
# =========================================================

st.subheader("Sprint Distance")

t2 = build(df_train_f, "Sprint Distance")

st.dataframe(t2)
st.plotly_chart(px.bar(t2, x="Nom du joueur", y="Ratio %"), use_container_width=True)

# =========================================================
# 3. HSR
# =========================================================

st.subheader("HSR Distance")

t3 = build(df_train_f, "HSR Distance")

st.dataframe(t3)
st.plotly_chart(px.bar(t3, x="Nom du joueur", y="Ratio %"), use_container_width=True)