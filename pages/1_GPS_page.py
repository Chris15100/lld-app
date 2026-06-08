import streamlit as st
import pandas as pd
import base64
import os

# Saison sélectionnée
saison = st.session_state.get("saison", "2026-2027")

# Chemins
image_path = "images/logo.png"
excel_path = f"data/{saison}/DonneesGPSPropres.xlsx" 

# ✅ Fonction avec vérification
def get_base64_of_bin_file(bin_file):
    if not os.path.exists(bin_file):
        st.error(f"❌ Fichier introuvable : {bin_file}")
        return ""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# ✅ Lecture image
img_base64 = get_base64_of_bin_file(image_path)

# ✅ Affichage logo si trouvé
if img_base64:
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

st.title("GPS")

# ✅ Lecture du fichier Excel
if not os.path.exists(excel_path):
    st.error(f"❌ Fichier Excel introuvable : {excel_path}")
    st.stop()

df = pd.read_excel(excel_path)

# 🔹 Conversion et formatage des dates
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Date_str"] = df["Date"].dt.strftime("%d/%m/%Y")  # format JJ/MM/AAAA

# 🔹 Filtres
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

col4, col5, col6 = st.columns(3)
with col4:
    mds = df['MD'].dropna().unique().tolist()
    filtre_md = st.selectbox("MD", [""] + sorted(mds))

with col5:
    postes = df['Poste'].dropna().unique().tolist()
    filtre_poste = st.selectbox("Poste", [""] + sorted(postes))

with col6:
   dates = df['Date'].dropna().sort_values().unique().tolist()
   filtre_date = st.selectbox("Date", [""] + [d.strftime("%d/%m/%Y") for d in dates])


# 🔹 Application des filtres
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
    filtre_date_dt = pd.to_datetime(filtre_date, format="%d/%m/%Y")
    df_filtré = df_filtré[df_filtré['Date'] == filtre_date_dt]

# 🔹 Préparation affichage final
df_affichage = df_filtré.copy()
df_affichage["Date"] = df_affichage["Date"].dt.strftime("%d/%m/%Y")

# 🔹 Affichage
st.subheader("")
st.write(f"{len(df_affichage)} lignes affichées")
st.dataframe(df_affichage)


