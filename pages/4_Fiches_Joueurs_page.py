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

saison = st.session_state.get("saison", "2026-2027")

# Chargement des données
df_fiche_joueur = pd.read_excel(
    f"data/{saison}/Informations joueurs.xlsx"
)
df_fiche_joueur.columns = df_fiche_joueur.columns.str.strip()
if 'Date de naissance' in df_fiche_joueur.columns:
    df_fiche_joueur['Date de naissance'] = pd.to_datetime(df_fiche_joueur['Date de naissance'], errors='coerce')

joueurs = sorted(df_fiche_joueur['Nom du joueur'].dropna().unique().tolist())
joueur_choisi = st.selectbox("Sélectionner un joueur", joueurs)
df_joueur = df_fiche_joueur[df_fiche_joueur['Nom du joueur'] == joueur_choisi]

col1, col2 = st.columns([1, 2])
with col1:
    chemin_photos = "Photos joueurs"
    image_trouvee = False
    for ext in ['.jpg', '.jpeg', '.png']:
        chemin_img = os.path.join(chemin_photos, joueur_choisi + ext)
        if os.path.isfile(chemin_img):
            st.image(chemin_img, caption=joueur_choisi, width=200)
            image_trouvee = True
            break
    if not image_trouvee:
        st.warning("📸 Aucune image trouvée.")
with col2:
    st.subheader(f"Informations sur {joueur_choisi}")
    for col in ['Poste', 'Date de naissance', 'Taille', 'Poids', 'Nationalité']:
        if col in df_joueur.columns:
            val = df_joueur[col].values[0]
            if col == 'Date de naissance' and pd.notnull(val):
                val = pd.to_datetime(val).strftime('%d/%m/%Y')
            st.write(f"**{col} :** {val}")

# Temps de jeu
df_stats = pd.read_excel(
    f"data/{saison}/Temps de jeu.xlsx"
)
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

    # --- Tableau Markdown ---
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"]*len(cols)) + " |"
    rows = [
        "| " + " | ".join(
            str(int(x)) if isinstance(x,(int,float)) and x==int(x) else str(x) 
            for x in r
        ) + " |" for r in df_leg.values
    ]
    st.markdown("\n".join([header, sep] + rows))

# --- Camemberts côte à côte ---
st.subheader("Répartition des matchs")

col1, col2 = st.columns(2)

# ----- Total -----
with col1:
    st.markdown("### Total")
    if not df_stats_f.empty:
        labels_total = ['N3','CDF','Matchs Amicaux','Réserve']
        values_total = [
            int(df_leg['Nombre matchs N3'].sum()),
            int(df_leg['Nombre matchs CDF'].sum()),
            int(df_leg['Nombre matchs amicaux'].sum()),
            int(df_leg['Nombre matchs Réserve'].sum())
        ]
        fig_total = px.pie(
            names=labels_total,
            values=values_total,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_total.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_total, use_container_width=True)
    else:
        st.info("ℹ️ Aucune statistique disponible pour ce joueur.")

# ----- N3 -----
with col2:
    st.markdown("### N3")
    if not df_stats_f.empty:
        # Vérification robuste des colonnes
        def get_col(df, search):
            cols = [c for c in df.columns if search in c]
            return cols[0] if cols else None

        tit_col = get_col(df_leg, "Nombre de Titularisation N3")
        entree_col = get_col(df_leg, "Entrée en jeu N3")
        non_entree_col = get_col(df_leg, "Non entrée en jeu N3")
        hors_groupe_col = get_col(df_leg, "Hors groupe N3")

        tit = int(df_leg[tit_col].sum()) if tit_col else 0
        entree = int(df_leg[entree_col].sum()) if entree_col else 0
        non_entree = int(df_leg[non_entree_col].sum()) if non_entree_col else 0
        hors_groupe = int(df_leg[hors_groupe_col].sum()) if hors_groupe_col else 0

        labels_n3 = ["Titularisations", "Entrées en jeu", "Non-entrées en jeu", "Hors groupe"]
        values_n3 = [tit, entree, non_entree, hors_groupe]

        fig_n3 = px.pie(
            names=labels_n3,
            values=values_n3,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_n3.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_n3, use_container_width=True)
    else:
        st.info("ℹ️ Aucune statistique disponible pour ce joueur.")





# --- Statistiques Buts et Passes D ---
import streamlit as st
import pandas as pd

st.subheader("Statistiques Buts & Passes Décisives")

if not df_stats_f.empty:
    stats_cols = {
        "Total": ["Buts Total", "Passes D Total"],
        "N3": ["Buts N3", "Passes D N3"],
        "CDF": ["Buts CDF", "Passes D CDF"],
        "Réserve": ["Buts Réserve", "Passes D Réserve"],
        "Amicaux": ["Buts Matchs Amicaux", "Passes D Matchs Amicaux"]
    }

    data = []
    for comp, cols in stats_cols.items():
        buts = int(df_stats_f[cols[0]].sum())
        passes = int(df_stats_f[cols[1]].sum())
        data.append([comp, buts, passes])

    df_buts_passes = pd.DataFrame(data, columns=["Compétition", "Buts", "Passes D"])

    # Affichage sans numéro de ligne
    st.markdown(df_buts_passes.to_html(index=False), unsafe_allow_html=True)

else:
    st.info("ℹ️ Aucune statistique disponible pour ce joueur.")












# Graphs supplémentaires par type...
# (similaire aux blocs précédents, en utilisant df_stats_f)

# Présences entraînements
df_pres = pd.read_excel(
    f"data/{saison}/Présences.xlsx"
)
df_pres.columns = df_pres.columns.str.strip()
pres_f = df_pres[df_pres['Nom du joueur'] == joueur_choisi]
st.subheader("Présences Entraînement")
if not pres_f.empty:
    cols = ['Nombre entrainements total','Présences','Absences','Blessures','Malade','Réserve','Sélections', 'Réathlé']
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
df_poids = pd.read_excel(
    f"data/{saison}/Poids-Masse grasse.xlsx"
)
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
