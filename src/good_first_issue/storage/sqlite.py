import datetime
import sqlite3
from pathlib import Path

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS issues (
    url         TEXT PRIMARY KEY,
    repo        TEXT NOT NULL,
    stars       INTEGER NOT NULL,
    number      INTEGER NOT NULL,
    title       TEXT NOT NULL,
    language    TEXT NOT NULL,
    fetched_at  TEXT NOT NULL
);
"""


def _find_project_root() -> Path:
    """Walk up until pyproject.toml is found (assumed project root)."""
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Could not locate project root (no pyproject.toml found)")


PROJECT_ROOT = _find_project_root()
DEFAULT_DB_PATH = PROJECT_ROOT / "issues.sqlite"


def init_db(path):
    conn = sqlite3.connect(path)
    conn.execute(DB_SCHEMA)
    conn.commit()
    return conn


def save_issues(conn, repos, language):
    now = datetime.datetime.now(datetime.UTC).isoformat()
    rows = [
        (
            issue["url"],
            repo["nameWithOwner"],
            repo["stargazerCount"],
            issue["number"],
            issue["title"],
            language,
            now,
        )
        for repo in repos
        for issue in repo["issues"]["nodes"]
    ]
    conn.executemany(
        """
        INSERT INTO issues (url, repo, stars, number, title, language, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            repo = excluded.repo,
            stars = excluded.stars,
            title = excluded.title,
            language = excluded.language,
            fetched_at = excluded.fetched_at
        """,
        rows,
    )
    conn.commit()
    return len(rows)
