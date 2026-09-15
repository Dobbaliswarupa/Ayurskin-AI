import cv2
import numpy as np


def extract_skin_region(image, face):
    """
    Extract a central facial region from the detected face.

    Parameters:
        image: RGB image as NumPy array
        face: (x, y, w, h)

    Returns:
        Cropped facial region.
    """

    x, y, w, h = face

    # Select central facial region
    x1 = x + int(0.20 * w)
    x2 = x + int(0.80 * w)

    y1 = y + int(0.25 * h)
    y2 = y + int(0.70 * h)

    # Get image dimensions
    height, width = image.shape[:2]

    # Keep coordinates inside image
    x1 = max(0, x1)
    x2 = min(width, x2)

    y1 = max(0, y1)
    y2 = min(height, y2)

    # Crop region
    skin_region = image[y1:y2, x1:x2]

    return skin_region