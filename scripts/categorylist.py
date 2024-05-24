import collections
import json
import pathlib
import uuid

from app.logger import logger

__filepath = pathlib.Path(__file__).parent


log = logger()

if __name__ == "__main__":
    paths = __filepath / "tests" / "snapshots"

    massivelist = []
    ##

    for path in paths.iterdir():
        if path.is_file() and path.suffix == ".json":
            with open(path, "r") as f:
                data = json.load(f)["data"]

                if "recipeCategory" in data:
                    massivelist.extend(data["recipeCategory"])

                if "keywords" in data:
                    massivelist.extend(data["keywords"])

                if "recipeCuisine" in data:
                    massivelist.append(data["recipeCuisine"])

    counter = collections.Counter(massivelist)

    items = []
    for key, value in counter.items():
        if value > 1:
            items.append((key, value))

    items.sort(key=lambda x: x[1], reverse=False)

    with open(__filepath / "categorylist.txt", "w") as f:
        for item in items:
            f.write(f'{{Name: "{item[0]}", ID: uuid.MustParse("{uuid.uuid4()}")}}, // {item[1]}\n')
