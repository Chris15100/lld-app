import streamlit as st
import pandas as pd
import os
import plotly.express as px
import base64

# Logo
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

img_base64 = get_base64_of_bin_file("images/logo.png")
html_code = f"""
<style>
.logo-top-right {{ position: fixed; top: 10px; right: 10px; z-index: 9999; max-width: 150px; }}
.logo-top-right img {{ width: 100%; height: auto; display: block; }}
</style>
<div class="logo-top-right"><img src="data:image/png;base64,{img_base64}" /></div>
"""
st.markdown(html_code, unsafe_allow_html=True)

st.title("Fiches Joueurs")

# Chargement des données
df_fiche_joueur = pd.read_excel("data/Informations joueurs.xlsx")
df_fiche_joueur.columns = df_fiche_joueur.columns.str.strip()
if 'Date de naissance' in df_fiche_joueur.columns:
    df_fiche_joueur['Date de naissance'] = pd.to_datetime(df_fiche_joueur['Date de naissance'], errors='coerce')

joueurs = sorted(df_fiche_joueur['Nom du joueur'].dropna().unique().tolist())
joueur_choisi = st.selectbox("Sélectionner un joueur", joueurs)
df_joueur = df_fiche_joueur[df_fiche_joueur['Nom du joueur'] == joueur_choisi]

col1, col2 = st.columns([1, 2])
with col1:
    chemin_photos = "Photos_joueurs"
    image_trouvee = False

    # Debug : afficher les fichiers présents
    fichiers_dispo = os.listdir(chemin_photos)
    st.write("📁 Fichiers présents :", fichiers_dispo)

    for ext in ['.jpg', '.jpeg', '.png']:
        chemin_img = os.path.join(chemin_photos, joueur_choisi + ext)
        if os.path.isfile(chemin_img):
            st.image(chemin_img, caption=joueur_choisi, width=200)
            image_trouvee = True
            break

    if not image_trouvee:
        st.warning(f"📸 Aucune image trouvée pour : {joueur_choisi}")
        st.text(f"Chemin testé : {chemin_img}")
with col2:
    st.subheader(f"Informations sur {joueur_choisi}")
    for col in ['Poste', 'Date de naissance', 'Taille', 'Poids', 'Nationalité']:
        if col in df_joueur.columns:
            val = df_joueur[col].values[0]
            if col == 'Date de naissance' and pd.notnull(val):
                val = pd.to_datetime(val).strftime('%d/%m/%Y')
            st.write(f"**{col} :** {val}")

# Temps de jeu
df_stats = pd.read_excel("data/Temps de jeu.xlsx")
df_stats.columns = df_stats.columns.str.strip()
df_stats_f = df_stats[df_stats['Nom du joueur'] == joueur_choisi]

st.subheader("Temps de jeu")
if not df_stats_f.empty:
    cols = [
        'Temps de jeu Total (min)',
        'Temps de jeu N3 (min)',
        'Temps de jeu CDF (min)',
        'Temps de jeu Matchs Amicaux (min)',
        'Temps de jeu Réserve (min)'
    ]
    df_leg = df_stats_f[cols].copy()
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"]*len(cols)) + " |"
    rows = ["| " + " | ".join(str(int(x)) if isinstance(x,(int,float)) and x==int(x) else str(x) for x in r) + " |" for r in df_leg.values]
    st.markdown("\n".join([header, sep] + rows))
    tot = df_leg.sum()
    labels = ['N3','CDF','Matchs Amicaux','Réserve']
    values = [tot[c] for c in cols[1:]]
    fig = px.pie(names=labels, values=values, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# Détail des matchs
st.subheader("Détails matchs")
if not df_stats_f.empty:
    cols = [
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
    df_leg = df_stats_f[cols].copy()
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"]*len(cols)) + " |"
    rows = ["| " + " | ".join(str(int(x)) if isinstance(x,(int,float)) and x==int(x) else str(x) for x in r)+ " |" for r in df_leg.values]
    st.markdown("\n".join([header, sep] + rows))
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# Graphs supplémentaires par type...
# (similaire aux blocs précédents, en utilisant df_stats_f)

# Présences entraînements
df_pres = pd.read_excel("data/Présences.xlsx")
df_pres.columns = df_pres.columns.str.strip()
pres_f = df_pres[df_pres['Nom du joueur'] == joueur_choisi]
st.subheader("Présences Entraînement")
if not pres_f.empty:
    cols = ['Nombre entrainements total','Présences','Absences','Blessures','Malade','Réserve','Sélections']
    df_leg = pres_f[cols].copy()
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"]*len(cols)) + " |"
    rows = ["| " + " | ".join(str(int(x)) if isinstance(x,(int,float)) and x==int(x) else str(x) for x in r)+ " |" for r in df_leg.values]
    st.markdown("\n".join([header, sep] + rows))
    tot = df_leg.sum()
    labels = cols[1:]
    values = [tot[c] for c in labels]
    fig = px.pie(names=labels, values=values, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# Poids & Masse Grasse
df_poids = pd.read_excel("data/Poids-Masse grasse.xlsx")
df_leg_p = df_poids[df_poids['Nom du joueur'] == joueur_choisi]

if not df_leg_p.empty:
    st.subheader("Poids")
    if all(c in df_leg_p.columns for c in ['Date','Poids (en kg)']):
        df_l = df_leg_p[['Date','Poids (en kg)']].copy()
        df_l['Date'] = pd.to_datetime(df_l['Date'])
        df_l = df_l.sort_values('Date')
        df_l['Date affichée'] = df_l['Date'].dt.strftime('%d/%m/%Y')
        st.markdown("\n".join([
            "| Date | Poids (en kg) |",
            "|---|---|"
        ] + [f"| {row[0]} | {row[1]} |" for row in df_l[['Date affichée','Poids (en kg)']].values]))
        fig = px.line(df_l, x='Date affichée', y='Poids (en kg)', title="", markers=True)
        fig.update_layout(xaxis_title="Date", yaxis_title="Poids (en kg)")
        st.plotly_chart(fig)
    else:
        st.warning("⚠️ Colonnes poids manquantes")
else:
    st.info("ℹ️ Aucune donnée de poids")

# Masse Grasse
if not df_leg_p.empty:
    st.subheader("Masse Grasse")
    if all(c in df_leg_p.columns for c in ['Date','MG (%)']):
        df_l = df_leg_p[['Date','MG (%)']].copy()
        df_l['Date'] = pd.to_datetime(df_l['Date'])
        df_l = df_l.sort_values('Date')
        df_l['Date affichée'] = df_l['Date'].dt.strftime('%d/%m/%Y')
        df_l['MG (%)'] = pd.to_numeric(df_l['MG (%)'], errors='coerce')
        if df_l['MG (%)'].max() <= 1:
            df_l['MG (%)'] *= 100
        df_l['MG affichée'] = df_l['MG (%)'].map(lambda x: f"{x:.1f} %" if pd.notnull(x) else "—")
        st.markdown("\n".join([
            "| Date | Masse grasse (%) |",
            "|---|---|"
        ] + [f"| {r[0]} | {r[1]} |" for r in df_l[['Date affichée','MG affichée']].values]))
        fig = px.line(df_l, x='Date affichée', y='MG (%)', title="", markers=True)
        fig.update_layout(xaxis_title="Date", yaxis_title="Masse grasse (%)")
        st.plotly_chart(fig)
    else:
        st.warning("⚠️ Colonnes masse grasse manquantes")
else:
    st.info("ℹ️ Aucune donnée de masse grasse")
