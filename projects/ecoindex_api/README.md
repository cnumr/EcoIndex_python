# Ecoindex-Api

[![Validate project quality](https://github.com/cnumr/ecoindex_python_fullstack/actions/workflows/quality_check.yml/badge.svg?branch=main)](https://github.com/cnumr/ecoindex_python_fullstack/actions/workflows/quality_check.yml)

![Docker Pulls](https://img.shields.io/docker/pulls/vvatelot/ecoindex-api-worker?style=social&logo=docker&label=API%20Worker)
![Docker Pulls](https://img.shields.io/docker/pulls/vvatelot/ecoindex-api-backend?style=social&logo=docker&label=API%20Backend)


This tool provides an easy way to analyze websites with [Ecoindex](https://www.ecoindex.fr) on a remote server. You have the ability to:

- Make a page analysis
- Define screen resolution
- Save results to a DB
- Retrieve results
- Limit the number of request per day for a given host
- Get screenshots of the analyzed page

This API is built on top of [ecoindex-scraper](https://pypi.org/project/ecoindex-scraper/) with [FastAPI](https://fastapi.tiangolo.com/) and [RQ](https://python-rq.org/)

## OpenAPI specification

The API specification can be found in the [documentation](projects/ecoindex_api/openapi.json). You can also access it with [Redoc](https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/cnumr/ecoindex_python_fullstack/main/projects/ecoindex_api/openapi.json).

## Requirements

- [Docker](https://www.docker.com/)
- [Docker-compose v2](https://docs.docker.com/compose/compose-v2/)

## Installation

With this docker setup you get 5 services running that are enough to make it all work:

- `db`: A MySQL instance
- `api`: The API instance running FastAPI application
- `worker`: The RQ task worker that runs ecoindex analysis
- `valkey`: The [Valkey](https://valkey.io/) instance (Redis-compatible) used by the RQ worker and API cache
- `garage`: A local [Garage](https://garagehq.deuxfleurs.fr/) object storage exposing an S3-compatible API for screenshots

### First start

```bash
cp docker-compose.yml.template docker-compose.yml && \
docker  compose up -d
```

Every services should start normaly, then you can go to:

- [http://localhost:8001/docs](http://localhost:8001/docs) to access to the swagger of the API

## Configuration

Here are the environment variables you can configure in your `.env` file:

| Service             | Variable Name              | Default value                      | Description                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------- | -------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API, Worker         | `DEBUG`                    | `False`                            | If you want to run the server in debug mode, you can set this variable to `True`                                                                                                                                                                                                                                                                                                                                           |
| API                 | `WAIT_BEFORE_SCROLL`       | 3                                  | You can configure the wait time of the scenario when a page is loaded before it scrolls down to the bottom of the page                                                                                                                                                                                                                                                                                                     |
| API                 | `WAIT_AFTER_SCROLL`        | 3                                  | You can configure the wait time of the scenario when a page is loaded after having scrolled down to the bottom of the page                                                                                                                                                                                                                                                                                                 |
| API                 | `CORS_ALLOWED_CREDENTIALS` | `True`                             | See [MDN web doc](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Credentials)                                                                                                                                                                                                                                                                                                              |
| API                 | `CORS_ALLOWED_HEADERS`     | `*`                                | See [MDN web doc](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Headers)                                                                                                                                                                                                                                                                                                                  |
| API                 | `CORS_ALLOWED_METHODS`     | `*`                                | See [MDN web doc](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Methods)                                                                                                                                                                                                                                                                                                                  |
| API                 | `CORS_ALLOWED_ORIGINS`     | `*`                                | See [MDN web doc](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Origin)                                                                                                                                                                                                                                                                                                                   |
| API                 | `EXCLUDED_HOSTS`           | `["localhost", "127.0.0.1"]`       | You can configure a list of hosts that will be excluded from the analysis.                                                                                                                                                                                                                                                                                                                                                 |
| API, Worker         | `DAILY_LIMIT_PER_HOST`     | 0                                  | When this variable is set, it won't be possible for a same host to make more request than defined in the same day to avoid overload. If the variable is set, you will get a header `x-remaining-daily-requests: 6` in your response. It is used for the POST methods. If you reach your authorized request quota for the day, the next requests will give you a 429 response. If the variable is set to 0, no limit is set |
| API, Worker         | `DATABASE_URL`             | `sqlite+aiosqlite:///./sql_app.db` | If you run your mysql instance on a dedicated server, you can configure it with your credentials. By default, it uses an sqlite database when running in local                                                                                                                                                                                                                                                             |  |
| API, Worker         | `SENTRY_DSN`               | ``                                 | If you want to use [Sentry](https://sentry.io/) to monitor your application, set this variable with your project DSN.                                                                                                                                                                                                                                                                                                      |
| API, Worker         | `SENTRY_ENVIRONMENT`       | ``                                 | Optional Sentry environment name (e.g. `production`, `staging`). If not set, defaults to `development` when `DEBUG=True`, otherwise `production`.                                                                                                                                                                                                                                                                    |
| API, Worker         | `SENTRY_TRACES_SAMPLE_RATE`| `0.0`                              | Fraction of transactions to send to Sentry for performance monitoring (0.0 to 1.0). Set to `0.1` in production to sample 10% of requests.                                                                                                                                                                                                                                                                                 |
| API, Worker         | `REDIS_CACHE_HOST`         | `localhost`                        | The hostname of the Valkey backend used by RQ and API cache (Redis-compatible protocol)                                                                                                                                                                                                                                                                                                                                      |
| API, Worker         | `RQ_FAILURE_TTL`           | `86400`                            | Time in seconds before failed job metadata is removed from Valkey                                                                                                                                                                                                                                                                                                                                                          |
| API, Worker         | `RQ_JOB_TIMEOUT`           | `600`                              | Maximum time in seconds a job is allowed to run before being stopped                                                                                                                                                                                                                                                                                                                                                       |
| API, Worker         | `RQ_RESULT_TTL`            | `86400`                            | Time in seconds before successful job results are removed from Valkey                                                                                                                                                                                                                                                                                                                                                      |
| Worker              | `RQ_WORKERS`               | `3`                                | Number of RQ worker processes started in parallel (one job per process)                                                                                                                                                                                                                                                                                                                                                    |
| API, Worker         | `TZ`                       | `Europe/Paris`                     | The timezone used by the API and the worker.                                                                                                                                                                                                                                                                                                                                                                               |
| API, Worker         | `ENABLE_SCREENSHOT`        | `False`                            | If screenshots are enabled, the analysis generates a `.webp` image that remains available on `/{version}/ecoindexes/{id}/screenshot`. The underlying storage backend depends on `SCREENSHOT_STORAGE_TYPE`.                                                                                                                                                                                                                |
| API, Worker         | `SCREENSHOT_STORAGE_TYPE`  | `filesystem`                       | Screenshot storage backend. Supported values are `filesystem` and `s3`. The provided Docker Compose configuration forces `s3` by default.                                                                                                                                                                                                                                                                                 |
| API, Worker         | `SCREENSHOT_FILESYSTEM_PATH` | `./screenshots`                  | Root folder used when `SCREENSHOT_STORAGE_TYPE=filesystem`. The API reads screenshots from this path and the worker writes them there.                                                                                                                                                                                                                                                                                     |
| API, Worker         | `SCREENSHOT_S3_ENDPOINT_URL` | ``                               | S3-compatible endpoint used when `SCREENSHOT_STORAGE_TYPE=s3` (for example `http://garage:3900` in the provided Docker Compose stack).                                                                                                                                                                                                                                                                                    |
| API, Worker         | `SCREENSHOT_S3_REGION`     | `garage`                           | Region sent by the S3 client. This must match the S3 region configured by your object storage server.                                                                                                                                                                                                                                                                                                                       |
| API, Worker         | `SCREENSHOT_S3_BUCKET`     | ``                                 | Bucket that stores screenshots when `SCREENSHOT_STORAGE_TYPE=s3`.                                                                                                                                                                                                                                                                                                                                                            |
| API, Worker         | `SCREENSHOT_S3_PREFIX`     | `screenshots`                      | Optional object key prefix used inside the screenshot bucket.                                                                                                                                                                                                                                                                                                                                                                 |
| API, Worker         | `SCREENSHOT_S3_ACCESS_KEY_ID` | ``                              | Access key used to write and read screenshots from the S3-compatible storage.                                                                                                                                                                                                                                                                                                                                                |
| API, Worker         | `SCREENSHOT_S3_SECRET_ACCESS_KEY` | ``                           | Secret key associated with `SCREENSHOT_S3_ACCESS_KEY_ID`.                                                                                                                                                                                                                                                                                                                                                                     |
| API, Worker         | `SCREENSHOT_S3_FORCE_PATH_STYLE` | `True`                        | Forces path-style S3 URLs. This should stay enabled for Garage and many local S3-compatible services.                                                                                                                                                                                                                                                                                                                        |
| Worker              | `SCREENSHOTS_GID`          | None                               | The group used to create the screenshot file before it is persisted. This is mainly useful with `filesystem` storage.                                                                                                                                                                                                                                                                                                       |
| Worker              | `SCREENSHOTS_UID`          | None                               | The user used to create the screenshot file before it is persisted. This is mainly useful with `filesystem` storage.                                                                                                                                                                                                                                                                                                        |

### Screenshot storage

Two screenshot storage strategies are available:

- `filesystem`: the worker writes screenshots to `SCREENSHOT_FILESYSTEM_PATH` and the API serves the same shared directory.
- `s3`: the worker creates the screenshot locally, uploads it to the configured S3-compatible bucket, then the API reads it back from object storage.

The Docker Compose stack is configured to use `s3` by default with a local Garage container. This makes the default setup closer to production-style object storage while still staying self-hosted.

If you want to go back to local disk storage, set:

```bash
SCREENSHOT_STORAGE_TYPE=filesystem
SCREENSHOT_FILESYSTEM_PATH=/code/screenshots
```

When using the bundled Garage service, screenshots are uploaded to:

- endpoint: `http://garage:3900`
- bucket: `ecoindex-screenshots`
- region: `garage`

The Garage container starts with a default access key and bucket created from the Docker Compose environment variables. For any environment exposed outside local development, change:

- `SCREENSHOT_S3_ACCESS_KEY_ID`
- `SCREENSHOT_S3_SECRET_ACCESS_KEY`
- `projects/ecoindex_api/garage.toml` secrets and tokens

## Local development with [task](https://taskfile.dev)

Task is a task runner and build tool. You can install it with the following command:

```bash
curl -sL https://taskfile.dev/install.sh | sh
```

### Setup

From the repository root:

```bash
task uv:install          # Install Python 3.12 and all dependencies
task api:init-dev-project # Initialize API dev environment (Playwright, .env, migrations)
```

### Run the API locally

Valkey is started automatically via Docker. Then run:

```bash
task api:start-dev
```

This starts the backend (http://localhost:8000), the RQ worker and the RQ dashboard (http://localhost:9181).

## Testing

We use Pytest to run unit tests for this project. The test suite are in the `tests` folder. Just execute :

```Bash
task tests

# or

task tests-coverage
```

> This runs pytest and also generate a [coverage report](https://pytest-cov.readthedocs.io/en/latest/) (terminal and html)
