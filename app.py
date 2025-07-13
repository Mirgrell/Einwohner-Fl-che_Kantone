import numpy as np
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from geojson_rewind import rewind
import requests


url_geo = "https://data.opendatasoft.com/explore/dataset/georef-switzerland-kanton@public/download/?format=geojson"
geojson = requests.get(url_geo).json()
geojson = rewind(geojson, rfc7946=False)

#url_geojson_gem = "https://data.opendatasoft.com/explore/dataset/georef-switzerland-gemeinde-millesime@public/download/?format=geojson"
#geojson_gem = requests.get(url_geojson_gem).json()
#geojson_gem = rewind(geojson_gem, rfc7946=False)
#print(geojson)
# Wikipedia‑Scraping
url_wiki = "https://de.wikipedia.org/wiki/Kantone_der_Schweiz"
url_wiki_gem = "https://de.wikipedia.org/wiki/Liste_Schweizer_Gemeinden"
tables = pd.read_html(url_wiki)
tables_gem = pd.read_html(url_wiki_gem)
print(tables_gem[0].columns)
kantone = tables[1][:-1][["Abk.","Kanton","Hauptort 5 (Regierungssitz)","Ein­wohner 1 31. Dezember 2023","Fläche (km²)"]]
gemeinde = tables_gem[0][:-1][['Offizieller Gemeindename', 'Kanton', 'BFS-Nr.', 'Einwohner',
       'Fläche in km²', 'Einwohnerdichte (Einwohner pro km²)']]
kantone.columns = ["Kanton_Abk","Kanton","Hauptstadt","Einwohner","Fläche (km²)"]
kantone["Einwohner"] = kantone["Einwohner"].str.replace(r"[^\d]", "", regex=True).astype(int)
kantone["Fläche (km²)"] = kantone["Fläche (km²)"].str.replace("'", "", regex=False).str.replace(",", ".", regex=False).astype(float)

gemeinde.columns = ["Gemeinde","Kanton","BFS","Einwohner","Fläche (km²)","ED"]
gemeinde["Einwohner"] = gemeinde["Einwohner"].str.replace(r"[^\d]", "", regex=True).astype(int)
gemeinde["Fläche (km²)"] = gemeinde["Fläche (km²)"].astype(float)/100

# Beispiel-Daten
kantone["Einwohner_log"] = np.log10(kantone["Einwohner"])
mapping={'Appenzell\xa0Ausserrhoden': 'Appenzell Ausserrhoden', 'Appenzell\xa0Innerrhoden': 'Appenzell Innerrhoden', 'Freiburg': 'Fribourg', 'Genf': 'Genève', 'Neuenburg': 'Neuchâtel', 'St.\xa0Gallen': 'St. Gallen', 'Tessin': 'Ticino', 'Thurgau': 'Thurgau', 'Waadt': 'Vaud', 'Wallis': 'Valais'}
mapping_gem={'AG':'Aargau','AR': 'Appenzell Ausserrhoden', 'AI': 'Appenzell Innerrhoden', 'FR': 'Fribourg', 'GE': 'Genève', 'NE': 'Neuchâtel', 'SG': 'St. Gallen', 'TI': 'Ticino', 'TG': 'Thurgau', 'VD': 'Vaud', 'VS': 'Valais','ZH':'Zürich','BE': 'Bern', 'LU':'Luzern','UR': 'Uri','SZ': 'Schwyz', 'OW': 'Obwalden','NW': 'Nidwalden','GL': 'Glarus','ZG': 'Zug', 'SO': 'Solothurn','BS': 'Basel-Stadt','BL': 'Basel-Landschaft','SH': 'Schaffhausen','GR': 'Graubünden', 'JU': 'Jura'
}

#print(list(kantone["Kanton"]))

kantone["Kanton"] = kantone["Kanton"].replace(mapping)
gemeinde["Kanton"] = gemeinde["Kanton"].replace(mapping_gem)
# Log-Spalten anlegen (falls gewünscht)
kantone["Einwohner_log"] = np.log10(kantone["Einwohner"])
#kantone["Flaeche_log"] = np.log10(kantone["Flaeche_km2"])

