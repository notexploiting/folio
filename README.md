# Folio

Folio is a Python-based receipt processing and household inventory project designed to turn receipts into structured, queryable records. The workflow so far is as follows: scan a receipt image into an inbox, let AI extract the important fields, validate the result against a schema, manually confirm or fix fuzzy matches, and persist the data in a PostgreSQL database for later analysis.

This is a project built for personal use and experimentation, but the future plan is to Dockerize this backend with a React frontend.

------------------------------------------------------------------------

## Project overview

Folio is centered around the following pipeline:

1.  A user places a receipt image in an inbox folder.
2.  The application reads the file and sends it to Google Gemini for structured extraction.
3.  The AI is guided by a strict Pydantic schema so that output follows a predictable format.
4.  The extracted receipt is reviewed in the CLI.
5.  Fuzzy matching is used to normalize item names against a canonical item table.
6.  The final receipt and line items are inserted into PostgreSQL.
7.  The original file is moved into an archive folder and the structured JSON payload is preserved.

------------------------------------------------------------------------

## Why this project exists

As I start becoming independent in managing my own expenses, I wanted to track groceries, my inventory, and spending patterns all in one place. There are several off-the-shelf and open-source applications that handle these needs, but very few combine all of them into one unified system. Furthermore:

-   Most commercial apps only read the receipt total and merchant name. My system records every single line item so the user can track the quantities of each item.

-   OCR models frequently extract slightly different strings for identical items. By integrating PostgreSQL's `pg-trgm`, an interactive human-in-the-loop review step can group together identical names into a canonical one.

-   Consumer expense apps push recurring subscriptions. Leveraging my existing Synology DS220+ server, free-tier Gemini API calls, and Tailscale networking provides virtually free data extraction and total data ownership. Understandably, commercializing this application would need some source of funding to continue running.

-   The custom PostgreSQL database has rich granularity, including as much detail as possible (e.g. currency, store address for maps).

------------------------------------------------------------------------

## Core features

-   AI-assisted receipt extraction from common image/PDF inputs
-   Structured extraction of:
    -   merchant name and metadata
    -   purchase date and time
    -   tax and tip
    -   total cost
    -   payment method and last four digits
    -   individual line items
-   Pydantic-backed validation for returned JSON
-   Canonical item normalization through fuzzy matching
-   PostgreSQL persistence with relational schema design
-   Manual override workflow for receipts and line items
-   Archive workflow for original files and JSON snapshots
-   Undo/delete support for a receipt entry and its related items

------------------------------------------------------------------------

## High-level architecture

The application is split into a few narrow responsibilities:

-   `src/folio/extractor.py` handles AI OCR/extraction
-   `src/folio/schema.py` defines the strict extraction contract
-   `src/folio/db.py` handles PostgreSQL interactions and item canonicalization
-   `src/folio/cli.py` provides the user-facing workflow and interaction flow
-   `db/*.sql` contains database creation, setup, and maintenance scripts
-   `.env` holds local environment variables such as API keys and DB connection details

Alternatively, this project can be seen as a layered application:

-   data collection layer: receipt files in the inbox
-   extraction layer: Gemini-based parsing
-   validation layer: Pydantic schema enforcement
-   normalization layer: canonical item matching and category handling
-   persistence layer: PostgreSQL
-   UI layer: Rich-powered terminal interface

------------------------------------------------------------------------

## Files

### `pyproject.toml`

This defines the Python package and dependencies. The project uses `uv`/PEP 621 metadata and declares dependencies like:

-   `google-genai` for the Gemini API client
-   `psycopg[binary]` for PostgreSQL connectivity
-   `pydantic` for schema validation
-   `python-dotenv` for `.env` loading
-   `rich` for terminal styling and prompts

It also declares the console script entry:

-   `folio = "folio:main"`

In practice, the actual interactive logic is in `src/folio/cli.py`, so for now the project is structured more like a package with a CLI submodule than a single-entry app.

### `src/folio/__init__.py`

This file is currently minimal and effectively acts as a package initializer. It does not yet contain the main application logic that the script entry hints at. In a fuller implementation, this file could expose the main CLI entry or package-level metadata.

### `src/folio/extractor.py`

This is the AI integration point. It does the following:

-   loads `GEMINI_API_KEY` from the environment `.env`
-   uploads a file to the Google GenAI API
-   sends a carefully crafted prompt with the image/document
-   requests structured JSON output using the `ExtractedReceipt` schema
-   validates the output with `ExtractedReceipt.model_validate_json(...)`

