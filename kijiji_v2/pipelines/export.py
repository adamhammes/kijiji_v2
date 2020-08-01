import sqlite3

import kijiji_v2.scrape_config

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

INSERT_SCRAPE = """
INSERT INTO ApartmentScrape (
    scrape_origin_short_code,
    url,
    content
) VALUES (?, ?, ?);
"""


class ExportPipeline:
    def __init__(self):
        self.db = sqlite3.connect("db.sqlite3")

        with open("schema.sql") as schema:
            self.db.executescript(schema.read())

        cursor = self.db.cursor()
        for origin in kijiji_v2.scrape_config.enabled_origins:
            cursor.execute(INSERT_ORIGIN, origin)

    def process_item(self, item, _):
        cursor = self.db.cursor()

        cursor.execute(INSERT_SCRAPE, (item.origin.short_code, item.url, item.content))

        self.db.commit()

    def close_spider(self, _):
        self.db.close()
