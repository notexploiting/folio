# TODO

## Next

Fix two-digit dates in extraction. A Dollarama receipt printed 26/09/13 on the card slip and 2026-09-13 in the footer, and Gemini returned 2013-09-26. The prompt should tell it to trust a full YYYY-MM-DD date on the receipt over a short one, and to reject years far from the current date. The expiration dates came back a year after the wrong date too.

Add pytest tests in tests for the API routes and db functions.

Set up a Vite and React app in frontend using plain JavaScript. First screen uploads a receipt, shows the extracted items, lets me confirm or change each item name, and saves it.

Add Vitest tests in frontend/tests.

Remove cli.py and the rich dependency once the web app does everything the CLI does.

Add Docker for the backend, frontend, and database.

## Later

Look into scanning receipts with the camera right in the app, the way the Apple Notes scanner or a banking app check scan works. Uploading files is fine until then.

Deleting a receipt keeps its archived file and snapshot. Decide if that should change, and whether old files should be compressed if storage gets big.

## Done

CLI that extracts a receipt with Gemini, checks it with Pydantic, fuzzy matches item names, and saves to PostgreSQL.

SQL scripts for setup, insert, update, delete, and primary key upkeep.

Switched the comments in db.py to docstrings.

FastAPI app in src/folio/api.py. Uploads go to the inbox. Saving a reviewed receipt moves the file to the archive and writes a JSON snapshot with both the reviewed receipt and the original AI extraction.

Tested every route end to end with a real receipt: upload, extract, match, save, archive, and delete.
