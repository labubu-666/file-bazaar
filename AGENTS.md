# Coding
- Prefer simple solutions to complicated ones.
- Only do what was asked, do not wander off into tangents.
# Dependencies
- The project uses `uv`.
# Linting
## pre-commit
- Manages git commit hooks installed via `pre-commit install`.
- `pre-commit install` has to be run again after any changes to `.pre-commit-config.yaml`.
## ruff
- After making changes, run `uv run ruff format` to make sure files are correctly linted.
# Testing
- The project exclusively uses `pytest`.
- Prefer `monkeypatch` to `unittest.mock.patch`.
- Run tests using `uv run pytest -vvv`.