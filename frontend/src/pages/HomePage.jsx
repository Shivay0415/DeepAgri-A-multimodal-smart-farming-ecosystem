import { Link } from "react-router-dom";

import { useWorkspace } from "../context/WorkspaceContext";

const journey = [
  {
    step: "01",
    title: "Choose the right crop",
    detail: "Start with soil chemistry and let the crop engine shortlist the best fit before the season begins.",
  },
  {
    step: "02",
    title: "Plan irrigation precisely",
    detail: "Balance soil moisture, rainfall, temperature, and crop stage before committing field water.",
  },
  {
    step: "03",
    title: "Detect stress early",
    detail: "Upload a leaf image and combine it with symptoms to catch disease before it spreads.",
  },
  {
    step: "04",
    title: "Sell with better timing",
    detail: "Use market intelligence to estimate the best selling window and likely revenue.",
  },
  {
    step: "05",
    title: "Explain decisions in local language",
    detail: "Use the advisor page to turn outputs into simple guidance that can be presented to farmers clearly.",
  },
];

const moduleLinks = [
  {
    to: "/crop",
    title: "Crop Intelligence",
    accent: "soil",
    description: "Recommend the best crop using soil and climate signals.",
  },
  {
    to: "/irrigation",
    title: "Water Planning",
    accent: "water",
    description: "Generate irrigation timing and quantity from field conditions.",
  },
  {
    to: "/disease",
    title: "Disease Desk",
    accent: "leaf",
    description: "Diagnose visible symptoms and review remedies.",
  },
  {
    to: "/market",
    title: "Market Studio",
    accent: "sun",
    description: "Forecast selling windows from price history and yield.",
  },
  {
    to: "/advisor",
    title: "Agri-Bot",
    accent: "grain",
    description: "Ask farmer-friendly questions in English, Hindi, or Tamil.",
  },
];

function HomePage() {
  const { cropReport, irrigationPlan, diseaseReport, marketReport } = useWorkspace();

  return (
    <>
      <section className="home-hero">
        <div className="home-hero__copy">
          <p className="section-label">Unified Farm Intelligence</p>
          <h1>One platform for crop choice, water planning, disease response, market timing, and multilingual advice.</h1>
          <p>
            AgriPulse is structured for live seminar presentation: each module has its own page,
            each workflow is interactive, and the outputs connect across the platform like a real
            operating system for farm decisions.
          </p>
          <div className="hero-actions">
            <Link className="hero-button hero-button--primary" to="/crop">
              Start with Module 1
            </Link>
            <Link className="hero-button hero-button--secondary" to="/advisor">
              Open Agri-Bot
            </Link>
          </div>
        </div>

        <div className="home-hero__panel">
          <article className="spotlight-card soil">
            <span>Current crop recommendation</span>
            <strong>{cropReport?.recommended_crop || "Not generated yet"}</strong>
            <small>{cropReport ? "Ready to feed irrigation, disease, and market pages" : "Run Module 1 to begin the chain"}</small>
          </article>
          <article className="spotlight-card water">
            <span>Water action</span>
            <strong>
              {irrigationPlan
                ? irrigationPlan.irrigation_needed
                  ? irrigationPlan.recommended_window
                  : "No irrigation needed now"
                : "Waiting for plan"}
            </strong>
            <small>Real-time farm operations become easier when the plan is visible in one place.</small>
          </article>
          <article className="spotlight-card leaf">
            <span>Health status</span>
            <strong>{diseaseReport?.disease_name || "No diagnosis yet"}</strong>
            <small>Leaf analysis can feed the multilingual advisor automatically.</small>
          </article>
          <article className="spotlight-card sun">
            <span>Best sale date</span>
            <strong>{marketReport?.best_sale_date || "Not forecast yet"}</strong>
            <small>Market timing is tied to the same crop decision path.</small>
          </article>
        </div>
      </section>

      <section className="module-link-grid">
        {moduleLinks.map((module) => (
          <Link key={module.to} to={module.to} className={`module-link-card ${module.accent}`}>
            <span>{module.title}</span>
            <p>{module.description}</p>
          </Link>
        ))}
      </section>

      <section className="presentation-grid">
        <article className="presentation-card">
          <p className="section-label">Seminar Storyline</p>
          <h2>Present the platform as one connected farmer journey.</h2>
          <div className="journey-list">
            {journey.map((item) => (
              <div className="journey-step" key={item.step}>
                <span>{item.step}</span>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="presentation-card">
          <p className="section-label">What Makes It Presentation-Ready</p>
          <h2>Not just a set of models, but a navigable product.</h2>
          <div className="feature-stack">
            <div className="feature-line">
              <strong>Separate module pages</strong>
              <p>Each AI function has its own route, layout, and working form.</p>
            </div>
            <div className="feature-line">
              <strong>Connected state</strong>
              <p>Crop and disease outputs can be reused across irrigation, market, and advisor pages.</p>
            </div>
            <div className="feature-line">
              <strong>Seminar-friendly narrative</strong>
              <p>The overview page explains the full value chain from soil check to selling strategy.</p>
            </div>
            <div className="feature-line">
              <strong>Working module actions</strong>
              <p>Each page includes real form submission, reset controls, and next-step buttons connected to Django.</p>
            </div>
          </div>
        </article>
      </section>
    </>
  );
}

export default HomePage;
