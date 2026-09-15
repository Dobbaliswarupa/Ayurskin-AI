import React, { useEffect, useRef, useState } from "react";

import axios from "axios";

import {
  Activity,
  ArrowRight,
  BrainCircuit,
  Camera,
  CheckCircle2,
  Clock3,
  ExternalLink,
  Gauge,
  Image as ImageIcon,
  Info,
  Moon,
  Palette,
  RefreshCw,
  ScanFace,
  ShieldCheck,
  Sparkles,
  Sun,
  Upload,
  UserRound,
} from "lucide-react";

import "./App.css";

const API_URL = "http://127.0.0.1:8000";

/* =======================================================
   LOCAL INGREDIENT IMAGES

   Put images inside:
   frontend/public/ingredients/
======================================================= */

const ingredientImageMap = {
  besan: "/ingredients/besan.jpg",
  besanpowder: "/ingredients/besan.jpg",
  aloevera: "/ingredients/aloe-vera.jpg",
  aloeveragel: "/ingredients/aloe-vera.jpg",
  oat: "/ingredients/oat.jpg",
  oats: "/ingredients/oat.jpg",
  rosewater: "/ingredients/rose-water.jpg",
  turmeric: "/ingredients/turmeric.jpg",
  neem: "/ingredients/neem.jpg",
  sandalwood: "/ingredients/sandalwood.jpg",
  honey: "/ingredients/honey.jpg",
  cucumber: "/ingredients/cucumber.jpg",
  greentea: "/ingredients/green-tea.jpg",
  coconutoil: "/ingredients/coconut-oil.jpg",
};

const normalizeName = (name = "") =>
  name.toLowerCase().replace(/[^a-z0-9]/g, "");

const getIngredientImage = (name) => {
  const key = normalizeName(name);

  return (
    ingredientImageMap[key] ||
    "/ingredients/default.jpg"
  );
};

/* =======================================================
   CONFIDENCE
======================================================= */

const getConfidencePercent = (value) => {
  if (typeof value !== "number") return 0;

  const percent =
    value <= 1 ? value * 100 : value;

  return Math.min(
    Math.max(percent, 0),
    100
  );
};

/* =======================================================
   GENERATE 7-DAY ILLUSTRATIVE IMAGE

   Uses the SAME uploaded/captured image.

   This is only an illustrative visualization.
   It does NOT predict actual future skin changes.

   The difference is intentionally more visible
   than the previous version.
======================================================= */

const generateSevenDayImage = (file) => {
  return new Promise((resolve) => {
    if (!file) {
      resolve(null);
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      const img = new Image();

      img.onload = () => {
        const canvas =
          document.createElement("canvas");

        const maxSize = 900;

        let width = img.width;
        let height = img.height;

        /* Resize large images */

        if (
          width > maxSize ||
          height > maxSize
        ) {
          const scale = Math.min(
            maxSize / width,
            maxSize / height
          );

          width = Math.round(
            width * scale
          );

          height = Math.round(
            height * scale
          );
        }

        canvas.width = width;
        canvas.height = height;

        const ctx =
          canvas.getContext("2d");

        if (!ctx) {
          resolve(null);
          return;
        }

        ctx.drawImage(
          img,
          0,
          0,
          width,
          height
        );

        const imageData =
          ctx.getImageData(
            0,
            0,
            width,
            height
          );

        const data =
          imageData.data;

        /*
          =================================================
          ILLUSTRATIVE VISUAL TRANSFORMATION
          =================================================

          We make a noticeable visual difference using:

          - moderate brightness
          - moderate contrast
          - slight neutral color balancing

          We do NOT:

          - change face shape
          - change eyes/nose/mouth
          - reshape the face
          - whiten skin
          - remove facial features
          - claim this is a real prediction
        */

        for (
          let i = 0;
          i < data.length;
          i += 4
        ) {
          let r = data[i];
          let g = data[i + 1];
          let b = data[i + 2];

          /*
            STEP 1: Moderate brightness
          */

          r = r * 1.10 + 8;
          g = g * 1.10 + 8;
          b = b * 1.10 + 8;

          /*
            STEP 2: Moderate contrast
          */

          r =
            (r - 128) * 1.06 +
            128;

          g =
            (g - 128) * 1.06 +
            128;

          b =
            (b - 128) * 1.06 +
            128;

          /*
            STEP 3: Very small neutral balance
          */

          r += 2;
          g += 2;
          b += 2;

          /*
            STEP 4: Keep valid RGB values
          */

          data[i] =
            Math.min(
              250,
              Math.max(
                0,
                Math.round(r)
              )
            );

          data[i + 1] =
            Math.min(
              250,
              Math.max(
                0,
                Math.round(g)
              )
            );

          data[i + 2] =
            Math.min(
              250,
              Math.max(
                0,
                Math.round(b)
              )
            );
        }

        ctx.putImageData(
          imageData,
          0,
          0
        );

        const output =
          canvas.toDataURL(
            "image/jpeg",
            0.92
          );

        resolve(output);
      };

      img.onerror = () => {
        resolve(null);
      };

      img.src =
        reader.result;
    };

    reader.onerror = () => {
      resolve(null);
    };

    reader.readAsDataURL(file);
  });
};

