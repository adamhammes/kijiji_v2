import datetime
import sqlite3


ORIGINS_QUERY = """
SELECT * FROM ScrapeOrigin;
"""

APARTMENTS_QUERY = """
SELECT
    a_s.id,
    a_s.url,
    ad.headline,
    ad.description,
    ad.date_posted,
    ad.price,
    ad.num_rooms,
    ad.num_bathrooms,
    aa.latitude,
    aa.longitude,
    aa.formatted_address,
    a_s.scrape_origin_short_code AS origin

    FROM
ApartmentScrape a_s
    INNER JOIN
ApartmentDetails ad ON a_s.id = ad.apartment_scrape_id
    INNER JOIN
ApartmentAddress aa ON a_s.id = aa.apartment_scrape_id;
"""

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

INSERT_APARTMENT = """
INSERT INTO Apartment (
    id,
    url,
    headline,
    description,
    date_posted,
    price,
    num_rooms,
    num_bathrooms,
    latitude,
    longitude,
    formatted_address,
    origin
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

SELECT_METADATA = "SELECT * FROM ScrapeMetadata;"
INSERT_METADATA = "INSERT INTO ScrapeMetadata (timestamp) VALUES (?)"


def run():
    read_db = sqlite3.connect("db.sqlite3")
    read_cursor = read_db.cursor()

    write_db = sqlite3.connect("frontend.sqlite3")
    write_db.execute("PRAGMA foreign_keys=ON")
    write_cursor = write_db.cursor()
    with open("frontend-schema.sql") as schema:
        write_cursor.executescript(schema.read())

    read_cursor.execute(ORIGINS_QUERY)
    for row in read_cursor:
        write_cursor.execute(INSERT_ORIGIN, row)

    write_db.commit()

    read_cursor.execute(APARTMENTS_QUERY)
    for row in read_cursor:
        write_cursor.execute(INSERT_APARTMENT, row)

    read_cursor.execute(SELECT_METADATA)
    for row in read_cursor:
        write_cursor.execute(INSERT_METADATA, row)

    write_db.commit()
    read_db.close()
