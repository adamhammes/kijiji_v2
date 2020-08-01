import sqlite3
import typing

import requests
import tabulate
import tqdm


INSERT_ADDRESS = """
INSERT INTO ApartmentAddress (
    apartment_scrape_id,
    latitude,
    longitude,
    formatted_address
) VALUES (?, ?, ?, ?);
"""


class ApartmentAddress(typing.NamedTuple):
    apartment_scrape_id: int
    latitude: float
    longitude: float
    formatted_address: str


def geocode(
    apartment_scrape_id, raw_address
) -> (typing.Optional[ApartmentAddress], bool):
    response = requests.get(
        "http://localhost:5000", params={"address": raw_address}
    ).json()
    result = response["result"]
    from_cache = response["cache_type"] == "HIT"

    if result is None:
        return None, from_cache

    return (
        ApartmentAddress(
            apartment_scrape_id=apartment_scrape_id,
            latitude=result["latitude"],
            longitude=result["longitude"],
            formatted_address=result["display_address"],
        ),
        from_cache,
    )


def run():
    db = sqlite3.connect("db.sqlite3")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")

    cursor = db.cursor()
    cursor.execute("BEGIN TRANSACTION;")
    cursor.execute("SELECT * FROM ApartmentDetails;")

    hit_count = 0
    successfully_geocoded = 0

    all_results = cursor.fetchall()
    for row in tqdm.tqdm(all_results):
        address, from_cache = geocode(row["apartment_scrape_id"], row["raw_address"])
        if address is not None:
            db.cursor().execute(INSERT_ADDRESS, address)
            successfully_geocoded += 1

        if from_cache:
            hit_count += 1

    cursor.execute("COMMIT;")
    db.close()

    percent_geocoded = successfully_geocoded / len(all_results) * 100
    cache_hit_percentage = hit_count / len(all_results) * 100

    table = [
        ["successfully geocoded", f"{percent_geocoded:.2f}%"],
        ["cache hit percentage", f"{cache_hit_percentage:.2f}%"],
    ]

    print(tabulate.tabulate(table))


if __name__ == "__main__":
    run()
