## Recipes API

Standalone Python API for working with Recipe data. This is a work in progress, and is not yet ready for use.

Runtime Dependencies
- Crfpp + model
- Python 3.9+ (See requirements.txt for package dependencies)

### Endpoints

`/scraper`

Scrapes a recipe from a URL and returns the unmodified data.

Method: `POST`

Body:

Maximum of 10 URLs per request.

```json
{
    "urls": [
        "https://www.allrecipes.com/recipe/228180/creamy-chicken-and-broccoli-pasta/",
        "https://www.allrecipes.com/recipe/228180/creamy-chicken-and-broccoli-pasta/"
    ]
}
```

`/parse`

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
