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

def get_base64(bin_file):
    if not os.path.exists(bin_file):
        return ""
    with open(bin_file, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_base64 = get_base64(image_path)

if img_base64:
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
        <img src="data:image/png;base64,{img_base64}">
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# DATA LOAD
# =========================================================

if not os.path.exists(excel_path):
    st.error(f"Fichier introuvable : {excel_path}")
    st.stop()

df = pd.read_excel(excel_path)

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])

df["Date_str"] = df["Date"].dt.strftime("%d/%m/%Y")

# =========================================================
# FILTRES PRINCIPAUX
# =========================================================

st.title("GPS Dashboard")

col1, col2, col3 = st.columns(3)

with col1:
    joueurs = sorted(df["Nom du joueur"].dropna().unique())
    filtre_joueur = st.multiselect("Joueur", joueurs)

with col2:
    types = sorted(df["Type"].dropna().unique())
    filtre_type = st.selectbox("Type", [""] + types)

with col3:
    periodes = sorted(df["Période"].dropna().unique())
    filtre_periode = st.selectbox("Période", [""] + periodes)

col4, col5, col6 = st.columns(3)

with col4:
    md = sorted(df["MD"].dropna().unique())
    filtre_md = st.selectbox("MD", [""] + md)

with col5:
    postes = sorted(df["Poste"].dropna().unique())
    filtre_poste = st.selectbox("Poste", [""] + postes)

with col6:
    dates = sorted(df["Date"].dt.date.unique())
    filtre_date = st.selectbox("Date", [""] + [d.strftime("%d/%m/%Y") for d in dates])

# =========================================================
# DATA FILTRÉ PRINCIPAL
# =========================================================

df_filtered = df.copy()

if filtre_joueur:
    df_filtered = df_filtered[df_filtered["Nom du joueur"].isin(filtre_joueur)]

if filtre_type:
    df_filtered = df_filtered[df_filtered["Type"] == filtre_type]

if filtre_periode:
    df_filtered = df_filtered[df_filtered["Période"] == filtre_periode]

if filtre_md:
    df_filtered = df_filtered[df_filtered["MD"] == filtre_md]

if filtre_poste:
    df_filtered = df_filtered[df_filtered["Poste"] == filtre_poste]

if filtre_date:
    d = pd.to_datetime(filtre_date, format="%d/%m/%Y")
    df_filtered = df_filtered[df_filtered["Date"].dt.date == d.date()]

# =========================================================
# DISPLAY
# =========================================================

st.write(f"{len(df_filtered)} lignes")
st.dataframe(df_filtered)

# =========================================================
# SPR DATA = BASE UNIQUE CORRIGÉE
# =========================================================

df_spr = df_filtered.copy()

df_spr["Sprint Distance"] = (
    df_spr["Distance par plage de vitesse (25-30 km/h)"]
    + df_spr["Distance par plage de vitesse (>30 km/h)"]
)

df_spr["HSR Distance"] = (
    df_spr["Distance par plage de vitesse (20-25 km/h)"]
    + df_spr["Distance par plage de vitesse (25-30 km/h)"]
    + df_spr["Distance par plage de vitesse (>30 km/h)"]
)

df_spr["Semaine"] = df_spr["Date"].dt.isocalendar().week

# =========================================================
# SIDEBAR SPR FILTERS
# =========================================================

st.sidebar.header("SPR Filters")

spr_players = sorted(df_spr["Nom du joueur"].dropna().unique())
spr_weeks = sorted(df_spr["Semaine"].dropna().unique())
spr_positions = sorted(df_spr["Poste"].dropna().unique())

filtre_joueurs = st.sidebar.multiselect(
    "Joueurs",
    spr_players,
    default=spr_players[:5] if len(spr_players) > 0 else []
)

filtre_semaines = st.sidebar.multiselect(
    "Semaines",
    spr_weeks,
    default=[max(spr_weeks)] if len(spr_weeks) > 0 else []
)

filtre_poste_spr = st.sidebar.selectbox(
    "Poste",
    ["Tous"] + spr_positions
)

# =========================================================
# APPLY SPR FILTERS
# =========================================================

df_spr_f = df_spr.copy()

if filtre_joueurs:
    df_spr_f = df_spr_f[df_spr_f["Nom du joueur"].isin(filtre_joueurs)]

if filtre_semaines:
    df_spr_f = df_spr_f[df_spr_f["Semaine"].isin(filtre_semaines)]

if filtre_poste_spr != "Tous":
    df_spr_f = df_spr_f[df_spr_f["Poste"] == filtre_poste_spr]

# =========================================================
# METRICS FUNCTIONS FIXED
# =========================================================

def compute_top3(metric):
    df_match = df_spr[df_spr["MD"] == "M"]

    top3 = (
        df_match.groupby("Nom du joueur")[metric]
        .apply(lambda x: x.nlargest(3).mean())
        .reset_index()
        .rename(columns={metric: "Top3"})
    )

    return top3


def compute_week(metric):
    return (
        df_spr_f.groupby("Nom du joueur")[metric]
        .sum()
        .reset_index()
        .rename(columns={metric: "Week"})
    )


def build_table(metric, low, high, name):
    week = compute_week(metric)
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
# TABLES
# =========================================================

SPRINT_COUNT = "# Sprints (>25 km/h)"
SPRINT_DISTANCE = "Sprint Distance"
HSR_DISTANCE = "HSR Distance"

t1 = build_table(SPRINT_COUNT, 90, 120, "Sprint Count")
t2 = build_table(SPRINT_DISTANCE, 80, 120, "Sprint Distance")
t3 = build_table(HSR_DISTANCE, 70, 100, "HSR Distance")

# =========================================================
# DISPLAY SECTION
# =========================================================

st.divider()
st.subheader("Sprint Count")

st.dataframe(t1)

st.divider()
st.subheader("Sprint Distance")

st.dataframe(t2)

st.divider()
st.subheader("HSR Distance")

st.dataframe(t3)