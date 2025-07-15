import streamlit as st
import pandas as pd
import os
import plotly.express as px
import base64

# Dossier base du script
BASE_DIR = os.path.dirname(__file__)

# Fonction pour charger image en base64 (logo)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Logo en haut à droite
image_path = os.path.join(BASE_DIR, "images", "Doc1-1.png")
if os.path.isfile(image_path):
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
else:
    st.warning(f"Logo non trouvé : {image_path}")

st.title("Fiches Joueurs")

data_dir = os.path.join(BASE_DIR, "data")

# --- Chargement données Fiche Joueur ---
fiche_joueur_path = os.path.join(data_dir, "Informations joueurs.xlsx")
try:
    df_fiche_joueur = pd.read_excel(fiche_joueur_path)
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier Informations joueurs.xlsx : {e}")
    st.stop()

df_fiche_joueur.columns = df_fiche_joueur.columns.str.strip()

if 'Date de naissance' in df_fiche_joueur.columns:
    df_fiche_joueur['Date de naissance'] = pd.to_datetime(df_fiche_joueur['Date de naissance'], errors='coerce')

joueurs = df_fiche_joueur['Nom du joueur'].dropna().unique().tolist()
joueurs.sort()

joueur_choisi = st.selectbox("Sélectionner un joueur", joueurs)

df_joueur = df_fiche_joueur[df_fiche_joueur['Nom du joueur'] == joueur_choisi]

col1, col2 = st.columns([1, 2])

with col1:
    chemin_photos = os.path.join(BASE_DIR, "Photos joueurs")
    image_trouvee = False
    for ext in ['.jpg', '.jpeg', '.png']:
        chemin_image = os.path.join(chemin_photos, joueur_choisi + ext)
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

# --- Temps de jeu ---
stats_path = os.path.join(data_dir, "Temps de jeu.xlsx")
try:
    df_stats_joueur = pd.read_excel(stats_path)
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier Temps de jeu.xlsx : {e}")
    st.stop()

df_stats_joueur.columns = df_stats_joueur.columns.str.strip()
df_stats_filtré = df_stats_joueur[df_stats_joueur['Nom du joueur'] == joueur_choisi]

st.subheader("Temps de jeu")

if not df_stats_filtré.empty:
    colonnes_temps = [
        'Temps de jeu Total (min)',
        'Temps de jeu N3 (min)',
        'Temps de jeu CDF (min)',
        'Temps de jeu Matchs Amicaux (min)',
        'Temps de jeu Réserve (min)'
    ]

    df_leg = df_stats_filtré[colonnes_temps].copy()

    header = "| " + " | ".join(colonnes_temps) + " |"
    separator = "| " + " | ".join(["---"] * len(colonnes_temps)) + " |"
    rows = [
        "| " + " | ".join(str(int(x)) if isinstance(x, (int, float)) and x == int(x) else str(x) for x in row) + " |"
        for row in df_leg.values
    ]

    st.markdown("\n".join([header, separator] + rows))

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
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# --- Détails matchs ---
st.subheader("Détails matchs")

