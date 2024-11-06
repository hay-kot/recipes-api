import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware

from . import __version__, core
from .web.processors import router as processors_router
from .web.scrapers import router as scraper_router
from .web.system import router as system_router

settings = core.settings()
logger = core.logger()


app: FastAPI = FastAPI(
    title="Recipe API", description="A simple API for parsing recipes and ingredients.", version=__version__
)


@app.middleware("http")
async def logger_middleware(request: Request, call_next):
    # Retrieve the request ID and handle the case where it's missing
    request_id = request.headers.get("X-Request-ID", "")
    if request_id == "":
        request_id = uuid.uuid4()

        # https://github.com/fastapi/fastapi/issues/2727
        new_headers = request.headers.mutablecopy()
        new_headers.append("X-Request-ID", request_id.__str__())
        request._headers = new_headers
        request.scope.update(headers=request.headers.raw)
    path = request.url.path
    method = request.method

    logger.info(f"rid={request_id} method={method} path={path}")

    # Record the start time for performance measurement
    start_time = time.perf_counter()

    try:
        # Call the next middleware or endpoint handler
        response = await call_next(request)
    except Exception as e:
        # Log the error if the request fails
        logger.error(f"rid={request_id} path={path} error={str(e)}")
        raise

    # Calculate and log the processing time
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log the request details including the response status code
    logger.info(
        f"rid={request_id} path={path} method={method} " f"status_code={response.status_code} dur_ms={process_time:.2f}"
    )

    return response


app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(system_router, prefix="/api")
app.include_router(scraper_router, prefix="/api/v1")
app.include_router(processors_router, prefix="/api/v1")


# ignore logs for uvicorn because they're a pain in the ass
# to configure and it's easier to write our own middleware
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)


logger.info(f"starting web application, see docs http://{settings.host}:{settings.port}/docs")
