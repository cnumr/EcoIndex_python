from ecoindex.backend import get_api_version
from ecoindex.backend.routers import router
from ecoindex.backend.services.cache import cache
from ecoindex.config.sentry import init_sentry
from ecoindex.database.engine import init_db
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager


def init_app():
    cache.init()
    init_sentry(with_fastapi=True, release=get_api_version())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init_db()
        yield

    app = FastAPI(
        title="Ecoindex API",
        version=get_api_version(),
        description=(
            "Ecoindex API enables you to perform ecoindex analysis of given web pages"
        ),
        lifespan=lifespan,
    )

    app.include_router(router)

    from ecoindex.backend.middlewares.cors import add_cors_middleware
    from ecoindex.backend.middlewares.exception_handler import handle_exceptions

    handle_exceptions(app)
    add_cors_middleware(app)

    return app


app = init_app()
