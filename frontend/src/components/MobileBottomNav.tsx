import React from "react";
import { NavLink, useLocation } from "react-router-dom";

interface Tab {
  path: string;
  label: string;
  icon: React.ReactNode;
  matchPaths: string[];
}

const tabs: Tab[] = [
  {
    path: "/",
    label: "首页",
    matchPaths: ["/"],
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    path: "/identity",
    label: "调查前",
    matchPaths: ["/identity", "/topic", "/questionnaire", "/methodology", "/scenarios"],
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
  },
  {
    path: "/fieldwork",
    label: "调查中",
    matchPaths: ["/fieldwork"],
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
        <line x1="12" y1="19" x2="12" y2="23" />
        <line x1="8" y1="23" x2="16" y2="23" />
      </svg>
    ),
  },
  {
    path: "/analysis",
    label: "调查后",
    matchPaths: ["/analysis", "/export"],
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    ),
  },
  {
    path: "/library",
    label: "成果库",
    matchPaths: ["/library"],
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
      </svg>
    ),
  },
];

export default function MobileBottomNav() {
  const location = useLocation();

  return (
    <nav className="mobile-bottom-nav" aria-label="主导航">
      {tabs.map((tab) => {
        const isActive = tab.matchPaths.some(
          (p) => (p === "/" ? location.pathname === "/" : location.pathname.startsWith(p))
        );
        return (
          <NavLink
            key={tab.path}
            to={tab.path}
            className={`mobile-nav-item ${isActive ? "active" : ""}`}
            end={tab.path === "/"}
          >
            <span className="mobile-nav-icon">{tab.icon}</span>
            <span className="mobile-nav-label">{tab.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
