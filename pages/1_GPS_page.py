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
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="GPS Dashboard",
    layout="wide"
)

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
        right: 20px;
        width: 140px;
        z-index: 9999;
    }}

    </style>

    <div class="logo">
        <img src="data:image/png;base64,{img}" width="140">
    </div>

    """, unsafe_allow_html=True)

# =========================================================
# LOAD DATA
# =========================================================

if not os.path.exists(excel_path):

    st.error(f"❌ Fichier introuvable : {excel_path}")
    st.stop()

df = pd.read_excel(excel_path)

# =========================================================
# DATE
# =========================================================

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

df = df.dropna(subset=["Date"])

# =========================================================
# WEEK START (LUNDI)
# =========================================================

df["Week Start"] = (
    df["Date"]
    - pd.to_timedelta(
        df["Date"].dt.weekday,
        unit="D"
    )
)

df["Week Label"] = (
    df["Week Start"]
    .dt.strftime("%d/%m/%Y")
)

# =========================================================
# GPS METRICS
# =========================================================

# Sprint Count réel GPS
df["Sprint Count"] = df["# of Sprints (>25 km/h)"]

# SPR >25 km/h
df["SPR Distance"] = (
    df["Distance par plage de vitesse (25-30 km/h)"]
    + df["Distance par plage de vitesse (>30 km/h)"]
)

# HSR >20 km/h
df["HSR Distance"] = (
    df["Distance par plage de vitesse (20-25 km/h)"]
    + df["Distance par plage de vitesse (25-30 km/h)"]
    + df["Distance par plage de vitesse (>30 km/h)"]
)

# =========================================================
# SPLIT DATA
# =========================================================

df_training = df[
    df["Type"] == "Entrainement"
].copy()

df_match = df[
    df["MD"] == "M"
].copy()

# =========================================================
# =========================================================
# TABLEAU BRUT
# =========================================================
# =========================================================

st.title("📊 GPS Dashboard")

st.subheader("📌 Données brutes")

# =========================================================
# FILTERS
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:

    joueurs = sorted(
        df["Nom du joueur"]
        .dropna()
        .unique()
    )

    filtre_joueur = st.multiselect(
        "Joueur",
        joueurs
    )

with col2:

    types = sorted(
        df["Type"]
        .dropna()
        .unique()
    )

    filtre_type = st.selectbox(
        "Type",
        [""] + types
    )

with col3:

    periodes = sorted(
        df["Période"]
        .dropna()
        .unique()
    )

    filtre_periode = st.selectbox(
        "Période",
        [""] + periodes
    )

# ---------------------------------------------------------

col4, col5, col6 = st.columns(3)

with col4:

    md = sorted(
        df["MD"]
        .dropna()
        .unique()
    )

    filtre_md = st.selectbox(
        "MD",
        [""] + md
    )

with col5:

    postes = sorted(
        df["Poste"]
        .dropna()
        .unique()
    )

    filtre_poste = st.selectbox(
        "Poste",
        [""] + postes
    )

with col6:

    dates = sorted(
        df["Date"]
        .dt.date
        .unique()
    )

    filtre_date = st.selectbox(
        "Date",
        [""] + [
            d.strftime("%d/%m/%Y")
            for d in dates
        ]
    )

# =========================================================
# APPLY FILTERS
# =========================================================

df_raw = df.copy()

if filtre_joueur:

    df_raw = df_raw[
        df_raw["Nom du joueur"]
        .isin(filtre_joueur)
    ]

if filtre_type:

    df_raw = df_raw[
        df_raw["Type"] == filtre_type
    ]

if filtre_periode:

    df_raw = df_raw[
        df_raw["Période"] == filtre_periode
    ]

if filtre_md:

    df_raw = df_raw[
        df_raw["MD"] == filtre_md
    ]

if filtre_poste:

    df_raw = df_raw[
        df_raw["Poste"] == filtre_poste
    ]

if filtre_date:

    d = pd.to_datetime(
        filtre_date,
        format="%d/%m/%Y"
    )

    df_raw = df_raw[
        df_raw["Date"].dt.date == d.date()
    ]

# =========================================================
# DISPLAY TABLE
# =========================================================

st.write(f"📊 {len(df_raw)} lignes")

df_display = df_raw.copy()

df_display["Date"] = (
    df_display["Date"]
    .dt.strftime("%d/%m/%Y")
)

st.dataframe(
    df_display,
    use_container_width=True
)

# =========================================================
# =========================================================
# SPR DASHBOARD
# =========================================================
# =========================================================

st.divider()

st.header("🏃 SPR Dashboard")

st.markdown("""
Comparaison entre :

- charge d'entraînement hebdomadaire
- référence match Top 3 individuelle

