import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import PageHero from "../components/PageHero";
import { useWorkspace } from "../context/WorkspaceContext";
import { requestIrrigationPlan } from "../lib/api";

const initialForm = {
  crop: "",
  soil_moisture_pct: "34",
  rainfall_forecast_mm: "6",
  temperature_c: "30",
  humidity_pct: "66",
  area_hectares: "1.5",
  growth_stage: "vegetative",
  location: "",
  use_live_weather: false,
};

const growthStageOptions = ["seedling", "vegetative", "flowering", "harvest"];

function toNumberOrNull(value) {
  return value === "" ? null : Number(value);
}

function IrrigationPage() {
  const { cropReport, irrigationPlan, saveIrrigationPlan } = useWorkspace();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(irrigationPlan);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setResult(irrigationPlan);
  }, [irrigationPlan]);

  useEffect(() => {
    if (cropReport?.recommended_crop && !form.crop) {
      setForm((current) => ({ ...current, crop: cropReport.recommended_crop }));
    }
  }, [cropReport, form.crop]);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await requestIrrigationPlan({
        crop: form.crop.trim(),
        soil_moisture_pct: Number(form.soil_moisture_pct),
        rainfall_forecast_mm: toNumberOrNull(form.rainfall_forecast_mm),
        temperature_c: toNumberOrNull(form.temperature_c),
        humidity_pct: toNumberOrNull(form.humidity_pct),
        area_hectares: Number(form.area_hectares),
        growth_stage: form.growth_stage,
        location: form.location.trim() || null,
        use_live_weather: form.use_live_weather,
      });

      setResult(data);
      saveIrrigationPlan(data);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to plan irrigation.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHero
        eyebrow="Module 2"
        title="Smart Irrigation and Weather Analysis"
        description="Give the farmer a precise watering action using crop stage, soil moisture, climate, area, and optional live weather."
        accent="water"
      >
        <div className="hero-badge-stack">
          <span>Water optimization</span>
          <span>Live weather optional</span>
        </div>
      </PageHero>

      <section className="operation-grid">
        <form className="operation-card" onSubmit={handleSubmit}>
          <div className="operation-card__header">
            <div>
              <p className="section-label">Field Input</p>
              <h2>Plan field watering</h2>
            </div>
            <span className="inline-chip">Irrigation API</span>
          </div>

          <div className="form-grid">
            <label className="field-group">
              <span>Crop</span>
              <input name="crop" value={form.crop} onChange={handleChange} placeholder="cotton" required />
            </label>
            <label className="field-group">
              <span>Growth Stage</span>
              <select name="growth_stage" value={form.growth_stage} onChange={handleChange}>
                {growthStageOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label className="field-group">
              <span>Soil Moisture (%)</span>
              <input name="soil_moisture_pct" type="number" step="0.1" value={form.soil_moisture_pct} onChange={handleChange} required />
            </label>
            <label className="field-group">
              <span>Area (hectares)</span>
              <input name="area_hectares" type="number" step="0.1" value={form.area_hectares} onChange={handleChange} required />
            </label>
            <label className="field-group">
              <span>Rainfall Forecast (mm)</span>
              <input name="rainfall_forecast_mm" type="number" step="0.1" value={form.rainfall_forecast_mm} onChange={handleChange} required={!form.use_live_weather} />
            </label>
            <label className="field-group">
              <span>Temperature (C)</span>
              <input name="temperature_c" type="number" step="0.1" value={form.temperature_c} onChange={handleChange} required={!form.use_live_weather} />
            </label>
            <label className="field-group">
              <span>Humidity (%)</span>
              <input name="humidity_pct" type="number" step="0.1" value={form.humidity_pct} onChange={handleChange} required={!form.use_live_weather} />
            </label>
            <label className="field-group">
              <span>Location</span>
              <input name="location" value={form.location} onChange={handleChange} placeholder="Coimbatore, IN" />
            </label>
          </div>

          <div className="quick-actions">
            {cropReport?.recommended_crop ? (
              <button
                className="ghost-link-button"
                type="button"
                onClick={() => setForm((current) => ({ ...current, crop: cropReport.recommended_crop }))}
              >
                Use Module 1 crop
              </button>
            ) : null}
            <button
              className="ghost-link-button"
              type="button"
              onClick={() =>
                setForm({
                  ...initialForm,
                  crop: cropReport?.recommended_crop || "cotton",
                })
              }
            >
              Load seminar irrigation case
            </button>
          </div>

          <label className="toggle-row">
            <input name="use_live_weather" type="checkbox" checked={form.use_live_weather} onChange={handleChange} />
            <span>Use live weather when the backend has an OpenWeatherMap API key configured</span>
          </label>

          <div className="form-actions">
            <button className="hero-button hero-button--water" type="submit" disabled={loading}>
              {loading ? "Planning..." : "Plan Irrigation"}
            </button>
            <button
              className="hero-button hero-button--secondary"
              type="button"
              onClick={() => {
                setForm({
                  ...initialForm,
                  crop: cropReport?.recommended_crop || "",
                });
                setResult(null);
                setError("");
                saveIrrigationPlan(null);
              }}
            >
              Reset
            </button>
          </div>
        </form>

        <section className="operation-card result-panel">
          <div className="operation-card__header">
            <div>
              <p className="section-label">Water Action</p>
              <h2>Irrigation output</h2>
            </div>
            <span className="inline-chip">
              {result?.model_status === "trained" ? "Trained engine" : "Rule-guided engine"}
            </span>
          </div>

          {loading ? (
            <div className="empty-state">
              <h3>Building irrigation plan...</h3>
              <p>The engine is combining field and weather signals into a water action.</p>
            </div>
          ) : error ? (
            <div className="empty-state empty-state--error">
              <h3>Irrigation request failed</h3>
              <p>{error}</p>
            </div>
          ) : !result ? (
            <div className="empty-state">
              <h3>No irrigation plan yet</h3>
              <p>Use the crop recommendation from Module 1 or enter the crop manually to generate the next action.</p>
            </div>
          ) : (
            <>
              <div className="headline-result water">
                <div>
                  <span>Recommended action</span>
                  <strong>{result.recommended_window}</strong>
                </div>
                <div className="headline-result__metric">
                  {Math.round(result.total_water_liters || 0).toLocaleString()} L
                </div>
              </div>

              <div className="meta-grid">
                <article className="metric-card">
                  <span>Water depth</span>
                  <strong>{result.water_depth_mm} mm</strong>
                </article>
                <article className="metric-card">
                  <span>Need status</span>
                  <strong>{result.irrigation_needed ? "Irrigation required" : "Hold water"}</strong>
                </article>
                <article className="metric-card">
                  <span>Weather source</span>
                  <strong>{result.weather_summary?.status || "manual"}</strong>
                </article>
              </div>

              <div className="detail-card detail-card--soft">
                <div className="detail-card__topline">
                  <strong>Applied weather context</strong>
                  <span>{result.weather_summary?.source || "Manual form input"}</span>
                </div>
                <p>
                  {result.weather_summary?.location
                    ? `${result.weather_summary.location} | `
                    : ""}
                  {result.weather_summary?.condition || "No weather description available"}
                </p>
              </div>

              <div className="stacked-list">
                {result.rationale?.map((item) => (
                  <article className="detail-card" key={item}>
                    <p>{item}</p>
                  </article>
                ))}
              </div>

              <div className="form-actions result-actions">
                <button
                  className="hero-button hero-button--primary"
                  type="button"
                  onClick={() => navigate("/disease")}
                >
                  Continue to Disease Desk
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

export default IrrigationPage;