/* =======================================================
   MAIN APP
======================================================= */

function App() {
  useEffect(() => {
    document.title =
      "AyurSkin Care Analysis";
  }, []);

  /* =====================================================
     MAIN STATES
  ===================================================== */

  const [image, setImage] =
    useState(null);

  const [preview, setPreview] =
    useState("");
const [result, setResult] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  /* =====================================================
     AFTER 7 DAYS IMAGE
  ===================================================== */

  const [
    sevenDayImage,
    setSevenDayImage,
  ] = useState(null);

  /* =====================================================
     CAMERA
  ===================================================== */

  const [cameraOpen, setCameraOpen] =
    useState(false);

  const [cameraStream, setCameraStream] =
    useState(null);

  const videoRef =
    useRef(null);

  /* =====================================================
     IMAGE UPLOAD
  ===================================================== */

  const handleImageChange = (
    event
  ) => {
    const file =
      event.target.files?.[0];

    if (!file) return;

    if (
      !file.type.startsWith(
        "image/"
      )
    ) {
      setError(
        "Please upload a valid image file."
      );

      return;
    }

    /* Stop camera */

    if (cameraStream) {
      cameraStream
        .getTracks()
        .forEach((track) =>
          track.stop()
        );

      setCameraStream(null);
      setCameraOpen(false);
    }

    setImage(file);

    setPreview(
      URL.createObjectURL(file)
    );

    setResult(null);

    setSevenDayImage(null);

    setError("");
  };

  /* =====================================================
     START CAMERA
  ===================================================== */

  const startCamera =
    async () => {
      try {
        setError("");

        const stream =
          await navigator.mediaDevices.getUserMedia(
            {
              video: {
                facingMode: "user",
              },
              audio: false,
            }
          );

        setCameraStream(stream);

        setCameraOpen(true);

        setTimeout(() => {
          if (videoRef.current) {
            videoRef.current.srcObject =
              stream;
          }
        }, 100);
      } catch (err) {
        console.error(err);

        setError(
          "Camera access was blocked. Please allow camera permission in your browser."
        );
      }
    };

  /* =====================================================
     STOP CAMERA
  ===================================================== */

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream
        .getTracks()
        .forEach((track) =>
          track.stop()
        );
    }

    setCameraStream(null);
    setCameraOpen(false);
  };

  /* =====================================================
     CAPTURE PHOTO
  ===================================================== */

  const capturePhoto = () => {
    const video =
      videoRef.current;

    if (
      !video ||
      !video.videoWidth
    ) {
      setError(
        "Camera is not ready yet. Please try again."
      );

      return;
    }

    const canvas =
      document.createElement(
        "canvas"
      );

    canvas.width =
      video.videoWidth;

    canvas.height =
      video.videoHeight;

    const context =
      canvas.getContext("2d");

    if (!context) {
      setError(
        "Unable to capture photo."
      );

      return;
    }

    context.drawImage(
      video,
      0,
      0,
      canvas.width,
      canvas.height
    );

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError(
            "Unable to capture photo."
          );

          return;
        }

        const file =
          new File(
            [blob],
            "camera-face.jpg",
            {
              type: "image/jpeg",
            }
          );

        setImage(file);

        setPreview(
          URL.createObjectURL(file)
        );

        setResult(null);

        setSevenDayImage(null);

        setError("");

        stopCamera();
      },
      "image/jpeg",
      0.92
    );
  };

  /* =====================================================
     CAMERA CLEANUP
  ===================================================== */

  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream
          .getTracks()
          .forEach((track) =>
            track.stop()
          );
      }
    };
  }, [cameraStream]);

  /* =====================================================
     ANALYZE SKIN
  ===================================================== */

  const analyzeSkin =
    async () => {
      if (!image) {
        setError(
          "Please upload a face image first."
        );

        return;
      }

      setLoading(true);

      setError("");

      setResult(null);

      setSevenDayImage(null);

      try {
        const formData =
          new FormData();

        formData.append(
          "file",
          image
        );

        const response =
          await axios.post(
            `${API_URL}/analyze`,
            formData,
            {
              headers: {
                "Content-Type":
                  "multipart/form-data",
              },
            }
          );

        /* Backend result */

        setResult(
          response.data
        );

        /* -----------------------------------------------
           Generate After 7 Days image
        ------------------------------------------------ */

        const transformedImage =
          await generateSevenDayImage(
            image
          );

        setSevenDayImage(
          transformedImage
        );
      } catch (err) {
        console.error(err);

        setError(
          err.response?.data
            ?.error ||
            "Unable to connect to the AyurSkin AI backend. Make sure FastAPI is running."
        );
      } finally {
        setLoading(false);
      }
    };

  /* =====================================================
     RESET
  ===================================================== */

  const resetAnalysis = () => {
    if (cameraStream) {
      cameraStream
        .getTracks()
        .forEach((track) =>
          track.stop()
        );
    }

    setCameraStream(null);

    setCameraOpen(false);

    setImage(null);

    setPreview("");

    setResult(null);

    setSevenDayImage(null);

    setError("");
};

  /* =====================================================
     CONFIDENCE
  ===================================================== */

  const confidence =
    getConfidencePercent(
      result?.confidence
    );

  /* =====================================================
     UI
  ===================================================== */

  return (
    <div className="app">

      {/* =================================================
          HEADER
      ================================================= */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-icon">

            <ScanFace
              size={25}
              strokeWidth={2}
            />

          </div>

          <div>

            <div className="brand-name">
              AyurSkin AI
            </div>

            <div className="brand-small">
              Personalized Skin Analysis
            </div>

          </div>

        </div>

        <div className="topbar-status">

          <span className="status-dot"></span>

          AI Skin Analysis

        </div>

      </header>


      {/* =================================================
          MAIN
      ================================================= */}

      <main className="main-content">


        {/* =================================================
            PAGE HEADING
        ================================================= */}

        <section className="page-heading">

          <h1>
            AyurSkin Care Analysis
          </h1>

          <p>
            AI-Powered Personalized Skincare
          </p>

        </section>


        {/* =================================================
            STEP 01
        ================================================= */}

        <section className="analysis-section">

          <div className="section-number">
            01
          </div>

          <div className="section-heading">

            <div className="section-icon">

              <ScanFace
                size={22}
              />

            </div>

            <div>

              <h2>
                Start Your Skin Analysis
              </h2>

              <p>
                Upload a clear face image and let AI automatically detect your skin type.
              </p>

            </div>

          </div>


          <div className="analysis-grid">


            {/* =================================================
                IMAGE CARD
            ================================================= */}

            <div className="upload-card">

              <div className="card-title">

                <ImageIcon
                  size={19}
                />

                <span>
                  Face Image
                </span>

              </div>


              {/* CAMERA */}

              {cameraOpen ? (

                <div className="camera-wrapper">

                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="camera-preview"
                  />

                  <div className="camera-controls">

                    <button
                      type="button"
                      className="capture-button"
                      onClick={
                        capturePhoto
                      }
                    >

                      <Camera
                        size={17}
                      />

                      Capture Photo

                    </button>


                    <button
                      type="button"
                      className="stop-camera-button"
                      onClick={
                        stopCamera
                      }
                    >

                      <RefreshCw
                        size={17}
                      />

                      Stop Camera

                    </button>

                  </div>

                </div>

              ) : preview ? (

                /* IMAGE PREVIEW */

                <div className="preview-wrapper">

                  <img
                    src={preview}
                    alt="Uploaded face"
                    className="face-preview"
                  />

                  <div className="preview-actions">

                    <label className="change-image">

                      <RefreshCw
                        size={16}
                      />

                      Change Image

                      <input
                        type="file"
                        accept="image/*"
                        onChange={
                          handleImageChange
                        }
                        hidden
                      />

                    </label>


                    <button
                      type="button"
                      className="camera-action"
                      onClick={
                        startCamera
                      }
                    >

                      <Camera
                        size={16}
                      />

                      Use Camera

                    </button>

                  </div>

                </div>

              ) : (

                /* UPLOAD AREA */

                <div className="upload-area">

                  <div className="upload-icon">

                    <Upload
                      size={30}
                    />

                  </div>

                  <strong>
                    Upload Face Image
                  </strong>

                  <span>
                    Select a clear front-facing image
                  </span>

                  <div className="capture-options">

                    <label className="upload-button">

                      <Upload
                        size={16}
                      />

                      Choose Image

                      <input
                        type="file"
                        accept="image/*"
                        onChange={
                          handleImageChange
                        }
                        hidden
                      />

                    </label>


                    <button
                      type="button"
                      className="camera-button"
                      onClick={
                        startCamera
                      }
                    >

                      <Camera
                        size={16}
                      />

                      Use Camera

                    </button>

                  </div>

                </div>

              )}

            </div>


            {/* =================================================
                AUTOMATIC SKIN-TYPE DETECTION
            ================================================= */}

            <div className="questionnaire-card">

              <div className="card-title">

                <ScanFace
                  size={19}
                />

                <span>
                  AI Skin-Type Detection
                </span>

              </div>

              <div className="question" style={{ marginBottom: "18px" }}>

                <label>
                  Skin Type
                </label>

                <div
                  style={{
                    padding: "16px",
                    borderRadius: "12px",
                    background: "rgba(0, 0, 0, 0.03)",
                    border: "1px solid rgba(0, 0, 0, 0.08)",
                    lineHeight: 1.5,
                  }}
                >

                  {result?.skin_type ? (
                    <>
                      <strong
                        style={{
                          display: "block",
                          fontSize: "20px",
                          marginBottom: "5px",
                        }}
                      >
                        {result.skin_type} Skin
                      </strong>

                      <span>
                        Automatically detected from your face image.
                      </span>
                    </>
                  ) : (
                    <>
                      <strong
                        style={{
                          display: "block",
                          marginBottom: "5px",
                        }}
                      >
                        Automatic Detection
                      </strong>

                      <span>
                        AI will analyze your face image and detect
                        whether your skin is Oily, Dry, Combination,
                        or Normal.
                      </span>
                    </>
                  )}

                </div>

              </div>


              <button
                className="analyze-button"
                onClick={
                  analyzeSkin
                }
                disabled={loading}
              >

                {loading ? (

                  <>

                    <RefreshCw
                      className="spin"
                      size={19}
                    />

                    Analyzing...

                  </>

                ) : (

                  <>

                    <BrainCircuit
                      size={19}
                    />

                    Analyze My Skin

                  </>

                )}

              </button>

            </div>

          </div>


          {error && (

            <div className="error-box">

              <Info
                size={19}
              />

              {error}

            </div>

          )}

        </section>


        {/* =================================================
            RESULTS
        ================================================= */}

        {result && (

          <>


            {/* =================================================
                AI ANALYSIS
            ================================================= */}

            <section className="results-section">

              <div className="section-number">
                02
              </div>

              <div className="section-heading">

                <div className="section-icon">

                  <BrainCircuit
                    size={22}
                  />

                </div>

                <div>

                  <h2>
                    Your AI Skin Analysis
                  </h2>

                  <p>
                    Personalized analysis based on your face image and AI skin-type detection.
                  </p>

                </div>

              </div>


              <div className="result-grid">

                <ResultCard
                  icon={
                    <Palette
                      size={22}
                    />
                  }
                  label="Skin Tone"
                  value={
                    result.skin_tone ||
                    "Not available"
                  }
                />


                <ResultCard
                  icon={
                    <UserRound
                      size={22}
                    />
                  }
                  label="Skin Type"
                  value={
                    result.skin_type ||
                    "Not available"
                  }
                />


                <ResultCard
                  icon={
                    <Gauge
                      size={22}
                    />
                  }
                  label="Brightness"
                  value={
                    result.brightness !==
                    undefined
                      ? Number(
                          result.brightness
                        ).toFixed(2)
                      : "N/A"
                  }
                />


                <ResultCard
                  icon={
                    <ScanFace
                      size={22}
                    />
                  }
                  label="Faces Detected"
                  value={
                    result.faces_detected ??
                    "N/A"
                  }
                />

              </div>


              {/* CONFIDENCE */}

              <div className="confidence-card">

                <div className="confidence-top">

                  <div className="confidence-title">

                    <ShieldCheck
                      size={20}
                    />

                    AI Analysis Confidence

                  </div>

                  <strong>

                    {confidence.toFixed(
                      1
                    )}

                    %

                  </strong>

                </div>


                <div className="confidence-track">

                  <div
                    className="confidence-fill"
                    style={{
                      width: `${confidence}%`,
                    }}
                  ></div>

                </div>

              </div>

            </section>


            {/* =================================================
                TRADITIONAL SKINCARE
            ================================================= */}

            <section className="recommendation-section">

              <div className="section-heading">

                <div className="section-icon">

                  <Sparkles
                    size={22}
                  />

                </div>

                <div>

                  <h2>
                    Traditional Skincare
                  </h2>

                  <p>
                    Natural ingredient recommendations based on your skin type.
                  </p>

                </div>

              </div>


              <div className="ingredient-grid">

                {(
                  result.traditional_recommendations ||
                  []
                ).map(

                  (
                    ingredient,
                    index
                  ) => (

                    <IngredientCard
                      key={index}
                      ingredient={
                        ingredient
                      }
                      skinType={
                        result.skin_type
                      }
                      beforeImage={
                        preview
                      }
                      afterImage={
                        sevenDayImage
                      }
                    />

                  )

                )}

              </div>

            </section>


            {/* =================================================
                MODERN SKINCARE
            ================================================= */}

            <section className="modern-section">

              <div className="section-heading">

                <div className="section-icon">

                  <Sun
                    size={22}
                  />

                </div>

                <div>

                  <h2>
                    Modern Skincare
                  </h2>

                  <p>
                    Personalized modern skincare recommendation.
                  </p>

                </div>

              </div>


              <div className="modern-card">

                <div className="modern-info">

                  <div className="modern-label">

                    <ShieldCheck
                      size={17}
                    />

                    DAILY SUN PROTECTION

                  </div>


                  {/* =================================================
                      FIXED SUNSCREEN RECOMMENDATION
                  ================================================= */}

                  <h3>

                    {result?.sunscreen?.recommendation ||
                      "Personalized Sunscreen Recommendation"}

                  </h3>


                  <p>

                    {result?.sunscreen?.description ||
                      "Choose a broad-spectrum SPF 30+ suitable for your skin type."}

                  </p>


                  {/* =================================================
                      FIXED VIEW SUNSCREEN BUTTON

                      Backend returns:
                      product_name
                      product_url

                      NOT:
                      products.map()
                  ================================================= */}

                  <div className="sunscreen-products">

                    {result?.sunscreen?.product_name && (

                      <div className="sunscreen-name">

                        {result.sunscreen.product_name}

                      </div>

                    )}


                    {result?.sunscreen?.product_url && (

                      <a
                        href={
                          result.sunscreen.product_url
                        }
                        target="_blank"
                        rel="noreferrer"
                        className="product-link"
                      >

                        <ExternalLink
                          size={16}
                        />

                        View Sunscreen

                      </a>

                    )}

                  </div>

                </div>


                {/* MODERN 7-DAY */}

                <div className="modern-progress">

                  <div className="progress-title">

                    <Clock3
                      size={18}
                    />

                    Expected Progress — 7 Days

                  </div>

                  <p>

                    Consistent sunscreen use helps protect skin from daily UV exposure.

                  </p>

                  <Comparison
                    beforeImage={
                      preview
                    }
                    afterImage={
                      sevenDayImage
                    }
                    beforeLabel="BEFORE"
                    afterLabel="AFTER 7 DAYS"
                  />

                </div>

              </div>

            </section>


            {/* =================================================
                ROUTINE
            ================================================= */}

            <section className="routine-section">

              <div className="section-heading">

                <div className="section-icon">

                  <Clock3
                    size={22}
                  />

                </div>

                <div>

                  <h2>
                    Personalized Routine
                  </h2>

                  <p>
                    Simple day and night skincare routine.
                  </p>

                </div>

              </div>


              <div className="routine-grid">


                {/* MORNING */}

                <div className="routine-card morning">

                  <div className="routine-icon">

                    <Sun
                      size={21}
                    />

                  </div>

                  <div>

                    <span className="routine-label">
                      MORNING
                    </span>

                    <h3>
                      Day Routine
                    </h3>

                    <p>

                      {result.day_routine ||
                        "Gentle Cleanser → Balanced Moisturizer → SPF 30+"}

                    </p>

                  </div>

                </div>


                {/* EVENING */}

                <div className="routine-card evening">

                  <div className="routine-icon">

                    <Moon
                      size={21}
                    />

                  </div>

                  <div>

                    <span className="routine-label">
                      EVENING
                    </span>

                    <h3>
                      Night Routine
                    </h3>

                    <p>

                      {result.night_routine ||
                        "Gentle Cleanser → Targeted Traditional Care → Moisturizer"}

                    </p>

                  </div>

                </div>

              </div>

            </section>


            {/* =================================================
                NEW ANALYSIS
            ================================================= */}

            <div className="new-analysis-wrapper">

              <button
                className="new-analysis-button"
                onClick={
                  resetAnalysis
                }
              >

                <RefreshCw
                  size={18}
                />

                Start New Analysis

              </button>

            </div>

          </>

        )}

      </main>

    </div>
  );
}


