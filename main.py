#!/usr/bin/env python3
"""
main.py
Responsible for generating social media posts for news articles and posting them to X/Twitter.
"""

import hashlib
import json
import logging
import re
from pathlib import Path
from textwrap import dedent
from typing import Optional, Tuple

import requests
import sqlite3
import tweepy
from settings import DB_PATH, Config

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Regex to strip out <think>…</think>
THINK_RE = re.compile(r"<think>.*?</think>", flags=re.DOTALL)


def init_db(db_path: Path = DB_PATH) -> None:
    """Ensure our SQLite database and tables exist."""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT,
                link TEXT NOT NULL,
                published_at TEXT,
                md5sum TEXT UNIQUE NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                md5sum TEXT UNIQUE NOT NULL
            )
        """)
        conn.commit()
    logger.info("Database initialized.")


def strip_think(text: str) -> str:
    """Remove any <think>…</think> sections from LLM output."""
    return THINK_RE.sub("", text).strip()


class LLMClient:
    """Simple wrapper around a streaming LLM endpoint."""
    def __init__(self, url: str, model: str):
        self.url = url
        self.model = model
        self.session = requests.Session()

    def generate(self, prompt: str, temperature: float = 0.1,
                 repetition_penalty: float = 1.0, strip: bool = True) -> Optional[str]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "repetition_penalty": repetition_penalty,
        }
        tokens = []
        try:
            resp = self.session.post(self.url, json=payload, stream=True, timeout=60)
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    tokens.append(data.get("response", ""))
                except json.JSONDecodeError as e:
                    logger.debug("Skipping malformed line: %s", e)
            text = "".join(tokens)
            return strip_think(text) if strip else text
        except requests.RequestException as e:
            logger.error("LLM request failed: %s", e)
            return None


def summarize(title: str, summary: str, link: str, llm: LLMClient) -> Optional[str]:
    """Ask the LLM to write a punchy, sub-300-char tweet for our article."""
    prompt = dedent(f"""
You are a cybersecurity journalist writing for X (formerly Twitter).

Write a tweet-style summary of the article that captures attention like a breaking news headline. It should be clear, urgent, and compelling — designed to stop the scroll and deliver the core story fast.

**Constraints:**
- Max 300 characters
- Tone: Direct, punchy, news-driven
- Style: Reads like a high-impact tweet — headline energy with just enough context
- Use emojis to enhance impact
- Do not include links, markdown, or any explanation — output only the tweet text

**Input:**
- Title: {title}
- Summary: {summary}

**Output:**
- Only the tweet
        """).strip()

    result = llm.generate(prompt, temperature=0.9)
    if not result:
        return None

    # Trim stray quotes and append link
    tweet = result.strip("\"'")

    return f"{tweet}\n\n{link}"



def fetch_next_article(db_path: Path = DB_PATH) -> Optional[Tuple[int,str,str,str,str]]:
    """Get the oldest article that hasn’t yet been tweeted."""
    query = """
        SELECT id, title, summary, link, md5sum
        FROM articles
        WHERE md5sum NOT IN (SELECT md5sum FROM posts)
        ORDER BY id
        LIMIT 1
    """
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(query).fetchone()
    return row  # or None


def mark_posted(md5sum: str, db_path: Path = DB_PATH) -> None:
    """Record that we’ve tweeted this article hash."""
    ins = "INSERT OR IGNORE INTO posts (md5sum) VALUES (?)"
    with sqlite3.connect(db_path) as conn:
        conn.execute(ins, (md5sum,))
        conn.commit()


def post_to_twitter(client: tweepy.Client, message: str, debug: bool = False) -> None:
    """Send (or log) a tweet."""
    if debug:
        logger.info("[DEBUG MODE] Tweet would be:\n%s", message)
        return

    try:
        client.create_tweet(text=message)
        logger.info("Tweet sent.")
    except tweepy.TweepyException as e:
        logger.error("Tweet failed: %s", e)
        if e.response is not None:
            logger.error("Status %s: %s", e.response.status_code, e.response.text)
        if getattr(e, "api_codes", None):
            logger.error("API codes: %s", e.api_codes)


def main() -> None:
    # Load config and init services
    cfg = Config.load()
    init_db()

    llm = LLMClient(cfg.llm_api_url, cfg.model_name)
    twitter = tweepy.Client(
        bearer_token=cfg.bearer_token,
        consumer_key=cfg.api_key,
        consumer_secret=cfg.api_secret,
        access_token=cfg.access_token,
        access_token_secret=cfg.access_token_secret,
    )

    # Grab the next fresh article
    article = fetch_next_article()
    if not article:
        logger.info("No new articles to post.")
        return

    art_id, title, summary, link, md5sum = article

    # Generate and send the tweet
    tweet_text = summarize(title, summary, link, llm)
    if not tweet_text:
        logger.warning("Failed to generate tweet for article %d", art_id)
        return

    post_to_twitter(twitter, tweet_text, debug=cfg.debug_mode)
    mark_posted(md5sum)


if __name__ == "__main__":
    main()