# Standard: Einwohner log
initial_z = kantone["Einwohner_log"]
initial_title = "Einwohner (log)"
initial_colorscale = "Blues"

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# -------------------------------
# STREAMLIT UI
# -------------------------------

st.title("Schweizer Kantone – Einwohner & Fläche")
st.text("Quellen, Daten: Wikipedia , Karte: Bundesamt für Landestopografie swisstopo")
# Auswahl, welche Kennzahl dargestellt wird
variable = st.radio(
    "Welche Kennzahl soll dargestellt werden?",
    ["Einwohner", "Fläche (km²)"],
    index=0
)

# Dropdown für Kanton-Highlight
kanton_list = ["(Keiner)"] + kantone["Kanton"].tolist()
selected_kanton = st.selectbox(
    "Wähle einen Kanton für die Detailansicht:",
    kanton_list
)

if selected_kanton == "(Keiner)":
    selected_kanton = None

# ----------------------------------------
# Farbschema wählen
# ----------------------------------------

if variable == "Einwohner":
    color_scale = "Blues"
else:
    color_scale = "Greens"

# ----------------------------------------
# MIN & MAX Werte für Skala setzen
# ----------------------------------------

vmin = kantone[variable].min()
vmax = kantone[variable].max()

# -------------------------------
# CHOROPLETH MAP
# -------------------------------

fig_map = px.choropleth(
    kantone,
    geojson=geojson,
    locations="Kanton",
    color=variable,
    hover_data=["Kanton", "Einwohner", "Fläche (km²)"],
    featureidkey="properties.kan_name",
    color_continuous_scale=color_scale,
    range_color=[vmin,vmax],
    title=f"Schweizer Kantone – {variable}"
)

fig_map.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig_map, use_container_width=True)

# -------------------------------
# BALKENDIAGRAMM
# -------------------------------

# Balkendiagramm-Daten vorbereiten
kantone_sorted = kantone.sort_values(variable, ascending=False)

# Balken-Farben setzen
bar_colors = [
    "red" if k == selected_kanton else ("royalblue" if variable == "Einwohner" else "green")
    for k in kantone_sorted["Kanton"]
]

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    x=kantone_sorted["Kanton"],
    y=kantone_sorted[variable],
    marker_color=bar_colors,
    text=kantone_sorted[variable],
    textposition="auto"
))

fig_bar.update_layout(
    title=f"Kantone sortiert nach {variable}",
    xaxis_title="Kanton",
    yaxis_title=variable,
    margin=dict(l=20, r=20, t=40, b=80),
    showlegend=False
)

st.plotly_chart(fig_bar, use_container_width=True)

df_gem_kanton = gemeinde[gemeinde["Kanton"] == selected_kanton]

# Balkendiagramm-Daten vorbereiten
gemeinde_sorted = df_gem_kanton.sort_values(variable, ascending=False)

top_n=15
df_top = gemeinde_sorted.head(top_n)
df_rest = gemeinde_sorted.iloc[top_n:]
rest_sum = df_rest[variable].sum()

if rest_sum > 0:
    # Zeile für "Sonstige" hinzufügen:
    df_top = pd.concat([
        df_top,
        pd.DataFrame({
            "Gemeinde": ["Sonstige"],
            variable: [rest_sum]
        })
    ], ignore_index=True)

gemeinde_sorted = df_top
# Balken-Farben setzen
bar_colors = [
    "royalblue" if variable == "Einwohner" else "green" for k in gemeinde_sorted["Gemeinde"]]


fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    x=gemeinde_sorted["Gemeinde"],
    y=gemeinde_sorted[variable],
    marker_color=bar_colors,
    text=gemeinde_sorted[variable],
    textposition="auto"
))

fig_bar.update_layout(
    title=f"Gemeinden des Kantons {selected_kanton} sortiert nach {variable}",
    xaxis_title="Gemeinde",
    yaxis_title=variable,
    margin=dict(l=20, r=20, t=40, b=80),
    showlegend=False
)

st.plotly_chart(fig_bar, use_container_width=True)

