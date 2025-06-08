"""
news_fetcher.py
Fetches news articles from configured RSS feeds and stores them in the database.
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
import sqlite3

import feedparser
from settings import CONFIG_PATH, DB_PATH
import configparser
from typing import Iterable, Optional

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Global Constants ---
TABLE_NAME = "articles"


def load_feeds(path: Path = CONFIG_PATH) -> list[str]:
    """Return a list of RSS feed URLs from the config file."""
    parser = configparser.ConfigParser()
    parser.read(path)
    return [url.strip() for url in parser["RSSFeeds"]["feeds"].split(',')]


def initialize_db() -> None:
    """
    Create the database and articles table if they do not exist.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT,
                link TEXT NOT NULL,
                published_at TEXT,
                md5sum TEXT UNIQUE NOT NULL
            )
        ''')
        conn.commit()
    logger.info("Database initialized.")


def generate_md5(title: str, summary: str) -> str:
    """
    Generate an MD5 hash from the article title and summary text.

    Args:
        title (str): The article title.
        summary (str): The article summary.

    Returns:
        str: The MD5 hash string.
    """
    md5_input = f"{title}{summary}".encode('utf-8')
    return hashlib.md5(md5_input).hexdigest()



def fetch_and_store_news(feeds: Optional[Iterable[str]] = None) -> None:
    """Fetch configured RSS feeds and store new articles in the database."""
    if feeds is None:
        feeds = load_feeds()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        for feed_url in feeds:
            feed = feedparser.parse(feed_url)

            if getattr(feed, "bozo", False):
                logger.warning("Error parsing feed %s: %s", feed_url, feed.bozo_exception)
                continue

            for entry in feed.entries[:3]:
                title = entry.get("title", "No title available")
                summary = entry.get("summary", "No summary available")
                link = entry.get("link", "No link available")
                published_at = entry.get("published", datetime.now().isoformat())

                md5sum = generate_md5(title, summary)

                cursor.execute(
                    f"SELECT 1 FROM {TABLE_NAME} WHERE md5sum = ?",
                    (md5sum,),
                )
                if cursor.fetchone():
                    logger.info("Article already exists: %s", title)
                    continue

                cursor.execute(
                    f"""INSERT INTO {TABLE_NAME}
                            (title, summary, link, published_at, md5sum)
                            VALUES (?, ?, ?, ?, ?)""",
                    (title, summary, link, published_at, md5sum),
                )

                logger.info("Stored Article: %s", title)

        conn.commit()
    logger.info("All articles have been stored in the database.")


if __name__ == '__main__':
    initialize_db()
    fetch_and_store_news()
