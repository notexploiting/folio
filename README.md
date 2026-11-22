# Folio

Folio turns receipts into records I can search and track. A receipt image goes into an inbox, Gemini pulls out the store, totals, and every line item, Pydantic checks the result, and I confirm item names before it all gets saved to PostgreSQL.

## Why

Most expense apps only keep the store name and total. Folio keeps every line item so I can track what I bought and how much is left. The same item often gets read a few different ways, so pg_trgm fuzzy matching groups them under one name, with me confirming each match. It runs on my own Synology server over Tailscale with the free Gemini tier, so it costs nothing and I own the data.

## Setup

You need Python 3.14+, PostgreSQL, and a Gemini API key. Copy .env_template to .env and fill it in.

```env
GEMINI_API_KEY=your_api_key_here
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=receipt_vault
RECEIPT_INBOX_PATH=/path/to/inbox
RECEIPT_ARCHIVE_PATH=/path/to/archive
JSON_ARCHIVE_PATH=/path/to/json_archive
```

Run db/db_setup.sql to create the database and tables. The other files in db are sample queries for inserts, updates, deletes, and resetting primary keys. Each one that changes data is wrapped in BEGIN and ROLLBACK so you can check it first.

## Running

```bash
uv sync

# process receipts in the inbox
python -m folio.cli auto

# enter a receipt by hand
python -m folio.cli manual

# delete a receipt by ID
python -m folio.cli undo 12
```

## Plans

The CLI is being replaced by a FastAPI backend and a React frontend. See TODO.md for what is next.
