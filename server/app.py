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

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

.main-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00C896, #00A8FF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}

.subtitle {
    color: #6B7280;
    font-size: 0.95rem;
    margin-top: 0;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.metric-card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid rgba(0,200,150,0.2);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    color: white;
}

.metric-card .label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #9CA3AF;
    margin-bottom: 0.2rem;
}

.metric-card .value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #00C896;
}

.function-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 2px;
}

.completeness-bar {
    height: 8px;
    border-radius: 4px;
    background: #1F2937;
    margin: 8px 0;
    overflow: hidden;
}

.completeness-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}

.stButton > button {
    background: linear-gradient(135deg, #00C896, #00A8FF);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    padding: 0.6rem 1.5rem;
    width: 100%;
    font-size: 1rem;
}

.stButton > button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

.info-box {
    background: rgba(0,200,150,0.08);
    border: 1px solid rgba(0,200,150,0.3);
    border-radius: 10px;
    padding: 1rem;
    font-size: 0.88rem;
    color: #D1FAE5;
    margin: 1rem 0;
}

.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #F9FAFB;
    margin: 1.2rem 0 0.5rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 0.4rem;
}

.poi-count {
    font-size: 0.85rem;
    color: #9CA3AF;
}

div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a, #1a1a2e);
}

div[data-testid="stSidebar"] * {
    color: #F9FAFB !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
col_title, col_badge = st.columns([3, 1])
with col_title:
    st.markdown('<h1 class="main-title">15-Minute City Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Makati City, Philippines · OSM-Powered Walkability Assessment</p>', unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    walk_speed = st.slider("Walking Speed (km/h)", 3.0, 6.0, 4.5, 0.5)
    walk_minutes = st.slider("Walk Time (minutes)", 5, 20, 15, 5)
    walk_distance_m = int((walk_speed * 1000 / 60) * walk_minutes)

    st.markdown(f"""
    <div class="info-box">
    📏 Catchment radius: <strong>{walk_distance_m}m</strong><br>
    🚶 Based on {walk_speed} km/h for {walk_minutes} min
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🗂️ Social Functions")
    for fn, info in SOCIAL_FUNCTIONS.items():
        st.markdown(f"{info['icon']} **{fn.capitalize()}** — {info['description']}")

    st.markdown("---")
    st.markdown("### ℹ️ How to use")
    st.markdown("""
    1. Click anywhere on the map
    2. Press **Analyze** to fetch OSM POIs
    3. View the 6-function breakdown
    """)

# ── Session State ─────────────────────────────────────────────────────────────
if "click_lat" not in st.session_state:
    st.session_state.click_lat = None
    st.session_state.click_lng = None
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "results" not in st.session_state:
    st.session_state.results = None

# ── Map Column Layout ─────────────────────────────────────────────────────────
map_col, result_col = st.columns([3, 2])

with map_col:
    st.markdown("#### 🗺️ Click a point in Makati City")

    # Build base map
    center = [14.5547, 121.0244]  # Makati CBD
    m = folium.Map(location=center, zoom_start=15,
                   tiles="CartoDB dark_matter")

    # Draw existing catchment if analysis done
    if st.session_state.analysis_done and st.session_state.results:
        res = st.session_state.results
        lat, lng = res["lat"], res["lng"]

        folium.Circle(
            location=[lat, lng],
            radius=walk_distance_m,
            color="#00C896",
            fill=True,
            fill_opacity=0.12,
            weight=2,
            tooltip=f"{walk_minutes}-min walk catchment ({walk_distance_m}m)"
        ).add_to(m)

        folium.Marker(
            location=[lat, lng],
            icon=folium.Icon(color="green", icon="person-walking", prefix="fa"),
            tooltip="Analysis Point"
        ).add_to(m)

        # Plot POIs
        for _, row in res["gdf"].iterrows():
            fn = row.get("social_function", "unknown")
            color = FUNCTION_COLORS.get(fn, "#888888")
            icon_name = FUNCTION_ICONS.get(fn, "circle")
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=5,
                color=color,
                fill=True,
                fill_opacity=0.85,
                tooltip=f"{row.get('name','POI')} [{fn}]"
            ).add_to(m)

    map_output = st_folium(m, width=None, height=550, returned_objects=["last_clicked"])

    # Capture click
    if map_output and map_output.get("last_clicked"):
        lc = map_output["last_clicked"]
        st.session_state.click_lat = lc["lat"]
        st.session_state.click_lng = lc["lng"]

    if st.session_state.click_lat:
        st.markdown(f"""
        <div class="info-box">
        📍 Selected: <strong>{st.session_state.click_lat:.5f}, {st.session_state.click_lng:.5f}</strong>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔍 Analyze 15-Minute City"):
            with st.spinner("Fetching POIs from OpenStreetMap…"):
                try:
                    lat = st.session_state.click_lat
                    lng = st.session_state.click_lng

                    # Query OSM
                    tags = {
                        "amenity": True,
                        "shop": True,
                        "office": True,
                        "leisure": True,
                        "tourism": True,
                        "healthcare": True,
                        "education": True,
                        "landuse": ["residential", "commercial", "retail"],
                        "building": ["residential", "apartments", "office", "school", "hospital", "retail", "commercial"]
                    }

                    gdf = ox.features_from_point(
                        (lat, lng),
                        tags=tags,
                        dist=walk_distance_m
                    )

                    if gdf.empty:
                        st.error("No POIs found. Try a different location.")
                    else:
                        # Keep only point and polygon geometries, convert to centroids
                        gdf = gdf[gdf.geometry.notnull()].copy()
                        gdf["geometry"] = gdf.geometry.centroid
                        gdf = gdf.set_crs(epsg=4326, allow_override=True)

                        # Clip to actual walk radius
                        origin = Point(lng, lat)
                        gdf_proj = gdf.to_crs(epsg=32651)
                        origin_proj = gpd.GeoDataFrame(geometry=[origin], crs=4326).to_crs(epsg=32651).geometry[0]
                        gdf_proj["dist"] = gdf_proj.geometry.distance(origin_proj)
                        gdf_proj = gdf_proj[gdf_proj["dist"] <= walk_distance_m]
                        gdf = gdf_proj.to_crs(epsg=4326)

                        # Classify
                        gdf["social_function"] = gdf.apply(classify_poi, axis=1)

                        # Build function summary
                        fn_counts = gdf["social_function"].value_counts().to_dict()
                        all_fns = list(SOCIAL_FUNCTIONS.keys())
                        present = {fn: fn_counts.get(fn, 0) for fn in all_fns}

                        st.session_state.results = {
                            "lat": lat, "lng": lng,
                            "gdf": gdf,
                            "fn_counts": present,
                            "total": len(gdf)
                        }
                        st.session_state.analysis_done = True
                        st.rerun()

                except Exception as e:
                    st.error(f"Error fetching data: {e}")
    else:
        st.info("👆 Click anywhere on the map to set your analysis point.")

# ── Results Panel ─────────────────────────────────────────────────────────────
with result_col:
    if st.session_state.analysis_done and st.session_state.results:
        res = st.session_state.results
        fn_counts = res["fn_counts"]
        total = res["total"]
        present_count = sum(1 for v in fn_counts.values() if v > 0)

        st.markdown("### 📊 Analysis Results")

        # Summary metrics
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
            <div class="label">Total POIs</div>
            <div class="value">{total}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
            <div class="label">Functions</div>
            <div class="value">{present_count}/6</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            score = round((present_count / 6) * 100)
            st.markdown(f"""
            <div class="metric-card">
            <div class="label">Score</div>
            <div class="value">{score}%</div>
            </div>
            """, unsafe_allow_html=True)

        # Completeness bar
        completeness_pct = int((present_count / 6) * 100)
        bar_color = "#00C896" if completeness_pct >= 80 else "#F59E0B" if completeness_pct >= 50 else "#EF4444"
        st.markdown(f"""
        <div style="margin-bottom:1rem;">
        <div style="display:flex;justify-content:space-between;font-size:0.8rem;color:#9CA3AF;">
            <span>15-Min City Completeness</span><span>{completeness_pct}%</span>
        </div>
        <div class="completeness-bar">
            <div class="completeness-fill" style="width:{completeness_pct}%;background:{bar_color};"></div>
        </div>
        </div>
        """, unsafe_allow_html=True)

        # Per-function breakdown
        st.markdown('<div class="section-header">🏙️ Social Function Breakdown</div>', unsafe_allow_html=True)

        for fn, info in SOCIAL_FUNCTIONS.items():
            count = fn_counts.get(fn, 0)
            color = FUNCTION_COLORS.get(fn, "#888")
            status = "✅" if count > 0 else "❌"
            bar_w = min(100, count * 3)

            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.6rem;border-left:3px solid {color};">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-weight:600;color:#F9FAFB;">{info['icon']} {fn.capitalize()}</span>
                <span style="font-size:0.8rem;color:{color};font-weight:700;">{status} {count} POIs</span>
              </div>
              <div style="font-size:0.75rem;color:#9CA3AF;margin-top:2px;">{info['description']}</div>
              <div style="height:4px;background:#1F2937;border-radius:2px;margin-top:8px;overflow:hidden;">
                <div style="width:{bar_w}%;height:100%;background:{color};border-radius:2px;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Missing functions warning
        missing = [fn for fn, v in fn_counts.items() if v == 0]
        if missing:
            st.markdown(f"""
            <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:10px;padding:0.8rem;margin-top:0.5rem;">
            ⚠️ <strong>Missing functions:</strong> {', '.join(f.capitalize() for f in missing)}<br>
            <span style="font-size:0.8rem;color:#9CA3AF;">This area does not fully qualify as a 15-minute city.</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(0,200,150,0.1);border:1px solid rgba(0,200,150,0.3);border-radius:10px;padding:0.8rem;margin-top:0.5rem;">
            🎉 <strong>All 6 social functions are present!</strong><br>
            <span style="font-size:0.8rem;color:#9CA3AF;">This area qualifies as a complete 15-minute city.</span>
            </div>
            """, unsafe_allow_html=True)

        # POI Table
        st.markdown('<div class="section-header">📋 POI Detail Table</div>', unsafe_allow_html=True)
        display_cols = ["name", "social_function", "amenity", "shop", "leisure"]
        available = [c for c in display_cols if c in res["gdf"].columns]
        df_show = res["gdf"][available].copy()
        df_show = df_show[df_show["social_function"] != "unknown"]
        df_show["name"] = df_show["name"].fillna("Unnamed")
        st.dataframe(df_show.head(50), use_container_width=True, height=280)

        # Download
        csv = df_show.to_csv(index=False)
        st.download_button("⬇️ Download POI Data (CSV)", csv,
                           "makati_15min_pois.csv", "text/csv")
    else:
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:400px;text-align:center;color:#6B7280;">
        <div style="font-size:4rem;margin-bottom:1rem;">🗺️</div>
        <div style="font-size:1.1rem;font-weight:600;color:#9CA3AF;">No analysis yet</div>
        <div style="font-size:0.85rem;margin-top:0.5rem;">Click a point on the map<br>then press Analyze</div>
        </div>
        """, unsafe_allow_html=True)
