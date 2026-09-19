import streamlit as st
import pandas as pd
import base64
import os
import plotly.express as px

# =========================================================
# CONFIG
# =========================================================

saison = st.session_state.get("saison", "2026-2027")

excel_path = f"data/{saison}/Gps propres catapult.xlsx"
image_path = "images/logo.png"

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="GPS Catapult Dashboard",
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

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])

# =========================================================
# WEEK START
# =========================================================

df["Week Start"] = (
    df["Date"]
    - pd.to_timedelta(df["Date"].dt.weekday, unit="D")
)

df["Week Label"] = df["Week Start"].dt.strftime("%d/%m/%Y")

# =========================================================
# CATAPULT METRICS
# =========================================================

# Zone 5 (>25.2 km/h)
df["SPR Distance"] = df["Distance Zone 5"]

# HSR (19.8 km/h et +)
df["HSR Distance"] = (
    df["Distance Zone 4"] +
    df["Distance Zone 5"]
)

# =========================================================
# SPLIT DATA
# =========================================================

df_training = df[df["Type"] == "Entrainement"].copy()
df_match = df[df["MD"] == "M"].copy()

# =========================================================
# DONNEES BRUTES
# =========================================================

st.title("📊 GPS Catapult Dashboard")

st.subheader("📌 Données brutes")

col1, col2, col3 = st.columns(3)

with col1:
    joueurs = sorted(df["Player Name"].dropna().unique())
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
    filtre_date = st.selectbox(
        "Date",
        [""] + [d.strftime("%d/%m/%Y") for d in dates]
    )

df_raw = df.copy()

if filtre_joueur:
    df_raw = df_raw[df_raw["Player Name"].isin(filtre_joueur)]

if filtre_type:
    df_raw = df_raw[df_raw["Type"] == filtre_type]

if filtre_periode:
    df_raw = df_raw[df_raw["Période"] == filtre_periode]

if filtre_md:
    df_raw = df_raw[df_raw["MD"] == filtre_md]

if filtre_poste:
    df_raw = df_raw[df_raw["Poste"] == filtre_poste]

if filtre_date:
    d = pd.to_datetime(filtre_date, format="%d/%m/%Y")
    df_raw = df_raw[df_raw["Date"].dt.date == d.date()]

st.write(f"📊 {len(df_raw)} lignes")

df_display = df_raw.copy()
df_display["Date"] = df_display["Date"].dt.strftime("%d/%m/%Y")

st.dataframe(df_display, use_container_width=True)

st.divider()

st.header("🏃 Dashboard Catapult")

st.markdown("""
Comparaison entre la charge hebdomadaire d'entraînement
et la référence Match Top 3.

**Métriques :**
- Zone 5 Distance (>25.2 km/h)
- HSR Distance (Zone 4 + Zone 5)
""")

# =========================================================
# FILTRES DASHBOARD CATAPULT
# =========================================================

col1, col2 = st.columns(2)

with col1:
    spr_players = st.multiselect(
        "Joueurs",
        sorted(df["Player Name"].dropna().unique()),
        key="catapult_players"
    )

with col2:
    week_options = (
        df_training[["Week Start", "Week Label"]]
        .drop_duplicates()
        .sort_values("Week Start")
    )

    selected_weeks = st.multiselect(
        "Semaines (Lundi)",
        week_options["Week Label"].tolist(),
        default=[week_options["Week Label"].iloc[-1]],
        key="catapult_weeks"
    )

# =========================================================
# APPLICATION DES FILTRES
# =========================================================

df_train_f = df_training.copy()

if spr_players:
    df_train_f = df_train_f[
        df_train_f["Player Name"].isin(spr_players)
    ]

if selected_weeks:
    df_train_f = df_train_f[
        df_train_f["Week Label"].isin(selected_weeks)
    ]

# =========================================================
# FONCTIONS
# =========================================================

def compute_training(df_input, metric):
    return (
        df_input
        .groupby("Player Name")[metric]
        .sum()
        .reset_index(name="Training")
    )


