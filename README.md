# Recipes API

A standalone Python API for scraping and parsing recipe data. It fetches a
recipe from a URL, extracts and normalizes the structured data, and uses NLP to
turn free-text ingredient lines into structured `{name, quantity, unit}` values.

Built with [FastAPI](https://fastapi.tiangolo.com/). Once running, interactive
docs are available at `/docs` (Swagger UI) and `/redoc`.

## Features

- **Recipe scraping** — extract structured recipe data from a URL (or supplied
  HTML) via [`recipe-scrapers`](https://github.com/hhursev/recipe-scrapers).
- **Data cleaning** — normalize instructions, ingredients, images, yields,
  durations, categories, and nutrition into a consistent schema.
- **Ingredient parsing** — turn unstructured ingredient lines into structured
  data (name, quantity, unit, comment) using
  [`ingredient-parser-nlp`](https://github.com/strangetom/ingredient-parser).
- **Nutrition parsing** — extract numeric amounts and units from nutrition
  strings via [`quantulum3`](https://github.com/nielstron/quantulum3).

## API

All endpoints are served under `/api`. See `/docs` for full request/response
schemas.

| Method | Path                          | Description                                                                 |
| ------ | ----------------------------- | --------------------------------------------------------------------------- |
| `GET`  | `/api/system/ready`           | Health check.                                                               |
| `GET`  | `/api/system/info`            | Version and build commit.                                                   |
| `POST` | `/api/v1/recipes/scrape`      | Scrape one or more URLs. Returns cleaned + parsed data, or raw data with `?clean=false`. |
| `POST` | `/api/v1/processors/ingredients` | Parse a list of ingredient strings into structured ingredients.          |

## Development Requirements

- [Python 3.14](https://www.python.org/)
- [mise](https://mise.jdx.dev/) — pins tool versions (Python, uv) and runs tasks
- [uv](https://docs.astral.sh/uv/) — Python package manager

`mise` installs the pinned Python and uv versions automatically. Sync
dependencies with:

```sh
mise run sync
```

## Tasks

Tasks are defined in `mise.toml` and run with `mise run <task>`:

| Task                       | Description                                                       |
| -------------------------- | ---------------------------------------------------------------- |
| `mise run run`             | Run the app locally with live reload.                            |
| `mise run test`            | Run the test suite (pass extra `pytest` args after the task).    |
| `mise run lint`            | Format and lint with autofix (`ruff`).                           |
| `mise run sync`            | Sync dependencies.                                               |
| `mise run testgen "<urls>"` | Fetch recipe URLs and generate snapshot test fixtures.          |

## Configuration

Configuration is read from environment variables (and an optional `.env` file),
all prefixed with `RECIPES_`:

| Variable             | Default     | Description                                          |
| -------------------- | ----------- | ---------------------------------------------------- |
| `RECIPES_HOST`       | `0.0.0.0`   | Host to bind to.                                     |
| `RECIPES_PORT`       | `8080`      | Port to bind to.                                     |
| `RECIPES_LOG_LEVEL`  | `INFO`      | Python logging level.                                |
| `RECIPES_DEV`        | `false`     | Enable development workflows such as live reloading. |
| `RECIPES_USER_AGENT` | Firefox UA  | User-Agent sent when fetching recipe URLs.           |
| `RECIPES_COMMIT`     | `nightly`   | Build commit hash (set by the build/release).        |

## Docker

A container image is published to the GitHub Container Registry on each release:

```sh
docker run -p 8080:8080 ghcr.io/hay-kot/recipes-api:latest
```

To build and run locally with Docker Compose:

```sh
docker compose up --build
```

## Testing

The test suite includes snapshot tests that run scrapers against saved HTML
fixtures in `tests/endpoint/testdata/` and compare against expected JSON in
`tests/endpoint/snapshots/`.

To add coverage for a new site, fetch fixtures from live URLs:

```sh
mise run testgen "https://example.com/recipe-a https://example.com/recipe-b"
```

This downloads each page's HTML into `tests/testgenfiles/`, then regenerates the
expected snapshots (it runs the suite with `SNAPSHOT=true`). Move the downloaded
HTML into `tests/endpoint/testdata/` and re-run so the new fixtures are picked up
and their snapshots written to `tests/endpoint/snapshots/`.
