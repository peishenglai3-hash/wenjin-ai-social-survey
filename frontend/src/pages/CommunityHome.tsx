import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/client";
import "./Community.css";

interface SkillSummary {
  id: number;
  name: string;
  description: string;
  category: string;
  skill_type: string;
  usage_count: number;
  fork_count: number;
  rating_avg: number;
  rating_count: number;
  published_at: string | null;
  author_id: number;
  tags: string[];
}

interface CatStat {
  name: string;
  count: number;
}

export default function CommunityHome() {
  const [latest, setLatest] = useState<SkillSummary[]>([]);
  const [popular, setPopular] = useState<SkillSummary[]>([]);
  const [categories, setCategories] = useState<CatStat[]>([]);
  const [totalPublished, setTotalPublished] = useState(0);
  const [tab, setTab] = useState<"latest" | "popular" | "researchers">("latest");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [latestRes, popularRes, catRes] = await Promise.all([
          api.get("/community/skills", { params: { sort: "latest", page_size: 6 } }),
          api.get("/community/skills", { params: { sort: "popular", page_size: 6 } }),
          api.get("/community/skills/categories"),
        ]);
        if (cancelled) return;
        setLatest(latestRes.data.skills || []);
        setPopular(popularRes.data.skills || []);
        setCategories(catRes.data.categories || []);
        setTotalPublished(catRes.data.total_published || 0);
      } catch {
        // Community may be empty — that's OK
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const CATEGORY_LABELS: Record<string, string> = {
    questionnaire: "📋 问卷设计",
    interview: "🎙 访谈指南",
    analysis: "📊 数据分析",
    writing: "✍️ 写作辅助",
    methodology: "🔬 方法论",
    general: "🔧 通用工具",
  };

  const totalResearchers = new Set([...latest, ...popular].map((s) => s.author_id)).size;

  function renderCard(s: SkillSummary) {
    return (
      <div key={s.id} className="skill-card" onClick={() => navigate(`/community/skills/${s.id}`)}>
        <div className="card-header">
          <h4 className="card-name">{s.name}</h4>
          <span className="card-category">{CATEGORY_LABELS[s.category] || s.category}</span>
        </div>
        <p className="card-desc">{s.description || "暂无描述"}</p>
        <div className="card-meta">
          <span>⭐ {s.rating_avg > 0 ? s.rating_avg.toFixed(1) : "—"}</span>
          <span>🍴 {s.fork_count}</span>
          <span>📊 {s.usage_count} 次使用</span>
        </div>
      </div>
    );
  }

  if (loading) return <div className="community-loading">加载中…</div>;

  return (
    <div className="community-page">
      {/* Hero */}
      <div className="community-hero">
        <div className="hero-icon">🌐</div>
        <div className="hero-text">
          <h2>调研者社区 <sup style={{ fontSize: 12, color: "#8b5cf6" }}>Beta</sup></h2>
          <p>
            分享你的AI调查技能，发现其他调研者创建的实用工具。
            每一个Prompt模板、访谈指南、分析框架都可以在这里被Fork、改进、再分享。
          </p>
          <div style={{ display: "flex", gap: 10 }}>
            <Link to="/community/skills" className="btn btn-primary" style={{ fontSize: 14, padding: "8px 20px", textDecoration: "none" }}>
              🔍 浏览技能市场
            </Link>
            <Link to="/community/publish" className="btn" style={{ fontSize: 14, padding: "8px 20px", textDecoration: "none", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)" }}>
              📤 发布技能
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="community-stats">
        <div className="stat-card">
          <div className="stat-num">{totalPublished}</div>
          <div className="stat-label">已发布技能</div>
        </div>
        <div className="stat-card">
          <div className="stat-num">{categories.length}</div>
          <div className="stat-label">技能分类</div>
        </div>
        <div className="stat-card">
          <div className="stat-num">{totalResearchers}</div>
          <div className="stat-label">贡献者</div>
        </div>
      </div>

      {/* Category Tags */}
      {categories.length > 0 && (
        <div style={{ marginBottom: 24, display: "flex", gap: 8, flexWrap: "wrap" }}>
          {categories.map((c) => (
            <Link
              key={c.name}
              to={`/community/skills?category=${c.name}`}
              style={{
                padding: "6px 14px",
                background: "var(--primary-light, #eef2ff)",
                borderRadius: 20,
                fontSize: 13,
                color: "var(--primary, #4f46e5)",
                textDecoration: "none",
                fontWeight: 500,
              }}
            >
              {CATEGORY_LABELS[c.name] || c.name} ({c.count})
            </Link>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="community-tabs">
        <button className={`community-tab ${tab === "latest" ? "active" : ""}`} onClick={() => setTab("latest")}>
          最新发布
        </button>
        <button className={`community-tab ${tab === "popular" ? "active" : ""}`} onClick={() => setTab("popular")}>
          使用最多
        </button>
        <button className={`community-tab ${tab === "researchers" ? "active" : ""}`} onClick={() => setTab("researchers")}>
          贡献者
        </button>
      </div>

      {/* Content */}
      {tab === "latest" && (
        latest.length > 0 ? (
          <div className="skill-card-grid">{latest.map(renderCard)}</div>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>还没有技能发布</h3>
            <p>成为第一个分享技能的人吧！</p>
          </div>
        )
      )}

      {tab === "popular" && (
        popular.length > 0 ? (
          <div className="skill-card-grid">{popular.map(renderCard)}</div>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>还没有使用数据</h3>
            <p>社区刚刚启动，使用数据会逐渐积累</p>
          </div>
        )
      )}

      {tab === "researchers" && (
        <div className="empty-state">
          <div className="empty-icon">👥</div>
          <h3>贡献者名录即将上线</h3>
          <p>到 <Link to="/community/skills">技能市场</Link> 发现更多</p>
        </div>
      )}

      <div style={{ textAlign: "center", marginTop: 24 }}>
        <Link to="/community/skills" style={{ fontSize: 14, color: "var(--primary)" }}>
          查看全部 →
        </Link>
      </div>
    </div>
  );
}
