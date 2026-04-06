import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import PageHero from "../components/PageHero";
import { useWorkspace } from "../context/WorkspaceContext";
import { requestDiseaseDetection } from "../lib/api";

const initialForm = {
  crop: "",
  symptom_hint: "leaf curl and twisting on tender leaves",
};

async function loadSampleLeafFile() {
  const response = await fetch("/samples/cotton-leaf-curl.svg");
  const blob = await response.blob();
  return new File([blob], "cotton-leaf-curl.svg", {
    type: blob.type || "image/svg+xml",
  });
}

function DiseasePage() {
  const { cropReport, diseaseReport, saveDiseaseReport } = useWorkspace();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [form, setForm] = useState(initialForm);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [result, setResult] = useState(diseaseReport);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (cropReport?.recommended_crop && !form.crop) {
      setForm((current) => ({ ...current, crop: cropReport.recommended_crop }));
    }
  }, [cropReport, form.crop]);

  useEffect(() => {
    setResult(diseaseReport);
  }, [diseaseReport]);

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl("");
      return undefined;
    }

    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedFile]);

  const resetForm = () => {
    setForm({
      ...initialForm,
      crop: cropReport?.recommended_crop || "",
    });
    setSelectedFile(null);
    setResult(null);
    setError("");
    saveDiseaseReport(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!selectedFile) {
      setError("Upload a leaf image or use the built-in seminar sample before analyzing.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await requestDiseaseDetection({
        crop: form.crop.trim(),
        symptomHint: form.symptom_hint.trim(),
        file: selectedFile,
      });
      setResult(data);
      saveDiseaseReport(data);
    } catch (requestError) {
      setResult(null);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to analyze the leaf image.",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = async () => {
    try {
      const file = await loadSampleLeafFile();
      setSelectedFile(file);
      setForm((current) => ({
        ...current,
        crop: current.crop || cropReport?.recommended_crop || "cotton",
        symptom_hint: current.symptom_hint || initialForm.symptom_hint,
      }));
      setError("");
    } catch {
      setError("The built-in sample image could not be loaded.");
    }
  };

  return (
    <>
      <PageHero
        eyebrow="Module 3"
        title="Visual Plant Disease Detection"
        description="Upload a leaf photo, add a symptom hint, and turn field stress into a diagnosis with remedies the farmer can act on immediately."
        accent="leaf"
      >
        <div className="hero-badge-stack">
          <span>Leaf diagnostics</span>
          <span>Remedies ready</span>
        </div>
      </PageHero>

      <section className="operation-grid">
        <form className="operation-card" onSubmit={handleSubmit}>
          <div className="operation-card__header">
            <div>
              <p className="section-label">Field Inspection</p>
              <h2>Analyze a leaf case</h2>
            </div>
            <span className="inline-chip">Disease API</span>
          </div>

          <div className="form-grid">
            <label className="field-group">
              <span>Crop</span>
              <input
                name="crop"
                value={form.crop}
                onChange={(event) =>
                  setForm((current) => ({ ...current, crop: event.target.value }))
                }
                placeholder="cotton"
                required
              />
            </label>
            <label className="field-group field-group--wide">
              <span>Symptom Hint</span>
              <textarea
                name="symptom_hint"
                rows="4"
                value={form.symptom_hint}
                onChange={(event) =>
                  setForm((current) => ({ ...current, symptom_hint: event.target.value }))
                }
                placeholder="leaf curl, yellow spots, mosaic pattern"
              />
            </label>
            <label className="field-group field-group--wide">
              <span>Leaf Image</span>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
              />
            </label>
          </div>

          <div className="quick-actions">
            {cropReport?.recommended_crop ? (
              <button
                className="ghost-link-button"
                type="button"
                onClick={() =>
                  setForm((current) => ({ ...current, crop: cropReport.recommended_crop }))
                }
              >
                Use Module 1 crop
              </button>
            ) : null}
            <button className="ghost-link-button" type="button" onClick={handleLoadSample}>
              Load built-in sample leaf
            </button>
          </div>

          <div className="upload-tile">
            <span>Selected image</span>
            <strong>{selectedFile?.name || "No file chosen yet"}</strong>
            <p>Use your own leaf photo or load the bundled sample for a faster seminar flow.</p>
          </div>

          <div className="form-actions">
            <button className="hero-button hero-button--leaf" type="submit" disabled={loading}>
              {loading ? "Diagnosing..." : "Detect Disease"}
            </button>
            <button className="hero-button hero-button--secondary" type="button" onClick={resetForm}>
              Reset
            </button>
          </div>
        </form>

        <section className="operation-card result-panel">
          <div className="operation-card__header">
            <div>
              <p className="section-label">Diagnosis Output</p>
              <h2>Plant health status</h2>
            </div>
            <span className="inline-chip">Connected to advisor</span>
          </div>

          {loading ? (
            <div className="empty-state">
              <h3>Analyzing the uploaded leaf...</h3>
              <p>The system is matching the case against the disease catalog and remedy guidance.</p>
            </div>
          ) : error ? (
            <div className="empty-state empty-state--error">
              <h3>Disease analysis failed</h3>
              <p>{error}</p>
            </div>
          ) : !result ? (
            <div className="empty-state">
              <h3>No diagnosis yet</h3>
              <p>Submit a leaf case to generate a disease name, severity level, and recommended remedies.</p>
            </div>
          ) : (
            <>
              <div className="headline-result leaf">
                <div>
                  <span>Detected condition</span>
                  <strong>{result.disease_name}</strong>
                </div>
                <div className="headline-result__score">
                  {Math.round((result.confidence || 0) * 100)}%
                </div>
              </div>

              <div className="meta-grid">
                <article className="metric-card">
                  <span>Severity</span>
                  <strong>{result.severity}</strong>
                </article>
                <article className="metric-card">
                  <span>Crop</span>
                  <strong>{result.crop}</strong>
                </article>
                <article className="metric-card">
                  <span>Image status</span>
                  <strong>{selectedFile ? "Uploaded" : "Pending"}</strong>
                </article>
              </div>

              {previewUrl ? (
                <div className="preview-frame">
                  <img src={previewUrl} alt="Selected leaf preview" />
                </div>
              ) : null}

              <div className="stacked-list">
                {result.remedies?.map((remedy) => (
                  <article className="detail-card" key={remedy}>
                    <p>{remedy}</p>
                  </article>
                ))}
              </div>

              <div className="detail-card detail-card--soft">
                <div className="detail-card__topline">
                  <strong>Field notes</strong>
                  <span>Context summary</span>
                </div>
                <ul>
                  {result.notes?.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </div>

              <div className="form-actions result-actions">
                <button
                  className="hero-button hero-button--grain"
                  type="button"
                  onClick={() => navigate("/advisor")}
                >
                  Ask Agri-Bot About This
                </button>
                <button
                  className="hero-button hero-button--secondary"
                  type="button"
                  onClick={() => navigate("/market")}
                >
                  Open Market Studio
                </button>
              </div>
            </>
          )}
        </section>
      </section>
    </>
  );
}

export default DiseasePage;
