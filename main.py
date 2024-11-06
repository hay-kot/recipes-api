import logging

import uvicorn

from pkg import core


def main():
    settings = core.settings()

    # patch log level
    logging.getLogger().setLevel(logging.INFO)

    uvicorn.run(
        "pkg.api:app",
        reload=settings.dev,
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
