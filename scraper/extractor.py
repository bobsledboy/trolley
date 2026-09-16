from typing import TypedDict

from recipe_scrapers import WebsiteNotImplementedError, scrape_me


class ExtractionError(Exception):
    pass


class ExtractedRecipe(TypedDict):
    title: str
    image_url: str | None
    servings: str | None
    prep_min: int | None
    cook_min: int | None
    ingredients: list[str]
    instructions: list[str]


def extract_sync(url: str) -> ExtractedRecipe:
    try:
        scraper = scrape_me(url)
    except WebsiteNotImplementedError:
        scraper = scrape_me(url, wild_mode=True)
    except Exception as exc:
        raise ExtractionError(f"couldn't fetch {url}") from exc

    try:
        title = scraper.title()
    except Exception as exc:
        raise ExtractionError("no recipe title found on that page") from exc

    try:
        ingredients = scraper.ingredients()
    except Exception:
        ingredients = []

    try:
        instructions = scraper.instructions_list()
    except Exception:
        try:
            instructions = [line for line in scraper.instructions().split("\n") if line.strip()]
        except Exception:
            instructions = []

    if not ingredients and not instructions:
        raise ExtractionError("no ingredients or instructions found on that page")

    try:
        image_url = scraper.image()
    except Exception:
        image_url = None

    try:
        servings = str(scraper.yields())
    except Exception:
        servings = None

    try:
        prep_min = int(scraper.prep_time())
    except Exception:
        prep_min = None

    try:
        cook_min = int(scraper.cook_time())
    except Exception:
        cook_min = None

    return {
        "title": title,
        "image_url": image_url,
        "servings": servings,
        "prep_min": prep_min,
        "cook_min": cook_min,
        "ingredients": ingredients,
        "instructions": instructions,
    }
