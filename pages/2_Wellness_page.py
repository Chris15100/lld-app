import streamlit as st
import base64
import pandas as pd
import plotly.express as px
import numpy as np

# Chemin relatif vers l'image dans ton projet
image_path = "images/logo.png"

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_base64 = get_base64_of_bin_file(image_path)

html_code = f"""
<style>
.logo-top-right {{
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 9999;
    max-width: 150px;
}}
.logo-top-right img {{
    width: 100%;
    height: auto;
    display: block;
}}
</style>
<div class="logo-top-right">
    <img src="data:image/png;base64,{img_base64}" />
</div>
"""
st.markdown(html_code, unsafe_allow_html=True)

st.title("Wellness/RPE")

# Saison sélectionnée
saison = st.session_state.get("saison", "2026-2027")

# Lecture du fichier Excel
df = pd.read_excel(f"data/{saison}/Wellness.xlsx")
# Conversion explicite de la colonne Date
df["Date"] = pd.to_datetime(df["Date"], errors="coerce", format="%d/%m/%Y")

# Création d'une colonne "Semaine" = lundi de la semaine correspondante
df["Semaine"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday, unit="D")

col1, col2, col3 = st.columns(3)

with col1:
    joueurs = df['Nom du joueur'].dropna().unique().tolist()
    filtre_joueur = st.multiselect("Nom du joueur", sorted(joueurs))

with col2:
    dates = df['Date'].dropna().sort_values().unique().tolist()
    filtre_date = st.multiselect("Dates", [d.strftime("%d/%m/%Y") for d in dates])

with col3:
    semaines = df["Semaine"].dropna().sort_values().unique().tolist()
    filtre_semaine = st.multiselect("Semaines (lundi)", [s.strftime("Semaine du %d/%m/%Y") for s in semaines])

# --- Application des filtres ---
df_filtré = df.copy()

if filtre_joueur:
    df_filtré = df_filtré[df_filtré['Nom du joueur'].isin(filtre_joueur)]

if filtre_date:
    filtre_date_dt = pd.to_datetime(filtre_date, format="%d/%m/%Y")
    df_filtré = df_filtré[df_filtré['Date'].isin(filtre_date_dt)]

if filtre_semaine:
    filtre_semaine_dt = [pd.to_datetime(s.split("du ")[1], format="%d/%m/%Y") for s in filtre_semaine]
    df_filtré = df_filtré[df_filtré["Semaine"].isin(filtre_semaine_dt)]
else:
    filtre_semaine_dt = []

# --- Tableau ---
df_affichage = df_filtré.copy()
df_affichage["Date"] = df_affichage["Date"].dt.strftime("%d/%m/%Y")

# ❌ On enlève la colonne "Semaine" de l'affichage
if "Semaine" in df_affichage.columns:
    df_affichage = df_affichage.drop(columns=["Semaine"])

st.subheader(f"Résultats : {len(df_affichage)} lignes")
st.dataframe(df_affichage)

# --- Graphique (unique, en dessous du tableau) ---
if not df_filtré.empty:
    # ✅ Si filtre semaine → on affiche lundi à dimanche
    if filtre_semaine_dt:
        lundi = filtre_semaine_dt[0]
        dimanche = lundi + pd.Timedelta(days=6)
        all_dates = pd.date_range(lundi, dimanche, freq="D")
    else:
        # Sinon on affiche la plage min → max des données filtrées
        all_dates = pd.date_range(df_filtré["Date"].min(), df_filtré["Date"].max(), freq="D")

    df_all = pd.DataFrame({"Date": all_dates})

    # Moyenne par date
    df_moyenne = df_filtré.groupby("Date", as_index=False)["Charge"].mean()

    # Fusion → inclure toutes les dates (jours sans données = 0)
    df_plot = df_all.merge(df_moyenne, on="Date", how="left").fillna(0)

    # Ajout du jour de la semaine
    jours = {
        0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi",
        4: "Vendredi", 5: "Samedi", 6: "Dimanche"
    }
    df_plot["JourDate"] = df_plot["Date"].dt.weekday.map(jours) + " " + df_plot["Date"].dt.strftime("%d/%m/%Y")

    # Graphique interactif
    fig = px.bar(
        df_plot,
        x="JourDate",
        y="Charge",
        labels={"Charge": "Charge moyenne", "JourDate": "Date"},
        title="Évolution de la charge moyenne"
    )

    fig.update_layout(xaxis=dict(tickangle=-45))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucune donnée correspondant aux filtres.")


# =========================================================
# DATA PREP
# =========================================================

df_clean = df.copy()
df_clean["Date"] = pd.to_datetime(df_clean["Date"], errors="coerce")
df_clean = df_clean.dropna(subset=["Date"])

