# AGENTS.md

## Overview

- Primary language: Python
- UI framework: PySide6 (Qt)
- Repo layout: core app under `tuiview/`
- Supported Python: 3.10+ 

## Coding conventions

- Prefer small, focused changes; avoid unrelated refactors.
- Keep comments rare and only for non-obvious logic.
- Default to ASCII unless file already uses Unicode.

## Common tasks

- Search: use `rg` for fast code search.
- UI defaults: preferences are read from QSettings.

## Testing

- No automated test suite in this repo.
- Optional doc doctests:
  - `make -C doc doctest` (Linux/macOS)
  - `doc\make.bat doctest` (Windows)
- For UI changes, verify:
  1. App launches without errors.
  2. Preferences load/save correctly.
  3. Affected widget renders and responds as expected.

## Extensions

- Built-in plugins live under `plugins/`.
- User plugins load from `~/.tuiview/plugins`.
- Avoid breaking plugin API without a deprecation note.
