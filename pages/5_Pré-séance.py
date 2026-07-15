import streamlit as st
import base64
import pandas as pd

# Logo
image_path = "images/logo.png"

def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
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
    <img src="data:image/png;base64,{img_base64}">
</div>
"""

st.markdown(html_code, unsafe_allow_html=True)

st.title("Pré-séance")

# Saison
saison = st.session_state.get("saison", "2026-2027")

# Lecture du fichier
df = pd.read_excel(f"data/{saison}/Pré-séance.xlsx")

# Conversion de la date
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# -------------------
# FILTRES
# -------------------

col1, col2 = st.columns(2)

with col1:
    joueurs = sorted(df["Nom du joueur"].dropna().unique())
    filtre_joueur = st.multiselect(
        "Nom du joueur",
        joueurs
    )

with col2:
    dates = sorted(df["Date"].dropna().unique())
    filtre_date = st.multiselect(
        "Date",
        [d.strftime("%d/%m/%Y") for d in dates]
    )

# -------------------
# APPLICATION DES FILTRES
# -------------------

df_filtre = df.copy()

if filtre_joueur:
    df_filtre = df_filtre[df_filtre["Nom du joueur"].isin(filtre_joueur)]

if filtre_date:
    dates_selectionnees = pd.to_datetime(filtre_date, format="%d/%m/%Y")
    df_filtre = df_filtre[df_filtre["Date"].isin(dates_selectionnees)]

# Format de la date pour l'affichage
df_filtre["Date"] = df_filtre["Date"].dt.strftime("%d/%m/%Y")

# -------------------
# TABLEAU
# -------------------

st.dataframe(
    df_filtre,
    use_container_width=True,
    hide_index=True
)