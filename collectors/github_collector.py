"""
GitHub API Collector
Fetches repository metadata, snapshots, releases, and contributors.
"""
import os
import time
import requests
import pandas as pd
from datetime import date
from sqlalchemy import text
from dotenv import load_dotenv
from models.database import get_engine

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}
BASE_URL = "https://api.github.com"

# List of open source repos to track (Ubuntu/Canonical ecosystem + popular OSS)
REPOS_TO_TRACK = [
    "canonical/ubuntu.com",
    "canonical/snapcraft",
    "canonical/multipass",
    "ubuntu/microk8s",
    "netdata/netdata",
    "grafana/grafana",
    "prometheus/prometheus",
]


def fetch_repo(full_name: str) -> dict:
    """Fetch basic repo metadata from GitHub API."""
    url = f"{BASE_URL}/repos/{full_name}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def fetch_releases(full_name: str, limit: int = 30) -> list:
    """Fetch latest releases for a repo."""
    url = f"{BASE_URL}/repos/{full_name}/releases?per_page={limit}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def fetch_contributors(full_name: str, limit: int = 50) -> list:
    """Fetch top contributors for a repo."""
    url = f"{BASE_URL}/repos/{full_name}/contributors?per_page={limit}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def save_repo(engine, repo_data: dict):
    """Insert or update repo in the repositories table."""
    sql = text("""
        INSERT INTO repositories (repo_id, name, full_name, description, language, created_at)
        VALUES (:repo_id, :name, :full_name, :description, :language, :created_at)
        ON CONFLICT (repo_id) DO UPDATE SET
            description = EXCLUDED.description,
            language = EXCLUDED.language
    """)
    with engine.connect() as conn:
        conn.execute(sql, {
            "repo_id": repo_data["id"],
            "name": repo_data["name"],
            "full_name": repo_data["full_name"],
            "description": repo_data.get("description"),
            "language": repo_data.get("language"),
            "created_at": repo_data["created_at"],
        })
        conn.commit()


def save_snapshot(engine, repo_id: int, repo_data: dict):
    """Save today's snapshot of stars/forks/issues."""
    sql = text("""
        INSERT INTO repo_snapshots (repo_id, snapshot_date, stars, forks, open_issues, watchers)
        VALUES (:repo_id, :snapshot_date, :stars, :forks, :open_issues, :watchers)
        ON CONFLICT (repo_id, snapshot_date) DO UPDATE SET
            stars = EXCLUDED.stars,
            forks = EXCLUDED.forks,
            open_issues = EXCLUDED.open_issues,
            watchers = EXCLUDED.watchers
    """)
    with engine.connect() as conn:
        conn.execute(sql, {
            "repo_id": repo_id,
            "snapshot_date": date.today(),
            "stars": repo_data["stargazers_count"],
            "forks": repo_data["forks_count"],
            "open_issues": repo_data["open_issues_count"],
            "watchers": repo_data["watchers_count"],
        })
        conn.commit()


def save_releases(engine, repo_id: int, releases: list):
    """Save release data."""
    sql = text("""
        INSERT INTO releases (repo_id, release_tag, release_name, published_at, body_length, is_prerelease)
        VALUES (:repo_id, :release_tag, :release_name, :published_at, :body_length, :is_prerelease)
        ON CONFLICT DO NOTHING
    """)
    with engine.connect() as conn:
        for r in releases:
            if r.get("published_at"):
                conn.execute(sql, {
                    "repo_id": repo_id,
                    "release_tag": r.get("tag_name"),
                    "release_name": r.get("name"),
                    "published_at": r.get("published_at"),
                    "body_length": len(r.get("body") or ""),
                    "is_prerelease": r.get("prerelease", False),
                })
        conn.commit()


def save_contributors(engine, repo_id: int, contributors: list):
    """Save contributor data."""
    sql = text("""
        INSERT INTO contributors (repo_id, username, contributions, snapshot_date)
        VALUES (:repo_id, :username, :contributions, :snapshot_date)
        ON CONFLICT (repo_id, username, snapshot_date) DO UPDATE SET
            contributions = EXCLUDED.contributions
    """)
    with engine.connect() as conn:
        for c in contributors:
            conn.execute(sql, {
                "repo_id": repo_id,
                "username": c.get("login"),
                "contributions": c.get("contributions", 0),
                "snapshot_date": date.today(),
            })
        conn.commit()


def run_collection():
    """Main collection loop — runs for all tracked repos."""
    engine = get_engine()
    print(f"🚀 Starting data collection for {len(REPOS_TO_TRACK)} repos...\n")

    for full_name in REPOS_TO_TRACK:
        try:
            print(f"📦 Collecting: {full_name}")
            repo_data = fetch_repo(full_name)
            save_repo(engine, repo_data)
            save_snapshot(engine, repo_data["id"], repo_data)

            releases = fetch_releases(full_name)
            save_releases(engine, repo_data["id"], releases)

            contributors = fetch_contributors(full_name)
            save_contributors(engine, repo_data["id"], contributors)

            print(f"   ✅ Stars: {repo_data['stargazers_count']:,} | Forks: {repo_data['forks_count']:,}")
            time.sleep(1)  # be polite to the API

        except Exception as e:
            print(f"   ❌ Error collecting {full_name}: {e}")

    print("\n✅ Collection complete!")


if __name__ == "__main__":
    run_collection()