Key technical notes:

-   the model used is `gemini-3.6-flash`
    -   `gemini-3.5-flash-lite` was tested for 'cheaper' requests, but wasn't as accurate (e.g. extracted date incorrectly)
-   `response_mime_type="application/json"` ensures machine-readable output
-   `response_schema=ExtractedReceipt` binds the AI output to the model contract
-   `temperature=0.0` reduces hallucination risk and improves determinism

### `src/folio/schema.py`

This file defines the core Pydantic objects:

-   `ExtractedItem`
-   `ExtractedReceipt`

These classes form the strict schema used for validation. In essence, they provide a contract for the AI response.

Examples of fields:

-   `raw_name`: the exact text as printed on the receipt
-   `specific_name`: a more detailed brand/item-specific name
-   `standard_name`: the normalized generic item label
-   `category`: broad classification like groceries, dairy, household
-   `price`, `quantity_purchased`, `unit`
-   `expiration_date`: date estimate for perishable goods

The schema also contains optional fields for missing info, such as `store_address`, `store_phone`, and `card_last_four`, which helps the model return partial but valid data instead of failing when something is not visible.

### `src/folio/db.py`

This file is the database layer. It handles all interactions with PostgreSQL through `psycopg` and the `dict_row` row factory. The main functions are:

-   `get_db_connection()`
-   `get_payment_methods()`
-   `fuzzy_match_canonical()`
-   `ensure_canonical_item()`
-   `insert_receipt_full()`
-   `delete_receipt()`

The database logic includes several important ideas:

-   it loads connection settings from the environment `.env`
-   it uses fuzzy text similarity against `canonical_items` to minimize duplicate item names
-   it ensures canonical records exist before writing receipt items
-   it avoids partial writes by inserting the parent receipt and then associated items
-   it supports deleting a receipt and cascading item cleanup, as defined by the database schema

### `src/folio/cli.py`

This is the main operational interface. It provides a terminal workflow for:

-   processing receipts from an inbox folder
-   asking the user to choose a payment method
-   optionally confirming AI matches for canonical item names
-   archiving processed files
-   manual receipt entry when no image is available
-   deleting a record by ID

Important functions include:

-   `process_auto()`
-   `process_manual()`
-   `review_and_insert()`
-   `select_payment_method()`
-   `main()`

The CLI uses `rich` to render colorized prompts and a simple guided experience. After AI extraction, the user still confirms the canonical item mapping before the data is committed.

------------------------------------------------------------------------

## Database design

The SQL scripts in the `db/` folder define the persistence model and some sample functions for interacting with it. The core database is a PostgreSQL database named `receipt_vault`.

**Note**: any file that modifies the database emphasizes the use of `BEGIN` and `ROLLBACK`/`COMMIT` patterns for safe verification.

### `db/db_setup.sql`

This creates the PostgreSQL schema and initial seed data:

-   `payment_methods`
-   `receipts`
-   `canonical_items`
-   `receipt_items`

It also enables the `pg_trgm` extension for fuzzy matching. That extension is essential because the application compares names like:

-   `greek yogurt`
-   `Greek Yogurt`
-   `Chobani Plain Greek Yogurt`

and wants to identify near matches with a similarity threshold.

The schema includes key design decisions:

-   `receipts` stores merchant and financial metadata
-   `receipt_items` stores per-line-item detail
-   `canonical_items` stores the generic normalized item names used across receipts
-   `receipt_items.canonical_id` links a receipt item to a generic item record
-   `receipt_items.receipt_id` is tied to `receipts(id)` with `ON DELETE CASCADE`

The schema also preserves useful metadata such as:

-   `currency`
-   `receipt_type` (`physical`, `digital`, `manual`)
-   `file_path`
-   `notes`
-   `created_at`

### `db/db_primary_keys.sql`

This SQL file is a maintenance script for resetting and checking serial sequence values. It is useful after bulk inserts or manual data cleanup, because PostgreSQL `SERIAL` counters can drift if rows are deleted or modified directly.

### `db/db_insert.sql`

This file contains sample insert patterns and examples. It demonstrates how to:

-   add a payment method
-   insert a canonical item
-   add a receipt and corresponding line items using a CTE pattern

### `db/db_update.sql`

This file shows common update operations for:

-   correcting receipt totals
-   updating inventory quantities
-   reclassifying items to a canonical item

### `db/db_delete.sql`

This file contains destructive and safety-wrapped SQL examples for:

