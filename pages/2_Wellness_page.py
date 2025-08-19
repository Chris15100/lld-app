import streamlit as st
import base64
import pandas as pd

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

# 🔥 Ici on utilise df et pas excel
df = pd.read_excel("data/Wellness.xlsx")

# 1re ligne : Nom du joueur, Date
col1, col2 = st.columns(2)

with col1:
    joueurs = df['Nom du joueur'].dropna().unique().tolist()
    filtre_joueur = st.multiselect("Nom du joueur", sorted(joueurs))

with col2:
    dates = df['Date'].dropna().unique().tolist()
    filtre_date = st.selectbox("Date", [""] + sorted(dates))

# Application des filtres
df_filtré = df.copy()

if filtre_joueur:
    df_filtré = df_filtré[df_filtré['Nom du joueur'].isin(filtre_joueur)]
    
if filtre_date:
    df_filtré = df_filtré[df_filtré['Date'] == filtre_date]

# Affichage
st.subheader(f"Résultats : {len(df_filtré)} lignes")
st.dataframe(df_filtré)
