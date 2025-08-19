import streamlit as st
import pandas as pd
import base64
import os

USERNAME = "coach"
PASSWORD = "lld6900920252026"

# Initialisation de la variable session_state 'authenticated'
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Interface utilisateur si connecté
if st.session_state["authenticated"]:
    with st.sidebar:
        st.markdown(f"✅ Connecté en tant que **{USERNAME}**")
        if st.button("🔓 Se déconnecter"):
            st.session_state["authenticated"] = False
            st.rerun()
else:
    # Interface de connexion
    st.title("🔐 Connexion sécurisée")
    username_input = st.text_input("Nom d'utilisateur")
    password_input = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if username_input == USERNAME and password_input == PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Connexion réussie ✅")
            st.rerun()
        else:
            st.error("Identifiants incorrects")
    st.stop()

# Configuration de la page
st.set_page_config(
    page_title="AMS",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': "https://www.formafoot.fr"
    }
)

# Chargement et affichage du logo
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

st.title("GPS Brut")

# CHEMIN RELATIF : place ton fichier Excel dans un dossier 'data' dans ton repo
data_path = os.path.join("data", "DonneesGPSPropres.xlsx")

# Chargement du fichier Excel
df = pd.read_excel(data_path)

# ✅ Conversion de la colonne Date au format datetime
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# ✅ Création d'une colonne texte formatée pour l'affichage
df["Date_str"] = df["Date"].dt.strftime("%d/%m/%Y")

# 1re ligne : Nom du joueur, Type, Période
col1, col2, col3 = st.columns(3)

with col1:
    joueurs = df['Nom du joueur'].dropna().unique().tolist()
    filtre_joueur = st.multiselect("Nom du joueur", sorted(joueurs))

with col2:
    types = df['Type'].dropna().unique().tolist()
    filtre_type = st.selectbox("Type", [""] + sorted(types))

with col3:
    periodes = df['Période'].dropna().unique().tolist()
    filtre_periode = st.selectbox("Période", [""] + sorted(periodes))

# 2e ligne : MD, Poste, Date
col4, col5, col6 = st.columns(3)

with col4:
    mds = df['MD'].dropna().unique().tolist()
    filtre_md = st.selectbox("MD", [""] + sorted(mds))

with col5:
    postes = df['Poste'].dropna().unique().tolist()
    filtre_poste = st.selectbox("Poste", [""] + sorted(postes))

with col6:
    dates = df['Date_str'].dropna().unique().tolist()
    filtre_date = st.selectbox("Date", [""] + sorted(dates))

# Application des filtres
df_filtré = df.copy()

if filtre_joueur:
    df_filtré = df_filtré[df_filtré['Nom du joueur'].isin(filtre_joueur)]
if filtre_type:
    df_filtré = df_filtré[df_filtré['Type'] == filtre_type]
if filtre_periode:
    df_filtré = df_filtré[df_filtré['Période'] == filtre_periode]
if filtre_md:
    df_filtré = df_filtré[df_filtré['MD'] == filtre_md]
if filtre_poste:
    df_filtré = df_filtré[df_filtré['Poste'] == filtre_poste]
if filtre_date:
    df_filtré = df_filtré[df_filtré['Date_str'] == filtre_date]

# ✅ Affichage du tableau avec la date formatée
st.subheader(f"Résultats : {len(df_filtré)} lignes")
st.dataframe(df_filtré.drop(columns=["Date"]).rename(columns={"Date_str": "Date"}))
