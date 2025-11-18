import asyncio
import pathlib
import sys

import httpx

# Add parent directory to path to import pkg module
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from pkg.core import logger

__filepath = pathlib.Path(__file__).parent


log = logger()

__urls = []


def get_urls(args: list[str]) -> list[str]:
    """Get urls from args."""
    if not args:
        return __urls

    urls = []
    for arg in args:
        if arg.startswith("http"):
            urls.append(arg)
    return urls


async def main():
    log.info("Starting...")

    ## get args
    log.info(sys.argv)

    urls = get_urls(sys.argv[1:])

    if not urls:
        log.error("No urls found")
        return

    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        results = await asyncio.gather(*tasks)

    for result in results:
        if result.status_code != 200:
            log.error(f"Failed to get {result.url} {result.status_code}")
            continue

        log.info(f"Got {result.url} {result.status_code}")

        log.info("extracting recipe")

        testfiledir = __filepath / "testgenfiles"

        testfiledir.mkdir(parents=True, exist_ok=True)

        # output format
        # testgenfiles / {domain}__{last_of_path_segment}.html
        # testgenfiles / {domain}__{last_of_path_segment}.json

        # build naming
        host = result.url.host
        segments = result.url.path.split("/")

        # reverse iterate over segments until we find a non empty one
        last_of_path_segment = None
        for segment in reversed(segments):
            if segment:
                last_of_path_segment = segment
                break

        htmlpath = testfiledir / f"{host}__{last_of_path_segment}.html"

        with htmlpath.open("w") as f:
            f.write(result.text)

    log.info("Finished...")


if __name__ == "__main__":
    asyncio.run(main())
