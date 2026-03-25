import sqlite3
import os
import logging

logger = logging.getLogger(__name__)


def init_db(db_path: str):
    """Initializeaza baza de date SQLite."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            url        TEXT    UNIQUE NOT NULL,
            title      TEXT,
            source     TEXT,
            posted_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", db_path)


def is_posted(db_path: str, url: str) -> bool:
    """Verifica daca un articol a fost deja postat."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
    result = c.fetchone()
    conn.close()
    return result is not None


def mark_posted(db_path: str, url: str, title: str, source: str):
    """Marcheaza un articol ca postat."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO articles (url, title, source) VALUES (?, ?, ?)",
            (url, title, source)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def get_stats(db_path: str) -> dict:
    """Returneaza statistici despre articolele postate."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM articles")
    total = c.fetchone()[0]
    c.execute("SELECT source, COUNT(*) as cnt FROM articles GROUP BY source ORDER BY cnt DESC LIMIT 5")
    top_sources = c.fetchall()
    conn.close()
    return {"total": total, "top_sources": top_sources}
