import streamlit as st
import base64
import pandas as pd
import plotly.express as px

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
# =========================================================
# ACUTE / CHRONIC LOAD DASHBOARD (EWMA)
# =========================================================
# =========================================================

st.divider()
st.header("📈 Acute / Chronic Load Dashboard")

st.markdown("""
Calcul basé sur la charge Wellness.

- Acute = EWMA 7 jours
- Chronic = EWMA 28 jours
- ACWR = Acute / Chronic

Zones :

🟦 < 0.80 = Sous-charge

🟩 0.80 - 1.30 = Optimal

🟧 1.30 - 1.50 = Vigilance

🟥 > 1.50 = Spike
""")

# =========================================================
# WELLNESS DATA
# =========================================================

wellness = df_wellness.copy()

wellness["Date"] = pd.to_datetime(
    wellness["Date"],
    errors="coerce"
)

wellness = wellness.dropna(
    subset=["Date"]
)

# =========================================================
# FILTERS
# =========================================================

col1, col2 = st.columns(2)

with col1:

    joueurs_acwr = st.multiselect(
        "Joueurs",
        sorted(
            wellness["Nom du joueur"]
            .dropna()
            .unique()
        ),
        key="acwr_players"
    )

with col2:

    date_ref = st.date_input(
        "Date de référence",
        value=wellness["Date"].max(),
        key="acwr_date"
    )

# =========================================================
# FILTER DATA
# =========================================================

df_acwr = wellness.copy()

if joueurs_acwr:

    df_acwr = df_acwr[
        df_acwr["Nom du joueur"]
        .isin(joueurs_acwr)
    ]

# =========================================================
# EWMA FUNCTION
# =========================================================

def compute_acwr(player_df):

    player_df = (
        player_df
        .sort_values("Date")
        .copy()
    )

    player_df["Acute"] = (
        player_df["Charge"]
        .ewm(span=7, adjust=False)
        .mean()
    )

    player_df["Chronic"] = (
        player_df["Charge"]
        .ewm(span=28, adjust=False)
        .mean()
    )

    player_df["ACWR"] = (
        player_df["Acute"]
        / player_df["Chronic"]
    )

    return player_df

# =========================================================
# CALCULS
# =========================================================

all_players = []

for joueur in df_acwr["Nom du joueur"].unique():

    temp = df_acwr[
        df_acwr["Nom du joueur"] == joueur
    ].copy()

    temp = compute_acwr(temp)

    all_players.append(temp)

acwr_df = pd.concat(
    all_players,
    ignore_index=True
)

# =========================================================
# DERNIERE VALEUR
# =========================================================

date_ref = pd.to_datetime(date_ref)

latest = (
    acwr_df[
        acwr_df["Date"] <= date_ref
    ]
    .sort_values("Date")
    .groupby("Nom du joueur")
    .tail(1)
)

# =========================================================
# STATUS
# =========================================================

def status(acwr):

    if pd.isna(acwr):
        return "⚪"

    if acwr < 0.80:
        return "🔵 Sous-charge"

    if acwr <= 1.30:
        return "🟢 Optimal"

    if acwr <= 1.50:
        return "🟠 Vigilance"

    return "🔴 Spike"

latest["Status"] = (
    latest["ACWR"]
    .apply(status)
)

# =========================================================
# TABLEAU
# =========================================================

table_acwr = latest[
    [
        "Nom du joueur",
        "Charge",
        "Acute",
        "Chronic",
        "ACWR",
        "Status"
    ]
].copy()

table_acwr.columns = [
    "Nom du joueur",
    "Charge J",
    "Acute EWMA",
    "Chronic EWMA",
    "ACWR",
    "Status"
]

table_acwr = table_acwr.round(2)

st.subheader("📋 Tableau ACWR")

st.dataframe(
    table_acwr,
    use_container_width=True
)

# =========================================================
# GRAPH ACWR
# =========================================================

st.subheader("📊 ACWR par joueur")

fig = px.bar(
    table_acwr.sort_values(
        "ACWR",
        ascending=False
    ),
    x="Nom du joueur",
    y="ACWR",
    text="ACWR",
    color="ACWR"
)

fig.add_hline(
    y=0.80,
    line_dash="dash"
)

fig.add_hline(
    y=1.30,
    line_dash="dash"
)

fig.add_hline(
    y=1.50,
    line_dash="dash"
)

fig.update_layout(
    height=500,
    xaxis_title="",
    yaxis_title="ACWR"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================================================
# EVOLUTION JOUEUR
# =========================================================

st.divider()

st.subheader("📈 Evolution individuelle")

joueur_graph = st.selectbox(
    "Choisir un joueur",
    sorted(
        acwr_df["Nom du joueur"]
        .unique()
    ),
    key="acwr_graph"
)

player_graph = acwr_df[
    acwr_df["Nom du joueur"] == joueur_graph
].copy()

fig2 = px.line(
    player_graph,
    x="Date",
    y=[
        "Acute",
        "Chronic"
    ]
)

fig2.update_layout(
    height=500,
    yaxis_title="Charge",
    xaxis_title=""
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# =========================================================
# EVOLUTION ACWR
# =========================================================

fig3 = px.line(
    player_graph,
    x="Date",
    y="ACWR"
)

fig3.add_hline(
    y=0.80,
    line_dash="dash"
)

fig3.add_hline(
    y=1.30,
    line_dash="dash"
)

fig3.add_hline(
    y=1.50,
    line_dash="dash"
)

fig3.update_layout(
    height=500,
    yaxis_title="ACWR",
    xaxis_title=""
)

st.plotly_chart(
    fig3,
    use_container_width=True
)