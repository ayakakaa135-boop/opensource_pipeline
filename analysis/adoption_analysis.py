"""
Analysis Module
- Market penetration metrics
- Adoption trends
- A/B test: does release note length affect post-release growth?
"""
import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy import text
from models.database import get_engine


def get_adoption_metrics() -> pd.DataFrame:
    """
    Calculate product adoption metrics per repo.
    Returns growth rate, momentum, and market penetration score.
    """
    engine = get_engine()
    sql = """
        SELECT
            r.full_name,
            r.language,
            s.snapshot_date,
            s.stars,
            s.forks,
            s.open_issues,
            s.stars - LAG(s.stars) OVER (PARTITION BY s.repo_id ORDER BY s.snapshot_date) AS daily_star_growth,
            s.forks - LAG(s.forks) OVER (PARTITION BY s.repo_id ORDER BY s.snapshot_date) AS daily_fork_growth
        FROM repo_snapshots s
        JOIN repositories r ON r.repo_id = s.repo_id
        ORDER BY r.full_name, s.snapshot_date
    """
    df = pd.read_sql(sql, engine)

    # Market Penetration Score: weighted combination of stars + forks
    df["penetration_score"] = (df["stars"] * 0.6) + (df["forks"] * 0.4)

    # Momentum: rolling 7-day average growth
    df["star_momentum"] = (
        df.groupby("full_name")["daily_star_growth"]
        .transform(lambda x: x.rolling(7, min_periods=1).mean())
    )

    return df


def run_ab_test_release_notes() -> dict:
    """
    A/B Test: Does a longer release note lead to more star growth in the 7 days after release?

    Group A: releases with short notes (body_length < median)
    Group B: releases with long notes  (body_length >= median)

    Metric: stars gained in the 7 days following the release.
    """
    engine = get_engine()

    sql = """
        SELECT
            rel.repo_id,
            rel.published_at::date AS release_date,
            rel.body_length,
            rel.is_prerelease,
            s_before.stars AS stars_before,
            s_after.stars  AS stars_after,
            s_after.stars - s_before.stars AS stars_gained
        FROM releases rel
        JOIN repo_snapshots s_before
            ON s_before.repo_id = rel.repo_id
            AND s_before.snapshot_date = rel.published_at::date
        JOIN repo_snapshots s_after
            ON s_after.repo_id = rel.repo_id
            AND s_after.snapshot_date = rel.published_at::date + INTERVAL '7 days'
        WHERE rel.is_prerelease = FALSE
          AND rel.body_length > 0
    """
    df = pd.read_sql(sql, engine)

    if df.empty or len(df) < 10:
        return {"error": "Not enough data yet. Run the collector for more days first."}

    median_length = df["body_length"].median()
    group_a = df[df["body_length"] < median_length]["stars_gained"].dropna()
    group_b = df[df["body_length"] >= median_length]["stars_gained"].dropna()

    t_stat, p_value = stats.ttest_ind(group_a, group_b)

    return {
        "hypothesis": "Longer release notes → more stars gained in 7 days",
        "group_a_label": f"Short notes (< {median_length:.0f} chars)",
        "group_b_label": f"Long notes (>= {median_length:.0f} chars)",
        "group_a_mean": round(group_a.mean(), 2),
        "group_b_mean": round(group_b.mean(), 2),
        "group_a_n": len(group_a),
        "group_b_n": len(group_b),
        "t_statistic": round(t_stat, 4),
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
        "conclusion": (
            "✅ Statistically significant difference found!" if p_value < 0.05
            else "❌ No statistically significant difference (need more data or effect is small)"
        ),
    }


def get_top_repos_summary() -> pd.DataFrame:
    """Get a summary table of all tracked repos sorted by penetration score."""
    engine = get_engine()
    sql = """
        SELECT
            r.full_name,
            r.language,
            s.stars,
            s.forks,
            s.open_issues,
            COUNT(DISTINCT c.username) AS contributor_count,
            (s.stars * 0.6 + s.forks * 0.4) AS penetration_score
        FROM repositories r
        JOIN repo_snapshots s ON s.repo_id = r.repo_id
        LEFT JOIN contributors c ON c.repo_id = r.repo_id
        WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM repo_snapshots)
        GROUP BY r.full_name, r.language, s.stars, s.forks, s.open_issues
        ORDER BY penetration_score DESC
    """
    return pd.read_sql(sql, engine)


if __name__ == "__main__":
    print("📊 Top Repos Summary:")
    print(get_top_repos_summary().to_string(index=False))

    print("\n🔬 A/B Test Results:")
    results = run_ab_test_release_notes()
    for k, v in results.items():
        print(f"  {k}: {v}")
