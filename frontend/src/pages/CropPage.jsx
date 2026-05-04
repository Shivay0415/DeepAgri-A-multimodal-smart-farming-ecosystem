import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import PageHero from "../components/PageHero";
import { useWorkspace } from "../context/WorkspaceContext";
import { requestCropRecommendation } from "../lib/api";

const initialForm = {
  nitrogen: "80",
  phosphorus: "45",
  potassium: "40",
  humidity_pct: "72",
  ph: "6.6",
  temperature_c: "29",
  rainfall_mm: "55",
  location: "",
};

const fields = [
  { name: "nitrogen", label: "Nitrogen (N)", type: "number", step: "0.1" },
  { name: "phosphorus", label: "Phosphorus (P)", type: "number", step: "0.1" },
  { name: "potassium", label: "Potassium (K)", type: "number", step: "0.1" },
  { name: "temperature_c", label: "Temperature (C)", type: "number", step: "0.1" },
  { name: "humidity_pct", label: "Humidity (%)", type: "number", step: "0.1" },
  { name: "ph", label: "Soil pH", type: "number", step: "0.1" },
  { name: "rainfall_mm", label: "Rainfall (mm)", type: "number", step: "0.1" },
  { name: "location", label: "Location (optional)", type: "text" },
];

function toNumberOrNull(value) {
  return value === "" ? null : Number(value);
}

function CropPage() {
  const { cropReport, saveCropReport } = useWorkspace();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(cropReport);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setResult(cropReport);
  }, [cropReport]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await requestCropRecommendation({
        nitrogen: Number(form.nitrogen),
        phosphorus: Number(form.phosphorus),
        potassium: Number(form.potassium),
        humidity_pct: toNumberOrNull(form.humidity_pct),
        ph: Number(form.ph),
        temperature_c: toNumberOrNull(form.temperature_c),
        rainfall_mm: toNumberOrNull(form.rainfall_mm),
        location: form.location.trim() || null,
      });

      setResult(data);
      saveCropReport(data);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to analyze soil.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHero
        eyebrow="Module 1"
        title="Crop Recommendation Engine"
        description="Turn N, P, K, temperature, humidity, pH, and rainfall into a recommended crop before the farmer commits the season."
        accent="soil"
      >
        <div className="hero-badge-stack">
          <span>Tabular intelligence</span>
          <span>Connected to shared workspace</span>
        </div>
      </PageHero>

      <section className="operation-grid">
        <form className="operation-card" onSubmit={handleSubmit}>
          <div className="operation-card__header">
            <div>
              <p className="section-label">Soil Intake</p>
              <h2>Enter farm chemistry</h2>
            </div>
            <span className="inline-chip">Crop API</span>
          </div>

          <div className="form-grid">
            {fields.map((field) => (
              <label className="field-group" key={field.name}>
                <span>{field.label}</span>
                <input
                  name={field.name}
                  type={field.type}
                  step={field.step}
                  value={form[field.name]}
                  onChange={handleChange}
                  placeholder={field.label}
                  required={field.name !== "location"}
                />
              </label>
            ))}
          </div>

          <div className="quick-actions">
            <button className="ghost-link-button" type="button" onClick={() => setForm(initialForm)}>
              Load sample soil profile
            </button>
          </div>

          <div className="form-actions">
            <button className="hero-button hero-button--primary" type="submit" disabled={loading}>
              {loading ? "Analyzing..." : "Recommend Crop"}
            </button>
            <button
              className="hero-button hero-button--secondary"
              type="button"
              onClick={() => {
                setForm(initialForm);
                setResult(null);
                setError("");
                saveCropReport(null);
              }}
            >
              Reset
            </button>
          </div>
        </form>

        <section className="operation-card result-panel">
          <div className="operation-card__header">
            <div>
              <p className="section-label">Decision Output</p>
              <h2>Recommended crop</h2>
            </div>
            <span className="inline-chip">
              {result?.model_status === "trained" ? "Trained engine" : "Rule-guided engine"}
            </span>
          </div>

          {loading ? (
            <div className="empty-state">
              <h3>Running soil analysis...</h3>
              <p>The engine is scoring crop suitability against the submitted farm profile.</p>
            </div>
          ) : error ? (
            <div className="empty-state empty-state--error">
              <h3>Recommendation request failed</h3>
              <p>{error}</p>
            </div>
          ) : !result ? (
            <div className="empty-state">
              <h3>Waiting for your first soil reading</h3>
              <p>Once a crop is recommended here, the irrigation, disease, market, and advisor pages can reuse it.</p>
            </div>
          ) : (
            <>
              <div className="headline-result soil">
                <div>
                  <span>Primary recommendation</span>
                  <strong>{result.recommended_crop}</strong>
                </div>
                <div className="headline-result__score">
                  {Math.round((result.confidence || 0) * 100)}%
                </div>
              </div>

              <div className="stacked-list">
                {result.top_predictions?.map((item) => (
                  <article className="detail-card" key={item.crop}>
                    <div className="detail-card__topline">
                      <strong>{item.crop}</strong>
                      <span>{Math.round((item.confidence || 0) * 100)}%</span>
                    </div>
                    <ul>
                      {item.rationale?.map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>
                  </article>
                ))}
              </div>

              <div className="form-actions result-actions">
                <button
                  className="hero-button hero-button--water"
                  type="button"
                  onClick={() => navigate("/irrigation")}
                >
                  Plan Irrigation
                </button>
                <button
                  className="hero-button hero-button--secondary"
                  type="button"
                  onClick={() => navigate("/disease")}
                >
                  Open Disease Desk
                </button>
              </div>
            </>
          )}
        </section>
      </section>
    </>
  );
}

export default CropPage;
