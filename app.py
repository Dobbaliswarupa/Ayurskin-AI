import streamlit as st
import os
import numpy as np
from PIL import Image

from utils.face_detection import detect_faces
from utils.skin_segmentation import extract_skin_region
from agents.tone_agent import analyze_skin_tone
from agents.skin_type_agent import analyze_skin_type
from agents.traditional_agent import recommend_traditional_skincare
from agents.wellness_agent import recommend_wellness


# ==========================================================
# PAGE SETTINGS
# ==========================================================

st.set_page_config(
    page_title="AyurSkin AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================================
# PROJECT PATH
# ==========================================================

PROJECT_FOLDER = os.path.dirname(
    os.path.abspath(__file__)
)


def get_image_path(path):
    """
    Safely find an image inside the project folder.
    """

    if not path:
        return None

    full_path = os.path.join(
        PROJECT_FOLDER,
        path
    )

    if os.path.exists(full_path):
        return full_path

    return None


# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    st.title("🌿 AyurSkin AI")

    st.caption(
        "Personalized Skin Analysis"
    )

    st.divider()

    # ------------------------------------------------------
    # FACE INPUT
    # ------------------------------------------------------

    st.subheader("📸 Face Input")

    input_method = st.radio(
        "Choose input method",
        [
            "📁 Upload Image",
            "📷 Use Camera"
        ]
    )

    image_source = None

    if input_method == "📁 Upload Image":

        image_source = st.file_uploader(
            "Upload your face image",
            type=[
                "jpg",
                "jpeg",
                "png"
            ]
        )

    else:

        image_source = st.camera_input(
            "Take a face picture"
        )


    # ------------------------------------------------------
    # QUESTIONNAIRE
    # ------------------------------------------------------

    st.divider()

    st.subheader("🧴 Skin Questionnaire")

    oiliness = st.selectbox(
        "How oily is your skin?",
        [
            "Low",
            "Medium",
            "High"
        ]
    )

    dryness = st.selectbox(
        "How dry is your skin?",
        [
            "Low",
            "Medium",
            "High"
        ]
    )

    t_zone_oily = st.selectbox(
        "Is your T-zone oily?",
        [
            "Yes",
            "No"
        ]
    )


    # ------------------------------------------------------
    # ANALYZE BUTTON
    # ------------------------------------------------------

    st.divider()

    analyze_button = st.button(
        "🔍 ANALYZE MY SKIN",
        type="primary",
        use_container_width=True
    )


# ==========================================================
# MAIN HEADER
# ==========================================================

st.title("🌿 AyurSkin AI")

st.subheader(
    "AI-Powered Personalized Skin Analysis & Traditional-First Skincare"
)

st.caption(
    "Skin tone • Skin type • Traditional ingredients • "
    "Sunscreen • Wellness • AI agents"
)


# ==========================================================
# WELCOME SCREEN
# ==========================================================

if image_source is None:

    st.info(
        "👈 Upload a face image or use the camera, "
        "answer the questionnaire, then click "
        "**ANALYZE MY SKIN**."
    )

    st.divider()

    st.subheader(
        "✨ What AyurSkin AI Provides"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        with st.container(border=True):

            st.subheader("🎨 Skin Tone")

            st.write(
                "AI-based approximate skin-tone estimation."
            )


    with c2:

        with st.container(border=True):

            st.subheader("🧴 Skin Type")

            st.write(
                "Questionnaire-based Dry, Oily, "
                "Combination or Normal profile."
            )


    with c3:

        with st.container(border=True):

            st.subheader("🌿 Traditional Care")

            st.write(
                "Traditional ingredient recommendations "
                "with benefits and cautions."
            )


    with c4:

        with st.container(border=True):

            st.subheader("🤖 Agentic AI")

            st.write(
                "Multiple specialized agents work together "
                "to create the recommendation."
            )

    st.stop()


# ==========================================================
# READ IMAGE
# ==========================================================

try:

    image = Image.open(
        image_source
    ).convert("RGB")

    image_array = np.array(
        image
    )

except Exception as error:

    st.error(
        "❌ Unable to read the selected image."
    )

    st.code(
        str(error)
    )

    st.stop()


# ==========================================================
# WAIT FOR ANALYSIS
# ==========================================================

if not analyze_button:

    st.info(
        "✅ Image received. Click "
        "**ANALYZE MY SKIN** in the left sidebar."
    )

    st.image(
        image,
        width=250
    )

    st.stop()


# ==========================================================
# FACE DETECTION
# ==========================================================

try:

    faces = detect_faces(
        image_array
    )

except Exception as error:

    st.error(
        "❌ Face detection error."
    )

    st.code(
        str(error)
    )

    st.stop()


# ==========================================================
# CHECK FACE
# ==========================================================

if len(faces) == 0:

    st.error(
        "❌ No face detected."
    )

    st.info(
        "Try a clear front-facing image with good lighting."
    )

    st.stop()


# ==========================================================
# FIRST FACE
# ==========================================================

face = faces[0]

x, y, w, h = face


# ==========================================================
# SKIN REGION
# ==========================================================

skin_region = extract_skin_region(
    image_array,
    (x, y, w, h)
)


if skin_region is None or skin_region.size == 0:

    st.error(
        "❌ Could not extract the facial analysis region."
    )

    st.stop()


# ==========================================================
# SKIN TONE AGENT
# ==========================================================

tone_result = analyze_skin_tone(
    skin_region
)


# ==========================================================
# SKIN TYPE AGENT
# ==========================================================

skin_type = analyze_skin_type(
    oiliness,
    dryness,
    t_zone_oily
)


# ==========================================================
# TRADITIONAL SKINCARE AGENT
# ==========================================================

try:

    traditional_recommendations = (
        recommend_traditional_skincare(
            skin_type
        )
    )

except Exception as error:

    traditional_recommendations = []


# ==========================================================
# WELLNESS AGENT
# ==========================================================

try:

    wellness_recommendations = (
        recommend_wellness(
            skin_type
        )
    )

except Exception as error:

    wellness_recommendations = []


# ==========================================================
# PERSONALIZED RECOMMENDATION LOGIC
# ==========================================================

if skin_type == "Oily":

    sunscreen_recommendation = (
        "Lightweight / non-comedogenic"
    )

    sunscreen_description = (
        "Choose a lightweight broad-spectrum SPF 30+ "
        "that feels comfortable on oily skin."
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
        "Choose a broad-spectrum SPF 30+ with "
        "a moisturizing feel."
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
        "Choose a broad-spectrum SPF 30+ that "
        "balances comfort and hydration."
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
        "Choose a comfortable broad-spectrum SPF 30+ "
        "for everyday use."
    )

    day_routine = (
        "Gentle Cleanser → Moisturizer → SPF 30+"
    )

    night_routine = (
        "Gentle Cleanser → Moisturizer"
    )


# ==========================================================
# DASHBOARD HEADER
# ==========================================================

st.divider()

st.header(
    "📊 Personalized Skin Dashboard"
)

st.caption(
    "AI-generated profile based on the selected person's "
    "image and questionnaire responses"
)


# ==========================================================
# PROFILE SUMMARY
# ==========================================================

col1, col2, col3, col4 = st.columns(4)


# ----------------------------------------------------------
# SKIN TONE
# ----------------------------------------------------------

with col1:

    with st.container(border=True):

        st.caption(
            "🎨 SKIN TONE"
        )

        st.subheader(
            tone_result["tone"]
        )

        st.caption(
            f"Brightness: {tone_result['brightness']}"
        )


# ----------------------------------------------------------
# SKIN TYPE
# ----------------------------------------------------------

with col2:

    with st.container(border=True):

        st.caption(
            "🧴 SKIN TYPE"
        )

        st.subheader(
            skin_type
        )

        st.caption(
            "Questionnaire based"
        )


# ----------------------------------------------------------
# FACE
# ----------------------------------------------------------

with col3:

    with st.container(border=True):

        st.caption(
            "👤 FACE"
        )

        st.subheader(
            "Detected ✓"
        )

        st.caption(
            f"{len(faces)} face detected"
        )


# ----------------------------------------------------------
# CONFIDENCE
# ----------------------------------------------------------

with col4:

    with st.container(border=True):

        st.caption(
            "🤖 AI CONFIDENCE"
        )

        st.subheader(
            f"{tone_result['confidence']}%"
        )

        st.caption(
            "Prototype estimate"
        )


# ==========================================================
# TRADITIONAL INGREDIENTS
# ==========================================================

st.subheader(
    "🌿 Recommended Traditional Ingredients"
)

st.caption(
    f"Selected for your {skin_type} skin profile"
)


# Show maximum four cards
ingredients_to_show = (
    traditional_recommendations[:4]
)


if ingredients_to_show:

    ingredient_columns = st.columns(
        len(ingredients_to_show)
    )


    for column, item in zip(
        ingredient_columns,
        ingredients_to_show
    ):

        with column:

            with st.container(border=True):

                # --------------------------------------------------
                # INGREDIENT IMAGE
                # --------------------------------------------------

                image_path = item.get(
                    "image",
                    ""
                )

                actual_image = get_image_path(
                    image_path
                )


                if actual_image:

                    try:

                        st.image(
                            actual_image,
                            width=80
                        )

                    except Exception:

                        st.write("🌿")

                else:

                    st.write("🌿")


                # --------------------------------------------------
                # INGREDIENT NAME
                # --------------------------------------------------

                st.markdown(
                    f"**{item.get('name', 'Ingredient')}**"
                )


                # --------------------------------------------------
                # SUITABLE SKIN
                # --------------------------------------------------

                suitable_for = item.get(
                    "suitable_for",
                    [skin_type]
                )

                st.caption(
                    "Suitable: "
                    + ", ".join(suitable_for)
                )


                # --------------------------------------------------
                # BENEFIT
                # --------------------------------------------------

                benefits = item.get(
                    "benefits",
                    []
                )


                if benefits:

                    st.write(
                        "✨ "
                        + benefits[0]
                    )


                # --------------------------------------------------
                # CAUTION
                # --------------------------------------------------

                caution = item.get(
                    "caution",
                    "Patch test before use."
                )

                st.caption(
                    "Caution: "
                    + caution
                )


else:

    st.info(
        "No traditional ingredient recommendations found "
        "for this skin profile."
    )


# ==========================================================
# PERSONALIZED RECOMMENDATIONS
# ==========================================================

st.subheader(
    "💡 Personalized Recommendations"
)

col1, col2, col3 = st.columns(3)


# ==========================================================
# SUNSCREEN
# ==========================================================

with col1:

    with st.container(border=True):

        st.subheader(
            "☀️ Sunscreen"
        )

        st.write(
            "Broad-spectrum SPF 30+"
        )

        st.write(
            "🧴 "
            + sunscreen_recommendation
        )

        st.caption(
            sunscreen_description
        )

        st.markdown(
            "[View Sunscreen](https://beminimalist.co/products/multi-vitamin-spf-50)"
        )


# ==========================================================
# WELLNESS
# ==========================================================

with col2:

    with st.container(border=True):

        st.subheader(
            "🥗 Wellness"
        )

        if wellness_recommendations:

            for item in wellness_recommendations[:4]:

                st.write(
                    "• "
                    + item["name"]
                )

        else:

            st.write(
                "• Regular hydration"
            )

            st.write(
                "• Balanced nutrition"
            )

            st.write(
                "• Adequate sleep"
            )


# ==========================================================
# AI AGENTS
# ==========================================================

with col3:

    with st.container(border=True):

        st.subheader(
            "🤖 AI Agent Pipeline"
        )

        st.write(
            "✓ Face Analysis Agent"
        )

        st.write(
            "✓ Skin Tone Agent"
        )

        st.write(
            "✓ Skin Type Agent"
        )

        st.write(
            "✓ Traditional Skincare Agent"
        )

        st.write(
            "✓ Wellness Agent"
        )


# ==========================================================
# PERSONALIZED ROUTINE
# ==========================================================

st.subheader(
    "🗓️ Personalized Routine"
)


col1, col2 = st.columns(2)


# ----------------------------------------------------------
# DAY ROUTINE
# ----------------------------------------------------------

with col1:

    with st.container(border=True):

        st.subheader(
            "🌞 Day Routine"
        )

        st.write(
            day_routine
        )


# ----------------------------------------------------------
# NIGHT ROUTINE
# ----------------------------------------------------------

with col2:

    with st.container(border=True):

        st.subheader(
            "🌙 Night Routine"
        )

        st.write(
            night_routine
        )


# ==========================================================
# FINAL RESULT
# ==========================================================

st.success(
    f"""
    ✅ FINAL RESULT

    Skin Tone: {tone_result['tone']} |

    Skin Type: {skin_type} |

    Face: Detected ✓ |

    Traditional Options: {len(traditional_recommendations)} |

    Sunscreen: SPF 30+
    """
)


# ==========================================================
# SAFETY NOTE
# ==========================================================

st.caption(
    "⚠️ Educational prototype. Skin-tone estimation is "
    "approximate and can be affected by lighting, camera "
    "quality, shadows, makeup and image conditions. "
    "Skin type is questionnaire-based. Patch-test new "
    "topical ingredients before use."
)