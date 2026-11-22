# TODO

## Next

Add a FastAPI app in src/folio/api.py that wraps the existing functions in db.py and extractor.py. It needs routes to list payment methods, upload a receipt for extraction, look up a fuzzy match, save a receipt, and delete a receipt.

Add pytest tests in tests for the API routes and db functions.

Set up a Vite and React app in frontend using plain JavaScript. First screen uploads a receipt, shows the extracted items, lets me confirm or change each item name, and saves it.

Add Vitest tests in frontend/tests.

Remove cli.py and the rich dependency once the web app does everything the CLI does.

Add Docker for the backend, frontend, and database.

## Done

CLI that extracts a receipt with Gemini, checks it with Pydantic, fuzzy matches item names, and saves to PostgreSQL.

SQL scripts for setup, insert, update, delete, and primary key upkeep.

Switched the comments in db.py to docstrings.
