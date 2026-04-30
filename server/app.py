import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import osmnx as ox
import pandas as pd
import plotly.graph_objects as go
from shapely.geometry import Point

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(layout="wide")

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS (PIXEL-STYLE UI)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, .stApp {
    margin: 0;
    padding: 0;
    background: #f8fafc;
    font-family: Inter, sans-serif;
}

/* FULLSCREEN MAP */
.map-wrap {
    position: relative;
}

/* LEFT PANEL */
.left-panel {
    position: absolute;
    top: 20px;
    left: 20px;
    width: 320px;
    background: white;
    border-radius: 16px;
    padding: 16px;
    z-index: 999;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

/* TITLE */
.title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 6px;
}

.subtitle {
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 16px;
}

/* METRIC */
.metric {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
}

.metric-label {
    font-size: 12px;
    color: #6b7280;
}

.metric-value {
    font-weight: 600;
}

/* RADAR */
.radar {
    margin-top: 10px;
}

/* LEGEND */
.legend {
    position: absolute;
    bottom: 20px;
    right: 20px;
    background: white;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

/* BUTTON */
.stButton button {
    width: 100%;
    border-radius: 10px;
    background: #4f46e5;
    color: white;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
if "lat" not in st.session_state:
    st.session_state.lat = None
    st.session_state.lng = None
    st.session_state.gdf = None

# ─────────────────────────────────────────────────────────────
# MAP
# ─────────────────────────────────────────────────────────────
m = folium.Map(
    location=[14.5547, 121.0244],
    zoom_start=15,
    tiles="CartoDB positron"
)

# ─────────────────────────────────────────────────────────────
# CLICK EVENT
# ─────────────────────────────────────────────────────────────
map_data = st_folium(m, height=700, width="100%", returned_objects=["last_clicked"])

if map_data and map_data.get("last_clicked"):
    st.session_state.lat = map_data["last_clicked"]["lat"]
    st.session_state.lng = map_data["last_clicked"]["lng"]

# ─────────────────────────────────────────────────────────────
# ANALYSIS
# ─────────────────────────────────────────────────────────────
def run_analysis(lat, lng):

    distances = {
        "5": 400,
        "10": 800,
        "15": 1200
    }

    tags = {"amenity": True, "shop": True}

    gdf = ox.features_from_point((lat, lng), tags=tags, dist=1200)

    gdf = gdf[gdf.geometry.notnull()].copy()
    gdf["geometry"] = gdf.geometry.centroid

    # classify simple
    def classify(row):
        if row.get("amenity") in ["school", "college"]:
            return "learning"
        if row.get("amenity") in ["hospital", "clinic"]:
            return "caring"
        if row.get("shop"):
            return "supplying"
        return "other"

    gdf["function"] = gdf.apply(classify, axis=1)

    return gdf

# ─────────────────────────────────────────────────────────────
# LEFT PANEL UI
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="left-panel">', unsafe_allow_html=True)

st.markdown('<div class="title">15-Minute City</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Makati, Philippines</div>', unsafe_allow_html=True)

if st.session_state.lat:
    st.markdown(f"""
    <div class="metric">
        <div class="metric-label">Lat</div>
        <div class="metric-value">{st.session_state.lat:.4f}</div>
    </div>
    <div class="metric">
        <div class="metric-label">Lng</div>
        <div class="metric-value">{st.session_state.lng:.4f}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Analyze"):
        gdf = run_analysis(st.session_state.lat, st.session_state.lng)
        st.session_state.gdf = gdf

# ─────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────
if st.session_state.gdf is not None:

    gdf = st.session_state.gdf

    counts = gdf["function"].value_counts().to_dict()

    categories = ["learning", "caring", "supplying"]
    values = [counts.get(c, 0) for c in categories]

    st.markdown('<div class="radar">', unsafe_allow_html=True)

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False)),
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# REBUILD MAP WITH DATA
# ─────────────────────────────────────────────────────────────
if st.session_state.lat and st.session_state.gdf is not None:

    m = folium.Map(
        location=[st.session_state.lat, st.session_state.lng],
        zoom_start=15,
        tiles="CartoDB positron"
    )

    # isochrones
    for dist, color in [(400, "#2dd4bf"), (800, "#fbbf24"), (1200, "#60a5fa")]:
        folium.Circle(
            [st.session_state.lat, st.session_state.lng],
            radius=dist,
            color=color,
            fill=True,
            fill_opacity=0.15,
            weight=2
        ).add_to(m)

    # points
    for _, row in st.session_state.gdf.iterrows():
        folium.CircleMarker(
            [row.geometry.y, row.geometry.x],
            radius=3,
            fill=True,
            fill_opacity=0.6
        ).add_to(m)

    st_folium(m, height=700, width="100%")

# ─────────────────────────────────────────────────────────────
# LEGEND
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="legend">
<b>Travel time</b><br>
<span style="color:#2dd4bf;">●</span> 5 min<br>
<span style="color:#fbbf24;">●</span> 10 min<br>
<span style="color:#60a5fa;">●</span> 15 min
</div>
""", unsafe_allow_html=True)
