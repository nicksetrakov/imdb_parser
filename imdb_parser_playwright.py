import asyncio
import logging
import time
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

import pandas as pd
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


@dataclass
class Actor:
    full_name: str
    url: str
    character: str


async def get_top_250_movies(page) -> list[str]:
    logging.info("Fetching the top 250 movies...")
    await page.goto("https://www.imdb.com/chart/top/?ref_=nv_mv_250")
    await page.wait_for_load_state("networkidle")

    movie_elements = await page.locator(
        (
            "div.ipc-title.ipc-title--base.ipc-title--title."
            "ipc-title-link-no-icon.ipc-title--on-textPrimary."
            "sc-b189961a-9.bnSrml.cli-title"
        )
    ).all()

    if not movie_elements:
        logging.error("No top 250 movies found.")
        return []

    movie_urls = [
        await element.get_by_role("link").get_attribute("href")
        for element in movie_elements
    ]

    return ["https://www.imdb.com" + url for url in movie_urls]


async def get_cast(movie_url: str, context, semaphore) -> list[Actor]:
    parsed_url = urlparse(movie_url)
    new_path = parsed_url.path.rstrip("/") + "/fullcredits/"
    full_cast_url = urlunparse(parsed_url._replace(path=new_path))

    async with semaphore:
        logging.info(f"Fetching cast for movie: {full_cast_url}")
        page = await context.new_page()
        await page.goto(full_cast_url)
        await page.wait_for_load_state("load", timeout=60000)

        cast = []
        rows = await page.locator(".cast_list tr").all()

        try:
            for row in rows:
                character_locator = row.locator(".character")
                if await character_locator.count() > 0:
                    full_name = await row.locator(
                        ".primary_photo + td"
                    ).text_content()
                    actor_url_locator = row.locator(".primary_photo + td a")
                    actor_url = (
                        await actor_url_locator.get_attribute("href")
                        if await actor_url_locator.count() > 0
                        else ""
                    )
                    character = await character_locator.text_content()
                    cast.append(
                        Actor(
                            full_name=full_name.strip(),
                            url="https://www.imdb.com" + actor_url,
                            character=character.strip(),
                        )
                    )

                if "Rest of cast" in await row.text_content():
                    logging.info("Reached 'Rest of cast', stopping.")
                    break

        except PlaywrightTimeoutError as e:
            logging.error(f"Timed out while fetching cast for movie.\n{e}")

        logging.info(f"Fetched {len(cast)} actors for movie: {full_cast_url}")
        await page.close()
    return cast


async def main() -> None:
    start_time = time.time()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("imdb_parser.log", mode="w"),
            logging.StreamHandler(),
        ],
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        )
        page = await context.new_page()

        movies = await get_top_250_movies(page)
        semaphore = asyncio.Semaphore(10)

        tasks = [
            get_cast(movie_url, context, semaphore) for movie_url in movies
        ]

        all_casts = await asyncio.gather(*tasks)

        data = [actor for cast in all_casts for actor in cast]

        await browser.close()

        df = pd.DataFrame([actor.__dict__ for actor in data])
        df.to_csv("imdb_top250_cast_async.csv", index=False)
        logging.info(
            "Parsing completed. Results saved to file 'imdb_top250_cast_async.csv'."
        )

    end_time = time.time()
    execution_time = end_time - start_time

    logging.info(f"Execution time: {round(execution_time / 60, 1)} min")


if __name__ == "__main__":
    asyncio.run(main())
