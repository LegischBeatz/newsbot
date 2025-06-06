# AI News Bot

A Python-based automation tool that fetches the latest articles from various cybersecurity and technology RSS feeds, summarizes them using a local LLM, and posts punchy tweets to X (formerly Twitter). It also provides a command-line interface for database management.

---

## Table of Contents

- [Features](#features)  
- [Prerequisites](#prerequisites)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [Usage](#usage)  
  - [1. Fetching News](#1-fetching-news)  
  - [2. Database Management](#2-database-management)  
  - [3. Posting Tweets](#3-posting-tweets)  
- [Database Schema](#database-schema)  
- [Logging](#logging)  
- [Development](#development)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Features

- **RSS Aggregation**: Pulls from multiple feeds (e.g., NYTimes Technology, Wired AI, Darknet Diaries, Schneier on Security).  
- **Duplicate Detection**: Uses an MD5 hash of title + summary to prevent storing duplicates.  
- **Local SQLite Database**: Stores articles and posted hashes for idempotent operations.  
- **LLM Summarization**: Sends article title and summary to a user-defined LLM endpoint for tweet generation.  
- **Twitter Integration**: Posts directly to X/Twitter via the `tweepy` client.  
- **CLI Database Manager**: List, delete, or clean up database tables.  

---

## Prerequisites

- Python 3.8 or newer  
- `sqlite3` (bundled with Python)  
- Python packages:  
  - `feedparser`  
  - `requests`  
  - `tweepy`  
  - `python-dotenv` (optional)  

Install packages with:
```bash
pip install -r requirements.txt
```

---

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/ai-news-bot.git
   cd ai-news-bot
   ```
2. **Install dependencies** (see [Prerequisites](#prerequisites)).
3. **Configure** the application by editing `config.ini` (see [Configuration](#configuration)).

---

## Configuration

All settings live in `config.ini` at the project root.

```ini
[TwitterAPI]
bearer_token = YOUR_BEARER_TOKEN
api_key = YOUR_API_KEY
api_secret = YOUR_API_SECRET
access_token = YOUR_ACCESS_TOKEN
access_token_secret = YOUR_ACCESS_TOKEN_SECRET

[LLM]
api_url = http://localhost:11434/api/generate
model_name = deepseek-r1:8b

[Settings]
debug_mode = False

[RSSFeeds]
feeds = https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml, https://www.wired.com/feed/tag/ai/latest/rss, ...
```

* **TwitterAPI**: Credentials for posting tweets.
* **LLM**: URL and model name for your local language model.
* **Settings**: Toggle `debug_mode` to log instead of post.
* **RSSFeeds**: Comma-separated list of RSS feed URLs.

---

## Usage

### 1. Fetching News

Use `news_fetcher.py` to pull the latest entries and store them in the database:

```bash
python news_fetcher.py
```

* Initializes the DB if necessary.
* Fetches up to 3 entries per feed.
* Skips already-seen articles via MD5.

### 2. Database Management

The `db_manager.py` CLI provides three subcommands:

* **List entries**:

  ```bash
  python db_manager.py list --table articles
  ```
* **Delete an entry by ID**:

  ```bash
  python db_manager.py delete --table articles --id 5
  ```
* **Cleanup tables** (wipe all rows):

  ```bash
  python db_manager.py cleanup --table posts
  ```

  Omitting `--table` cleans both `articles` and `posts`.

### 3. Posting Tweets

Run `main.py` to pick the next unposted article, generate a tweet, and post it:

```bash
python main.py
```

* Connects to your LLM to craft a sub-300-character tweet.
* Posts via Tweepy (or logs if `debug_mode=True`).
* Records the article’s MD5 in `posts` to prevent reposting.

---

## Database Schema

* **articles**:

  | Column        | Type    | Description                        |
  | ------------- | ------- | ---------------------------------- |
  | id            | INTEGER | Auto-increment primary key         |
  | title         | TEXT    | Article headline                   |
  | summary       | TEXT    | Brief description from RSS feed    |
  | link          | TEXT    | URL to the full article            |
  | published\_at | TEXT    | Publication timestamp (ISO format) |
  | md5sum        | TEXT    | Unique hash of title+summary       |

* **posts**:

  | Column | Type    | Description                              |
  | ------ | ------- | ---------------------------------------- |
  | id     | INTEGER | Auto-increment primary key               |
  | md5sum | TEXT    | Hash of posted article (unique, foreign) |

---

## Logging

* Uses Python's built-in `logging` module.
* Default level is `INFO`.
* Log format includes timestamp, level, and message.

---

## Development

* **Add new feeds** by updating `RSSFeeds` in `config.ini`.
* **Adjust fetch limits** in `news_fetcher.py` (currently `entries[:3]`).
* **Customize tweet style** in `main.py`'s `summarize()` prompt.
