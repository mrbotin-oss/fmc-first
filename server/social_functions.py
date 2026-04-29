# social_functions.py
# Definitions for the 6 social functions of the 15-minute city

SOCIAL_FUNCTIONS = {
    "living": {
        "icon": "🏠",
        "description": "Residential areas, housing, accommodation",
        "color": "#6366F1"
    },
    "working": {
        "icon": "💼",
        "description": "Offices, coworking spaces, employment hubs",
        "color": "#F59E0B"
    },
    "enjoying": {
        "icon": "🎭",
        "description": "Parks, culture, sports, entertainment, leisure",
        "color": "#EC4899"
    },
    "learning": {
        "icon": "📚",
        "description": "Schools, universities, libraries, training centers",
        "color": "#10B981"
    },
    "supplying": {
        "icon": "🛒",
        "description": "Markets, groceries, shops, essential retail",
        "color": "#F97316"
    },
    "caring": {
        "icon": "❤️",
        "description": "Hospitals, clinics, social services, childcare",
        "color": "#EF4444"
    }
}

FUNCTION_COLORS = {fn: info["color"] for fn, info in SOCIAL_FUNCTIONS.items()}
FUNCTION_ICONS = {
    "living": "home",
    "working": "briefcase",
    "enjoying": "star",
    "learning": "book",
    "supplying": "shopping-cart",
    "caring": "heart"
}
