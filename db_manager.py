#!/usr/bin/env python3
"""
db_manager.py
A simple command-line tool to manage the database for AI News Bot.
Provides commands to list entries, delete a specific entry by ID, or cleanup tables.
"""

import sqlite3
import argparse
import logging
import sys
import os

# --- Global Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "news_articles.db")
TABLE_ARTICLES = "articles"
TABLE_POSTS = "posts"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def list_entries(table):
    """
    List all entries from the specified table.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        if not rows:
            logger.info("No entries found in table '%s'.", table)
            return

        # Print column headers based on table name
        if table == TABLE_ARTICLES:
            headers = ["ID", "Title", "Summary", "Link", "Published At", "MD5Sum"]
        elif table == TABLE_POSTS:
            headers = ["ID", "MD5Sum"]
        else:
            headers = []
        
        # Print header row
        print(" | ".join(headers))
        print("-" * 80)
        for row in rows:
            # Convert all items to string for uniform display
            row_str = " | ".join(str(item) for item in row)
            print(row_str)
    except sqlite3.Error as e:
        logger.error("Error listing entries from %s: %s", table, e)
    finally:
        conn.close()


def delete_entry(table, entry_id):
    """
    Delete a specific entry by ID from the specified table.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(f"DELETE FROM {table} WHERE id = ?", (entry_id,))
        if cursor.rowcount == 0:
            logger.info("No entry with ID %d found in table '%s'.", entry_id, table)
        else:
            conn.commit()
            logger.info("Deleted entry with ID %d from table '%s'.", entry_id, table)
    except sqlite3.Error as e:
        logger.error("Error deleting entry from %s: %s", table, e)
    finally:
        conn.close()


def cleanup_table(table):
    """
    Delete all entries from the specified table.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(f"DELETE FROM {table}")
        conn.commit()
        logger.info("Cleaned up all entries from table '%s'.", table)
    except sqlite3.Error as e:
        logger.error("Error cleaning up table %s: %s", table, e)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Database Manager for AI News Bot.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: list
    list_parser = subparsers.add_parser("list", help="List entries from a table.")
    list_parser.add_argument("--table", choices=[TABLE_ARTICLES, TABLE_POSTS], default=TABLE_ARTICLES,
                             help="Table to list entries from (default: articles)")

    # Sub-command: delete
    delete_parser = subparsers.add_parser("delete", help="Delete an entry by ID from a table.")
    delete_parser.add_argument("--table", choices=[TABLE_ARTICLES, TABLE_POSTS], default=TABLE_ARTICLES,
                               help="Table to delete entry from (default: articles)")
    delete_parser.add_argument("--id", type=int, required=True, help="ID of the entry to delete.")

    # Sub-command: cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="Delete all entries from a table, or from both tables if not specified.")
    cleanup_parser.add_argument("--table", choices=[TABLE_ARTICLES, TABLE_POSTS],
                                help="Table to cleanup. If omitted, both articles and posts tables will be cleaned.")

    args = parser.parse_args()

    if args.command == "list":
        list_entries(args.table)
    elif args.command == "delete":
        delete_entry(args.table, args.id)
    elif args.command == "cleanup":
        if args.table:
            cleanup_table(args.table)
        else:
            # Cleanup both tables if no specific table provided
            cleanup_table(TABLE_ARTICLES)
            cleanup_table(TABLE_POSTS)
    else:
        logger.error("Unknown command: %s", args.command)
        sys.exit(1)


if __name__ == '__main__':
    main()

