import streamlit as st
import pandas as pd
import base64

USERNAME = "coach"
PASSWORD = "lld6900920252026"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if st.session_state["authenticated"]:
    with st.sidebar:
        st.markdown(f"✅ Connecté en tant que **{USERNAME}**")
        if st.button("🔓 Se déconnecter"):
            st.session_state["authenticated"] = False
            st.rerun()  # ✅ version corrigée
else:
    st.title("🔐 Connexion sécurisée")
    username_input = st.text_input("Nom d'utilisateur")
    password_input = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if username_input == USERNAME and password_input == PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Connexion réussie ✅")
            st.rerun()  # ✅ version corrigée
        else:
            st.error("Identifiants incorrects")
    st.stop()

st.set_page_config(
    page_title="AMS",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': "https://www.formafoot.fr"
    }
)

# Chemin vers ton image
image_path = "images/Doc1-1.png"

# Lire l'image en base64
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_base64 = get_base64_of_bin_file(image_path)

# CSS + HTML pour logo fixé en haut à droite, image en taille native
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

# Chargement du fichier Excel
df = pd.read_excel("/Users/christophergallo/Desktop/Application perso/data/Données GPS Propres.xlsx")

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
    dates = df['Date'].dropna().unique().tolist()
    filtre_date = st.selectbox("Date", [""] + sorted(dates))

# 🔹 Application des filtres sur le DataFrame
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
    df_filtré = df_filtré[df_filtré['Date'] == filtre_date]

# 🔹 Affichage
st.subheader("")
st.write(f"{len(df_filtré)}")
st.dataframe(df_filtré)
