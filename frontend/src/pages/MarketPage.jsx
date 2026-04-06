import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import PageHero from "../components/PageHero";
import { useWorkspace } from "../context/WorkspaceContext";
import { requestMarketForecast } from "../lib/api";

const initialForm = {
  crop: "",
  market_name: "Coimbatore Market",
  current_price_per_quintal: "",
  expected_yield_tons: "4.2",
  horizon_days: "14",
};

function toNumberOrNull(value) {
  return value === "" ? null : Number(value);
}

function MarketPage() {
  const { cropReport, marketReport, saveMarketReport } = useWorkspace();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(marketReport);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (cropReport?.recommended_crop && !form.crop) {
      setForm((current) => ({ ...current, crop: cropReport.recommended_crop }));
    }
  }, [cropReport, form.crop]);

  useEffect(() => {
    setResult(marketReport);
  }, [marketReport]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await requestMarketForecast({
        crop: form.crop.trim(),
        market_name: form.market_name.trim() || null,
        current_price_per_quintal: toNumberOrNull(form.current_price_per_quintal),
        expected_yield_tons: Number(form.expected_yield_tons),
        horizon_days: Number(form.horizon_days),
      });

      setResult(data);
      saveMarketReport(data);
    } catch (requestError) {
      setResult(null);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to generate the market forecast.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHero
        eyebrow="Module 4"
        title="Market Intelligence and Yield Forecasting"
        description="Estimate the best selling window, peak price, and likely revenue so the farmer can choose when to sell instead of reacting blindly."
        accent="sun"
      >
        <div className="hero-badge-stack">
          <span>Price timing</span>
          <span>Revenue outlook</span>
        </div>
      </PageHero>

      <section className="operation-grid">
        <form className="operation-card" onSubmit={handleSubmit}>
          <div className="operation-card__header">
            <div>
              <p className="section-label">Market Input</p>
              <h2>Forecast selling strategy</h2>
            </div>
            <span className="inline-chip">Market API</span>
          </div>

          <div className="form-grid">
            <label className="field-group">
              <span>Crop</span>
              <input
                name="crop"
                value={form.crop}
                onChange={handleChange}
                placeholder="cotton"
                required
              />
            </label>
            <label className="field-group">
              <span>Market Name</span>
              <input name="market_name" value={form.market_name} onChange={handleChange} />
            </label>
            <label className="field-group">
              <span>Current Price per Quintal (optional)</span>
              <input
                name="current_price_per_quintal"
                type="number"
                step="0.1"
                value={form.current_price_per_quintal}
                onChange={handleChange}
                placeholder="Leave blank to use dataset history"
              />
            </label>
            <label className="field-group">
              <span>Expected Yield (tons)</span>
              <input
                name="expected_yield_tons"
                type="number"
                step="0.1"
                value={form.expected_yield_tons}
                onChange={handleChange}
                required
              />
            </label>
            <label className="field-group">
              <span>Forecast Horizon (days)</span>
              <input
                name="horizon_days"
                type="number"
                min="3"
                max="30"
                value={form.horizon_days}
                onChange={handleChange}
                required
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
              Load seminar market case
            </button>
          </div>

          <p className="operation-note">
            Leave the current price blank to let the backend use the bundled market history dataset.
          </p>

          <div className="form-actions">
            <button className="hero-button hero-button--sun" type="submit" disabled={loading}>
              {loading ? "Forecasting..." : "Forecast Market"}
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
                saveMarketReport(null);
              }}
            >
              Reset
            </button>
          </div>
        </form>

        <section className="operation-card result-panel">
          <div className="operation-card__header">
            <div>
              <p className="section-label">Forecast Output</p>
              <h2>Best selling window</h2>
            </div>
            <span className="inline-chip">Revenue-aware</span>
          </div>

          {loading ? (
            <div className="empty-state">
              <h3>Projecting market movement...</h3>
              <p>The backend is combining recent trend and seasonal movement into a sale window.</p>
            </div>
          ) : error ? (
            <div className="empty-state empty-state--error">
              <h3>Market forecast failed</h3>
              <p>{error}</p>
            </div>
          ) : !result ? (
            <div className="empty-state">
              <h3>No market strategy yet</h3>
              <p>Generate the forecast to display the best sale date, price outlook, and expected revenue.</p>
            </div>
          ) : (
            <>
              <div className="headline-result sun">
                <div>
                  <span>Best sale date</span>
                  <strong>{result.best_sale_date}</strong>
                </div>
                <div className="headline-result__metric">
                  Rs {Math.round(result.peak_price_per_quintal || 0)}
                </div>
              </div>

              <div className="meta-grid">
                <article className="metric-card">
                  <span>Expected revenue</span>
                  <strong>Rs {Math.round(result.expected_revenue || 0).toLocaleString()}</strong>
                </article>
                <article className="metric-card">
                  <span>Price source</span>
                  <strong>{result.price_source}</strong>
                </article>
                <article className="metric-card">
                  <span>History used</span>
                  <strong>{result.history_points_used} rows</strong>
                </article>
              </div>

              <div className="forecast-grid">
                {result.daily_forecast?.slice(0, 7).map((point) => (
                  <article className="forecast-card" key={point.date}>
                    <span>{point.date}</span>
                    <strong>Rs {Math.round(point.predicted_price_per_quintal)}</strong>
                  </article>
                ))}
              </div>

              <div className="stacked-list">
                {result.rationale?.map((reason) => (
                  <article className="detail-card" key={reason}>
                    <p>{reason}</p>
                  </article>
                ))}
              </div>

              <div className="form-actions result-actions">
                <button
                  className="hero-button hero-button--grain"
                  type="button"
                  onClick={() => navigate("/advisor")}
                >
                  Ask If Farmer Should Wait
                </button>
                <button
                  className="hero-button hero-button--secondary"
                  type="button"
                  onClick={() => navigate("/")}
                >
                  Back to Overview
                </button>
              </div>
            </>
          )}
        </section>
      </section>
    </>
  );
}

export default MarketPage;