if not df_stats_filtré.empty:
    colonnes_matchs = [
        'Nombre de matchs Total',
        'Nombre de Titularisation Totale',
        'Entrée en jeu Total',
        'Nombre matchs N3',
        'Nombre de Titularisation N3',
        'Entrée en jeu N3',
        'Nombre matchs CDF',
        'Nombre de Titularisation CDF',
        'Entrée en jeu CDF',
        'Nombre matchs Réserve',
        'Nombre matchs amicaux'
    ]

    df_leg = df_stats_filtré[colonnes_matchs].copy()

    header = "| " + " | ".join(colonnes_matchs) + " |"
    separator = "| " + " | ".join(["---"] * len(colonnes_matchs)) + " |"
    rows = [
        "| " + " | ".join(str(int(x)) if isinstance(x, (int, float)) and x == int(x) else str(x) for x in row) + " |"
        for row in df_leg.values
    ]

    st.markdown("\n".join([header, separator] + rows))
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# --- Graphs détails matchs ---
if not df_stats_filtré.empty:
    col1, col2 = st.columns(2)

    with col1:
        colonnes_cam1 = [
            'Nombre de matchs Total',
            'Nombre matchs N3',
            'Nombre matchs CDF',
            'Nombre matchs amicaux',
            'Nombre matchs Réserve'
        ]

        df_leg = df_stats_filtré[colonnes_cam1].copy()
        totaux = df_leg.sum()
        labels = ['N3', 'CDF', 'Matchs Amicaux', 'Réserve']
        values = [
            totaux['Nombre matchs N3'],
            totaux['Nombre matchs CDF'],
            totaux['Nombre matchs amicaux'],
            totaux['Nombre matchs Réserve']
        ]

        fig = px.pie(
            names=labels,
            values=values,
            title="Matchs Total",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        colonnes_cam2 = [
            'Nombre matchs N3',
            'Nombre de Titularisation N3',
            'Entrée en jeu N3',
            'Non entrée en jeu N3',
            'Hors groupe N3'
        ]

        df_leg = df_stats_filtré[colonnes_cam2].copy()
        totaux = df_leg.sum()
        labels = ['Titularisation', 'Entrée en jeu', 'Non entrée en jeu', 'Hors groupe']
        values = [
            totaux['Nombre de Titularisation N3'],
            totaux['Entrée en jeu N3'],
            totaux['Non entrée en jeu N3'],
            totaux['Hors groupe N3']
        ]

        fig = px.pie(
            names=labels,
            values=values,
            title="N3",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

if not df_stats_filtré.empty:
    col1, col2 = st.columns(2)

    with col1:
        colonnes_cam3 = [
            'Nombre matchs CDF',
            'Nombre de Titularisation CDF',
            'Entrée en jeu CDF',
            'Non entrée en jeu CDF',
            'Hors groupe CDF'
        ]

        df_leg = df_stats_filtré[colonnes_cam3].copy()
        totaux = df_leg.sum()
        labels = ['Titularisation', 'Entrée en jeu', 'Non entrée en jeu', 'Hors groupe']
        values = [
            totaux['Nombre de Titularisation CDF'],
            totaux['Entrée en jeu CDF'],
            totaux['Non entrée en jeu CDF'],
            totaux['Hors groupe CDF']
        ]

        fig = px.pie(
            names=labels,
            values=values,
            title="CDF",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        colonnes_cam4 = [
            'Nombre matchs Réserve',
            'Nombre de Titularisation Réserve',
            'Entrée en jeu Réserve',
            'Non entrée en jeu Réserve',
            'Hors groupe Réserve'
        ]

        df_leg = df_stats_filtré[colonnes_cam4].copy()
        totaux = df_leg.sum()
        labels = ['Titularisation', 'Entrée en jeu', 'Non entrée en jeu', 'Hors groupe']
        values = [
            totaux['Nombre de Titularisation Réserve'],
            totaux['Entrée en jeu Réserve'],
            totaux['Non entrée en jeu Réserve'],
            totaux['Hors groupe Réserve']
        ]

        fig = px.pie(
            names=labels,
            values=values,
            title="Réserve",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# --- Statistiques matchs ---
st.subheader("Statistiques matchs")

if not df_stats_filtré.empty:
    colonnes_stats = [
        'Buts Total',
        'Passes D Total',
        'Buts Ttes compét confondues',
        'Passes D Ttes compét confondues',
        'Buts N3',
        'Passes D N3',
        'Buts CDF',
        'Passes D CDF',
        'Buts Matchs Amicaux',
        'Passes D Matchs Amicaux',
        'Buts Réserve',
        'Passes D Réserve'
    ]

    df_leg = df_stats_filtré[colonnes_stats].copy()

    header = "| " + " | ".join(colonnes_stats) + " |"
    separator = "| " + " | ".join(["---"] * len(colonnes_stats)) + " |"
    rows = [
        "| " + " | ".join(str(int(x)) if isinstance(x, (int, float)) and x == int(x) else str(x) for x in row) + " |"
        for row in df_leg.values
    ]

    st.markdown("\n".join([header, separator] + rows))
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# --- Graphs Statistiques matchs ---
if not df_stats_filtré.empty:
    col1, col2 = st.columns(2)

    with col1:
        colonnes_buts = [
            'Buts Ttes compét confondues',
            'Buts N3',
            'Buts CDF',
            'Buts Réserve'
        ]

        df_leg = df_stats_filtré[colonnes_buts].copy()
        totaux = df_leg.sum()
        labels = ['N3', 'CDF', 'Réserve']
        values = [
            totaux['Buts N3'],
            totaux['Buts CDF'],
            totaux['Buts Réserve'],
        ]

        fig = px.pie(
            names=labels,
            values=values,
            title="Buts Ttes compét confondues",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        colonnes_passes = [
            'Passes D Ttes compét confondues',
            'Passes D N3',
            'Passes D CDF',
            'Passes D Réserve'
        ]

        df_leg = df_stats_filtré[colonnes_passes].copy()
        totaux = df_leg.sum()
        labels = ['N3', 'CDF', 'Réserve']
        values = [
            totaux['Passes D N3'],
            totaux['Passes D CDF'],
            totaux['Passes D Réserve'],
        ]

        fig = px.pie(
            names=labels,
            values=values,
            title="Passes D Ttes compét confondues",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# --- Présences Entraînement ---
présences_path = os.path.join(data_dir, "Présences.xlsx")
try:
    df_présences_joueur = pd.read_excel(présences_path)
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier Présences.xlsx : {e}")
    st.stop()

df_présences_joueur.columns = df_présences_joueur.columns.str.strip()
df_présence_filtré = df_présences_joueur[df_présences_joueur['Nom du joueur'] == joueur_choisi]

st.subheader("Présences Entraînement")

if not df_présence_filtré.empty:
    colonnes_présences = [
        'Nombre entrainements total',
        'Présences',
        'Absences',
        'Blessures',
        'Malade',
        'Réserve',
        'Sélections'
    ]

    df_leg = df_présence_filtré[colonnes_présences].copy()

    header = "| " + " | ".join(colonnes_présences) + " |"
    separator = "| " + " | ".join(["---"] * len(colonnes_présences)) + " |"
    rows = [
        "| " + " | ".join(str(int(x)) if isinstance(x, (int, float)) and x == int(x) else str(x) for x in row) + " |"
        for row in df_leg.values
    ]

    st.markdown("\n".join([header, separator] + rows))
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# Graph Présences
if not df_présence_filtré.empty:
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
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# --- Poids et Masse Grasse ---
poids_path = os.path.join(data_dir, "Poids-Masse grasse.xlsx")
try:
    df_PoidsMG_joueur = pd.read_excel(poids_path)
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier Poids-Masse grasse.xlsx : {e}")
    st.stop()

st.subheader("Poids")

df_PoidsMG_filtré = df_PoidsMG_joueur[df_PoidsMG_joueur['Nom du joueur'] == joueur_choisi]

if not df_PoidsMG_filtré.empty:
    colonnes_poids = ['Date', 'Poids (en kg)']

    if all(col in df_PoidsMG_filtré.columns for col in colonnes_poids):
        df_leg = df_PoidsMG_filtré[colonnes_poids].copy()
        df_leg['Date'] = pd.to_datetime(df_leg['Date'])
        df_leg = df_leg.sort_values('Date')
        df_leg['Date affichée'] = df_leg['Date'].dt.strftime("%d/%m/%Y")

        # Tableau Markdown
        header = "| Date | Poids (en kg) |"
        separator = "|---|---|"
        rows = [f"| {row[0]} | {row[1]} |" for row in df_leg[['Date affichée', 'Poids (en kg)']].values]
        st.markdown("\n".join([header, separator] + rows))

        # Graph évolution poids
        fig = px.line(df_leg, x='Date', y='Poids (en kg)', title="Évolution du poids")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Colonnes Poids non trouvées dans le fichier.")
else:
    st.info("ℹ️ Pas de données de poids pour ce joueur.")

# Masse grasse
st.subheader("Masse Grasse")

if not df_PoidsMG_filtré.empty:
    colonnes_masse = ['Date', 'Masse grasse (%)']

    if all(col in df_PoidsMG_filtré.columns for col in colonnes_masse):
        df_leg = df_PoidsMG_filtré[colonnes_masse].copy()
        df_leg['Date'] = pd.to_datetime(df_leg['Date'])
        df_leg = df_leg.sort_values('Date')
        df_leg['Date affichée'] = df_leg['Date'].dt.strftime("%d/%m/%Y")

        header = "| Date | Masse grasse (%) |"
        separator = "|---|---|"
        rows = [f"| {row[0]} | {row[1]} |" for row in df_leg[['Date affichée', 'Masse grasse (%)']].values]
        st.markdown("\n".join([header, separator] + rows))

        fig = px.line(df_leg, x='Date', y='Masse grasse (%)', title="Évolution masse grasse")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Colonnes Masse grasse non trouvées dans le fichier.")
else:
    st.info("ℹ️ Pas de données de masse grasse pour ce joueur.")
