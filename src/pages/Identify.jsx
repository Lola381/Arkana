import { useState, useRef } from "react";
import { analyzeImage } from "../services/visionApi";

export default function Identify() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = (file) => {
    if (!file || !file.type.startsWith("image/")) {
      setError("Please upload an image file.");
      return;
    }
    setImage(file);
    setPreview(URL.createObjectURL(file));
    setResult(null);
    setError(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const handleAnalyze = async () => {
    if (!image) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeImage(image);
      setResult(data.answer);
    } catch (err) {
      setError("Failed to analyze image. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setImage(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "var(--color-bg, #1a1208)",
      color: "var(--color-text, #e8d5a3)",
      padding: "6rem 2rem 4rem",
      fontFamily: "var(--font-body, serif)"
    }}>
      <div style={{ maxWidth: "860px", margin: "0 auto" }}>

        {/* Header */}
        <div style={{ marginBottom: "3rem" }}>
          <p style={{
            fontSize: "0.75rem",
            letterSpacing: "0.2em",
            textTransform: "uppercase",
            color: "var(--color-gold, #c9a227)",
            marginBottom: "0.75rem"
          }}>
            Visual Intelligence
          </p>
          <h1 style={{
            fontSize: "clamp(2rem, 5vw, 3.5rem)",
            fontWeight: "300",
            lineHeight: 1.1,
            marginBottom: "1rem"
          }}>
            Identify an Artifact
          </h1>
          <p style={{
            fontSize: "1rem",
            color: "var(--color-text-muted, #9e8a6a)",
            maxWidth: "520px",
            lineHeight: 1.7
          }}>
            Upload a photograph of any Indian monument, sculpture, painting, or cultural artifact.
            Arkana will identify it and share its historical and cultural significance.
          </p>
        </div>

        {/* Upload area */}
        {!preview && (
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `1.5px dashed ${dragOver ? "var(--color-gold, #c9a227)" : "rgba(201,162,39,0.3)"}`,
              borderRadius: "12px",
              padding: "4rem 2rem",
              textAlign: "center",
              cursor: "pointer",
              transition: "border-color 0.2s",
              background: dragOver ? "rgba(201,162,39,0.04)" : "transparent",
              marginBottom: "2rem"
            }}
          >
            <div style={{ fontSize: "2.5rem", marginBottom: "1rem", opacity: 0.5 }}>⬆</div>
            <p style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>
              Drag & drop an image here
            </p>
            <p style={{ fontSize: "0.85rem", color: "var(--color-text-muted, #9e8a6a)" }}>
              or click to browse — JPG, PNG, WEBP supported
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              style={{ display: "none" }}
              onChange={(e) => handleFile(e.target.files[0])}
            />
          </div>
        )}

        {/* Preview + analyze */}
        {preview && (
          <div style={{ marginBottom: "2rem" }}>
            <div style={{
              display: "grid",
              gridTemplateColumns: result ? "1fr 1fr" : "1fr",
              gap: "2rem",
              alignItems: "start"
            }}>
              {/* Image preview */}
              <div>
                <img
                  src={preview}
                  alt="Uploaded artifact"
                  style={{
                    width: "100%",
                    borderRadius: "8px",
                    objectFit: "cover",
                    maxHeight: "420px",
                    display: "block"
                  }}
                />
                <div style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
                  <button
                    onClick={handleAnalyze}
                    disabled={loading}
                    style={{
                      flex: 1,
                      padding: "0.8rem 1.5rem",
                      background: loading ? "rgba(201,162,39,0.3)" : "var(--color-gold, #c9a227)",
                      color: loading ? "var(--color-text-muted, #9e8a6a)" : "#1a1208",
                      border: "none",
                      borderRadius: "6px",
                      fontSize: "0.9rem",
                      fontWeight: "600",
                      cursor: loading ? "not-allowed" : "pointer",
                      letterSpacing: "0.05em",
                      transition: "all 0.2s"
                    }}
                  >
                    {loading ? "Analyzing…" : "Identify Artifact"}
                  </button>
                  <button
                    onClick={handleReset}
                    style={{
                      padding: "0.8rem 1.2rem",
                      background: "transparent",
                      color: "var(--color-text-muted, #9e8a6a)",
                      border: "1px solid rgba(201,162,39,0.2)",
                      borderRadius: "6px",
                      fontSize: "0.9rem",
                      cursor: "pointer"
                    }}
                  >
                    Reset
                  </button>
                </div>
              </div>

              {/* Result */}
              {result && (
                <div style={{
                  background: "rgba(201,162,39,0.04)",
                  border: "1px solid rgba(201,162,39,0.15)",
                  borderRadius: "8px",
                  padding: "1.5rem",
                }}>
                  <p style={{
                    fontSize: "0.7rem",
                    letterSpacing: "0.15em",
                    textTransform: "uppercase",
                    color: "var(--color-gold, #c9a227)",
                    marginBottom: "1rem"
                  }}>
                    Arkana's Analysis
                  </p>
                  <p style={{
                    fontSize: "0.95rem",
                    lineHeight: 1.8,
                    color: "var(--color-text, #e8d5a3)",
                    whiteSpace: "pre-wrap"
                  }}>
                    {result}
                  </p>
                </div>
              )}
            </div>

            {/* Loading state */}
            {loading && (
              <div style={{
                marginTop: "1.5rem",
                padding: "1.5rem",
                background: "rgba(201,162,39,0.04)",
                border: "1px solid rgba(201,162,39,0.15)",
                borderRadius: "8px",
                textAlign: "center"
              }}>
                <p style={{ color: "var(--color-text-muted, #9e8a6a)", fontSize: "0.9rem" }}>
                  Arkana is examining the artifact…
                </p>
              </div>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            padding: "1rem 1.5rem",
            background: "rgba(200,50,50,0.08)",
            border: "1px solid rgba(200,50,50,0.2)",
            borderRadius: "6px",
            color: "#e08080",
            fontSize: "0.9rem"
          }}>
            {error}
          </div>
        )}

      </div>
    </div>
  );
}