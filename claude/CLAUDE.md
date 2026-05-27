# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Two Python environments are available:

- **`myenv/`** — Python 3.11 venv at `C:\Users\beni3\myenv`. Activate with `source myenv/Scripts/activate` (bash) or `myenv\Scripts\activate` (cmd).
- **`miniconda3/`** — Miniconda installation for conda-managed environments.

The PyCharm project at `PyCharmMiscProject/` uses a separate per-project interpreter: `Python 3.13 (PyCharmMiscProject)`.

## Common Commands

```bash
# Activate the venv
source myenv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Run the main script
python PyCharmMiscProject/script.py
```

## Project Structure

- `PyCharmMiscProject/script.py` — main Python script (currently imports numpy/pandas)
- `requirements.txt` — pinned data science dependencies: numpy, pandas, matplotlib, pillow, and their transitive deps
- `myenv/` — Python 3.11 virtual environment
- `miniconda3/` — Miniconda base installation
