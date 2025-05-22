"""
news_fetcher.py
Fetches news articles from configured RSS feeds and stores them in the database.
"""

import sqlite3
import feedparser
import logging
import hashlib
import configparser
from datetime import datetime
import os

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Global Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "news_articles.db")
TABLE_NAME = "articles"

print("BASE_DIR is:", BASE_DIR, DB_NAME )

# --- Read Config ---
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

config = configparser.ConfigParser()
config.read(CONFIG_PATH)
RSS_FEEDS = config['RSSFeeds']['feeds'].split(',')


def initialize_db():
    """
    Create the database and articles table if they do not exist.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(f'''
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
    conn.close()
    logger.info("Database initialized.")


def generate_md5(title, summary):
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


def fetch_and_store_news():
    """
    Fetch news articles from RSS feeds defined in the config and store them in the database.
    Skips articles that are already present (based on the MD5 hash).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for feed_url in RSS_FEEDS:
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
        
            # Check if the article already exists
            cursor.execute(f"SELECT 1 FROM {TABLE_NAME} WHERE md5sum = ?", (md5sum,))
            if cursor.fetchone():
                logger.info("Article already exists: %s", title)
                continue
        
            # Insert new article
            cursor.execute(f'''
                INSERT INTO {TABLE_NAME} (title, summary, link, published_at, md5sum)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, summary, link, published_at, md5sum))
        
            logger.info("Stored Article: %s", title)


    conn.commit()
    conn.close()
    logger.info("All articles have been stored in the database.")


if __name__ == '__main__':
    initialize_db()
    fetch_and_store_news()
