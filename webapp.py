from pathlib import Path
import sqlite3
from flask import Flask, render_template_string

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "news_articles.db"

app = Flask(__name__)


def get_articles():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, title, summary, link, published_at FROM articles ORDER BY id DESC"
        ).fetchall()
    return rows


@app.route("/")
def index():
    articles = get_articles()
    html = """
    <!doctype html>
    <html>
    <head><title>News Articles</title></head>
    <body>
        <h1>News Articles</h1>
        <table border="1" cellpadding="5">
            <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Summary</th>
                <th>Link</th>
                <th>Published</th>
            </tr>
            {% for row in articles %}
            <tr>
                <td>{{ row.id }}</td>
                <td>{{ row.title }}</td>
                <td>{{ row.summary }}</td>
                <td><a href="{{ row.link }}">link</a></td>
                <td>{{ row.published_at }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html, articles=articles)


if __name__ == "__main__":
    app.run(debug=True)