Métriques :

- Sprint Count (>25 km/h)
- SPR Distance (>25 km/h)
- HSR Distance (>20 km/h)
""")

# =========================================================
# FILTERS SPR
# =========================================================

col1, col2 = st.columns(2)

with col1:

    spr_players = st.multiselect(
        "Joueurs",
        sorted(
            df["Nom du joueur"]
            .dropna()
            .unique()
        ),
        key="spr_players"
    )

with col2:

    week_options = (
        df_training[
            ["Week Start", "Week Label"]
        ]
        .drop_duplicates()
        .sort_values("Week Start")
    )

    selected_weeks = st.multiselect(
        "Semaines (Lundi)",
        week_options["Week Label"].tolist(),
        default=[
            week_options["Week Label"].iloc[-1]
        ],
        key="spr_weeks"
    )

# =========================================================
# APPLY FILTERS SPR
# =========================================================

df_train_f = df_training.copy()

if spr_players:

    df_train_f = df_train_f[
        df_train_f["Nom du joueur"]
        .isin(spr_players)
    ]

if selected_weeks:

    df_train_f = df_train_f[
        df_train_f["Week Label"]
        .isin(selected_weeks)
    ]

# =========================================================
# FUNCTIONS
# =========================================================

def compute_training(df_input, metric):

    return (
        df_input
        .groupby("Nom du joueur")[metric]
        .sum()
        .reset_index(name="Training")
    )

def compute_match_top3(metric):

    return (
        df_match
        .groupby("Nom du joueur")[metric]
        .apply(lambda x: x.nlargest(3).mean())
        .reset_index(name="Match Top3")
    )

def build_table(
    df_input,
    metric,
    low,
    high
):

    training = compute_training(
        df_input,
        metric
    )

    top3 = compute_match_top3(metric)

    result = training.merge(
        top3,
        on="Nom du joueur",
        how="left"
    )

    result["Exposure %"] = (
        result["Training"]
        / result["Match Top3"]
    ) * 100

    result["Exposure %"] = (
        result["Exposure %"]
        .round(1)
    )

    def status(x):

        if pd.isna(x):
            return "⚪"

        if x < low:
            return "🔴 Sous-exposé"

        if x <= high:
            return "🟢 Optimal"

        return "🟠 Surcharge"

    result["Status"] = (
        result["Exposure %"]
        .apply(status)
    )

    return result

# =========================================================
# 1️⃣ SPRINT COUNT
# =========================================================

st.divider()

st.subheader("1️⃣ Sprint Count (>25 km/h)")

t1 = build_table(
    df_train_f,
    "Sprint Count",
    90,
    120
)

st.dataframe(
    t1,
    use_container_width=True
)

fig1 = px.bar(
    t1.sort_values(
        "Exposure %",
        ascending=False
    ),
    x="Nom du joueur",
    y="Exposure %",
    text="Exposure %"
)

fig1.add_hline(
    y=90,
    line_dash="dash"
)

fig1.add_hline(
    y=120,
    line_dash="dash"
)

fig1.update_layout(
    height=450,
    yaxis_title="% Match Exposure",
    xaxis_title=""
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# =========================================================
# 2️⃣ SPR DISTANCE
# =========================================================

st.divider()

st.subheader("2️⃣ SPR Distance (>25 km/h)")

t2 = build_table(
    df_train_f,
    "SPR Distance",
    80,
    120
)

st.dataframe(
    t2,
    use_container_width=True
)

fig2 = px.bar(
    t2.sort_values(
        "Exposure %",
        ascending=False
    ),
    x="Nom du joueur",
    y="Exposure %",
    text="Exposure %"
)

fig2.add_hline(
    y=80,
    line_dash="dash"
)

fig2.add_hline(
    y=120,
    line_dash="dash"
)

fig2.update_layout(
    height=450,
    yaxis_title="% Match Exposure",
    xaxis_title=""
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# =========================================================
# 3️⃣ HSR DISTANCE
# =========================================================

st.divider()

st.subheader("3️⃣ HSR Distance (>20 km/h)")

t3 = build_table(
    df_train_f,
    "HSR Distance",
    70,
    100
)

st.dataframe(
    t3,
    use_container_width=True
)

fig3 = px.bar(
    t3.sort_values(
        "Exposure %",
        ascending=False
    ),
    x="Nom du joueur",
    y="Exposure %",
    text="Exposure %"
)

fig3.add_hline(
    y=70,
    line_dash="dash"
)

fig3.add_hline(
    y=100,
    line_dash="dash"
)

fig3.update_layout(
    height=450,
    yaxis_title="% Match Exposure",
    xaxis_title=""
)

st.plotly_chart(
    fig3,
    use_container_width=True
)