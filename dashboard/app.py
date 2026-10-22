"""
PipelineOps Streamlit Dashboard (Phase 6)
Interactive analytical dashboard answering all 4 business questions:
Q1: Skill Trends WoW  Q2: Top Paying Roles  Q3: Company Reposts  Q4: Remote Shift
Plus: Pipeline Health tab with quality scorecard and statistical headline card.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional
import sys

import pandas as pd

# ── Streamlit / Plotly with friendly error ──────────────────────────────────────
try:
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    print("Streamlit or Plotly not installed. Run: pip install streamlit plotly")
    sys.exit(1)

# ── Project paths ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "clean_data"
DB_PATH = CLEAN_DIR / "pipelineops.db"
QUALITY_REPORT_PATH = CLEAN_DIR / "quality_report.json"
STATS_REPORT_PATH = CLEAN_DIR / "statistical_insights.json"

st.set_page_config(
    page_title="PipelineOps Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Styling ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2980b9 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .kpi-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        border-left: 4px solid #2980b9;
        margin-bottom: 0.5rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #1e3a5f, #2980b9);
        color: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .quality-pass { color: #27ae60; font-weight: bold; }
    .quality-fail { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ── Data Loading ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_db_query(query: str) -> pd.DataFrame:
    """Load data from SQLite database."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            return pd.read_sql_query(query, conn)
    except Exception as e:
        st.warning(f"DB query failed: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def load_jobs_df() -> pd.DataFrame:
    csv_path = CLEAN_DIR / "fact_jobs.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return load_db_query("SELECT * FROM fact_job_postings")


@st.cache_data(ttl=300)
def load_bridge_df() -> pd.DataFrame:
    csv_path = CLEAN_DIR / "job_skills_bridge.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return load_db_query("SELECT * FROM job_skills_bridge")


@st.cache_data(ttl=300)
def load_quality_report() -> dict:
    if QUALITY_REPORT_PATH.exists():
        with open(QUALITY_REPORT_PATH) as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=300)
def load_stats_report() -> dict:
    if STATS_REPORT_PATH.exists():
        with open(STATS_REPORT_PATH) as f:
            return json.load(f)
    return {}


# ── Header ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size:2rem;">📊 PipelineOps Analytics Dashboard</h1>
    <p style="margin:0.3rem 0 0 0; opacity:0.85;">
        Orchestrated Job Market Intelligence Pipeline &mdash; Live data via Remotive API
    </p>
