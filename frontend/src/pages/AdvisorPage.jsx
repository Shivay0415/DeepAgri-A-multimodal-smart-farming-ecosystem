import { useEffect, useMemo, useRef, useState } from "react";

import PageHero from "../components/PageHero";
import { useWorkspace } from "../context/WorkspaceContext";
import { requestAdvisorAnswer } from "../lib/api";

const languageOptions = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "ta", label: "Tamil" },
];

function createMessage(role, content, extra = {}) {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    content,
    ...extra,
  };
}

function buildIntroMessage() {
  return createMessage(
    "assistant",
    "Hello, I am AgriPulse AI. Ask anything about crop choice, irrigation timing, disease symptoms, remedies, market strategy, or general farming decisions. I will use your module outputs whenever they are available.",
    {
      isIntro: true,
    },
  );
}

function summarizeCropReport(cropReport) {
  if (!cropReport?.recommended_crop) {
    return "";
  }
  return `Recommended crop is ${cropReport.recommended_crop} with ${
    Math.round((cropReport.confidence || 0) * 100)
  }% confidence.`;
}

function summarizeIrrigationPlan(irrigationPlan) {
  if (!irrigationPlan) {
    return "";
  }

  if (irrigationPlan.irrigation_needed) {
    return `Irrigation is recommended during ${irrigationPlan.recommended_window} with about ${Math.round(
      irrigationPlan.total_water_liters || 0,
    ).toLocaleString()} liters of water.`;
  }

  return "The irrigation planner says no immediate watering is needed.";
}

function summarizeDiseaseReport(diseaseReport) {
  if (!diseaseReport?.disease_name) {
    return "";
  }

  return `${diseaseReport.disease_name} is the latest detected issue. Suggested remedy: ${
    diseaseReport.remedy || "review the disease module for treatment guidance"
  }.`;
}

function summarizeMarketReport(marketReport) {
  if (!marketReport?.best_sale_date) {
    return "";
  }

  return `The market module suggests ${marketReport.best_sale_date} as the strongest sale date with projected revenue of ${
    marketReport.projected_revenue
      ? `${Math.round(marketReport.projected_revenue).toLocaleString()}`
      : "the latest forecast"
  }.`;
}