# =========================================================
# FILTERS
# =========================================================

col1, col2 = st.columns(2)

with col1:
    joueurs = st.multiselect(
        "Joueurs",
        sorted(df_clean["Nom du joueur"].dropna().unique()),
        key="players"
    )

with col2:
    date_ref = st.date_input(
        "Date de référence",
        value=df_clean["Date"].max()
    )

if joueurs:
    df_clean = df_clean[df_clean["Nom du joueur"].isin(joueurs)]

# =========================================================
# 🔥 BUILD FULL DAILY MATRIX (FIX PRINCIPAL)
# =========================================================

all_dates = pd.date_range(df_clean["Date"].min(), df_clean["Date"].max(), freq="D")
all_players = df_clean["Nom du joueur"].dropna().unique()

full_index = pd.MultiIndex.from_product(
    [all_players, all_dates],
    names=["Nom du joueur", "Date"]
).to_frame(index=False)

df_full = full_index.merge(
    df_clean,
    on=["Nom du joueur", "Date"],
    how="left"
)

# 👉 règle métier : absence = 0
df_full["Charge"] = df_full["Charge"].fillna(0)

# =========================================================
# ACWR FUNCTION
# =========================================================

def compute_acwr(df_player):

    df_player = df_player.sort_values("Date").copy()

    df_player["Acute"] = df_player["Charge"].ewm(span=7, adjust=False).mean()
    df_player["Chronic"] = df_player["Charge"].ewm(span=28, adjust=False).mean()
    df_player["ACWR"] = df_player["Acute"] / df_player["Chronic"]

    return df_player

# =========================================================
# APPLY PER PLAYER
# =========================================================

all_players = []

for p in df_full["Nom du joueur"].unique():

    tmp = df_full[df_full["Nom du joueur"] == p].copy()
    tmp = compute_acwr(tmp)
    all_players.append(tmp)

acwr_df = pd.concat(all_players, ignore_index=True)

# =========================================================
# 🔥 CRITICAL FIX: EXACT DATE SNAPSHOT (NO BACKSHIFT BUG)
# =========================================================

date_ref = pd.to_datetime(date_ref)

latest = acwr_df[acwr_df["Date"] == date_ref]

# si aucun match exact (sécurité)
if latest.empty:
    latest = (
        acwr_df[acwr_df["Date"] <= date_ref]
        .sort_values("Date")
        .groupby("Nom du joueur")
        .tail(1)
    )

# =========================================================
# STATUS
# =========================================================

def get_status(x):
    if pd.isna(x):
        return "⚪"
    if x < 0.80:
        return "🔵 Sous-charge"
    elif x <= 1.20:
        return "🟢 Optimal"
    elif x <= 1.50:
        return "🟠 Vigilance"
    return "🔴 Spike"

latest["Status"] = latest["ACWR"].apply(get_status)

# =========================================================
# TABLE
# =========================================================

table = latest[
    ["Nom du joueur", "Charge", "Acute", "Chronic", "ACWR", "Status"]
].copy()

table.columns = [
    "Nom du joueur",
    "Charge du jour",
    "Acute EWMA",
    "Chronic EWMA",
    "ACWR",
    "Status"
]

table = table.round(2)

st.subheader("📋 Tableau ACWR")
st.dataframe(table, use_container_width=True)

# =========================================================
# GLOBAL GRAPH
# =========================================================

st.subheader("📊 ACWR")

fig = px.bar(
    table.sort_values("ACWR", ascending=False),
    x="Nom du joueur",
    y="ACWR",
    color="ACWR",
    text="ACWR"
)

fig.add_hline(y=0.8, line_dash="dash")
fig.add_hline(y=1.2, line_dash="dash")
fig.add_hline(y=1.5, line_dash="dash")

st.plotly_chart(fig, use_container_width=True)

# =========================================================
# INDIVIDUAL
# =========================================================

st.subheader("📈 Evolution")

player = st.selectbox(
    "Joueur",
    sorted(acwr_df["Nom du joueur"].unique())
)

player_df = acwr_df[acwr_df["Nom du joueur"] == player]

fig2 = px.line(
    player_df,
    x="Date",
    y=["Acute", "Chronic"],
    title="Acute vs Chronic"
)

st.plotly_chart(fig2, use_container_width=True)

fig3 = px.line(
    player_df,
    x="Date",
    y="ACWR",
    title="ACWR Evolution"
)

fig3.add_hline(y=0.8, line_dash="dash")
fig3.add_hline(y=1.2, line_dash="dash")
fig3.add_hline(y=1.5, line_dash="dash")

st.plotly_chart(fig3, use_container_width=True)