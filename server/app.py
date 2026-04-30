import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import osmnx as ox
import pandas as pd
import numpy as np
from shapely.geometry import Point, mapping
import json
from poi_classifier import classify_poi
from social_functions import SOCIAL_FUNCTIONS, FUNCTION_COLORS, FUNCTION_ICONS

st.set_page_config(
    page_title="15-Minute City · Makati",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── ENHANCED CUSTOM CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

* {
    scrollbar-width: thin;
    scrollbar-color: rgba(0,200,150,0.3) transparent;
}

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: rgba(0,200,150,0.3);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(0,200,150,0.5);
}

/* Main layout */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --success-gradient: linear-gradient(135deg, #00C896 0%, #00A8FF 100%);
    --dark-bg: #0a0a0f;
    --card-bg: rgba(20, 20, 35, 0.8);
    --glass-bg: rgba(255, 255, 255, 0.05);
    --border-glow: rgba(0, 200, 150, 0.3);
}

/* Page background */
.stApp {
    background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
}

/* Header */
.main-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 800;
    background: var(--success-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.02em;
}

.subtitle {
    font-size: 1rem;
    font-weight: 400;
    color: rgba(156, 163, 175, 0.8);
    margin: 0.5rem 0 2rem 0;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* Cards */
.metric-card, .function-card {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-glow);
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.metric-card::before, .function-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: var(--success-gradient);
    opacity: 0.5;
}

.metric-card:hover, .function-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 40px rgba(0,200,150,0.15);
    border-color: rgba(0,200,150,0.5);
}

.metric-label {
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: rgba(156, 163, 175, 0.7);
    margin-bottom: 0.5rem;
}

.metric-value {
    font-size: clamp(1.8rem, 4vw, 2.8rem);
    font-weight: 800;
    font-family: 'Space Grotesk', sans-serif;
    background: var(--success-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.function-card .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.8rem;
}

.function-name {
    font-weight: 600;
    font-size: 1.1rem;
    color: #f8fafc;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.function-count {
    font-size: 1.2rem;
    font-weight: 700;
    padding: 0.5rem 1rem;
    border-radius: 12px;
    background: rgba(0,200,150,0.15);
    border: 1px solid rgba(0,200,150,0.3);
}

.function-desc {
    color: rgba(156, 163, 175, 0.8);
    font-size: 0.9rem;
    line-height: 1.5;
    margin-bottom: 1rem;
}

.progress-bar {
    height: 8px;
    background: rgba(31, 41, 55, 0.5);
    border-radius: 10px;
    overflow: hidden;
    position: relative;
}

.progress-fill {
    height: 100%;
    border-radius: 10px;
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.progress-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { left: -100%; }
    100% { left: 100%; }
}

/* Buttons */
.stButton > button {
    background: var(--success-gradient);
    color: white !important;
    border: none;
    border-radius: 16px;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    padding: 1rem 2rem;
    width: 100%;
    font-size: 1rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 8px 25px rgba(0,200,150,0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 35px rgba(0,200,150,0.4);
}

.stButton > button:active {
    transform: translateY(0);
}

/* Info boxes */
.info-box {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-glow);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    color: #e2e8f0;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 50px;
    font-size: 0.85rem;
    font-weight: 600;
    backdrop-filter: blur(10px);
}

/* Sidebar */
div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(10,10,15,0.95) 0%, rgba(26,26,46,0.95) 100%);
    backdrop-filter: blur(20px);
    border-right: 1px solid var(--border-glow);
}

div[data-testid="stSidebar"] .stMarkdown {
    color: #e2e8f0 !important;
}

/* Map container */
.map-container {
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    border: 1px solid var(--border-glow);
    background: var(--dark-bg);
}

/* Dataframe */
.stDataFrame {
    border-radius: 16px !important;
    overflow: hidden;
    border: 1px solid var(--border-glow);
}

.element-container .dataframe {
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
}

/* Section headers */
.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    background: var(--success-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 2rem 0 1.5rem 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

/* Empty state */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 450px;
    text-align: center;
    color: rgba(156, 163, 175, 0.6);
}

.empty-state .icon {
    font-size: 5rem;
    margin-bottom: 1.5rem;
    opacity: 0.7;
}

.empty-state .title {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: rgba(156, 163, 175, 0.8);
}

.empty-state .subtitle {
    font-size: 1rem;
    opacity: 0.7;
}