function AdvisorPage() {
  const {
    cropReport,
    irrigationPlan,
    diseaseReport,
    marketReport,
    advisorAnswer,
    saveAdvisorAnswer,
  } = useWorkspace();
  const [language, setLanguage] = useState(advisorAnswer?.language || "en");
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState(
    advisorAnswer?.messages?.length ? advisorAnswer.messages : [buildIntroMessage()],
  );
  const [followUpSuggestions, setFollowUpSuggestions] = useState(
    advisorAnswer?.followUpSuggestions || [],
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const transcriptRef = useRef(null);

  useEffect(() => {
    if (!advisorAnswer) {
      return;
    }

    setLanguage(advisorAnswer.language || "en");
    setMessages(
      advisorAnswer.messages?.length ? advisorAnswer.messages : [buildIntroMessage()],
    );
    setFollowUpSuggestions(advisorAnswer.followUpSuggestions || []);
  }, [advisorAnswer]);

  useEffect(() => {
    const node = transcriptRef.current;
    if (node) {
      node.scrollTop = node.scrollHeight;
    }
  }, [messages, loading]);

  const context = useMemo(
    () => ({
      crop: cropReport?.recommended_crop || "",
      crop_summary: summarizeCropReport(cropReport),
      disease_name: diseaseReport?.disease_name || "",
      disease_summary: summarizeDiseaseReport(diseaseReport),
      irrigation_summary: summarizeIrrigationPlan(irrigationPlan),
      market_summary: summarizeMarketReport(marketReport),
    }),
    [cropReport, irrigationPlan, diseaseReport, marketReport],
  );

  const latestSession = advisorAnswer || null;
  const visibleMessages = messages.length ? messages : [buildIntroMessage()];
  const connectedContext = [
    { label: "Crop", value: context.crop || "No crop recommendation yet" },
    {
      label: "Irrigation",
      value: context.irrigation_summary || "No irrigation plan connected yet",
    },
    {
      label: "Disease",
      value: context.disease_name || "No disease diagnosis connected yet",
    },
    {
      label: "Market",
      value: context.market_summary || "No market forecast connected yet",
    },
  ];

  const submitQuestion = async (questionText) => {
    const cleanQuestion = questionText.trim();
    if (!cleanQuestion) {
      return;
    }

    const userMessage = createMessage("user", cleanQuestion);
    const baseConversation = messages.filter((message) => !message.isIntro);
    const visibleConversation = [...messages, userMessage];
    setLoading(true);
    setError("");
    setDraft("");
    setMessages(visibleConversation);

    try {
      const data = await requestAdvisorAnswer({
        messages: [...baseConversation, userMessage].map(({ role, content }) => ({
          role,
          content,
        })),
        language,
        context,
      });

      const assistantMessage = createMessage("assistant", data.answer, {
        providerLabel: data.provider_label,
        responseMode: data.response_mode,
        model: data.model,
      });
      const sessionMessages = [...baseConversation, userMessage, assistantMessage];
      const session = {
        language: data.language,
        messages: sessionMessages,
        providerLabel: data.provider_label,
        providerName: data.provider_name,
        model: data.model,
        responseMode: data.response_mode,
        providerNotice: data.provider_notice,
        knowledgeSource: data.knowledge_source,
        followUpSuggestions: data.follow_up_suggestions || [],
        configuredProviders: data.configured_providers || [],
      };

      setMessages(sessionMessages);
      setLanguage(data.language || language);
      setFollowUpSuggestions(session.followUpSuggestions);
      saveAdvisorAnswer(session);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to get an advisor response right now.",
      );
      setMessages(messages);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await submitQuestion(draft);
  };

  return (
    <>
      <PageHero
        eyebrow="Module 5"
        title="Agri-Bot AI Assistant"
        description="Chat naturally with the farm advisor. It can use crop, irrigation, disease, and market context while replying in English, Hindi, or Tamil."
        accent="grain"
      >
        <div className="hero-badge-stack">
          <span>OpenAI / Gemini ready</span>
          <span>Context-aware farm chat</span>
        </div>
      </PageHero>

      <section className="advisor-layout">
        <section className="operation-card advisor-chat-card">
          <div className="operation-card__header advisor-chat-card__header">
            <div>
              <p className="section-label">AI Conversation</p>
              <h2>Chat with Agri-Bot</h2>
              <p className="workspace-note">
                Ask naturally. The bot will reuse your connected module outputs whenever they are
                available.
              </p>
            </div>
            <div className="advisor-toolbar">
              <label className="advisor-language">
                <span>Response Language</span>
                <select value={language} onChange={(event) => setLanguage(event.target.value)}>
                  {languageOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="status-button"
                type="button"
                onClick={() => {
                  setMessages([buildIntroMessage()]);
                  setFollowUpSuggestions([]);
                  setDraft("");
                  setError("");
                  saveAdvisorAnswer(null);
                }}
              >
                New Chat
              </button>
            </div>
          </div>

          <div className="chat-transcript" ref={transcriptRef}>
            {visibleMessages.map((message) => (
              <article
                className={`chat-bubble chat-bubble--${message.role}`}
                key={message.id}
              >
                <div className="chat-bubble__meta">
                  <span>{message.role === "assistant" ? "Agri-Bot" : "You"}</span>
                  {message.role === "assistant" && !message.isIntro ? (
                    <small>
                      {message.providerLabel || latestSession?.providerLabel || "Local fallback"}
                    </small>
                  ) : null}
                </div>
                <p>{message.content}</p>
              </article>
            ))}

            {loading ? (
              <article className="chat-bubble chat-bubble--assistant chat-bubble--typing">
                <div className="chat-bubble__meta">
                  <span>Agri-Bot</span>
                  <small>Thinking...</small>
                </div>
                <p>Preparing a context-aware answer...</p>
              </article>
            ) : null}
          </div>

          {error ? (
            <div className="empty-state empty-state--error">
              <h3>Agri-Bot request failed</h3>
              <p>{error}</p>
            </div>
          ) : null}

          {followUpSuggestions.length ? (
            <div className="chat-suggestions">
              {followUpSuggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  className="ghost-link-button"
                  type="button"
                  onClick={() => submitQuestion(suggestion)}
                  disabled={loading}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          ) : null}

          <form className="chat-composer" onSubmit={handleSubmit}>
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask anything about your farm, crop health, irrigation timing, market strategy, or remedies..."
              rows="4"
            />

            <div className="chat-composer__actions">
              <p className="chat-composer__hint">
                The Agri-Bot can answer generally, but it becomes much stronger when crop, disease,
                irrigation, and market modules are already connected.
              </p>
              <button
                className="hero-button hero-button--grain"
                type="submit"
                disabled={loading || !draft.trim()}
              >
                {loading ? "Generating..." : "Send"}
              </button>
            </div>
          </form>
        </section>

        <aside className="advisor-sidebar">
          <section className="operation-card advisor-side-card">
            <div className="operation-card__header">
              <div>
                <p className="section-label">Connected Context</p>
                <h2>Live farm signals</h2>
              </div>
              <span className="inline-chip">Modules 1-4</span>
            </div>

            <div className="context-summary">
              {connectedContext.map((item) => (
                <article className="detail-card" key={item.label}>
                  <span>{item.label}</span>
                  <p>{item.value}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="operation-card advisor-side-card">
            <div className="operation-card__header">
              <div>
                <p className="section-label">AI Backend</p>
                <h2>Response engine</h2>
              </div>
              <span className="inline-chip">
                {latestSession?.responseMode === "provider" ? "Provider live" : "Fallback ready"}
              </span>
            </div>

            <div className="detail-card detail-card--soft">
              <div className="detail-card__topline">
                <strong>{latestSession?.providerLabel || "Local agriculture fallback"}</strong>
                <span>{language.toUpperCase()}</span>
              </div>
              <p>
                {latestSession?.responseMode === "provider"
                  ? `Replies are currently generated by ${latestSession.providerLabel}${
                      latestSession.model ? ` using ${latestSession.model}` : ""
                    }, grounded with agriculture notes and your module outputs.`
                  : "To enable full open-ended AI answers, add OPENAI_API_KEY or GEMINI_API_KEY in backend/.env and restart Django."}
              </p>
              {latestSession?.providerNotice ? <p>{latestSession.providerNotice}</p> : null}
            </div>

            {latestSession?.knowledgeSource ? (
              <div className="detail-card">
                <span>Knowledge source</span>
                <p>{latestSession.knowledgeSource}</p>
              </div>
            ) : null}
          </section>
        </aside>
      </section>
    </>
  );
}

export default AdvisorPage;
