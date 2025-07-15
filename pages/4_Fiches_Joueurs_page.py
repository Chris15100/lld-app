import streamlit as st
import pandas as pd
import os
import plotly.express as px
import base64

# --- Configuration des dossiers (à adapter selon ta structure) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PHOTOS_DIR = os.path.join(BASE_DIR, "Photos joueurs")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# --- Fonction pour convertir une image en base64 ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        st.warning(f"⚠️ Image non trouvée : {bin_file}")
        return None

# --- Affichage du logo fixé en haut à droite ---
image_path = os.path.join(IMAGES_DIR, "Doc1-1.png")
img_base64 = get_base64_of_bin_file(image_path)

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

# --- Titre principal ---
st.title("Fiches Joueurs")

# --- Chargement de la fiche joueur ---
try:
    fichier_fiche = os.path.join(DATA_DIR, "Informations joueurs.xlsx")
    df_fiche_joueur = pd.read_excel(fichier_fiche)
    df_fiche_joueur.columns = df_fiche_joueur.columns.str.strip()
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier Informations joueurs.xlsx : {e}")
    st.stop()

# Conversion date de naissance
if 'Date de naissance' in df_fiche_joueur.columns:
    df_fiche_joueur['Date de naissance'] = pd.to_datetime(df_fiche_joueur['Date de naissance'], errors='coerce')

# --- Sélection du joueur ---
joueurs = df_fiche_joueur['Nom du joueur'].dropna().unique().tolist()
joueurs.sort()
joueur_choisi = st.selectbox("Sélectionner un joueur", joueurs)

# Filtrage joueur
df_joueur = df_fiche_joueur[df_fiche_joueur['Nom du joueur'] == joueur_choisi]

# --- Affichage photo + infos ---
col1, col2 = st.columns([1, 2])

with col1:
    image_trouvee = False
    for ext in ['.jpg', '.jpeg', '.png']:
        chemin_image = os.path.join(PHOTOS_DIR, joueur_choisi + ext)
        if os.path.isfile(chemin_image):
            st.image(chemin_image, caption=joueur_choisi, width=200)
            image_trouvee = True
            break
    if not image_trouvee:
        st.warning("📸 Aucune image trouvée.")

with col2:
    st.subheader(f"Informations sur {joueur_choisi}")
    colonnes_a_afficher = ['Poste', 'Date de naissance', 'Taille', 'Poids', 'Nationalité']
    for col in colonnes_a_afficher:
        if col in df_joueur.columns:
            valeur = df_joueur[col].values[0]
            if col == 'Date de naissance' and pd.notnull(valeur):
                valeur = pd.to_datetime(valeur).strftime('%d/%m/%Y')
            st.write(f"**{col} :** {valeur}")

# --- Chargement des stats Temps de jeu ---
try:
    fichier_stats = os.path.join(DATA_DIR, "Temps de jeu.xlsx")
    df_stats_joueur = pd.read_excel(fichier_stats)
    df_stats_joueur.columns = df_stats_joueur.columns.str.strip()
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier Temps de jeu.xlsx : {e}")
    st.stop()

df_stats_filtré = df_stats_joueur[df_stats_joueur['Nom du joueur'] == joueur_choisi]

st.subheader("Temps de jeu")