/* Responsive */
@media (max-width: 768px) {
    .metric-card, .function-card {
        padding: 1.2rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<h1 class="main-title">15-Minute City Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Makati City, Philippines · OSM-Powered Walkability Assessment</p>', unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        walk_speed = st.slider("🚶 Walking Speed", 3.0, 6.0, 4.5, 0.5, 
                              help="Average walking speed in km/h")
    with col2:
        walk_minutes = st.slider("⏱️ Walk Time", 5, 20, 15, 5,
                                help="Maximum walking time in minutes")
    
    walk_distance_m = int((walk_speed * 1000 / 60) * walk_minutes)
    
    st.markdown(f"""
    <div class="info-box">
        <div style="font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem;">
            📏 {walk_distance_m:,}m Catchment
        </div>
        <div style="color: rgba(156,163,175,0.8);">
            Based on {walk_speed} km/h for {walk_minutes} minutes
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🏙️ Social Functions")
    for fn, info in SOCIAL_FUNCTIONS.items():
        st.markdown(f"**{info['icon']} {fn.capitalize()}**  {info['description']}")

# ── Session State ─────────────────────────────────────────────────────────────
if "click_lat" not in st.session_state:
    st.session_state.click_lat = None
    st.session_state.click_lng = None
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "results" not in st.session_state:
    st.session_state.results = None

# ── Main Layout ──────────────────────────────────────────────────────────────
map_col, results_col = st.columns([3, 2], gap="large")

with map_col:
    st.markdown('<div class="section-title">🗺️ Interactive Map</div>', unsafe_allow_html=True)
    
    # Build enhanced map
    center = [14.5547, 121.0244]
    m = folium.Map(
        location=center, 
        zoom_start=15,
        tiles="CartoDB dark_matter",
        control_scale=True
    )
    
    # Add analysis circle and POIs if available
    if st.session_state.analysis_done and st.session_state.results:
        res = st.session_state.results
        lat, lng = res["lat"], res["lng"]
        
        # Enhanced catchment circle
        folium.Circle(
            [lat, lng], radius=walk_distance_m,
            color="#00C896", weight=3, fillOpacity=0.15,
            tooltip=f"<b>{walk_minutes}min walk</b><br>{walk_distance_m:,}m radius"
        ).add_to(m)
        
        # Analysis point marker
        folium.Marker(
            [lat, lng],
            icon=folium.Icon(color="green", icon="user", prefix="fa", icon_color="white"),
            tooltip="<b>📍 Analysis Point</b>"
        ).add_to(m)
        
        # Enhanced POI markers
        for _, row in res["gdf"].iterrows():
            fn = row.get("social_function", "unknown")
            color = FUNCTION_COLORS.get(fn, "#888")
            folium.CircleMarker(
                [row.geometry.y, row.geometry.x],
                radius=6, color=color, fillOpacity=0.9,
                tooltip=f"<b>{row.get('name','POI')}</b><br>Function: {fn}"
            ).add_to(m)

    # Render map with custom container
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    map_output = st_folium(m, width="100%", height=600, returned_objects=["last_clicked"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Click handler
    if map_output and map_output.get("last_clicked"):
        lc = map_output["last_clicked"]
        st.session_state.click_lat = lc["lat"]
        st.session_state.click_lng = lc["lng"]

    if st.session_state.click_lat:
        st.markdown(f"""
        <div class="info-box">
            <div style="font-size:1.3rem;font-weight:700;margin-bottom:0.3rem;">
                📍 {st.session_state.click_lat:.5f}, {st.session_state.click_lng:.5f}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔍 **ANALYZE 15-MINUTE CITY**", use_container_width=True):
            with st.spinner("🔄 Fetching POIs from OpenStreetMap..."):
                # [Keep your existing analysis code here - unchanged]
                try:
                    lat = st.session_state.click_lat
                    lng = st.session_state.click_lng

                    tags = {
                        "amenity": True, "shop": True, "office": True,
                        "leisure": True, "tourism": True, "healthcare": True,
                        "education": True, "landuse": ["residential", "commercial", "retail"],
                        "building": ["residential", "apartments", "office", "school", "hospital", "retail", "commercial"]
                    }

                    gdf = ox.features_from_point((lat, lng), tags=tags, dist=walk_distance_m)

                    if gdf.empty:
                        st.error("❌ No POIs found. Try a different location.")
                    else:
                        gdf = gdf[gdf.geometry.notnull()].copy()
                        gdf["geometry"] = gdf.geometry.centroid
                        gdf = gdf.set_crs(epsg=4326, allow_override=True)

                        origin = Point(lng, lat)
                        gdf_proj = gdf.to_crs(epsg=32651)
                        origin_proj = gpd.GeoDataFrame(geometry=[origin], crs=4326).to_crs(epsg=32651).geometry[0]
                        gdf_proj["dist"] = gdf_proj.geometry.distance(origin_proj)
                        gdf_proj = gdf_proj[gdf_proj["dist"] <= walk_distance_m]
                        gdf = gdf_proj.to_crs(epsg=4326)

                        gdf["social_function"] = gdf.apply(classify_poi, axis=1)

                        fn_counts = gdf["social_function"].value_counts().to_dict()
                        all_fns = list(SOCIAL_FUNCTIONS.keys())
                        present = {fn: fn_counts.get(fn, 0) for fn in all_fns}

                        st.session_state.results = {
                            "lat": lat, "lng": lng, "gdf": gdf,
                            "fn_counts": present, "total": len(gdf)
                        }
                        st.session_state.analysis_done = True
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">🗺️</div>
            <div class="title">Click anywhere on the map</div>
            <div class="subtitle">Select your analysis point to begin</div>
        </div>
        """, unsafe_allow_html=True)

# ── Results Panel ─────────────────────────────────────────────────────────────
with results_col:
    if st.session_state.analysis_done and st.session_state.results:
        res = st.session_state.results
        fn_counts = res["fn_counts"]
        total = res["total"]
        present_count = sum(1 for v in fn_counts.values() if v > 0)

        st.markdown('<div class="section-title">📊 Analysis Results</div>', unsafe_allow_html=True)

        # Enhanced metrics
        col1, col2, col3 = st.columns(3, gap="medium")
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total POIs</div>
                <div class="metric-value">{total:,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Functions Present</div>
                <div class="metric-value">{present_count}/6</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            score = round((present_count / 6) * 100)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">15-Min Score</div>
                <div class="metric-value">{score}%</div>
            </div>
            """, unsafe_allow_html=True)

        # Enhanced completeness bar
        completeness_pct = int((present_count / 6) * 100)
        bar_color = "#00C896" if completeness_pct >= 80 else "#F59E0B" if completeness_pct >= 50 else "#EF4444"
        st.markdown(f"""
        <div class="metric-card">
            <div style="display:flex;justify-content:space-between;font-size:0.9rem;color:rgba(156,163,175,0.8);margin-bottom:1rem;">
                <span>15-Minute City Completeness</span>
                <span><strong>{completeness_pct}%</strong></span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width:{completeness_pct}%;background:{bar_color};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Social functions breakdown
        st.markdown('<div class="section-title">🏙️ Social Functions</div>', unsafe_allow_html=True)
        
        for fn, info in SOCIAL_FUNCTIONS.items():
            count = fn_counts.get(fn, 0)
            color = FUNCTION_COLORS.get(fn, "#888")
            status_icon = "✅" if count > 0 else "❌"
            
            st.markdown(f"""
            <div class="function-card" style="border-left: 4px solid {color};">
                <div class="header">
                    <div class="function-name">
                        {info['icon']} {fn.replace('_', ' ').title()}
                    </div>
                    <div class="function-count" style="color:{color};">
                        {status_icon} {count}
                    </div>
                </div>
                <div class="function-desc">{info['description']}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width:{min(100, count*2.5)}%;background:{color};opacity:0.8;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Status badge
        missing = [fn for fn, v in fn_counts.items() if v == 0]
        if not missing:
            st.markdown("""
            <div class="status-badge" style="background:rgba(0,200,150,0.15);border:1px solid rgba(0,200,150,0.3);color:#00C896;">
                🎉 All 6 social functions present! This is a complete 15-minute city.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="status-badge" style="background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.3);color:#EF4444;">
                ⚠️ Missing: {', '.join(fn.replace('_',' ').title() for fn in missing[:2])}{'...' if len(missing)>2 else ''}
            </div>
            """, unsafe_allow_html=True)

        # POI Table
        st.markdown('<div class="section-title">📋 POI Details</div>', unsafe_allow_html=True)
        display_cols = ["name", "social_function", "amenity", "shop"]
        available = [c for c in display_cols if c in res["gdf"].columns]
        df_show = res["gdf"][available + ["geometry"]].copy()
        df_show = df_show[df_show["social_function"] != "unknown"]
        df_show["name"] = df_show["name"].fillna("Unnamed POI")
        df_show = df_show.head(25)
        
        st.dataframe(df_show, use_container_width=True, height=300, hide_index=True)

        # Download
        csv = df_show.to_csv(index=False)
        st.download_button(
            "⬇️ Download Full Dataset", 
            csv, 
            "makati_15min_analysis.csv",
            "text/csv",
            use_container_width=True
        )
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">📊</div>
            <div class="title">Analysis Results</div>
            <div class="subtitle">Complete your first analysis to see results here</div>
        </div>
        """, unsafe_allow_html=True)
