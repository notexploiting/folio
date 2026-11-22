# AGENTS.md

## Project

Folio turns receipt images into rows in PostgreSQL. Gemini extracts the data, Pydantic checks it, and the user confirms item names before saving. The CLI is being replaced by a FastAPI backend and a React frontend.

## Layout

Backend code is in src/folio. Frontend code will be in frontend. SQL scripts are in db. Python tests go in tests. Frontend tests go in frontend/tests. Test files start with test_ so they never get mixed up with real code.

## Writing

Write like a person, not a tool. Use short sentences and common words. Keep comments, docs, commit messages, and UI text as short as they can be while still being clear. Docs use only headers, plain paragraphs, and code blocks when needed. No bullet lists, tables, bold, emoji, or filler.

## Code

Readable beats clever. Write code out plainly, even if it is longer. Avoid extra layers, helpers used once, and abstractions that hide what is happening. Name things for what they are. The goal is code that is easy to read, check, and learn the stack from.

Follow the style already in the repo. Each file starts with a banner like "# --------- TITLE ---------". Functions get a triple-quoted docstring with a one-line summary and an Args: section (and Returns: if useful). In JavaScript, use a /** */ comment in the same shape. Short trailing comments are fine for lines that need them, lined up when there are several. SQL keeps the existing comment style and wraps changes in BEGIN and ROLLBACK/COMMIT.

## Frontend

Function first, looks last. Use default fonts, no rounded corners, and no colors unless they are needed to tell things apart. No bold, italics, or underline unless needed. Keep text on screen to a minimum, mostly labels for things that are not obvious. Make sure nothing overlaps or collides at any window size.

## Progress

TODO.md tracks what is next and what is done. Update it when a task is finished.
