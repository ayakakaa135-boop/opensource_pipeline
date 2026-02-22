"""
Open Source Adoption Dashboard
Run with: streamlit run dashboard/app.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from analysis.adoption_analysis import (
    get_adoption_metrics,
    run_ab_test_release_notes,
    get_top_repos_summary,
)

st.set_page_config(
    page_title="Open Source Adoption Pipeline",
    page_icon="🐧",
    layout="wide",
)

st.title("🐧 Open Source Adoption & Market Penetration Dashboard")
st.caption("Tracking Ubuntu/Canonical ecosystem and key OSS projects · Built with Python + PostgreSQL")

# ── Summary Table ──────────────────────────────────────────────
st.header("📊 Market Penetration Overview")
try:
    summary = get_top_repos_summary()
    if summary.empty:
        st.warning("No data yet. Run the collector first: `python collectors/github_collector.py`")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Repos Tracked", len(summary))
        col2.metric("Top Stars", f"{summary['stars'].max():,}")
        col3.metric("Top Forks", f"{summary['forks'].max():,}")

        fig = px.bar(
            summary,
            x="full_name",
            y="penetration_score",
            color="language",
            title="Market Penetration Score by Repository",
            labels={"full_name": "Repository", "penetration_score": "Score"},
        )
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(summary.style.highlight_max(subset=["penetration_score"], color="#d4edda"))

except Exception as e:
    st.error(f"Database error: {e}")

# ── Adoption Trends ────────────────────────────────────────────
st.header("📈 Adoption Trends Over Time")
try:
    metrics = get_adoption_metrics()
    if not metrics.empty:
        repos = metrics["full_name"].unique().tolist()
        selected = st.multiselect("Select repositories", repos, default=repos[:3])
        filtered = metrics[metrics["full_name"].isin(selected)]

        fig2 = px.line(
            filtered,
            x="snapshot_date",
            y="stars",
            color="full_name",
            title="Star Growth Over Time",
            labels={"snapshot_date": "Date", "stars": "Total Stars"},
        )
        st.plotly_chart(fig2, use_container_width=True)

        fig3 = px.line(
            filtered,
            x="snapshot_date",
            y="star_momentum",
            color="full_name",
            title="7-Day Rolling Star Momentum",
            labels={"snapshot_date": "Date", "star_momentum": "Avg Daily Stars Gained"},
        )
        st.plotly_chart(fig3, use_container_width=True)
except Exception as e:
    st.error(f"Error loading trends: {e}")

# ── A/B Test ───────────────────────────────────────────────────
st.header("🔬 A/B Test: Release Notes Length vs. Post-Release Growth")
st.caption("Hypothesis: Repos with longer release notes gain more stars in the 7 days after a release.")

try:
    ab = run_ab_test_release_notes()
    if "error" in ab:
        st.info(ab["error"])
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric(ab["group_a_label"], f"{ab['group_a_mean']} stars", f"n={ab['group_a_n']}")
        col2.metric(ab["group_b_label"], f"{ab['group_b_mean']} stars", f"n={ab['group_b_n']}")
        col3.metric("p-value", ab["p_value"], delta="significant ✅" if ab["significant"] else "not significant")

        st.info(f"**Conclusion:** {ab['conclusion']}")

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(name=ab["group_a_label"], x=["Short Notes"], y=[ab["group_a_mean"]]))
        fig4.add_trace(go.Bar(name=ab["group_b_label"], x=["Long Notes"], y=[ab["group_b_mean"]]))
        fig4.update_layout(title="Average Stars Gained 7 Days Post-Release", barmode="group")
        st.plotly_chart(fig4, use_container_width=True)
except Exception as e:
    st.error(f"Error running A/B test: {e}")

st.divider()
st.caption("Pipeline by Aya · Data sourced from GitHub API · Powered by Python, PostgreSQL, Streamlit")
