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

With this docker setup you get 4 services running that are enough to make it all work:

- `db`: A MySQL instance
- `api`: The API instance running FastAPI application
- `worker`: The RQ task worker that runs ecoindex analysis
- `redis`: The [redis](https://redis.io/) instance that is used by the RQ worker and API cache

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
| API, Worker         | `REDIS_CACHE_HOST`         | `localhost`                        | The hostname of the redis backend used by RQ and API cache                                                                                                                                                                                                                                                                                                                                                                 |
| API, Worker         | `RQ_FAILURE_TTL`           | `86400`                            | Time in seconds before failed job metadata is removed from Redis                                                                                                                                                                                                                                                                                                                                                           |
| API, Worker         | `RQ_JOB_TIMEOUT`           | `600`                              | Maximum time in seconds a job is allowed to run before being stopped                                                                                                                                                                                                                                                                                                                                                       |
| API, Worker         | `RQ_RESULT_TTL`            | `86400`                            | Time in seconds before successful job results are removed from Redis                                                                                                                                                                                                                                                                                                                                                       |
| Worker              | `RQ_WORKERS`               | `3`                                | Number of RQ worker processes started in parallel (one job per process)                                                                                                                                                                                                                                                                                                                                                    |
| API, Worker         | `TZ`                       | `Europe/Paris`                     | The timezone used by the API and the worker.                                                                                                                                                                                                                                                                                                                                                                               |
| Worker              | `ENABLE_SCREENSHOT`        | `False`                            | If screenshots are enabled, when analyzing the page the image will be generated in the `./screenshot` directory with the image name corresponding to the analysis ID and will be available on the path `/{version}/ecoindexes/{id}/screenshot`                                                                                                                                                                             |
| Worker              | `SCREENSHOT_GID`           | None                               | The group used to create the screenshot. If not set, the group of the current user will be used.                                                                                                                                                                                                                                                                                                                           |
| Worker              | `SCREENSHOT_UID`           | None                               | The user used to create the screenshot. If not set, the current user will be used.                                                                                                                                                                                                                                                                                                                                         |

## Local development with [task](https://taskfile.dev)

Task is a task runner and build tool. You can install it with the following command:

```bash
curl -sL https://taskfile.dev/install.sh | sh
```

Then you can run the server in debug mode with the following command:

```bash
task start-dev
```

## Testing

We use Pytest to run unit tests for this project. The test suite are in the `tests` folder. Just execute :

```Bash
task tests

# or

task tests-coverage
```

> This runs pytest and also generate a [coverage report](https://pytest-cov.readthedocs.io/en/latest/) (terminal and html)
