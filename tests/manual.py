import pprint
from pathlib import Path

import httpx

CWD = Path(__file__).parent


def html(name):
    return (CWD / "data" / name).read_text()


data = {
    "https://www.bonappetit.com/recipe/pimiento-cheese-crackers": html(
        "pimiento-cheese-crackers.html"
    )
}


def main():
    print("Starting...")

    with httpx.Client() as client:
        for url, url_html in data.items():

            payload = {
                "urls": [url],
                "html": {
                    url: url_html,
                },
            }

            response = client.post("http://localhost:8000/api/v1/scrape", json=payload)
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(response.text)
                continue

            pprint.pprint(response.json())

    print("Finished...")


if __name__ == "__main__":
    main()
