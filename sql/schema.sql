-- ============================================
-- Open Source Adoption Pipeline - DB Schema
-- ============================================

CREATE TABLE IF NOT EXISTS repositories (
    id              SERIAL PRIMARY KEY,
    repo_id         BIGINT UNIQUE NOT NULL,
    name            VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    description     TEXT,
    language        VARCHAR(100),
    created_at      TIMESTAMP,
    collected_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS repo_snapshots (
    id              SERIAL PRIMARY KEY,
    repo_id         BIGINT REFERENCES repositories(repo_id),
    snapshot_date   DATE NOT NULL,
    stars           INTEGER DEFAULT 0,
    forks           INTEGER DEFAULT 0,
    open_issues     INTEGER DEFAULT 0,
    watchers        INTEGER DEFAULT 0,
    UNIQUE(repo_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS releases (
    id              SERIAL PRIMARY KEY,
    repo_id         BIGINT REFERENCES repositories(repo_id),
    release_tag     VARCHAR(100),
    release_name    VARCHAR(255),
    published_at    TIMESTAMP,
    body_length     INTEGER,   -- length of release notes
    is_prerelease   BOOLEAN DEFAULT FALSE,
    collected_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contributors (
    id              SERIAL PRIMARY KEY,
    repo_id         BIGINT REFERENCES repositories(repo_id),
    username        VARCHAR(255),
    contributions   INTEGER,
    snapshot_date   DATE DEFAULT CURRENT_DATE,
    UNIQUE(repo_id, username, snapshot_date)
);

-- View: growth rate per repo per week
CREATE OR REPLACE VIEW weekly_growth AS
SELECT
    r.full_name,
    s.snapshot_date,
    s.stars,
    s.forks,
    LAG(s.stars) OVER (PARTITION BY s.repo_id ORDER BY s.snapshot_date) AS prev_stars,
    s.stars - LAG(s.stars) OVER (PARTITION BY s.repo_id ORDER BY s.snapshot_date) AS stars_growth
FROM repo_snapshots s
JOIN repositories r ON r.repo_id = s.repo_id;
