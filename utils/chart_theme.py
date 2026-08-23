PALETTE = {
    "navy": "#16324F",
    "teal": "#0E8FB0",
    "blue": "#1D6FD1",
    "indigo": "#4B5DFF",
    "violet": "#8B5CF6",
    "magenta": "#D946EF",
    "green": "#10B981",
    "gold": "#FBBF24",
    "orange": "#F59E0B",
    "red": "#EF4444",
    "deep_red": "#B91C1C",
    "slate": "#64748B",
    "light_slate": "#CBD5E1",
}

QUALITATIVE = [
    PALETTE["teal"],
    PALETTE["blue"],
    PALETTE["violet"],
    PALETTE["orange"],
    PALETTE["green"],
    PALETTE["red"],
    PALETTE["magenta"],
    PALETTE["slate"],
]

RISK_SCALE = [
    [0.00, "#10B981"],
    [0.28, "#1D6FD1"],
    [0.48, "#FBBF24"],
    [0.68, "#F59E0B"],
    [0.84, "#EF4444"],
    [1.00, "#B91C1C"],
]

POSITIVE_SCALE = [
    [0.00, "#EF4444"],
    [0.35, "#F59E0B"],
    [0.60, "#FBBF24"],
    [0.78, "#0E8FB0"],
    [1.00, "#10B981"],
]

COOL_SCALE = [
    [0.00, "#E8F4F8"],
    [0.25, "#8ED3E5"],
    [0.50, "#0E8FB0"],
    [0.75, "#4B5DFF"],
    [1.00, "#8B5CF6"],
]

MIXED_SCALE = [
    [0.00, "#E8F4F8"],
    [0.30, "#0E8FB0"],
    [0.55, "#4B5DFF"],
    [0.78, "#D946EF"],
    [1.00, "#F59E0B"],
]


def risk_color(value):
    value = float(value)
    if value >= 80:
        return PALETTE["deep_red"]
    if value >= 65:
        return PALETTE["red"]
    if value >= 45:
        return PALETTE["orange"]
    if value >= 25:
        return PALETTE["blue"]
    return PALETTE["green"]


def categorical_colors(count):
    return [
        QUALITATIVE[index % len(QUALITATIVE)]
        for index in range(int(count))
    ]