/* ==========================================================
   RESULT CARD
========================================================== */

function ResultCard({
  icon,
  label,
  value,
}) {

  return (

    <div className="result-card">

      <div className="result-icon">

        {icon}

      </div>

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


/* ==========================================================
   INGREDIENT CARD
========================================================== */

function IngredientCard({
  ingredient,
  skinType,
  beforeImage,
  afterImage,
}) {

  const name =
    ingredient?.name ||
    "Traditional Ingredient";

  const ingredientImage =
    getIngredientImage(name);

  return (

    <article className="ingredient-card">


      {/* INGREDIENT IMAGE */}

      <div className="ingredient-image-wrapper">

        <img
          src={ingredientImage}
          alt={name}
          className="ingredient-image"
          onError={(event) => {

            event.currentTarget.src =
              "/ingredients/default.jpg";

          }}
        />

      </div>


      <div className="ingredient-content">


        {/* TITLE */}

        <div className="ingredient-title-row">

          <h3>
            {name}
          </h3>

          <CheckCircle2
            size={20}
            className="check-icon"
          />

        </div>


        {/* DETECTED SKIN TYPE ONLY */}

        <div className="suitable">

          Suitable for:{" "}

          <strong>

            {skinType ||
              ingredient?.suitable_for ||
              "Your skin type"}{" "}

            Skin

          </strong>

        </div>


        {/* INGREDIENT IMAGE LINK */}

        <a
          href={ingredientImage}
          target="_blank"
          rel="noreferrer"
          className="image-link"
        >

          <ImageIcon
            size={16}
          />

          View Ingredient Image

          <ExternalLink
            size={14}
          />

        </a>


        {/* 7 DAY */}

        <div className="progress-header">

          <Clock3
            size={17}
          />

          Expected Progress — 7 Days

        </div>


        <p className="progress-text">

          Skin may feel more comfortable with suitable and consistent care.

        </p>


        {/* BEFORE / AFTER */}

        <Comparison
          beforeImage={
            beforeImage
          }
          afterImage={
            afterImage
          }
          beforeLabel="BEFORE"
          afterLabel="AFTER 7 DAYS"
        />

      </div>

    </article>
  );
}


/* ==========================================================
   BEFORE / AFTER
========================================================== */

function Comparison({
  beforeImage,
  afterImage,
  beforeLabel,
  afterLabel,
}) {

  return (

    <div className="comparison">

      <div className="comparison-heading">

        <ImageIcon
          size={17}
        />

        <span>
          7-Day Example
        </span>

      </div>


      <div className="comparison-grid">


        {/* BEFORE */}

        <div className="comparison-item">

          <span>
            {beforeLabel}
          </span>

          <div className="comparison-image-box">

            {beforeImage ? (

              <img
                src={beforeImage}
                alt="Before analysis"
              />

            ) : (

              <div className="image-placeholder">

                <ScanFace
                  size={25}
                />

                <small>
                  Upload image
                </small>

              </div>

            )}

          </div>

        </div>


        {/* ARROW */}

        <div className="comparison-arrow">

          <ArrowRight
            size={20}
          />

        </div>


        {/* AFTER */}

        <div className="comparison-item">

          <span>
            {afterLabel}
          </span>

          <div className="comparison-image-box">

            {afterImage ? (

              <img
                src={afterImage}
                alt="Illustrative 7-day example"
              />

            ) : (

              <div className="image-placeholder">

                <ImageIcon
                  size={25}
                />

                <small>
                  7-day example
                </small>

              </div>

            )}

          </div>

        </div>

      </div>


      {/* DISCLAIMER */}

      <p className="comparison-note">

        Illustrative 7-day visualization only.
        It does not guarantee or predict actual skin changes after seven days.

      </p>

    </div>
  );
}

export default App;