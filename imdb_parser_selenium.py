import logging
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time


@dataclass
class Actor:
    full_name: str
    url: str
    character: str


def get_top_250_movies(driver: webdriver):
    driver.get("https://www.imdb.com/chart/top/?ref_=nv_mv_250")

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (
                By.CSS_SELECTOR,
                (
                    "div.ipc-title.ipc-title--base.ipc-title--title."
                    "ipc-title-link-no-icon.ipc-title--on-textPrimary."
                    "sc-b189961a-9.bnSrml.cli-title"
                ),
            )
        )
    )

    movies = driver.find_elements(
        By.CSS_SELECTOR,
        (
            "div.ipc-title.ipc-title--base.ipc-title--title."
            "ipc-title-link-no-icon.ipc-title--on-textPrimary."
            "sc-b189961a-9.bnSrml.cli-title"
        ),
    )
    movie_urls = [
        movie.find_element(By.TAG_NAME, "a").get_attribute("href")
        for movie in movies
    ]

    return movie_urls


def get_cast(movie_url: str, driver: webdriver):
    parsed_url = urlparse(movie_url)

    new_path = parsed_url.path.rstrip("/") + "/fullcredits/"

    full_cast_url = urlunparse(parsed_url._replace(path=new_path))

    logging.info(f"Fetching cast for movie: {full_cast_url}")

    driver.get(full_cast_url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "cast_list"))
    )

    cast_table = driver.find_element(By.CLASS_NAME, "cast_list")
    cast = []

    for row in cast_table.find_elements(By.TAG_NAME, "tr"):
        if row.find_elements(By.CLASS_NAME, "character"):
            element = row.find_element(
                By.CLASS_NAME, "primary_photo"
            ).find_element(By.XPATH, "./following-sibling::td")
            full_name = element.text.strip()
            url = element.find_element(By.TAG_NAME, "a").get_attribute("href")
            character = row.find_element(
                By.CLASS_NAME, "character"
            ).text.strip()
            cast.append(
                Actor(full_name=full_name, url=url, character=character)
            )

        if "Rest of cast" in row.text:
            logging.info("Reached 'Rest of cast', stopping.")
            break

    logging.info(f"Fetched {len(cast)} actors for movie: {full_cast_url}")

    return cast


def main():
    start_time = time.time()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("imdb_parser.log", mode="w"),
            logging.StreamHandler(),
        ],
    )

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )
    chrome_options.add_argument(
        (
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    )

    driver = webdriver.Chrome(options=chrome_options)

    try:
        movies = get_top_250_movies(driver)
        data = []

        for movie_url in movies:
            cast = get_cast(movie_url, driver)
            data.extend(cast)
    finally:
        driver.quit()

    df = pd.DataFrame(data)
    df.to_csv("imdb_top250_cast.csv", index=False)
    logging.info(
        "Parsing completed. Results saved to file 'imdb_top250_cast.csv'."
    )

    end_time = time.time()
    execution_time = end_time - start_time

    logging.info(f"Execution time: {round(execution_time / 60, 1)} min")


if __name__ == "__main__":
    main()
