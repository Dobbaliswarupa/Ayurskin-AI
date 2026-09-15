from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np
import io
import os
import base64
import json
import re
from dotenv import load_dotenv
from google import genai

from utils.face_detection import detect_faces
from utils.skin_segmentation import extract_skin_region
from agents.tone_agent import analyze_skin_tone
from agents.traditional_agent import recommend_traditional_skincare


# ========================================================
# ENVIRONMENT
# ========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None


# ========================================================
# AUTOMATIC IMAGE-BASED SKIN TYPE DETECTION
# ========================================================

def _normalize_skin_type(value):
    """Convert model output to one of the four dashboard labels."""
    text = str(value or "").strip().lower()

    if "combination" in text:
        return "Combination"
    if "oily" in text:
        return "Oily"
    if "dry" in text:
        return "Dry"
    if "normal" in text:
        return "Normal"

    return "Normal"


def _extract_json_from_text(text):
    """Safely extract a JSON object from a Gemini text response."""
    if not text:
        return None

    cleaned = text.strip()

    # Remove optional markdown code fences.
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Try the first JSON object in the response.
    match = re.search(r"\{.*?\}", cleaned, flags=re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    return None


def _fallback_skin_type_from_pixels(skin_region):
    """
    Fallback only when Gemini is unavailable.

    This is an image-based estimate using simple visual statistics.
    It is not a medical diagnosis and is less reliable than a trained
    skin-type classifier.
    """
    pixels = np.asarray(skin_region).reshape(-1, 3).astype(np.float32)

    if pixels.size == 0:
        return "Normal", 0.50

    brightness_values = np.mean(pixels, axis=1)
    brightness_mean = float(np.mean(brightness_values))
    brightness_std = float(np.std(brightness_values))

    # Estimate saturation from RGB.
    max_rgb = np.max(pixels, axis=1)
    min_rgb = np.min(pixels, axis=1)
    saturation = (max_rgb - min_rgb) / np.maximum(max_rgb, 1.0)
    saturation_mean = float(np.mean(saturation))

    # Bright highlight ratio is a rough proxy for visible surface shine.
    highlight_ratio = float(np.mean(brightness_values > 210))

    # Conservative image-only estimate.
    if highlight_ratio > 0.08 and brightness_std > 28:
        return "Oily", 0.62

    if brightness_std > 34 and saturation_mean < 0.30:
        return "Dry", 0.58

    if highlight_ratio > 0.04 and brightness_std > 24:
        return "Combination", 0.57

    return "Normal", 0.55


def analyze_skin_type_from_image(image_bytes, content_type, skin_region):
    """
    Automatically determine skin type from the submitted face image.

    Gemini provides the primary AI classification. The local pixel-based
    estimate is used as a fallback so the dashboard can still return a
    result if Gemini is unavailable.
    """
    if client is not None:
        try:
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            prompt = """
Analyze the visible facial skin in this image for a skincare
demonstration.

Classify the apparent skin type into EXACTLY ONE of:
- Oily
- Dry
- Combination
- Normal

Use visible skin characteristics only. Do not diagnose a medical
condition. Do not infer age, ethnicity, identity, or health conditions.

Return ONLY valid JSON in this exact format:
{
  "skin_type": "Oily",
  "confidence": 0.90,
  "reason": "brief visual reason"
}

Confidence must be a number from 0 to 1.

If lighting, image quality, makeup, filters, or the face angle make
the classification uncertain, lower the confidence instead of
inventing certainty.
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    {
                        "inline_data": {
                            "mime_type": content_type or "image/jpeg",
                            "data": image_base64,
                        }
                    },
                    prompt,
                ],
            )

            parsed = _extract_json_from_text(
                getattr(response, "text", "")
            )

            if parsed:
                skin_type = _normalize_skin_type(
                    parsed.get("skin_type")
                )

                raw_confidence = parsed.get(
                    "confidence",
                    0.75
                )

                try:
                    confidence = float(raw_confidence)
                    if confidence > 1:
                        confidence = confidence / 100.0
                except Exception:
                    confidence = 0.75

                confidence = max(
                    0.0,
                    min(confidence, 1.0)
                )

                return skin_type, confidence

        except Exception as exc:
            print(
                "Automatic Gemini skin-type detection failed:",
                str(exc)
            )

    return _fallback_skin_type_from_pixels(
        skin_region
    )


# ========================================================
# FASTAPI APP
# ========================================================

app = FastAPI(
    title="AyurSkin AI",
    description="AI-Powered Personalized Skincare",
    version="1.0"
)


# ========================================================
# CORS
# ========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================================
# ROOT
# ========================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": "AyurSkin AI Backend is running"
    }


# ========================================================
# HEALTH CHECK
# ========================================================

@app.get("/health")
def health():
    return {
        "success": True,
        "status": "healthy",
        "gemini_configured": client is not None
    }


# ========================================================
# ANALYZE SKIN
# ========================================================

@app.post("/analyze")
async def analyze_skin(
    file: UploadFile = File(...)
):

    try:

        # ====================================================
        # 1. READ IMAGE
        # ====================================================

        image_bytes = await file.read()

        if not image_bytes:
            return {
                "success": False,
                "message": "No image received."
            }

        try:
            image = Image.open(
                io.BytesIO(image_bytes)
            ).convert("RGB")

        except Exception:
            return {
                "success": False,
                "message": "Invalid image file."
            }


        # ====================================================
        # 2. CONVERT IMAGE TO NUMPY
        # ====================================================

        image_np = np.array(image)


        # ====================================================
        # 3. FACE DETECTION
        # ====================================================

        faces = detect_faces(image_np)

        if faces is None or len(faces) == 0:
            return {
                "success": False,
                "message": "No face detected. Please upload a clear face image."
            }


        # ====================================================
        # 4. SELECT FIRST FACE
        # ====================================================

        face = faces[0]


        # ====================================================
        # 5. EXTRACT SKIN REGION
        # ====================================================

        skin_region = extract_skin_region(
            image_np,
            face
        )

        if skin_region is None:
            return {
                "success": False,
                "message": "Unable to extract skin region."
            }


        # ====================================================
        # 6. ANALYZE SKIN TONE
        # ====================================================

        tone_result = analyze_skin_tone(
            skin_region
        )

        if isinstance(tone_result, dict):

            skin_tone = tone_result.get(
                "skin_tone",
                tone_result.get(
                    "tone",
                    "Medium"
                )
            )

            tone_confidence = tone_result.get(
                "confidence",
                0
            )

        else:

            skin_tone = str(
                tone_result
            )

            tone_confidence = 0


        # ====================================================
        # 7. AUTOMATIC SKIN-TYPE DETECTION FROM FACE IMAGE
        # ====================================================

        skin_type, skin_type_confidence = (
            analyze_skin_type_from_image(
                image_bytes=image_bytes,
                content_type=file.content_type,
                skin_region=skin_region
            )
        )


        # ====================================================
        # 8. TRADITIONAL SKINCARE
        # ====================================================

        traditional_recommendations = (
            recommend_traditional_skincare(
                skin_type
            )
        )


        # ====================================================
        # 9. SUNSCREEN RECOMMENDATION
        # ====================================================

        # Sunscreen is selected according to
        # the detected skin type.

        if skin_type == "Oily":

            sunscreen_recommendation = (
                "Lightweight / non-comedogenic"
            )

            sunscreen_description = (
                "Choose a lightweight broad-spectrum "
                "SPF 30+ that feels comfortable on oily skin."
            )

            sunscreen_product_name = (
                "Deconstruct Gel Sunscreen SPF 50 PA++++"
            )

            sunscreen_product_url = (
                "https://thedeconstruct.in/products/"
                "gel-sunscreen-for-oily-skin"
            )

            day_routine = (
                "Gentle Cleanser → Lightweight Moisturizer → SPF 30+"
            )

            night_routine = (
                "Gentle Cleanser → Lightweight Moisturizer"
            )


        elif skin_type == "Dry":

            sunscreen_recommendation = (
                "Moisturizing sunscreen"
            )

            sunscreen_description = (
                "Choose a broad-spectrum SPF 30+ "
                "with a moisturizing feel for dry skin."
            )

            sunscreen_product_name = (
                "Dot & Key Barrier Repair Sunscreen "
                "SPF 50+ PA++++"
            )

            sunscreen_product_url = (
                "https://www.dotandkey.com/products/"
                "barrier-repair-sunscreen"
            )

            day_routine = (
                "Gentle Cleanser → Hydrating Care → "
                "Moisturizer → SPF 30+"
            )

            night_routine = (
                "Gentle Cleanser → Hydrating Care → "
                "Moisturizer"
            )


        elif skin_type == "Combination":

            sunscreen_recommendation = (
                "Lightweight + moisturizing"
            )

            sunscreen_description = (
                "Choose a broad-spectrum SPF 30+ "
                "that balances comfort and hydration."
            )

            # Use the currently available Dot & Key
            # Barrier Repair Sunscreen product page
            # instead of the old Watermelon URL that
            # was returning 404.

            sunscreen_product_name = (
                "Dot & Key Barrier Repair Sunscreen "
                "SPF 50+ PA++++"
            )

            sunscreen_product_url = (
                "https://www.dotandkey.com/products/"
                "barrier-repair-sunscreen"
            )

            day_routine = (
                "Gentle Cleanser → Balanced Moisturizer → SPF 30+"
            )

            night_routine = (
                "Gentle Cleanser → Targeted Traditional Care → "
                "Moisturizer"
            )


        else:

            sunscreen_recommendation = (
                "Comfortable daily sunscreen"
            )

            sunscreen_description = (
                "Choose a comfortable broad-spectrum "
                "SPF 30+ for everyday use."
            )

            sunscreen_product_name = (
                "Minimalist Light Fluid SPF 50"
            )

            sunscreen_product_url = (
                "https://beminimalist.co/products/"
                "light-fluid-spf-50-sunscreen"
            )

            day_routine = (
                "Gentle Cleanser → Moisturizer → SPF 30+"
            )

            night_routine = (
                "Gentle Cleanser → Moisturizer"
            )


        # ====================================================
        # SUNSCREEN OBJECT
        # ====================================================

        sunscreen = {
            "recommendation":
                sunscreen_recommendation,

            "description":
                sunscreen_description,

            "product_name":
                sunscreen_product_name,

            "product_url":
                sunscreen_product_url
        }


        # ====================================================
        # 10. SKIN BRIGHTNESS
        # ====================================================

        skin_pixels = skin_region.reshape(
            -1,
            3
        )

        brightness = float(
            np.mean(skin_pixels)
        )

        brightness = round(
            brightness,
            2
        )


        # ====================================================
        # 11. CONFIDENCE
        # ====================================================

        confidence_values = []

        if isinstance(
            tone_confidence,
            (int, float)
        ):

            tone_value = float(tone_confidence)

            if tone_value > 1:
                tone_value = tone_value / 100.0

            confidence_values.append(
                max(0.0, min(tone_value, 1.0))
            )

        if isinstance(
            skin_type_confidence,
            (int, float)
        ):

            type_value = float(skin_type_confidence)

            if type_value > 1:
                type_value = type_value / 100.0

            confidence_values.append(
                max(0.0, min(type_value, 1.0))
            )

        if confidence_values:

            confidence = round(
                float(np.mean(confidence_values)),
                3
            )

        else:

            confidence = 0


        # ====================================================
        # 12. FINAL RESPONSE
        # ====================================================

        return {

            "success": True,

            "skin_tone":
                skin_tone,

            "skin_type":
                skin_type,

            "brightness":
                brightness,

            "faces_detected":
                len(faces),

            "confidence":
                confidence,

            "traditional_recommendations":
                traditional_recommendations,

            "sunscreen":
                sunscreen,

            "day_routine":
                day_routine,

            "night_routine":
                night_routine
        }


    except Exception as e:

        print(
            "ERROR:",
            str(e)
        )

        return {

            "success": False,

            "message":
                f"Analysis failed: {str(e)}"
        }


# ========================================================
# GEMINI 7-DAY IMAGE
# ========================================================

@app.post("/generate-7-day-image")
async def generate_7_day_image(
    file: UploadFile = File(...)
):

    try:

        if client is None:

            return {
                "success": False,
                "message":
                    "Gemini API key is not configured."
            }


        # ====================================================
        # READ IMAGE
        # ====================================================

        image_bytes = await file.read()

        if not image_bytes:

            return {
                "success": False,
                "message":
                    "No image received."
            }


        # ====================================================
        # CONVERT IMAGE TO BASE64
        # ====================================================

        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")


        # ====================================================
        # GEMINI PROMPT
        # ====================================================

        prompt = """
Create a neutral illustrative 7-day skincare
progress example based on the uploaded face image.

Do not change the person's identity.

Do not whiten, reshape, beautify, or alter
facial structure.

Only show a subtle, natural-looking illustrative
difference in overall skin appearance.

This image is an illustration only and is not
a prediction or medical result.
"""


        # ====================================================
        # GEMINI IMAGE GENERATION
        # ====================================================

        response = client.models.generate_content(

            model="gemini-3.1-flash-image",

            contents=[

                {
                    "inline_data": {
                        "mime_type":
                            file.content_type or "image/jpeg",

                        "data":
                            image_base64
                    }
                },

                prompt
            ]
        )


        # ====================================================
        # FIND GENERATED IMAGE
        # ====================================================

        generated_image = None

        try:

            for part in response.candidates[0].content.parts:

                if hasattr(
                    part,
                    "inline_data"
                ):

                    generated_image = (
                        part.inline_data.data
                    )

                    break

        except Exception:

            generated_image = None


        if generated_image is None:

            return {
                "success": False,
                "message":
                    "Gemini did not return an image."
            }


        # ====================================================
        # RETURN IMAGE
        # ====================================================

        if isinstance(
            generated_image,
            bytes
        ):

            generated_image = base64.b64encode(
                generated_image
            ).decode("utf-8")


        return {

            "success": True,

            "image":
                f"data:image/png;base64,{generated_image}"
        }


    except Exception as e:

        print(
            "7-DAY IMAGE ERROR:",
            str(e)
        )

        return {

            "success": False,

            "message":
                f"Image generation failed: {str(e)}"
        }