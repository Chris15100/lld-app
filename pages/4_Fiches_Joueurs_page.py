import streamlit as st
import pandas as pd
import os
import plotly.express as px
import base64

# Chemin vers ton image
image_path = "images/logo.png"

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


# Intro Fiche joueur



st.title("Fiches Joueurs")

# 📂 Chargement des données
df_fiche_joueur = pd.read_excel("data/Informations joueurs.xlsx")

# 🧼 Nettoyage du nom des colonnes
df_fiche_joueur.columns = df_fiche_joueur.columns.str.strip()

# 📋 Conversion de la date de naissance en datetime (si nécessaire)
if 'Date de naissance' in df_fiche_joueur.columns:
    df_fiche_joueur['Date de naissance'] = pd.to_datetime(df_fiche_joueur['Date de naissance'], errors='coerce')

# 📋 Sélection d’un joueur unique
joueurs = df_fiche_joueur['Nom du joueur'].dropna().unique().tolist()
joueurs.sort()

joueur_choisi = st.selectbox("Sélectionner un joueur", joueurs)

# 📄 Filtrage
df_joueur = df_fiche_joueur[df_fiche_joueur['Nom du joueur'] == joueur_choisi]

# 📸 Affichage en 2 colonnes : photo | infos
col1, col2 = st.columns([1, 2])

with col1:
    chemin_photos = "/Users/christophergallo/Desktop/Application perso/Photos joueurs"
    image_trouvée = False
    for ext in ['.jpg', '.jpeg', '.png']:
        chemin_image = os.path.join(chemin_photos, joueur_choisi + ext)
        if os.path.isfile(chemin_image):
            st.image(chemin_image, caption=joueur_choisi, width=200)
            image_trouvée = True
            break
    if not image_trouvée:
        st.warning("📸 Aucune image trouvée.")

with col2:
    st.subheader(f"Informations sur {joueur_choisi}")
    colonnes_a_afficher = ['Poste', 'Date de naissance', 'Taille', 'Poids', 'Nationalité']
    for col in colonnes_a_afficher:
        if col in df_joueur.columns:
            valeur = df_joueur[col].values[0]
            if col == 'Date de naissance' and pd.notnull(valeur):
                valeur = pd.to_datetime(valeur).strftime('%d/%m/%Y')  # Format personnalisé ici
            st.write(f"**{col} :** {valeur}")





# Tableau temps de jeu





# 📂 Chargement du nouveau fichier Excel
df_stats_joueur = pd.read_excel("/Users/christophergallo/Desktop/Application perso/data/Temps de jeu.xlsx", index_col=None)

# 🧼 Nettoyage des colonnes si nécessaire
df_stats_joueur.columns = df_stats_joueur.columns.str.strip()

# 📄 Filtrage sur le joueur choisi
df_stats_filtré = df_stats_joueur[df_stats_joueur['Nom du joueur'] == joueur_choisi]

st.subheader(f"Temps de jeu")

if not df_stats_filtré.empty:
    colonnes_a_afficher = [
        'Temps de jeu Total (min)',
        'Temps de jeu N3 (min)',
        'Temps de jeu CDF (min)',
        'Temps de jeu Matchs Amicaux (min)',
        'Temps de jeu Réserve (min)'
    ]
    
    df_leg = df_stats_filtré[colonnes_a_afficher].copy()

    # Construction du markdown du tableau
    header = "| " + " | ".join(colonnes_a_afficher) + " |"
    separator = "| " + " | ".join(["---"] * len(colonnes_a_afficher)) + " |"
    rows = [
        "| " + " | ".join(str(int(x)) if isinstance(x, (int, float)) and x == int(x) else str(x) for x in row) + " |"
        for row in df_leg.values
    ]

    tableau_md = "\n".join([header, separator] + rows)

    st.markdown(tableau_md)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")





# Graph Temps de jeu






if not df_stats_filtré.empty:
    colonnes_a_afficher = [
        'Temps de jeu Total (min)',
        'Temps de jeu N3 (min)',
        'Temps de jeu CDF (min)',
        'Temps de jeu Matchs Amicaux (min)',
        'Temps de jeu Réserve (min)'
    ]

    df_leg = df_stats_filtré[colonnes_a_afficher].copy()

    # Tableau Markdown
    header = "| " + " | ".join(colonnes_a_afficher) + " |"
    separator = "| " + " | ".join(["---"] * len(colonnes_a_afficher)) + " |"
    rows = [
        "| " + " | ".join(str(int(x)) if isinstance(x, (int, float)) and x == int(x) else str(x) for x in row) + " |"
        for row in df_leg.values
    ]
    tableau_md = "\n".join([header, separator] + rows)
    #st.markdown(tableau_md)

    # Calcul des totaux pour le camembert
    totaux = df_leg.sum()

    # On évite de compter "Temps de jeu Total (min)" dans le camembert si tu veux juste les composantes
    labels = ['N3', 'CDF', 'Matchs Amicaux', 'Réserve']
    values = [
        totaux['Temps de jeu N3 (min)'],
        totaux['Temps de jeu CDF (min)'],
        totaux['Temps de jeu Matchs Amicaux (min)'],
        totaux['Temps de jeu Réserve (min)']
    ]

    # Génération du camembert avec Plotly
    fig = px.pie(
        names=labels,
        values=values,
        title="",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textinfo='percent+label')

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.") 







