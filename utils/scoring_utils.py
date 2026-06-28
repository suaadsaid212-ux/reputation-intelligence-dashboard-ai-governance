def calculate_rii(
    exposure,
    vulnerability,
    resilience,
):
    rii = (
        0.35 * exposure
        + 0.35 * vulnerability
        - 0.30 * resilience
    )

    rii = max(
        0,
        min(100, rii),
    )

    return round(rii, 2)
