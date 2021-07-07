import datetime
import sqlite3
import time
import typing as t

import lxml.etree
import lxml.html
import requests
import tqdm

from .scrape_config import ScrapeOrigin, enabled_origins

RATE_LIMIT_PERIOD = 3.5  # seconds
INSERT_ORIGIN = """
INSERT INTO ScrapeOrigin (
    short_code,
    full_name,
    kijiji_id,
    kijiji_name,
    latitude,
    longitude,
    radius
) VALUES (?, ?, ?, ?, ?, ?, ?);
"""

INSERT_METADATA = """
INSERT INTO ScrapeMetadata (timestamp) VALUES (?);
"""

INSERT_SCRAPE = """
INSERT INTO ApartmentScrape (
    scrape_origin_short_code,
    url,
    content
) VALUES (?, ?, ?);
"""

BASE_URL = "https://www.kijiji.ca/"


class IndexPage(t.NamedTuple):
    origin: ScrapeOrigin
    tree: lxml.etree.Element
    index: int


class Listing(t.NamedTuple):
    origin: ScrapeOrigin
    url: str


def rate_limited_get(url: str) -> requests.Response:
    retry_count = 3
    for i in range(retry_count):
        try:
            time.sleep(RATE_LIMIT_PERIOD)
            return requests.get(url)
        except Exception as e:
            if i < retry_count - 1:
                print(f"exception fetching {url}, retrying")
            else:
                raise e


def prepare_db():
    db = sqlite3.connect("db.sqlite3")

    with open("schema.sql") as schema:
        db.executescript(schema.read())

    cursor = db.cursor()
    for origin in enabled_origins:
        cursor.execute(INSERT_ORIGIN, origin)

    timestamp = datetime.datetime.utcnow().isoformat()
    cursor.execute(INSERT_METADATA, (timestamp,))

    return db


def build_apartment_listing_url(origin: ScrapeOrigin) -> str:
    return "".join(
        [
            BASE_URL,
            "b-appartement-condo/",
            origin.kijiji_name,
            "c37",
            origin.kijiji_id,
            "?ad=offering",
        ]
    )


def crawl(disable_progress=False):
    index_pages: t.List[IndexPage] = []
    listings: t.List[Listing] = []

    print("Scraping original results page")
    for origin in enabled_origins:
        origin_url = build_apartment_listing_url(origin)
        print(f"Fetching initial results page for {origin.full_name} ({origin_url})")
        response = rate_limited_get(origin_url)
        tree = lxml.html.fromstring(response.content)
        index_pages.append(IndexPage(origin, tree, 0))

    print("Building the full list of results pages")
    for results_page in index_pages:
        seen_urls = {listing.url for listing in listings}

        apartment_nodes = results_page.tree.cssselect(".info-container a.title")
        apartment_urls = {
            BASE_URL.rstrip("/") + node.get("href") for node in apartment_nodes
        } - seen_urls

        print(
            f"Found {len(apartment_urls)} apartments on {results_page.origin.full_name}, page {results_page.index}"
        )

        listings += [Listing(results_page.origin, url) for url in apartment_urls]

        next_nodes = results_page.tree.cssselect('[title~="Suivante"]')
        if next_nodes:
            url = BASE_URL.rstrip("/") + next_nodes[0].get("href")
            tree = lxml.html.fromstring(rate_limited_get(url).text)
            next_index = results_page.index + 1
            print(
                f"Found link to page {next_index} for {results_page.origin.full_name} ({url})"
            )
            index_pages.append(
                IndexPage(results_page.origin, tree, results_page.index + 1)
            )

    print(f"Found {len(listings)} total listings")
    db = prepare_db()
    for listing in tqdm.tqdm(listings, disable=disable_progress):
        origin, url = listing
        page = rate_limited_get(url).text

        row = origin.short_code, url, page
        db.cursor().execute(INSERT_SCRAPE, row)
        db.commit()

    db.close()