# Tableau détail Match







st.subheader(f"Détails matchs")

if not df_stats_filtré.empty:
    colonnes_a_afficher = [
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
    
    df_leg = df_stats_filtré[colonnes_a_afficher].copy()

    # Construction du markdown du tableau
    header = "| " + " | ".join(colonnes_a_afficher) + " |"
    separator = "| " + " | ".join(["---"] * len(colonnes_a_afficher)) + " |"
    rows = [
        "| " + " | ".join(str(int(x)) if isinstance(x, (int, float)) and x == int(x) else str(x) for x in row) + " |"
        for row in df_leg.values
    ]

    tableau_md = "\n".join([header, separator] + rows)

    st.markdown(tableau_md)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")




# Graphs Détail Match






if not df_stats_filtré.empty:

    # COLONNES STREAMLIT POUR ORGANISER LES CAMEMBERTS
    col1, col2 = st.columns(2)

    # Premier camembert : répartition des matchs par type
    with col1:
        colonnes_a_afficher = [
            'Nombre de matchs Total',
            'Nombre matchs N3',
            'Nombre matchs CDF',
            'Nombre matchs amicaux',
            'Nombre matchs Réserve'
        ]

        df_leg = df_stats_filtré[colonnes_a_afficher].copy()
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

    # Deuxième camembert : statut N3
    with col2:
        colonnes_a_afficher = [
            'Nombre matchs N3',
            'Nombre de Titularisation N3',
            'Entrée en jeu N3',
            'Non entrée en jeu N3',
            'Hors groupe N3'
        ]

        df_leg = df_stats_filtré[colonnes_a_afficher].copy()
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

    # COLONNES STREAMLIT POUR ORGANISER LES CAMEMBERTS
    col1, col2 = st.columns(2)

    with col1:
        colonnes_a_afficher = [
            'Nombre matchs CDF',
            'Nombre de Titularisation CDF',
            'Entrée en jeu CDF',
            'Non entrée en jeu CDF',
            'Hors groupe CDF'
        ]

        df_leg = df_stats_filtré[colonnes_a_afficher].copy()
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
        colonnes_a_afficher = [
            'Nombre matchs Réserve',
            'Nombre de Titularisation Réserve',
            'Entrée en jeu Réserve',
            'Non entrée en jeu Réserve',
            'Hors groupe Réserve'
        ]

        df_leg = df_stats_filtré[colonnes_a_afficher].copy()
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




# Tableau Statistique Matchs



st.subheader(f"Statistiques matchs")

if not df_stats_filtré.empty:
    colonnes_a_afficher = [
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
    
    df_leg = df_stats_filtré[colonnes_a_afficher].copy()

    # Construction du markdown du tableau
    header = "| " + " | ".join(colonnes_a_afficher) + " |"
    separator = "| " + " | ".join(["---"] * len(colonnes_a_afficher)) + " |"
    rows = [
        "| " + " | ".join(str(int(x)) if isinstance(x, (int, float)) and x == int(x) else str(x) for x in row) + " |"
        for row in df_leg.values
    ]

    tableau_md = "\n".join([header, separator] + rows)

    st.markdown(tableau_md)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")





# Graph Statistique Matchs






if not df_stats_filtré.empty:

    # COLONNES STREAMLIT POUR ORGANISER LES CAMEMBERTS
    col1, col2 = st.columns(2)

    with col1:
        colonnes_a_afficher = [
            'Buts Ttes compét confondues',
            'Buts N3',
            'Buts CDF',
            'Buts Réserve'
        ]

        df_leg = df_stats_filtré[colonnes_a_afficher].copy()
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
        colonnes_a_afficher = [
            'Passes D Ttes compét confondues',
            'Passes D N3',
            'Passes D CDF',
            'Passes D Réserve'
        ]

        df_leg = df_stats_filtré[colonnes_a_afficher].copy()
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








# Présences Entrainement







# 📂 Chargement du nouveau fichier Excel
df_présences_joueur = pd.read_excel("/Users/christophergallo/Desktop/Application perso/data/Présences.xlsx", index_col=None)
df_présences_joueur.columns = df_présences_joueur.columns.str.strip()


# Tableau présences
st.subheader(f"Présences Entraînement")

df_présence_filtré = df_présences_joueur[df_présences_joueur['Nom du joueur'] == joueur_choisi]

if not df_présence_filtré.empty:
    colonnes_a_afficher = [
        'Nombre entrainements total',
        'Présences',
        'Absences',
        'Blessures',
        'Malade',
        'Réserve',
        'Sélections'
    ]
    
    df_leg = df_présence_filtré[colonnes_a_afficher].copy()

    header = "| " + " | ".join(colonnes_a_afficher) + " |"
    separator = "| " + " | ".join(["---"] * len(colonnes_a_afficher)) + " |"
    rows = [
        "| " + " | ".join(str(int(x)) if isinstance(x, (int, float)) and x == int(x) else str(x) for x in row) + " |"
        for row in df_leg.values
    ]

    tableau_md = "\n".join([header, separator] + rows)
    st.markdown(tableau_md)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")







# Graph présence






# Filtrage sur le joueur pour les présences
df_présence_filtré = df_présences_joueur[df_présences_joueur['Nom du joueur'] == joueur_choisi]

if not df_présence_filtré.empty:
    colonnes_a_afficher = [
        'Nombre entrainements total',
        'Présences',
        'Absences',
        'Blessures',
        'Malade',
        'Réserve',
        'Sélections'
    ]

    df_leg = df_présence_filtré[colonnes_a_afficher].copy()
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
        title="",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")





# Tableau et Graph Poids


# 📂 Chargement du nouveau fichier Excel
df_PoidsMG_joueur = pd.read_excel("/Users/christophergallo/Desktop/Application perso/data/Poids-Masse grasse.xlsx", index_col=None)


st.subheader("Poids")

# 🎯 Filtrage du joueur
df_PoidsMG_filtré = df_PoidsMG_joueur[df_PoidsMG_joueur['Nom du joueur'] == joueur_choisi]

if not df_PoidsMG_filtré.empty:
    colonnes_a_afficher = ['Date', 'Poids (en kg)']

    if all(col in df_PoidsMG_filtré.columns for col in colonnes_a_afficher):
        df_leg = df_PoidsMG_filtré[colonnes_a_afficher].copy()

        # ✅ Convertir Date en datetime pour le tri
        df_leg['Date'] = pd.to_datetime(df_leg['Date'])
        df_leg = df_leg.sort_values('Date')

        # ➕ Création d'une colonne "Date formatée" pour affichage
        df_leg['Date affichée'] = df_leg['Date'].dt.strftime("%d/%m/%Y")

        # 📋 Tableau Markdown
        df_leg_affichage = df_leg[['Date affichée', 'Poids (en kg)']]
        header = "| Date | Poids (en kg) |"
        separator = "|---|---|"
        rows = [f"| {row[0]} | {row[1]} |" for row in df_leg_affichage.values]
        st.markdown("\n".join([header, separator] + rows))

        # 📈 Graphique avec dates en abscisse formatées
        fig = px.line(
            df_leg,
            x="Date affichée",
            y="Poids (en kg)",
            title="",
            markers=True,
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Poids (en kg)")
        st.plotly_chart(fig)

    else:
        st.warning("⚠️ Les colonnes attendues sont absentes.")
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")







# Tableau et Graph MG



st.subheader("Masse Grasse")

# 🎯 Filtrage du joueur sélectionné
df_PoidsMG_filtré = df_PoidsMG_joueur[df_PoidsMG_joueur['Nom du joueur'] == joueur_choisi]

# 📋 Vérification et traitement
if not df_PoidsMG_filtré.empty:
    colonnes_a_afficher = ['Date', 'MG (%)']

    if all(col in df_PoidsMG_filtré.columns for col in colonnes_a_afficher):
        df_leg = df_PoidsMG_filtré[colonnes_a_afficher].copy()

        # ✅ Formatage date
        df_leg['Date'] = pd.to_datetime(df_leg['Date'])
        df_leg = df_leg.sort_values('Date')
        df_leg['Date affichée'] = df_leg['Date'].dt.strftime("%d/%m/%Y")

        # ✅ Conversion MG en pourcentage si exprimé en fraction
        df_leg['MG (%)'] = pd.to_numeric(df_leg['MG (%)'], errors='coerce')
        if df_leg['MG (%)'].max() <= 1:
            df_leg['MG (%)'] = df_leg['MG (%)'] * 100

        # ✅ Colonne formatée pour affichage dans le tableau
        df_leg['MG affichée'] = df_leg['MG (%)'].map(lambda x: f"{x:.1f} %" if pd.notnull(x) else "—")

        # 📋 Affichage tableau Markdown
        df_leg_affichage = df_leg[['Date affichée', 'MG affichée']]
        header = "| Date | Masse grasse (%) |"
        separator = "|---|---|"
        rows = [f"| {row[0]} | {row[1]} |" for row in df_leg_affichage.values]
        st.markdown("\n".join([header, separator] + rows))

        # 📈 Graphique Plotly
        fig = px.line(
            df_leg,
            x='Date affichée',
            y='MG (%)',
            title="",
            markers=True
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Masse grasse (%)")
        st.plotly_chart(fig)

    else:
        st.warning("⚠️ Les colonnes 'Date' ou 'MG (%)' sont absentes.")
else:
    st.info("ℹ️ Aucune donnée de masse grasse pour ce joueur.")