def compute_match_top3(metric):
    return (
        df_match
        .groupby("Player Name")[metric]
        .apply(lambda x: x.nlargest(3).mean())
        .reset_index(name="Match Top3")
    )


def build_table(df_input, metric, low, high):

    training = compute_training(df_input, metric)
    top3 = compute_match_top3(metric)

    result = training.merge(
        top3,
        on="Player Name",
        how="left"
    )

    result["Exposure %"] = (
        result["Training"] /
        result["Match Top3"]
    ) * 100

    result["Exposure %"] = result["Exposure %"].round(1)

    def status(x):
        if pd.isna(x):
            return "⚪"

        if x < low:
            return "🔴 Sous-exposé"

        if x <= high:
            return "🟢 Optimal"

        return "🟠 Surcharge"

    result["Status"] = result["Exposure %"].apply(status)

    return result

# =========================================================
# 1️⃣ ZONE 5 DISTANCE (>25.2 km/h)
# =========================================================

st.divider()

st.subheader("1️⃣ Zone 5 Distance (>25.2 km/h)")

t1 = build_table(
    df_train_f,
    "SPR Distance",
    80,
    120
)

st.dataframe(
    t1,
    use_container_width=True
)

fig1 = px.bar(
    t1.sort_values("Exposure %", ascending=False),
    x="Player Name",
    y="Exposure %",
    text="Exposure %",
    color="Exposure %"
)

fig1.add_hline(y=80, line_dash="dash")
fig1.add_hline(y=120, line_dash="dash")

fig1.update_layout(
    height=450,
    yaxis_title="% Match Exposure",
    xaxis_title="",
    coloraxis_showscale=False
)

st.plotly_chart(fig1, use_container_width=True)

# =========================================================
# 2️⃣ HSR DISTANCE (>19.8 km/h)
# =========================================================

st.divider()

st.subheader("2️⃣ HSR Distance (>19.8 km/h)")

t2 = build_table(
    df_train_f,
    "HSR Distance",
    70,
    100
)

st.dataframe(
    t2,
    use_container_width=True
)

fig2 = px.bar(
    t2.sort_values("Exposure %", ascending=False),
    x="Player Name",
    y="Exposure %",
    text="Exposure %",
    color="Exposure %"
)

fig2.add_hline(y=70, line_dash="dash")
fig2.add_hline(y=100, line_dash="dash")

fig2.update_layout(
    height=450,
    yaxis_title="% Match Exposure",
    xaxis_title="",
    coloraxis_showscale=False
)

st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# VMAX EXPOSURE DASHBOARD
# =========================================================

st.divider()
st.header("⚡ VMAX Exposure Dashboard")

st.markdown("""
Analyse de l'exposition à la vitesse maximale (Top Speed).

- >90% VMAX
- >95% VMAX
- =100% VMAX
- >100% VMAX (nouveau record)

Les matchs et entraînements servent à calculer la VMAX historique.
Seuls les entraînements sélectionnés sont utilisés pour l'exposition hebdomadaire.
""")

# =========================================================
# COLONNE VMAX CATAPULT
# =========================================================

vmax_col = "Top Speed"

# =========================================================
# VMAX HISTORIQUE
# =========================================================

player_vmax = (
    df.groupby("Player Name")[vmax_col]
      .max()
      .reset_index()
      .rename(columns={vmax_col: "VMAX"})
)

# =========================================================
# FILTRES
# =========================================================

col1, col2 = st.columns(2)

with col1:
    vmax_players = st.multiselect(
        "Joueurs (VMAX)",
        sorted(df["Player Name"].dropna().unique()),
        key="vmax_players"
    )

with col2:
    vmax_week_options = (
        df_training[["Week Start", "Week Label"]]
        .drop_duplicates()
        .sort_values("Week Start")
    )

    vmax_weeks = st.multiselect(
        "Semaines (Lundi)",
        vmax_week_options["Week Label"].tolist(),
        default=[vmax_week_options["Week Label"].iloc[-1]],
        key="vmax_weeks"
    )

# =========================================================
# FILTRE DONNEES
# =========================================================

df_vmax = df_training.copy()

