# 🐧 Open Source Adoption Pipeline

A data engineering pipeline that tracks **product adoption and market penetration** for open source projects in the Ubuntu/Canonical ecosystem — built to demonstrate real-world data engineering skills.

## 🎯 What This Project Does

- **Collects** daily snapshots of GitHub metrics (stars, forks, issues, contributors, releases) for key OSS repos
- **Stores** all data in a structured PostgreSQL schema optimized for time-series analysis
- **Analyzes** market penetration trends and product adoption velocity
- **Experiments** using A/B testing to measure whether release note quality affects post-release adoption
- **Visualizes** everything in an interactive Streamlit dashboard

## 🏗️ Architecture

```
GitHub API
    │
    ▼
collectors/github_collector.py   ← Fetches & ingests data
    │
    ▼
PostgreSQL (sql/schema.sql)      ← Structured storage
    │
    ▼
analysis/adoption_analysis.py    ← Metrics + A/B testing
    │
    ▼
dashboard/app.py                 ← Streamlit visualization
```

## ⚡ Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/YOUR_USERNAME/opensource-adoption-pipeline
cd opensource-adoption-pipeline
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your GitHub token and PostgreSQL credentials
```
Get a GitHub token at: https://github.com/settings/tokens (select `public_repo` scope)

### 3. Initialize Database
```bash
python models/database.py
```

### 4. Run Data Collection
```bash
python collectors/github_collector.py
```

### 5. Launch Dashboard
```bash
streamlit run dashboard/app.py
```

## 🔬 A/B Experiment Design

**Hypothesis:** Repositories that publish longer, more detailed release notes experience greater star growth in the 7 days following a release.

- **Group A (Control):** Releases with below-median release note length
- **Group B (Treatment):** Releases with above-median release note length
- **Metric:** Stars gained in the 7-day window post-release
- **Test:** Welch's t-test (α = 0.05)

## 📊 Key Metrics

| Metric | Description |
|--------|-------------|
| **Penetration Score** | `stars × 0.6 + forks × 0.4` — composite adoption signal |
| **Star Momentum** | 7-day rolling average of daily star growth |
| **Contributor Growth** | New contributors per snapshot period |

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Database | PostgreSQL 15 |
| ORM / DB | SQLAlchemy + psycopg2 |
| Analysis | Pandas, NumPy, SciPy |
| Dashboard | Streamlit + Plotly |
| Data Source | GitHub REST API v3 |

## 📁 Project Structure

```
opensource_pipeline/
├── collectors/
│   └── github_collector.py    # GitHub API ingestion
├── models/
│   └── database.py            # DB connection & init
├── sql/
│   └── schema.sql             # Tables + views
├── analysis/
│   └── adoption_analysis.py   # Metrics & A/B test
├── dashboard/
│   └── app.py                 # Streamlit UI
├── requirements.txt
└── .env.example
```

## 🔄 Scheduling (Optional)

To collect data automatically every day on Windows, use **Task Scheduler** to run:
```
python C:\path\to\opensource_pipeline\collectors\github_collector.py
```

---
*Built as a portfolio project demonstrating data engineering skills relevant to open-source product analytics.*
