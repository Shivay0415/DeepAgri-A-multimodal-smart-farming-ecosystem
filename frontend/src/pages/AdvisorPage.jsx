import { useEffect, useState } from "react";

import PageHero from "../components/PageHero";
import { useWorkspace } from "../context/WorkspaceContext";
import { requestAdvisorAnswer } from "../lib/api";

const initialForm = {
  question: "What organic spray works for leaf curl in cotton?",
  language: "en",
  crop: "",
  disease_name: "",
};

const languageOptions = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "ta", label: "Tamil" },
];

function AdvisorPage() {
  const {
    cropReport,
    irrigationPlan,
    diseaseReport,
    marketReport,
    advisorAnswer,
    saveAdvisorAnswer,
  } = useWorkspace();
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(advisorAnswer);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setForm((current) => ({
      ...current,
      crop: current.crop || cropReport?.recommended_crop || "",
      disease_name: current.disease_name || diseaseReport?.disease_name || "",
    }));
  }, [cropReport, diseaseReport]);

  useEffect(() => {
    setResult(advisorAnswer);
  }, [advisorAnswer]);

  const setQuestion = (question) => {
    setForm((current) => ({ ...current, question }));
  };

  const submitQuestion = async (languageOverride = form.language) => {
    setLoading(true);
    setError("");

    try {
      const data = await requestAdvisorAnswer({
        question: form.question.trim(),
        language: languageOverride,
        crop: form.crop.trim() || null,
        disease_name: form.disease_name.trim() || null,
      });
      setResult(data);
      saveAdvisorAnswer(data);
      setForm((current) => ({ ...current, language: languageOverride }));
    } catch (requestError) {
      setResult(null);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to get an advisor response right now.",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await submitQuestion(form.language);
  };

  const irrigationQuestion = irrigationPlan
    ? `Why does the system suggest "${irrigationPlan.recommended_window}" for ${cropReport?.recommended_crop || "this crop"}?`
    : "Should I irrigate now or wait until tomorrow?";
  const diseaseQuestion = diseaseReport
    ? `What organic spray works for ${diseaseReport.disease_name} in ${cropReport?.recommended_crop || "my crop"}?`
    : "Why are my leaves turning yellow?";
  const marketQuestion = marketReport
    ? `Should I wait until ${marketReport.best_sale_date} to sell my crop?`
    : "When is the best time to sell after harvest?";

  return (
    <>
      <PageHero
        eyebrow="Module 5"
        title="Multilingual AI Agri-Bot"
        description="Convert soil, irrigation, disease, and market outputs into farmer-friendly answers in English, Hindi, or Tamil."
        accent="grain"
      >
        <div className="hero-badge-stack">
          <span>RAG-style support</span>
          <span>Multilingual answers</span>
        </div>
      </PageHero>

      <section className="operation-grid">
        <form className="operation-card" onSubmit={handleSubmit}>
          <div className="operation-card__header">
            <div>
              <p className="section-label">Consultation Input</p>
              <h2>Ask the farming advisor</h2>
            </div>
            <span className="inline-chip">Chat API</span>
          </div>

          <div className="form-grid">
            <label className="field-group field-group--wide">
              <span>Question</span>
              <textarea
                name="question"
                rows="5"
                value={form.question}
                onChange={(event) =>
                  setForm((current) => ({ ...current, question: event.target.value }))
                }
                required
              />
            </label>
            <label className="field-group">
              <span>Language</span>
              <select
                name="language"
                value={form.language}
                onChange={(event) =>
                  setForm((current) => ({ ...current, language: event.target.value }))
                }
              >
                {languageOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="field-group">
              <span>Crop Context</span>
              <input
                name="crop"
                value={form.crop}
                onChange={(event) =>
                  setForm((current) => ({ ...current, crop: event.target.value }))
                }
                placeholder="cotton"
              />
            </label>
            <label className="field-group">
              <span>Disease Context</span>
              <input
                name="disease_name"
                value={form.disease_name}
                onChange={(event) =>
                  setForm((current) => ({ ...current, disease_name: event.target.value }))
                }
                placeholder="Leaf Curl Virus"
              />
            </label>
          </div>

          <div className="quick-actions">
            <button className="ghost-link-button" type="button" onClick={() => setQuestion(diseaseQuestion)}>
              Load disease remedy question
            </button>
            <button className="ghost-link-button" type="button" onClick={() => setQuestion(irrigationQuestion)}>
              Load irrigation question
            </button>
            <button className="ghost-link-button" type="button" onClick={() => setQuestion(marketQuestion)}>
              Load market timing question
            </button>
          </div>

          <div className="form-actions">
            <button className="hero-button hero-button--grain" type="submit" disabled={loading}>
              {loading ? "Generating..." : "Ask Agri-Bot"}
            </button>
            <button
              className="hero-button hero-button--secondary"
              type="button"
              onClick={() => {
                setForm({
                  ...initialForm,
                  crop: cropReport?.recommended_crop || "",
                  disease_name: diseaseReport?.disease_name || "",
                });
                setResult(null);
                setError("");
                saveAdvisorAnswer(null);
              }}
            >
              Reset
            </button>
          </div>
        </form>

        <section className="operation-card result-panel">
          <div className="operation-card__header">
            <div>
              <p className="section-label">Advisor Output</p>
              <h2>Farmer-friendly explanation</h2>
            </div>
            <span className="inline-chip">English / Hindi / Tamil</span>
          </div>

          {loading ? (
            <div className="empty-state">
              <h3>Generating the answer...</h3>
              <p>The advisor is matching the question against the agriculture knowledge base.</p>
            </div>
          ) : error ? (
            <div className="empty-state empty-state--error">
              <h3>Advisor request failed</h3>
              <p>{error}</p>
            </div>
          ) : !result ? (
            <div className="empty-state">
              <h3>No answer yet</h3>
              <p>Ask about disease remedies, irrigation timing, crop stress, or market timing to generate a farmer-facing response.</p>
            </div>
          ) : (
            <>
              <div className="answer-card">
                <span>Response language: {result.language.toUpperCase()}</span>
                <p>{result.answer}</p>
              </div>

              <div className="quick-actions">
                <button
                  className="ghost-link-button"
                  type="button"
                  onClick={() => submitQuestion("en")}
                  disabled={loading}
                >
                  English
                </button>
                <button
                  className="ghost-link-button"
                  type="button"
                  onClick={() => submitQuestion("hi")}
                  disabled={loading}
                >
                  Hindi
                </button>
                <button
                  className="ghost-link-button"
                  type="button"
                  onClick={() => submitQuestion("ta")}
                  disabled={loading}
                >
                  Tamil
                </button>
              </div>

              <div className="detail-card detail-card--soft">
                <div className="detail-card__topline">
                  <strong>Knowledge source</strong>
                  <span>RAG-style retrieval</span>
                </div>
                <p>{result.knowledge_source}</p>
              </div>

              <div className="stacked-list">
                {result.follow_up_suggestions?.map((suggestion) => (
                  <article className="detail-card" key={suggestion}>
                    <p>{suggestion}</p>
                  </article>
                ))}
              </div>
            </>
          )}
        </section>
      </section>
    </>
  );
}

export default AdvisorPage;