if vmax_players:
    df_vmax = df_vmax[
        df_vmax["Player Name"].isin(vmax_players)
    ]

if vmax_weeks:
    df_vmax = df_vmax[
        df_vmax["Week Label"].isin(vmax_weeks)
    ]

# =========================================================
# MERGE VMAX
# =========================================================

df_vmax = df_vmax.merge(
    player_vmax,
    on="Player Name",
    how="left"
)

df_vmax["%VMAX"] = (
    df_vmax[vmax_col] /
    df_vmax["VMAX"]
) * 100

# =========================================================
# FLAGS
# =========================================================

df_vmax["90%+"] = df_vmax["%VMAX"] >= 90
df_vmax["95%+"] = df_vmax["%VMAX"] >= 95
df_vmax["100%"] = df_vmax["%VMAX"] >= 100
df_vmax[">100%"] = df_vmax["%VMAX"] > 100

# =========================================================
# TABLEAU
# =========================================================

vmax_dashboard = (
    df_vmax.groupby("Player Name")
    .agg(
        VMAX=("VMAX", "max"),
        Max_This_Week=(vmax_col, "max"),
        Best_Percent=("%VMAX", "max"),
        Over90=("90%+", "sum"),
        Over95=("95%+", "sum"),
        At100=("100%", "sum"),
        Over100=(">100%", "sum")
    )
    .reset_index()
)

vmax_dashboard["VMAX"] = vmax_dashboard["VMAX"].round(2)
vmax_dashboard["Max_This_Week"] = vmax_dashboard["Max_This_Week"].round(2)
vmax_dashboard["Best_Percent"] = vmax_dashboard["Best_Percent"].round(1)

def exposure_status(x):
    if x < 90:
        return "🔴 Sous-exposé"
    elif x < 95:
        return "🟠 Exposition modérée"
    else:
        return "🟢 Exposé"

vmax_dashboard["Status"] = (
    vmax_dashboard["Best_Percent"]
    .apply(exposure_status)
)

st.subheader("📋 Tableau exposition VMAX")

st.dataframe(
    vmax_dashboard,
    use_container_width=True
)

# =========================================================
# GRAPHIQUE 1
# =========================================================

st.subheader("📈 Meilleure exposition vitesse")

fig1 = px.bar(
    vmax_dashboard.sort_values(
        "Best_Percent",
        ascending=False
    ),
    x="Player Name",
    y="Best_Percent",
    text="Best_Percent",
    color="Best_Percent"
)

fig1.add_hline(y=90, line_dash="dash")
fig1.add_hline(y=95, line_dash="dash")
fig1.add_hline(y=100, line_dash="dash")

fig1.update_layout(
    height=500,
    yaxis_title="% VMAX",
    xaxis_title="",
    coloraxis_showscale=False
)

st.plotly_chart(fig1, use_container_width=True)

# =========================================================
# GRAPHIQUE 2
# =========================================================

st.subheader("📊 Nombre d'expositions vitesse")

counts_melt = vmax_dashboard.melt(
    id_vars=["Player Name"],
    value_vars=[
        "Over90",
        "Over95",
        "At100",
        "Over100"
    ],
    var_name="Zone",
    value_name="Count"
)

fig2 = px.bar(
    counts_melt,
    x="Player Name",
    y="Count",
    color="Zone",
    barmode="group",
    text="Count"
)

fig2.update_layout(
    height=500,
    yaxis_title="Nombre d'expositions",
    xaxis_title=""
)

st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# GRAPHIQUE 3
# =========================================================

st.subheader("⚡ VMAX historique vs semaine")

compare_melt = vmax_dashboard.melt(
    id_vars=["Player Name"],
    value_vars=["VMAX", "Max_This_Week"],
    var_name="Type",
    value_name="Speed"
)

fig3 = px.bar(
    compare_melt,
    x="Player Name",
    y="Speed",
    color="Type",
    barmode="group",
    text="Speed"
)

fig3.update_layout(
    height=500,
    yaxis_title="km/h",
    xaxis_title=""
)

st.plotly_chart(fig3, use_container_width=True)