</div>
""", unsafe_allow_html=True)

df_jobs = load_jobs_df()
df_bridge = load_bridge_df()
quality_report = load_quality_report()
stats_report = load_stats_report()

if df_jobs.empty:
    st.error(
        "No data found. Please run the pipeline first:\n\n"
        "```bash\n"
        "python python/orchestrator.py --seed --seed-days 30\n"
        "```"
    )
    st.stop()

# Ensure posted_at is datetime
df_jobs["posted_at"] = pd.to_datetime(df_jobs["posted_at"], errors="coerce")

# ── Headline KPIs ────────────────────────────────────────────────────────────────
total_jobs = len(df_jobs)
unique_skills = df_bridge["skill_name"].nunique() if not df_bridge.empty else 0
avg_salary = df_jobs["salary_avg"].dropna().mean()
remote_pct = (df_jobs["remote_type"] == "Fully Remote").mean() * 100
quality_score = quality_report.get("quality_score_pct", 100.0)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Jobs", f"{total_jobs:,}")
with col2:
    st.metric("Tracked Skills", f"{unique_skills}")
with col3:
    st.metric("Avg Salary (USD)", f"${avg_salary:,.0f}" if pd.notna(avg_salary) else "N/A")
with col4:
    st.metric("% Fully Remote", f"{remote_pct:.1f}%")
with col5:
    st.metric("Quality Score", f"{quality_score:.1f}%", delta="All gates passed" if quality_score == 100 else f"{quality_report.get('failed_checks', 0)} issues")

st.markdown("---")

# ── Statistical Headline Card ─────────────────────────────────────────────────────
if stats_report:
    reg = stats_report.get("primary_skill_regression", {})
    slope = reg.get("slope", 0)
    p_val = reg.get("p_value", 1.0)
    r2 = reg.get("r_squared", 0)
    direction = "Trending UP" if slope > 0 else "Trending DOWN"
    col_stat1, col_stat2 = st.columns([2, 1])
    with col_stat1:
        st.info(
            f"**📈 Statistical Headline (SciPy linregress):** "
            f"{stats_report.get('headline_card', 'Computing...')}  \n"
            f"_{reg.get('plain_english_insight', '')}_"
        )
    with col_stat2:
        st.info(
            f"**Interview Talking Point:**  \n"
            f"{reg.get('interview_talking_point', '')}"
        )
    st.markdown("---")

# ── Tabs ─────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Q1 — Skill Trends WoW",
    "Q2 — Top Paying Roles",
    "Q3 — Company Reposts",
    "Q4 — Remote Shift",
    "Pipeline Health",
])

# ── Q1: Skill Trends Week-over-Week ──────────────────────────────────────────────
with tab1:
    st.subheader("Which skills are trending up in demand week over week?")
    if df_bridge.empty or df_jobs.empty:
        st.warning("Skill bridge data not available.")
    else:
        df_merged = df_bridge.merge(df_jobs[["job_id", "posted_at"]], on="job_id", how="inner")
        df_merged["week"] = pd.to_datetime(df_merged["posted_at"]).dt.to_period("W").astype(str)

        weekly_skill = (
            df_merged.groupby(["week", "skill_name"])
            .size()
            .reset_index(name="count")
        )

        # Top 12 skills by total demand
        top_skills = df_bridge["skill_name"].value_counts().head(12).index.tolist()
        filtered = weekly_skill[weekly_skill["skill_name"].isin(top_skills)]

        if not filtered.empty:
            fig1 = px.line(
                filtered,
                x="week",
                y="count",
                color="skill_name",
                title="Weekly Skill Demand Trends (Top 12 Skills)",
                labels={"count": "Job Mentions", "week": "Week", "skill_name": "Skill"},
                template="plotly_white",
            )
            fig1.update_traces(mode="lines+markers")
            fig1.update_layout(height=450, legend_title="Skill")
            st.plotly_chart(fig1, use_container_width=True)

        # Rising Skills Leaderboard
        st.markdown("#### Rising Skills Leaderboard")
        skill_counts = df_bridge["skill_name"].value_counts().reset_index()
        skill_counts.columns = ["Skill", "Total Mentions"]
        skill_counts["Rank"] = range(1, len(skill_counts) + 1)
        st.dataframe(
            skill_counts.head(20).set_index("Rank"),
            use_container_width=True,
        )

# ── Q2: Top Paying Roles by Skill ────────────────────────────────────────────────
with tab2:
    st.subheader("Which roles pay the most for your current skill set?")
    salary_df = df_jobs[df_jobs["salary_avg"].notna() & (df_jobs["salary_avg"] > 0)].copy()

    if not salary_df.empty:
        col_q2a, col_q2b = st.columns(2)

        with col_q2a:
            # Box plot: salary by seniority
            fig2a = px.box(
                salary_df,
                x="seniority_level",
                y="salary_avg",
                color="seniority_level",
                title="Salary Distribution by Seniority",
                labels={"salary_avg": "Average Salary (USD)", "seniority_level": "Seniority"},
                template="plotly_white",
                category_orders={"seniority_level": ["Junior", "Mid", "Senior", "Lead", "Staff"]},
            )
            fig2a.update_layout(showlegend=False, height=380)
            st.plotly_chart(fig2a, use_container_width=True)

        with col_q2b:
            # Bar: Avg salary by category
            cat_salary = (
                salary_df.groupby("category")["salary_avg"]
                .mean()
                .sort_values(ascending=True)
                .reset_index()
            )
            fig2b = px.bar(
                cat_salary,
                x="salary_avg",
                y="category",
                orientation="h",
                title="Average Salary by Role Category",
                labels={"salary_avg": "Avg Salary USD", "category": "Role Category"},
                color="salary_avg",
                color_continuous_scale="Blues",
                template="plotly_white",
            )
            fig2b.update_layout(height=380, showlegend=False)
            st.plotly_chart(fig2b, use_container_width=True)

        # Skill × Salary heatmap data
        if not df_bridge.empty:
            skill_salary = df_bridge.merge(salary_df[["job_id", "salary_avg", "seniority_level"]], on="job_id")
            skill_avg = (
                skill_salary.groupby(["skill_name", "seniority_level"])["salary_avg"]
                .mean()
                .reset_index()
            )
            pivot = skill_avg.pivot_table(index="skill_name", columns="seniority_level", values="salary_avg")
            top_pivot = pivot.loc[pivot.mean(axis=1).nlargest(15).index]
            fig2c = px.imshow(
                top_pivot,
                title="Avg Salary (USD): Top 15 Skills × Seniority",
                labels={"x": "Seniority", "y": "Skill", "color": "Avg Salary USD"},
                aspect="auto",
                color_continuous_scale="Blues",
                template="plotly_white",
            )
            fig2c.update_layout(height=500)
            st.plotly_chart(fig2c, use_container_width=True)
    else:
        st.warning("Salary data not available.")

# ── Q3: Company Reposting Cadence ────────────────────────────────────────────────
with tab3:
    st.subheader("Which companies post the most listings, and how often do they repost?")
    company_df = df_jobs.groupby("company_name").agg(
        total_postings=("job_id", "count"),
        repost_count=("repost_status", lambda x: (x == "repost").sum()),
        unique_roles=("job_title", "nunique"),
        latest_post=("posted_at", "max"),
    ).reset_index()
    company_df["repost_ratio_pct"] = (company_df["repost_count"] / company_df["total_postings"] * 100).round(1)
    company_df = company_df.sort_values("total_postings", ascending=False)

    col_q3a, col_q3b = st.columns(2)

    with col_q3a:
        top20 = company_df.head(15)
        fig3a = px.bar(
            top20,
            x="total_postings",
            y="company_name",
            orientation="h",
            color="repost_ratio_pct",
            title="Top 15 Hiring Companies (color = Repost %)",
            labels={"total_postings": "Total Postings", "company_name": "Company", "repost_ratio_pct": "Repost %"},
            color_continuous_scale="RdYlGn_r",
            template="plotly_white",
        )
        fig3a.update_layout(height=500)
        st.plotly_chart(fig3a, use_container_width=True)

    with col_q3b:
        fig3b = px.scatter(
            company_df.head(20),
            x="total_postings",
            y="repost_ratio_pct",
            size="unique_roles",
            color="repost_ratio_pct",
            hover_name="company_name",
            title="Postings vs Repost Rate (bubble = unique roles)",
            labels={"total_postings": "Total Postings", "repost_ratio_pct": "Repost Rate %"},
            color_continuous_scale="RdYlGn_r",
            template="plotly_white",
        )
        fig3b.update_layout(height=500)
        st.plotly_chart(fig3b, use_container_width=True)

    st.markdown("#### Company Posting Details")
    st.dataframe(
        company_df.rename(columns={
            "company_name": "Company",
            "total_postings": "Total Posts",
            "repost_count": "Reposts",
            "unique_roles": "Unique Roles",
            "repost_ratio_pct": "Repost %",
        }).set_index("Company").head(25),
        use_container_width=True,
    )

# ── Q4: Remote vs On-site Shift ──────────────────────────────────────────────────
with tab4:
    st.subheader("How does remote vs on-site demand shift over time?")
    df_jobs["post_date"] = df_jobs["posted_at"].dt.date
    daily_remote = df_jobs.groupby(["post_date", "remote_type"]).size().reset_index(name="count")

    if not daily_remote.empty:
        # Stacked area chart
        fig4a = px.area(
            daily_remote,
            x="post_date",
            y="count",
            color="remote_type",
            title="Daily Job Postings by Work Type",
            labels={"count": "# Job Postings", "post_date": "Date", "remote_type": "Work Type"},
            color_discrete_map={
                "Fully Remote": "#2980b9",
                "Hybrid": "#f39c12",
                "On-site": "#e74c3c",
            },
            template="plotly_white",
        )
        fig4a.update_layout(height=400)
        st.plotly_chart(fig4a, use_container_width=True)

        # Summary pie
        remote_summary = df_jobs["remote_type"].value_counts().reset_index()
        remote_summary.columns = ["Work Type", "Count"]
        col_pie, col_weekly = st.columns(2)
        with col_pie:
            fig4b = px.pie(
                remote_summary,
                names="Work Type",
                values="Count",
                title="Current Remote / Hybrid / On-site Distribution",
                color_discrete_map={
                    "Fully Remote": "#2980b9",
                    "Hybrid": "#f39c12",
                    "On-site": "#e74c3c",
                },
                template="plotly_white",
            )
            fig4b.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig4b, use_container_width=True)

        with col_weekly:
            df_jobs["week"] = df_jobs["posted_at"].dt.to_period("W").astype(str)
            weekly_remote = df_jobs.groupby("week")["remote_type"].apply(
                lambda x: (x == "Fully Remote").mean() * 100
            ).reset_index(name="remote_pct")
            fig4c = px.bar(
                weekly_remote,
                x="week",
                y="remote_pct",
                title="Weekly % Fully Remote Postings",
                labels={"remote_pct": "% Fully Remote", "week": "Week"},
                color="remote_pct",
                color_continuous_scale="Blues",
                template="plotly_white",
            )
            fig4c.update_layout(height=380, showlegend=False)
            st.plotly_chart(fig4c, use_container_width=True)

# ── Pipeline Health & Quality Scorecard ──────────────────────────────────────────
with tab5:
    st.subheader("Pipeline Health & Data Quality Scorecard")

    if quality_report:
        overall = quality_report.get("overall_status", "UNKNOWN")
        color_class = "quality-pass" if overall == "PASSED" else "quality-fail"
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            st.metric("Overall Status", overall)
        with col_h2:
            st.metric("Quality Score", f"{quality_report.get('quality_score_pct', 0):.1f}%")
        with col_h3:
            st.metric("Checks", f"{quality_report.get('passed_checks', 0)}/{quality_report.get('total_checks', 0)} passed")

        st.markdown("#### Individual Quality Gate Results")
        checks = quality_report.get("checks", [])
        if checks:
            df_checks = pd.DataFrame(checks)
            df_checks["Status"] = df_checks["passed"].apply(lambda x: "PASS" if x else "FAIL")
            df_checks = df_checks.rename(columns={
                "check_name": "Check Name",
                "actual": "Observed",
                "expected": "Expected",
                "description": "Description",
                "Status": "Status",
            })
            display_cols = ["Check Name", "Status", "Observed", "Expected", "Description"]
            st.dataframe(df_checks[[c for c in display_cols if c in df_checks.columns]], use_container_width=True)
    else:
        st.info("Run the pipeline to see quality reports.")

    # Statistical Insights summary
    st.markdown("---")
    st.subheader("SciPy Statistical Analysis Report")
    if stats_report:
        reg = stats_report.get("primary_skill_regression", {})
        sal_reg = stats_report.get("salary_skill_correlation", {})

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("**Python Demand Trend Regression**")
            st.json({
                "slope (listings/day)": reg.get("slope"),
                "p_value": reg.get("p_value"),
                "R²": reg.get("r_squared"),
                "statistically_significant": reg.get("is_statistically_significant"),
                "data_points": reg.get("data_points"),
            })
        with col_s2:
            st.markdown("**Salary-Skill Stack Correlation**")
            st.json({
                "slope ($/skill)": sal_reg.get("slope"),
                "p_value": sal_reg.get("p_value"),
                "R²": sal_reg.get("r_squared"),
            })
        st.info(f"**Interview Card:** {reg.get('interview_talking_point', '')}")

    # Pipeline run history from DB
    st.markdown("---")
    st.subheader("Pipeline Run History")
    run_history = load_db_query(
        "SELECT run_id, status, stage, started_at, completed_at, duration_seconds, "
        "records_ingested, records_transformed, quality_passed "
        "FROM pipeline_runs ORDER BY started_at DESC LIMIT 20"
    )
    if not run_history.empty:
        st.dataframe(run_history, use_container_width=True)
    else:
        st.info("No run history found yet.")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**PipelineOps v1.0**  \n"
    "Built with Python • SQLite • SciPy • Streamlit  \n\n"
    "**Data Source:** Remotive API  \n"
    "**Refresh:** Every 24 hours  \n\n"
    "**Run Pipeline:**\n"
    "```bash\n"
    "python python/orchestrator.py\n"
    "```"
)
