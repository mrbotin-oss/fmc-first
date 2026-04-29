# poi_classifier.py
# Maps OSM tags to the 6 social functions of the 15-minute city

# ── LIVING ────────────────────────────────────────────────────────────────────
LIVING_AMENITY = {"shelter", "dormitory"}
LIVING_BUILDING = {"residential", "apartments", "house", "detached",
                   "semidetached_house", "terrace", "bungalow", "dormitory"}
LIVING_LANDUSE = {"residential"}

# ── WORKING ───────────────────────────────────────────────────────────────────
WORKING_AMENITY = {"workplace", "coworking_space"}
WORKING_OFFICE = True  # any office= tag
WORKING_BUILDING = {"office", "commercial", "industrial", "warehouse"}
WORKING_LANDUSE = {"commercial", "industrial", "office"}

# ── ENJOYING ──────────────────────────────────────────────────────────────────
ENJOYING_AMENITY = {
    "cinema", "theatre", "arts_centre", "nightclub", "bar", "pub",
    "restaurant", "cafe", "fast_food", "food_court", "biergarten",
    "ice_cream", "events_venue", "community_centre", "social_centre",
    "gambling", "stripclub", "casino"
}
ENJOYING_LEISURE = {
    "park", "garden", "playground", "sports_centre", "fitness_centre",
    "swimming_pool", "stadium", "golf_course", "pitch", "track",
    "ice_rink", "marina", "nature_reserve", "bird_hide", "miniature_golf",
    "water_park", "dance", "escape_game", "adult_gaming_centre"
}
ENJOYING_TOURISM = {
    "museum", "gallery", "theme_park", "attraction", "viewpoint",
    "zoo", "aquarium", "artwork"
}

# ── LEARNING ─────────────────────────────────────────────────────────────────
LEARNING_AMENITY = {
    "school", "university", "college", "kindergarten", "library",
    "language_school", "music_school", "driving_school", "research_institute",
    "training", "prep_school"
}
LEARNING_BUILDING = {"school", "university", "college", "kindergarten"}

# ── SUPPLYING ─────────────────────────────────────────────────────────────────
SUPPLYING_AMENITY = {
    "marketplace", "supermarket", "convenience", "fuel", "atm", "bank",
    "post_office", "post_box", "vending_machine", "laundry",
    "dry_cleaning", "car_wash", "money_transfer"
}
SUPPLYING_SHOP = True  # any shop= tag is supplying (retail / commerce)
SUPPLYING_LANDUSE = {"retail", "commercial"}
SUPPLYING_BUILDING = {"retail", "supermarket", "kiosk"}

# ── CARING ────────────────────────────────────────────────────────────────────
CARING_AMENITY = {
    "hospital", "clinic", "doctors", "dentist", "pharmacy",
    "veterinary", "nursing_home", "social_facility", "childcare",
    "baby_hatch", "healthcare", "blood_bank", "blood_donation",
    "mortuary", "first_aid"
}
CARING_HEALTHCARE = True  # any healthcare= tag
CARING_BUILDING = {"hospital", "clinic"}


def classify_poi(row) -> str:
    """
    Given a GeoDataFrame row (from osmnx.features_from_point),
    return the best-matching social function string, or 'unknown'.
    """

    amenity = str(row.get("amenity", "") or "").strip().lower()
    shop = str(row.get("shop", "") or "").strip().lower()
    office = str(row.get("office", "") or "").strip().lower()
    leisure = str(row.get("leisure", "") or "").strip().lower()
    tourism = str(row.get("tourism", "") or "").strip().lower()
    building = str(row.get("building", "") or "").strip().lower()
    landuse = str(row.get("landuse", "") or "").strip().lower()
    healthcare = str(row.get("healthcare", "") or "").strip().lower()

    # ── CARING (highest priority — safety/health) ─────────────────────────────
    if amenity in CARING_AMENITY:
        return "caring"
    if healthcare and healthcare not in ("", "nan", "no"):
        return "caring"
    if building in CARING_BUILDING:
        return "caring"

    # ── LEARNING ──────────────────────────────────────────────────────────────
    if amenity in LEARNING_AMENITY:
        return "learning"
    if building in LEARNING_BUILDING:
        return "learning"

    # ── ENJOYING ──────────────────────────────────────────────────────────────
    if amenity in ENJOYING_AMENITY:
        return "enjoying"
    if leisure in ENJOYING_LEISURE:
        return "enjoying"
    if tourism in ENJOYING_TOURISM:
        return "enjoying"

    # ── SUPPLYING ─────────────────────────────────────────────────────────────
    if amenity in SUPPLYING_AMENITY:
        return "supplying"
    if shop and shop not in ("", "nan", "no"):
        return "supplying"
    if building in SUPPLYING_BUILDING:
        return "supplying"
    if landuse in SUPPLYING_LANDUSE:
        return "supplying"

    # ── WORKING ───────────────────────────────────────────────────────────────
    if amenity in WORKING_AMENITY:
        return "working"
    if office and office not in ("", "nan", "no"):
        return "working"
    if building in WORKING_BUILDING:
        return "working"
    if landuse in WORKING_LANDUSE:
        return "working"

    # ── LIVING ────────────────────────────────────────────────────────────────
    if amenity in LIVING_AMENITY:
        return "living"
    if building in LIVING_BUILDING:
        return "living"
    if landuse in LIVING_LANDUSE:
        return "living"

    return "unknown"
