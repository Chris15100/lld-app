import streamlit as st
import base64
import pandas as pd
import matplotlib.pyplot as plt

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

# 1re ligne : Nom du joueur, Date
col1, col2 = st.columns(2)

with col1:
    joueurs = df['Nom du joueur'].dropna().unique().tolist()
    filtre_joueur = st.multiselect("Nom du joueur", sorted(joueurs))

with col2:
    dates = df['Date'].dropna().sort_values().unique().tolist()
    filtre_date = st.selectbox("Date", [""] + [d.strftime("%d/%m/%Y") for d in dates])

# Application des filtres
df_filtré = df.copy()

if filtre_joueur:
    df_filtré = df_filtré[df_filtré['Nom du joueur'].isin(filtre_joueur)]

if filtre_date:
    filtre_date_dt = pd.to_datetime(filtre_date, format="%d/%m/%Y")
    df_filtré = df_filtré[df_filtré['Date'] == filtre_date_dt]

# Préparer l'affichage final (dates formatées)
df_affichage = df_filtré.copy()
df_affichage["Date"] = df_affichage["Date"].dt.strftime("%d/%m/%Y")

# Affichage
st.subheader(f"Résultats : {len(df_affichage)} lignes")
st.dataframe(df_affichage)

# On calcule la moyenne de la charge par date
df_moyenne = df_filtre.groupby("Date", as_index=False)["Charge"].mean()

# Création du graphique
fig, ax = plt.subplots()
ax.bar(df_moyenne["Date"].dt.strftime("%d/%m/%Y"), df_moyenne["Charge"])
ax.set_xlabel("Date")
ax.set_ylabel("Charge moyenne")
ax.set_title("Évolution de la charge moyenne")

# Affichage dans Streamlit
st.pyplot(fig)