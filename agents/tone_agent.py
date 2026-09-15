import numpy as np


def analyze_skin_tone(skin_region):
    """
    Estimate a neutral skin-tone category.

    This is an approximate computer-vision estimate.
    Lighting, camera settings, shadows and filters
    can affect the result.
    """

    # Check whether skin region exists
    if skin_region is None or skin_region.size == 0:
        return {
            "tone": "Unable to estimate",
            "brightness": 0,
            "confidence": 0
        }

    # Convert image to floating-point values
    pixels = skin_region.astype(np.float32)

    # Calculate average RGB values
    average_rgb = pixels.mean(axis=(0, 1))

    red = average_rgb[0]
    green = average_rgb[1]
    blue = average_rgb[2]

    # Calculate average brightness
    brightness = (red + green + blue) / 3

    # Estimate neutral tone category
    if brightness >= 210:
        tone = "Very Light"

    elif brightness >= 175:
        tone = "Light"

    elif brightness >= 135:
        tone = "Medium"

    elif brightness >= 95:
        tone = "Tan"

    else:
        tone = "Deep"

    return {
        "tone": tone,
        "brightness": round(float(brightness), 2),
        "confidence": 75
    }