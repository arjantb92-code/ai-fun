"""
Transaction Category Classifier

Categories:
- boodschappen (groceries): supermarkets, food stores
- huishoudelijk (household): home supplies, hardware stores
- winkelen (shopping): general retail, clothing
- vervoer (transport): gas stations, public transport, parking
- reizen_vrije_tijd (travel & leisure): restaurants, hotels, entertainment
- overig (other): default category
"""

CATEGORIES = {
    "boodschappen": "Boodschappen",
    "huishoudelijk": "Huishoudelijk",
    "winkelen": "Winkelen",
    "vervoer": "Vervoer",
    "reizen_vrije_tijd": "Reizen & Vrije Tijd",
    "overig": "Overig"
}

# Keywords for each category (lowercase)
CATEGORY_KEYWORDS = {
    "boodschappen": [
        # Dutch supermarkets
        "albert heijn", "ah ", "jumbo", "lidl", "aldi", "plus", "dirk",
        "coop", "dekamarkt", "nettorama", "vomar", "hoogvliet", "poiesz",
        "deen", "spar", "boni", "picnic", "crisp",
        # Generic grocery terms
        "supermarkt", "boodschappen", "levensmiddelen", "bakker", "slager",
        "groente", "fruit", "zuivel",
    ],
    "huishoudelijk": [
        # Dutch household/hardware stores
        "action", "blokker", "hema", "xenos", "ikea", "leen bakker",
        "kwantum", "gamma", "praxis", "karwei", "hornbach", "hubo",
        "bouwmarkt", "intratuin", "tuincentrum",
        # Generic terms
        "huishoud", "schoonmaak", "was", "poetsmiddel",
    ],
    "winkelen": [
        # Clothing/fashion
        "h&m", "zara", "primark", "c&a", "we fashion", "only",
        "vero moda", "jack & jones", "zalando", "bol.com", "coolblue",
        "mediamarkt", "bcc", "expert", "amazon",
        # Generic retail
        "winkel", "shop", "store", "fashion", "kleding", "schoenen",
    ],
    "vervoer": [
        # Gas stations
        "shell", "bp", "esso", "texaco", "total", "tinq", "tango",
        "tamoil", "gulf", "argos", "makro", "avia",
        # Transport
        "ns ", "ov-chipkaart", "ovpay", "connexxion", "arriva", "gvb",
        "ret", "htm", "qpark", "q-park", "parkeren", "parking",
        "benzine", "diesel", "tankstation", "laadpaal", "fastned",
        "uber", "bolt", "taxi", "swapfiets",
    ],
    "reizen_vrije_tijd": [
        # Restaurants and bars
        "restaurant", "cafe", "bar", "eetcafe", "pizzeria", "sushi",
        "mcdonalds", "mcdonald's", "burger king", "kfc", "subway",
        "dominos", "new york pizza", "thuisbezorgd", "deliveroo", "uber eats",
        "starbucks", "coffee company", "lunch", "diner", "ontbijt",
        # Entertainment
        "bioscoop", "pathe", "kinepolis", "vue", "theater", "concert",
        "museum", "attractiepark", "efteling", "walibi", "madurodam",
        "escape room", "bowling", "sportschool", "gym", "fitness",
        # Hotels and travel
        "hotel", "hostel", "airbnb", "booking.com", "booking", "trivago",
        "vliegticket", "transavia", "klm", "ryanair", "easyjet",
        "vakantie", "reis", "trip", "excursie",
        # Leisure
        "loetje", "vapiano", "la place", "happy italy", "happy thai",
        "bagels & beans", "anne&max",
    ],
}


def classify_transaction(description: str) -> str:
    """
    Classify a transaction based on its description.
    Returns the category key (e.g., 'boodschappen', 'vervoer', etc.)
    """
    if not description:
        return "overig"
    
    desc_lower = description.lower()
    
    # Check each category's keywords
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return category
    
    return "overig"


def get_category_label(category_key: str) -> str:
    """Get the display label for a category key"""
    return CATEGORIES.get(category_key, "Overig")


def get_all_categories():
    """Return all available categories with their keys and labels"""
    return [{"key": k, "label": v} for k, v in CATEGORIES.items()]
