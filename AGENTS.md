# AGENTS.md

## Repo Shape
- Python 3.11+ project; CI runs on Python 3.12.
- The runtime entrypoint is `main.py`, which calls `src.cli.main`.
- The installed CLI is `cpacodexkeeper` via `pyproject.toml`.
- Source lives under `src/`; tests live under `tests/` and use stdlib `unittest`.

## Commands
- Install dependencies with `python -m pip install -r requirements.txt`.
- Run the full test suite with `python -m unittest discover -s tests` or `just test`.
- Run one maintenance pass with `python main.py --once` or `just run-once`.
- Run dry-run mode with `python main.py --once --dry-run` or `just dry-run`.
- Run daemon mode with `python main.py` or `just daemon`.
- Build the Docker image with `docker build -t cpacodexkeeper .` or `just docker-build`.
- Bring up the Compose stack with `docker compose up -d --build` or `just docker-up`.

## Config Rules
- Configuration is `.env`-based; `config.json` is not used.
- `src/settings.py` reads the repo-root `.env` file first, then environment variables override it.
- `CPA_ENDPOINT` and `CPA_TOKEN` are required; `CPA_ENDPOINT` must start with `http://` or `https://`.
- `CPA_QUOTA_THRESHOLD` is validated as `0..100`; `CPA_MAX_RETRIES` is validated as `0..5`.
- `--once` disables daemon mode; `--dry-run` must not perform real deletes, disables, enables, or uploads.

## Workflow Notes
- CI only verifies unit tests and Docker image build; there is no repo-defined lint or typecheck step.
- Keep changes aligned with the existing `unittest` style unless the repo adds a different test runner.
- Prefer the executable sources of truth (`pyproject.toml`, `justfile`, `src/settings.py`, `.github/workflows/ci.yml`) over README prose when they disagree.
