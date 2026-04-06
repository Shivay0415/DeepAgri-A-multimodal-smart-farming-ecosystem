import { useState } from "react";

const diseaseInitialForm = {
  crop: "",
  symptom_hint: "leaf curl and twisting",
};

const marketInitialForm = {
  crop: "",
  market_name: "Coimbatore Market",
  current_price_per_quintal: "",
  expected_yield_tons: "4.2",
  horizon_days: "14",
};

const chatInitialForm = {
  question: "What organic spray works for leaf curl?",
  language: "en",
  crop: "",
  disease_name: "",
};

const languageOptions = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "ta", label: "Tamil" },
];

function toNumberOrNull(value) {
  return value === "" || value === null ? null : Number(value);
}

function EmptyStateCard({ moduleLabel, title, message, loading, error }) {
  if (loading) {
    return (
      <div className="result-card loading-card">
        <p className="eyebrow">{moduleLabel}</p>
        <h3>Processing request...</h3>
        <p>{message}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="result-card error-card">
        <p className="eyebrow">{moduleLabel}</p>
        <h3>Request failed</h3>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="result-card empty-card">
      <p className="eyebrow">{moduleLabel}</p>
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}

function DiseaseResultPanel({ result, error, loading }) {
  if (loading || error || !result) {
    return (
      <EmptyStateCard
        moduleLabel="Module 3 Result"
        title="Ready for disease detection"
        message="Upload a leaf image and add a symptom hint to get a diagnosis, severity, and remedy list."
        loading={loading}
        error={error}
      />
    );
  }

  return (
    <div className="result-card">
      <p className="eyebrow">Module 3 Result</p>
      <div className="result-topline">
        <div>
          <h3>{result.disease_name}</h3>
          <p className="result-subtitle">Detected condition for the uploaded leaf</p>
        </div>
        <div className="confidence-pill leaf-pill">{Math.round((result.confidence || 0) * 100)}%</div>
      </div>
      <div className="result-meta">
        <span>Severity: {result.severity}</span>
        <span>{result.model_family}</span>
      </div>
      <div className="prediction-list">
        {Array.isArray(result.remedies) &&
          result.remedies.map((remedy) => (
            <article className="prediction-item" key={remedy}>
              <p>{remedy}</p>
            </article>
          ))}
      </div>
      <div className="prediction-list compact-list">
        {Array.isArray(result.notes) &&
          result.notes.map((note) => (
            <article className="prediction-item" key={note}>
              <p>{note}</p>
            </article>
          ))}
      </div>
    </div>
  );
}

function MarketResultPanel({ result, error, loading }) {
  if (loading || error || !result) {
    return (
      <EmptyStateCard
        moduleLabel="Module 4 Result"
        title="Ready for market forecasting"
        message="Submit the market form to estimate the best selling window, peak price, and expected revenue."
        loading={loading}
        error={error}
      />
    );
  }

  return (
    <div className="result-card">
      <p className="eyebrow">Module 4 Result</p>
      <div className="result-topline">
        <div>
          <h3>{result.best_sale_date}</h3>
          <p className="result-subtitle">Best estimated sale date</p>
        </div>
        <div className="confidence-pill sun-pill">Rs {Math.round(result.peak_price_per_quintal || 0)}</div>
      </div>
      <div className="result-meta">
        <span>Revenue: Rs {Math.round(result.expected_revenue || 0).toLocaleString()}</span>
        <span>Source: {result.price_source || "manual input"}</span>
        <span>History rows: {result.history_points_used || 0}</span>
      </div>
      <div className="prediction-list">
        {Array.isArray(result.daily_forecast) &&
          result.daily_forecast.slice(0, 5).map((point) => (
            <article className="prediction-item" key={point.date}>
              <div className="prediction-head">
                <strong>{point.date}</strong>
                <span>Rs {Math.round(point.predicted_price_per_quintal)}</span>
              </div>
            </article>
          ))}
      </div>
      <div className="prediction-list compact-list">
        {Array.isArray(result.rationale) &&
          result.rationale.map((reason) => (
            <article className="prediction-item" key={reason}>
              <p>{reason}</p>
            </article>
          ))}
      </div>
    </div>
  );
}

function ChatResultPanel({ result, error, loading }) {
  if (loading || error || !result) {
    return (
      <EmptyStateCard
        moduleLabel="Module 5 Result"
        title="Ready for a multilingual farming question"
        message="Ask about disease, irrigation, market timing, or soil issues to get a local-language answer from the backend knowledge base."
        loading={loading}
        error={error}
      />
    );
  }

  return (
    <div className="result-card">
      <p className="eyebrow">Module 5 Result</p>
      <div className="result-topline">
        <div>
          <h3>{result.language.toUpperCase()}</h3>
          <p className="result-subtitle">{result.knowledge_source}</p>
        </div>
        <div className="confidence-pill grain-pill">Q&A</div>
      </div>
      <div className="answer-block">
        <p>{result.answer}</p>
      </div>
      <div className="prediction-list">
        {Array.isArray(result.follow_up_suggestions) &&
          result.follow_up_suggestions.map((item) => (
            <article className="prediction-item" key={item}>
              <p>{item}</p>
            </article>
          ))}
      </div>
    </div>
  );
}

function ExtraModules({ recommendedCrop }) {
  const [diseaseForm, setDiseaseForm] = useState(diseaseInitialForm);
  const [diseaseFile, setDiseaseFile] = useState(null);
  const [diseaseResult, setDiseaseResult] = useState(null);
  const [diseaseLoading, setDiseaseLoading] = useState(false);
  const [diseaseError, setDiseaseError] = useState("");

  const [marketForm, setMarketForm] = useState(marketInitialForm);
  const [marketResult, setMarketResult] = useState(null);
  const [marketLoading, setMarketLoading] = useState(false);
  const [marketError, setMarketError] = useState("");

  const [chatForm, setChatForm] = useState(chatInitialForm);
  const [chatResult, setChatResult] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");

  const handleDiseaseChange = (event) => {
    const { name, value } = event.target;
    setDiseaseForm((current) => ({ ...current, [name]: value }));
  };

  const handleMarketChange = (event) => {
    const { name, value } = event.target;
    setMarketForm((current) => ({ ...current, [name]: value }));
  };

  const handleChatChange = (event) => {
    const { name, value } = event.target;
    setChatForm((current) => ({ ...current, [name]: value }));
  };

  const handleDiseaseSubmit = async (event) => {
    event.preventDefault();
    setDiseaseLoading(true);
    setDiseaseError("");

    try {
      const formData = new FormData();
      formData.append("crop", diseaseForm.crop.trim());
      formData.append("symptom_hint", diseaseForm.symptom_hint.trim());
      if (diseaseFile) {
        formData.append("image", diseaseFile);
      }

      const response = await fetch("/api/v1/disease/detect/", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "The backend rejected the disease request.");
      }

      setDiseaseResult(data);
      setChatForm((current) =>
        current.disease_name ? current : { ...current, disease_name: data.disease_name },
      );
      setChatForm((current) =>
        current.crop ? current : { ...current, crop: diseaseForm.crop.trim() || recommendedCrop || "" },
      );
    } catch (requestError) {
      setDiseaseResult(null);
      setDiseaseError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to reach the disease detection API.",
      );
    } finally {
      setDiseaseLoading(false);
    }
  };

  const handleMarketSubmit = async (event) => {
    event.preventDefault();
    setMarketLoading(true);
    setMarketError("");

    try {
      const payload = {
        crop: marketForm.crop.trim(),
        market_name: marketForm.market_name.trim() || null,
        current_price_per_quintal: toNumberOrNull(marketForm.current_price_per_quintal),
        expected_yield_tons: Number(marketForm.expected_yield_tons),
        horizon_days: Number(marketForm.horizon_days),
      };

      const response = await fetch("/api/v1/market/forecast/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "The backend rejected the market request.");
      }

      setMarketResult(data);
      setChatForm((current) =>
        current.crop ? current : { ...current, crop: marketForm.crop.trim() || recommendedCrop || "" },
      );
    } catch (requestError) {
      setMarketResult(null);
      setMarketError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to reach the market forecasting API.",
      );
    } finally {
      setMarketLoading(false);
    }
  };

  const handleChatSubmit = async (event) => {
    event.preventDefault();
    setChatLoading(true);
    setChatError("");

    try {
      const payload = {
        question: chatForm.question.trim(),
        language: chatForm.language,
        crop: chatForm.crop.trim() || null,
        disease_name: chatForm.disease_name.trim() || null,
      };

      const response = await fetch("/api/v1/chat/ask/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "The backend rejected the chatbot request.");
      }

      setChatResult(data);
    } catch (requestError) {
      setChatResult(null);
      setChatError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to reach the chatbot API.",
      );
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <>
      <section className="section-head">
        <p className="eyebrow">Live Module 3</p>
        <h2>Upload a leaf image and combine it with symptom text for a disease diagnosis.</h2>
      </section>
      <section className="live-lab">
        <form className="lab-card leaf-form" onSubmit={handleDiseaseSubmit}>
          <div className="lab-head">
            <div>
              <p className="eyebrow">Plant Health</p>
              <h3>Disease detection input</h3>
            </div>
            <span className="mini-chip">POST /api/v1/disease/detect/</span>
          </div>
          <div className="form-grid">
            <label className="field-group">
              <span>Crop</span>
              <input name="crop" type="text" value={diseaseForm.crop} onChange={handleDiseaseChange} />
            </label>
            <label className="field-group field-span">
              <span>Symptom Hint</span>
              <textarea
                name="symptom_hint"
                value={diseaseForm.symptom_hint}
                onChange={handleDiseaseChange}
                placeholder="leaf curl, yellowing, brown spots"
              />
            </label>
            <label className="field-group field-span">
              <span>Leaf Image</span>
              <input
                className="file-input"
                type="file"
                accept="image/*"
                onChange={(event) => setDiseaseFile(event.target.files?.[0] || null)}
              />
            </label>
          </div>
          {recommendedCrop ? (
            <div className="inline-actions">
              <button
                className="ghost-button"
                type="button"
                onClick={() =>
                  setDiseaseForm((current) => ({
                    ...current,
                    crop: recommendedCrop,
                  }))
                }
              >
                Use Module 1 crop: {recommendedCrop}
              </button>
            </div>
          ) : null}
          <div className="form-actions">
            <button className="primary-button leaf-button" type="submit" disabled={diseaseLoading}>
              {diseaseLoading ? "Detecting..." : "Detect Disease"}
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => {
                setDiseaseForm(diseaseInitialForm);
                setDiseaseFile(null);
                setDiseaseResult(null);
                setDiseaseError("");
              }}
            >
              Reset
            </button>
          </div>
        </form>
        <DiseaseResultPanel result={diseaseResult} error={diseaseError} loading={diseaseLoading} />
      </section>

      <section className="section-head">
        <p className="eyebrow">Live Module 4</p>
        <h2>Estimate the best sale date and revenue from bundled market history.</h2>
      </section>
      <section className="live-lab">
        <form className="lab-card market-form" onSubmit={handleMarketSubmit}>
          <div className="lab-head">
            <div>
              <p className="eyebrow">Profit Optimization</p>
              <h3>Market forecasting input</h3>
            </div>
            <span className="mini-chip">POST /api/v1/market/forecast/</span>
          </div>
          <div className="form-grid">
            <label className="field-group">
              <span>Crop</span>
              <input name="crop" type="text" value={marketForm.crop} onChange={handleMarketChange} />
            </label>
            <label className="field-group">
              <span>Market Name</span>
              <input name="market_name" type="text" value={marketForm.market_name} onChange={handleMarketChange} />
            </label>
            <label className="field-group">
              <span>Current Price (optional)</span>
              <input
                name="current_price_per_quintal"
                type="number"
                step="0.1"
                value={marketForm.current_price_per_quintal}
                onChange={handleMarketChange}
              />
            </label>
            <label className="field-group">
              <span>Expected Yield (tons)</span>
              <input
                name="expected_yield_tons"
                type="number"
                step="0.1"
                value={marketForm.expected_yield_tons}
                onChange={handleMarketChange}
              />
            </label>
            <label className="field-group">
              <span>Forecast Horizon (days)</span>
              <input
                name="horizon_days"
                type="number"
                step="1"
                value={marketForm.horizon_days}
                onChange={handleMarketChange}
              />
            </label>
          </div>
          {recommendedCrop ? (
            <div className="inline-actions">
              <button
                className="ghost-button"
                type="button"
                onClick={() =>
                  setMarketForm((current) => ({
                    ...current,
                    crop: recommendedCrop,
                  }))
                }
              >
                Use Module 1 crop: {recommendedCrop}
              </button>
            </div>
          ) : null}
          <div className="form-actions">
            <button className="primary-button sun-button" type="submit" disabled={marketLoading}>
              {marketLoading ? "Forecasting..." : "Forecast Market"}
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => {
                setMarketForm(marketInitialForm);
                setMarketResult(null);
                setMarketError("");
              }}
            >
              Reset
            </button>
          </div>
        </form>
        <MarketResultPanel result={marketResult} error={marketError} loading={marketLoading} />
      </section>

      <section className="section-head">
        <p className="eyebrow">Live Module 5</p>
        <h2>Ask the Agri-Bot about disease, irrigation, market, or soil issues.</h2>
      </section>
      <section className="live-lab">
        <form className="lab-card chat-form" onSubmit={handleChatSubmit}>
          <div className="lab-head">
            <div>
              <p className="eyebrow">Expert Consultant</p>
              <h3>Multilingual Agri-Bot input</h3>
            </div>
            <span className="mini-chip">POST /api/v1/chat/ask/</span>
          </div>
          <div className="form-grid">
            <label className="field-group field-span">
              <span>Question</span>
              <textarea name="question" value={chatForm.question} onChange={handleChatChange} />
            </label>
            <label className="field-group">
              <span>Language</span>
              <select name="language" value={chatForm.language} onChange={handleChatChange}>
                {languageOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="field-group">
              <span>Crop</span>
              <input name="crop" type="text" value={chatForm.crop} onChange={handleChatChange} />
            </label>
            <label className="field-group">
              <span>Disease Name</span>
              <input name="disease_name" type="text" value={chatForm.disease_name} onChange={handleChatChange} />
            </label>
          </div>
          <div className="inline-actions multi-inline">
            {recommendedCrop ? (
              <button
                className="ghost-button"
                type="button"
                onClick={() =>
                  setChatForm((current) => ({
                    ...current,
                    crop: recommendedCrop,
                  }))
                }
              >
                Use Module 1 crop
              </button>
            ) : null}
            {diseaseResult?.disease_name ? (
              <button
                className="ghost-button"
                type="button"
                onClick={() =>
                  setChatForm((current) => ({
                    ...current,
                    disease_name: diseaseResult.disease_name,
                  }))
                }
              >
                Use Module 3 disease
              </button>
            ) : null}
          </div>
          <div className="form-actions">
            <button className="primary-button grain-button" type="submit" disabled={chatLoading}>
              {chatLoading ? "Answering..." : "Ask Agri-Bot"}
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => {
                setChatForm(chatInitialForm);
                setChatResult(null);
                setChatError("");
              }}
            >
              Reset
            </button>
          </div>
        </form>
        <ChatResultPanel result={chatResult} error={chatError} loading={chatLoading} />
      </section>
    </>
  );
}

export default ExtraModules;