if not df_stats_filtré.empty:
    colonnes_a_afficher = [
        'Temps de jeu Total (min)',
        'Temps de jeu N3 (min)',
        'Temps de jeu CDF (min)',
        'Temps de jeu Matchs Amicaux (min)',
        'Temps de jeu Réserve (min)'
    ]
    
    df_leg = df_stats_filtré[colonnes_a_afficher].copy()

    header = "| " + " | ".join(colonnes_a_afficher) + " |"
    separator = "| " + " | ".join(["---"] * len(colonnes_a_afficher)) + " |"
    rows = [
        "| " + " | ".join(str(int(x)) if isinstance(x, (int, float)) and x == int(x) else str(x) for x in row) + " |"
        for row in df_leg.values
    ]
    tableau_md = "\n".join([header, separator] + rows)
    st.markdown(tableau_md)

    totaux = df_leg.sum()
    labels = ['N3', 'CDF', 'Matchs Amicaux', 'Réserve']
    values = [
        totaux['Temps de jeu N3 (min)'],
        totaux['Temps de jeu CDF (min)'],
        totaux['Temps de jeu Matchs Amicaux (min)'],
        totaux['Temps de jeu Réserve (min)']
    ]

    fig = px.pie(
        names=labels,
        values=values,
        title="Répartition Temps de jeu",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# --- Présences Entraînement ---
try:
    fichier_presences = os.path.join(DATA_DIR, "Présences.xlsx")
    df_presences_joueur = pd.read_excel(fichier_presences)
    df_presences_joueur.columns = df_presences_joueur.columns.str.strip()
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier Présences.xlsx : {e}")
    st.stop()

st.subheader("Présences Entraînement")

df_presence_filtre = df_presences_joueur[df_presences_joueur['Nom du joueur'] == joueur_choisi]

if not df_presence_filtre.empty:
    colonnes_a_afficher = [
        'Nombre entrainements total',
        'Présences',
        'Absences',
        'Blessures',
        'Malade',
        'Réserve',
        'Sélections'
    ]
    df_leg = df_presence_filtre[colonnes_a_afficher].copy()
    header = "| " + " | ".join(colonnes_a_afficher) + " |"
    separator = "| " + " | ".join(["---"] * len(colonnes_a_afficher)) + " |"
    rows = [
        "| " + " | ".join(str(int(x)) if isinstance(x, (int, float)) and x == int(x) else str(x) for x in row) + " |"
        for row in df_leg.values
    ]
    tableau_md = "\n".join([header, separator] + rows)
    st.markdown(tableau_md)

    totaux = df_leg.sum()
    labels = ['Présences', 'Absences', 'Blessures', 'Malade', 'Réserve', 'Sélections']
    values = [
        totaux['Présences'],
        totaux['Absences'],
        totaux['Blessures'],
        totaux['Malade'],
        totaux['Réserve'],
        totaux['Sélections']
    ]
    fig = px.pie(
        names=labels,
        values=values,
        title="Répartition des présences",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# --- Poids ---

try:
    fichier_poids = os.path.join(DATA_DIR, "Poids-Masse grasse.xlsx")
    df_PoidsMG_joueur = pd.read_excel(fichier_poids)
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier Poids-Masse grasse.xlsx : {e}")
    st.stop()

st.subheader("Poids")

df_PoidsMG_filtré = df_PoidsMG_joueur[df_PoidsMG_joueur['Nom du joueur'] == joueur_choisi]

if not df_PoidsMG_filtré.empty:
    colonnes_a_afficher = ['Date', 'Poids (en kg)']

    if all(col in df_PoidsMG_filtré.columns for col in colonnes_a_afficher):
        df_leg = df_PoidsMG_filtré[colonnes_a_afficher].copy()
        df_leg['Date'] = pd.to_datetime(df_leg['Date'])
        df_leg = df_leg.sort_values('Date')
        df_leg['Date affichée'] = df_leg['Date'].dt.strftime("%d/%m/%Y")

        df_leg_affichage = df_leg[['Date affichée', 'Poids (en kg)']]
        header = "| Date | Poids (en kg) |"
        separator = "|---|---|"
        rows = [f"| {row[0]} | {row[1]} |" for row in df_leg_affichage.values]
        st.markdown("\n".join([header, separator] + rows))

        fig = px.line(
            df_leg,
            x="Date affichée",
            y="Poids (en kg)",
            title="Évolution du poids",
            markers=True,
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Poids (en kg)")
        st.plotly_chart(fig)
    else:
        st.warning("⚠️ Colonnes 'Date' ou 'Poids (en kg)' manquantes dans le fichier.")
else:
    st.info("ℹ️ Aucune donnée de poids disponible pour ce joueur.")

# --- Masse Grasse ---

st.subheader("Masse Grasse")

df_PoidsMG_filtré = df_PoidsMG_joueur[df_PoidsMG_joueur['Nom du joueur'] == joueur_choisi]

if not df_PoidsMG_filtré.empty:
    colonnes_a_afficher = ['Date', 'MG (%)']

    if all(col in df_PoidsMG_filtré.columns for col in colonnes_a_afficher):
        df_leg = df_PoidsMG_filtré[colonnes_a_afficher].copy()
        df_leg['Date'] = pd.to_datetime(df_leg['Date'])
        df_leg = df_leg.sort_values('Date')
        df_leg['Date affichée'] = df_leg['Date'].dt.strftime("%d/%m/%Y")

        df_leg['MG (%)'] = pd.to_numeric(df_leg['MG (%)'], errors='coerce')
        if df_leg['MG (%)'].max() <= 1:
            df_leg['MG (%)'] = df_leg['MG (%)'] * 100

        df_leg['MG affichée'] = df_leg['MG (%)'].map(lambda x: f"{x:.1f} %" if pd.notnull(x) else "—")

        df_leg_affichage = df_leg[['Date affichée', 'MG affichée']]
        header = "| Date | Masse grasse (%) |"
        separator = "|---|---|"
        rows = [f"| {row[0]} | {row[1]} |" for row in df_leg_affichage.values]
        st.markdown("\n".join([header, separator] + rows))

        fig = px.line(
            df_leg,
            x='Date affichée',
            y='MG (%)',
            title="Évolution de la masse grasse",
            markers=True
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Masse grasse (%)")
        st.plotly_chart(fig)
    else:
        st.warning("⚠️ Colonnes 'Date' ou 'MG (%)' manquantes dans le fichier.")
else:
    st.info("ℹ️ Aucune donnée de masse grasse disponible pour ce joueur.")
