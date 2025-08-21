import streamlit as st
import base64
import pandas as pd
import plotly.express as px

# Chemin relatif vers l'image dans ton projet (assure-toi que l'image existe ici)
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

# 🔥 Lecture du fichier Excel
df = pd.read_excel("data/Wellness.xlsx")

# Conversion explicite de la colonne Date
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# Assurons-nous que la colonne Date est bien en datetime
df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

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

# Application des filtres
df_filtré = df.copy()

if filtre_joueur:
    df_filtré = df_filtré[df_filtré['Nom du joueur'].isin(filtre_joueur)]

if filtre_date:
    filtre_date_dt = pd.to_datetime(filtre_date, format="%d/%m/%Y")
    df_filtré = df_filtré[df_filtré['Date'].isin(filtre_date_dt)]

if filtre_semaine:
    filtre_semaine_dt = [pd.to_datetime(s.split("du ")[1], format="%d/%m/%Y") for s in filtre_semaine]
    df_filtré = df_filtré[df_filtré["Semaine"].isin(filtre_semaine_dt)]

    # 🔹 Inclure toutes les dates de chaque semaine sélectionnée
    all_dates = []
    for lundi in filtre_semaine_dt:
        semaine_complète = pd.date_range(lundi, lundi + pd.Timedelta(days=6), freq="D")
        all_dates.extend(semaine_complète)

    all_dates = pd.DataFrame({"Date": pd.to_datetime(all_dates)})

    # Moyenne par date
    df_moyenne = df_filtré.groupby("Date", as_index=False)["Charge"].mean()

    # Fusion pour inclure toutes les dates (remplit NaN par 0)
    df_plot = all_dates.merge(df_moyenne, on="Date", how="left").fillna(0)

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
        title="Charge moyenne par semaine sélectionnée"
    )

    # Inclinaison des labels
    fig.update_layout(xaxis=dict(tickangle=-45))

    st.plotly_chart(fig, use_container_width=True)

# Préparer l'affichage final (dates formatées)
df_affichage = df_filtré.copy()
df_affichage["Date"] = df_affichage["Date"].dt.strftime("%d/%m/%Y")

# Affichage
st.subheader(f"Résultats : {len(df_affichage)} lignes")
st.dataframe(df_affichage)

# Assurons-nous que la colonne Date est bien en datetime
df_filtré["Date"] = pd.to_datetime(df_filtré["Date"], format="%d/%m/%Y")

# On définit la plage de dates complète (du min au max de ton filtre)
all_dates = pd.date_range(df_filtré["Date"].min(), df_filtré["Date"].max(), freq="D")
df_all = pd.DataFrame({"Date": all_dates})

# Moyenne par date
df_moyenne = df_filtré.groupby("Date", as_index=False)["Charge"].mean()

# Jointure pour inclure toutes les dates (remplit NaN par 0)
df_plot = df_all.merge(df_moyenne, on="Date", how="left").fillna(0)

# Ajout du jour de la semaine en français + format
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
    title="Évolution de la charge moyenne (avec jours)"
)

# Inclinaison des labels en X
fig.update_layout(
    xaxis=dict(tickangle=-45)  # -45° pour lisibilité
)

st.plotly_chart(fig, use_container_width=True)