-   deleting a receipt and all related items
-   deleting a single item
-   dropping tables
-   clearing canonical item references before deleting a generic item

------------------------------------------------------------------------

## Database and business logic details

The project includes a normalization layer that matters a lot for real usability.

### Canonical item normalization

One of the main ideas is that raw product names vary widely, but people often want a consistent record across receipts. For example:

-   `Signature Select Greek Yogurt`
-   `Chobani Plain Greek Yogurt`
-   `Fage Total 2% Greek Yogurt`

All of these should ideally resolve to one generic canonical item like `Greek Yogurt`.

This is handled by:

-   fuzzy matching against `canonical_items.standard_name`
-   a similarity threshold (`0.4` in the current implementation)
-   a manual review step in the CLI before insertion

The function `fuzzy_match_canonical()` queries PostgreSQL using the `pg_trgm` trigram extension so approximate matches can be found efficiently.

### Receipt item lifecycle

Each line item contains:

-   raw printed name
-   specific item name
-   canonical mapping
-   category
-   price
-   quantity purchased
-   unit
-   quantity remaining
-   expiration date estimate

This makes the design suitable for both personal finance tracking and inventory use cases. For example, item quantities and remaining stock can be tracked over time as receipts are added.

------------------------------------------------------------------------

## AI utilization and limitations

The project uses Google Gemini as a structured document parser for receipts. This is a strong fit for the problem because receipt images are visually noisy and often contain inconsistent formatting, localized measurements, and brand names that vary widely.

### How the AI is used

The AI pipeline does the heavy lifting for:

-   reading receipt text in noisy layouts
-   identifying line items and totals
-   extracting merchant metadata
-   inferring dates/times
-   assigning generalized item categories and names

The critical part is that the model is not allowed to return freeform output. Instead, it is constrained by `response_schema=ExtractedReceipt`, which dramatically reduces malformed JSON and makes downstream validation easier.

### Current limitations

This implementation is intentionally practical but still imperfect:

-   AI extraction can still misread low-quality or unusual receipts
-   ambiguous currency or dates may require human confirmation
-   fuzzy canonical mapping may still require manual override
-   some products are too specific or too generic to match perfectly without review

That's one of the reasons the CLI intentionally lets the user review or revise item mappings.

------------------------------------------------------------------------

## Data validation and safety

### Pydantic validation

`src/folio/schema.py` ensures that extracted receipt data follows a predictable structure. Each field is typed, and optional values are explicitly supported where necessary.

Examples:

-   `purchase_date` is expected as a `str` in `YYYY-MM-DD` format
-   `total_cost` is a required float
-   `expiration_date` may be `None`
-   `items` is a list of `ExtractedItem` objects

### Database constraints

The database schema also enforces constraints:

-   `currency` must be `USD` or `CAD`
-   `receipt_type` must be one of `physical`, `digital`, or `manual`
-   foreign keys ensure relational integrity between receipts and items
-   unique constraints on `canonical_items.standard_name` prevent duplicate generic names
-   `UNIQUE` on `payment_methods.name` avoids duplicated payment method records

------------------------------------------------------------------------

## Setup and environment

To run Folio locally, you will need:

-   Python 3.14+
-   PostgreSQL running locally or remotely
-   a Google Gemini API key
-   environment variables in a `.env` file

### Typical `.env` variables

``` env
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

### Database setup

1.  Create the PostgreSQL database and user if needed.
2.  Run the setup SQL in `db/db_setup.sql`.
3.  Verify the tables and sample data are present.

### Running the CLI

Typical workflow examples include:

``` bash
# process receipts in the inbox
python -m folio.cli auto

# manually enter a receipt
python -m folio.cli manual

# delete a receipt by ID
python -m folio.cli undo 12
```

If you are using `uv` in the repo, the environment is already configured by `pyproject.toml` and a virtual environment can be activated/updated with:

``` bash
uv sync
```

------------------------------------------------------------------------

## Tentative To-Do List

The current codebase is clearly a focused prototype/tooling workspace rather than a polished full production app. There are several natural next steps:

-   add a web dashboard or API layer
-   support batch processing of many receipts
-   add tests for extraction and database logic

One day I hope to evolve it into a more complete household finance and inventory product.

------------------------------------------------------------------------

## Summary

Folio is a personal receipt ingestion and normalization project that blends AI, schema validation, and PostgreSQL to transform receipts into manageable data. Essentially, you scan a receipt, review the extraction, normalize the items, store them, and keep a historical record of what was bought and how much it cost.