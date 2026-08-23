COUNTRY_COORDS = {
    "united states": (39.8283, -98.5795),
    "united kingdom": (55.3781, -3.4360),
    "russia": (61.5240, 105.3188),
    "oman": (21.4735, 55.9754),
    "united arab emirates": (23.4241, 53.8478),
    "saudi arabia": (23.8859, 45.0792),
    "qatar": (25.3548, 51.1839),
    "kuwait": (29.3117, 47.4818),
    "bahrain": (25.9304, 50.6378),
    "egypt": (26.8206, 30.8025),
    "jordan": (30.5852, 36.2384),
    "lebanon": (33.8547, 35.8623),
    "iraq": (33.2232, 43.6793),
    "turkey": (38.9637, 35.2433),
    "france": (46.2276, 2.2137),
    "germany": (51.1657, 10.4515),
    "italy": (41.8719, 12.5674),
    "spain": (40.4637, -3.7492),
    "portugal": (39.3999, -8.2245),
    "netherlands": (52.1326, 5.2913),
    "belgium": (50.5039, 4.4699),
    "switzerland": (46.8182, 8.2275),
    "austria": (47.5162, 14.5501),
    "sweden": (60.1282, 18.6435),
    "norway": (60.4720, 8.4689),
    "denmark": (56.2639, 9.5018),
    "finland": (61.9241, 25.7482),
    "poland": (51.9194, 19.1451),
    "ukraine": (48.3794, 31.1656),
    "china": (35.8617, 104.1954),
    "japan": (36.2048, 138.2529),
    "south korea": (35.9078, 127.7669),
    "india": (20.5937, 78.9629),
    "singapore": (1.3521, 103.8198),
    "indonesia": (-0.7893, 113.9213),
    "malaysia": (4.2105, 101.9758),
    "australia": (-25.2744, 133.7751),
    "new zealand": (-40.9006, 174.8860),
    "brazil": (-14.2350, -51.9253),
    "mexico": (23.6345, -102.5528),
    "canada": (56.1304, -106.3468),
    "south africa": (-30.5595, 22.9375),
    "nigeria": (9.0820, 8.6753),
    "kazakhstan": (48.0196, 66.9237),
}

ALIASES = {
    "usa": "united states",
    "us": "united states",
    "u.s.": "united states",
    "u.s.a.": "united states",
    "uk": "united kingdom",
    "u.k.": "united kingdom",
    "uae": "united arab emirates",
    "russian federation": "russia",
    "korea, south": "south korea",
}


def normalize_country_name(value):
    if value is None:
        return ""
    name = str(value).strip().lower()
    return ALIASES.get(name, name)


def get_country_coords(value):
    key = normalize_country_name(value)
    return COUNTRY_COORDS.get(key)
