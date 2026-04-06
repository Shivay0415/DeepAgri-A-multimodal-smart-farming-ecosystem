import { useEffect, useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";

import { useWorkspace } from "../context/WorkspaceContext";
import { requestBackendHealth } from "../lib/api";

const navItems = [
  { to: "/", label: "Overview" },
  { to: "/crop", label: "Crop" },
  { to: "/irrigation", label: "Irrigation" },
  { to: "/disease", label: "Disease" },
  { to: "/market", label: "Market" },
  { to: "/advisor", label: "Agri-Bot" },
];

function AppShell() {
  const { cropReport, irrigationPlan, diseaseReport, marketReport, advisorAnswer } =
    useWorkspace();
  const [backendState, setBackendState] = useState("checking");
  const [backendLabel, setBackendLabel] = useState("Checking backend");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const completedModules = [
    cropReport,
    irrigationPlan,
    diseaseReport,
    marketReport,
    advisorAnswer,
  ].filter(Boolean).length;
  const completionPercent = Math.round((completedModules / 5) * 100);
  const nextRoute = !cropReport
    ? "/crop"
    : !irrigationPlan
      ? "/irrigation"
      : !diseaseReport
        ? "/disease"
        : !marketReport
          ? "/market"
          : !advisorAnswer
            ? "/advisor"
            : "/";

  const refreshBackend = async () => {
    setIsRefreshing(true);
    setBackendState("checking");
    setBackendLabel("Checking backend");

    try {
      const data = await requestBackendHealth();
      setBackendState(data.status === "ok" ? "online" : "checking");
      setBackendLabel(data.status === "ok" ? "Django backend online" : "Backend responded");
    } catch {
      setBackendState("offline");
      setBackendLabel("Backend not reachable");
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    refreshBackend();
  }, []);

  return (
    <div className="site-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark">AP</div>
          <div>
            <p className="brand-name">AgriPulse</p>
            <p className="brand-subtitle">Seminar-Ready Smart Farming Platform</p>
          </div>
        </div>

        <nav className="topbar__nav" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                isActive ? "topbar__link topbar__link--active" : "topbar__link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="topbar__status">
          <span className={`status-pill status-pill--${backendState}`}>{backendLabel}</span>
          <button
            className="status-button"
            type="button"
            onClick={refreshBackend}
            disabled={isRefreshing}
          >
            {isRefreshing ? "Checking..." : "Refresh"}
          </button>
        </div>
      </header>

      <div className="workspace-layout">
        <aside className="workspace-rail">
          <div className="workspace-card">
            <p className="workspace-card__eyebrow">Connected Workspace</p>
            <h2>Latest field intelligence</h2>
            <div className="progress-track" aria-hidden="true">
              <span className="progress-fill" style={{ width: `${completionPercent}%` }} />
            </div>
            <p className="workspace-note">
              {completedModules} of 5 live modules completed in the current presentation flow.
            </p>

            <div className="workspace-list">
              <article className="workspace-pill soil">
                <span>Crop</span>
                <strong>{cropReport?.recommended_crop || "Waiting for soil analysis"}</strong>
              </article>
              <article className="workspace-pill water">
                <span>Irrigation</span>
                <strong>
                  {irrigationPlan
                    ? irrigationPlan.irrigation_needed
                      ? `${Math.round(irrigationPlan.total_water_liters).toLocaleString()} L`
                      : "No immediate irrigation"
                    : "Plan not generated"}
                </strong>
              </article>
              <article className="workspace-pill leaf">
                <span>Disease</span>
                <strong>{diseaseReport?.disease_name || "No diagnosis yet"}</strong>
              </article>
              <article className="workspace-pill sun">
                <span>Market</span>
                <strong>{marketReport?.best_sale_date || "No sale window yet"}</strong>
              </article>
              <article className="workspace-pill grain">
                <span>Advisor</span>
                <strong>{advisorAnswer?.language?.toUpperCase() || "No consultation yet"}</strong>
              </article>
            </div>

            <div className="workspace-actions">
              <Link className="hero-button hero-button--primary" to={nextRoute}>
                {nextRoute === "/" ? "Review Overview" : "Continue Seminar Flow"}
              </Link>
              <Link className="hero-button hero-button--secondary" to="/">
                Dashboard Overview
              </Link>
            </div>
          </div>
        </aside>

        <main className="page-shell">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppShell;
