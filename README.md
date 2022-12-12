## Recipes API

Standalone Python API for working with Recipe data. This is a work in progress. After deploying, you can view the docs at `/docs` or `/redoc`.

TODO's
- [ ] Remove HTML Scrape Support (remove httpx from deps + improve security profile)

Runtime Dependencies
- Crfpp + model
- Python 3.9+ (See requirements.txt for package dependencies)

### Endpoints

`/api/v1/scraper`

Scrapes a recipe from a URL and returns the unmodified data.

Method: `POST`

Body:

Maximum of 10 URLs per request. You can optionally provide a "html" key with a key-value pair of the URL and the HTML of the page. If the HTML is not provided, the API will scrape the page for you. This is useful if you want to use another language to do the IO work of web scraping, but still use the Python API to parse the data.

```json
{
    "urls": [
        "https://www.allrecipes.com/recipe/228180/creamy-chicken-and-broccoli-pasta/",
        "https://www.allrecipes.com/recipe/228180/creamy-chicken-and-broccoli-pasta/"
    ],
    "html": {
        "https://www.allrecipes.com/recipe/228180/creamy-chicken-and-broccoli-pasta/": "<html>...</html>"
    }
}
```

`/api/v1/parse`

Parses a list of ingredient strings and returns the parsed data. Parsing is done using the CRFPP library and the model published by the New York Times. Code is largely adapted from [TODO]()

Method: `POST`

Body:

```json
{
    "ingredients": [
        "1 (16 ounce) package linguine",
        "1/2 cup butter",
    ]
}
```
