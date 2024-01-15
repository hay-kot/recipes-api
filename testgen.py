import asyncio
import pathlib
import sys

import httpx

from app.logger import logger

__filepath = pathlib.Path(__file__).parent


log = logger()

__urls = [
    "https://basicswithbabish.co/basicsepisodes/pizza-dough",
    "https://basicswithbabish.co/basicsepisodes/shepherdspie",
    "https://cooking.nytimes.com/recipes/1015819-chocolate-chip-cookies",
    "https://cooking.nytimes.com/recipes/1023460-challah-bread",
    "https://cooking.nytimes.com/recipes/4735-old-fashioned-beef-stew",
    "https://delightbaking.com/little-fluffy-dinner-rolls/",
    "https://food52.com/recipes/65940-gingerbread-dough-for-houses",
    "https://leelalicious.com/earl-grey-tea-cake/#wprm-recipe-container-59869",
    "https://preppykitchen.com/chocolate-chip-banana-bread/",
    "https://prettysimplesweet.com/chocolate-buns-2/",
    "https://sallysbakingaddiction.com/spinach-bacon-breakfast-strata/",
    "https://thedomesticrebel.com/2021/04/28/levain-bakery-style-ultimate-peanut-butter-cookies/",
    "https://themodernproper.com/thai-basil-beef",
    "https://therecipecritic.com/crispy-parmesan-garlic-chicken-zucchini/",
    "https://www.bonappetit.com/recipe/adult-mac-and-cheese",
    "https://www.bonappetit.com/recipe/beef-stroganoff",
    "https://www.bonappetit.com/recipe/best-pumpkin-pie",
    "https://www.bonappetit.com/recipe/cabbage-roll-casserole",
    "https://www.bonappetit.com/recipe/cheesesteaks",
    "https://www.bonappetit.com/recipe/chicken-scarpariello",
    "https://www.bonappetit.com/recipe/easiest-chicken-adobo",
    "https://www.bonappetit.com/recipe/grilled-chicken-tacos",
    "https://www.bonappetit.com/recipe/mama-rosas-lasagna-de-carne",
    "https://www.bonappetit.com/recipe/roasted-broccoli",
    "https://www.bonappetit.com/recipe/seafood-chowder",
    "https://www.budgetbytes.com/beef-cabbage-stir-fry/",
    "https://www.budgetbytes.com/easy-pesto-chicken-and-vegetables/",
    "https://www.budgetbytes.com/fried-cabbage-and-noodles/",
    "https://www.budgetbytes.com/one-pot-creamy-cajun-chicken-pasta/",
    "https://www.budgetbytes.com/unstuffed-bell-peppers/",
    "https://www.cookingchanneltv.com/recipes/alton-brown/baked-potato-fries-reloaded-5470330",
    "https://www.delish.com/cooking/recipe-ideas/a19636089/creamy-tuscan-chicken-recipe/",
    "https://www.ethanchlebowski.com/cooking-techniques-recipes/grams-buns-the-greatest-bread-roll",
    "https://www.ethanchlebowski.com/cooking-techniques-recipes/kolaches-sweet-amp-savory",
    "https://www.foodnetwork.com/recipes/alton-brown/baked-macaroni-and-cheese-recipe-1939524",
    "https://www.foodnetwork.com/recipes/alton-brown/instant-pancake-mix-recipe-1938544",
    "https://www.halfbakedharvest.com/brown-butter-oatmeal-chocolate-chip-cookies/",
    "https://www.halfbakedharvest.com/chicken-gyros-with-feta-tzatziki/",
    "https://www.halfbakedharvest.com/chili-crisp-peanut-noodles/",
    "https://www.halfbakedharvest.com/creamy-parmesan-chicken-and-spinach-tortellini/",
    "https://www.halfbakedharvest.com/green-chile-chicken/",
    "https://www.halfbakedharvest.com/korean-beef-sesame-noodles/",
    "https://www.halfbakedharvest.com/one-pot-hamburger-helper/",
    "https://www.halfbakedharvest.com/roasted-red-pepper-chicken-pasta/",
    "https://www.halfbakedharvest.com/stove-top-mac-and-cheese/",
    "https://www.joshuaweissman.com/post/burger-buns",
    "https://www.joshuaweissman.com/post/levian-chocolate-chip-cookies",
    "https://www.recipetineats.com/greek-chicken-gyros-with-tzatziki/#wprm-recipe-container-21826",
    "https://www.recipetineats.com/naan-recipe/",
    "https://www.seriouseats.com/copycat-chicken-nuggets-with-sweet-n-sour-sauce",
    "https://www.seriouseats.com/easy-no-knead-focaccia",
    "https://www.seriouseats.com/five-minute-grilled-chicken-cutlet-rosemary-garlic-lemon-recipe",
    "https://www.seriouseats.com/ingredient-stovetop-mac-and-cheese-recipe",
    "https://www.seriouseats.com/salmon-burgers-remoulade-fennel-slaw-recipe",
    "https://www.seriouseats.com/spicy-spring-sicilian-pizza-recipe",
    "https://www.seriouseats.com/the-best-roast-potatoes-ever-recipe",
    "https://www.tasteofhome.com/recipes/dutch-oven-bread/",
]


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
