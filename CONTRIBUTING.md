# Contributing to aiohttp-autodocs

Thank you for your interest in contributing to `aiohttp-autodocs`! This document outlines our development setup, workflow, and guidelines.


## Development Setup

I use [`uv`](https://github.com/astral-sh/uv) Python environment and package management.

### 1. Clone the repository

```bash
git clone https://github.com/kappall/aiohttp_autodocs.git
cd aiohttp_autodocs
```

### 2. Create virtual environment & install dependencies

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```


## Development Commands

You can run commands directly using `uv run`:

### Running Tests
```bash
uv run pytest
```


## Git & Branching Workflow

1. **Base branch**: New work should branch off `development`.
2. **Branch naming**:
   - `bug/<issue-number>-<short-description>` (for bug fixes)
   - `feature/<issue-number>-<short-description>` (for features)
   - `chore/<issue-number>-<short-description>` (for maintenance, types, docs)
3. **Pull Requests**:
   - Target the `development` branch for PRs.
   - Link the relevant issue (e.g. `Closes #123`).
