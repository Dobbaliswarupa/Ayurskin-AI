import cv2
import os


def detect_faces(image):
    """
    Detect faces using OpenCV Haar Cascade.
    """

    # Get Haar Cascade path
    cascade_path = os.path.join(
        cv2.data.haarcascades,
        "haarcascade_frontalface_default.xml"
    )

    # Check file
    if not os.path.exists(cascade_path):
        raise FileNotFoundError(
            f"Haar Cascade file not found:\n{cascade_path}"
        )

    # Load detector
    face_cascade = cv2.CascadeClassifier(
        cascade_path
    )

    # Check detector
    if face_cascade.empty():
        raise RuntimeError(
            "OpenCV could not load the Haar Cascade file."
        )

    # Convert RGB to grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    return faces