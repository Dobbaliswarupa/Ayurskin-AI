def analyze_skin_type(
    oiliness,
    dryness,
    t_zone_oily
):
    """
    Estimate skin type using questionnaire responses.
    """

    # Dry skin
    if dryness == "High" and oiliness == "Low":
        skin_type = "Dry"

    # Oily skin
    elif oiliness == "High" and dryness == "Low":
        skin_type = "Oily"

    # Combination skin
    elif t_zone_oily == "Yes":
        skin_type = "Combination"

    # If both oiliness and dryness are high
    elif oiliness == "High" and dryness == "High":
        skin_type = "Combination"

    # Otherwise
    else:
        skin_type = "Normal"

    return skin_type