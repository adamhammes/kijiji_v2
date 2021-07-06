import argparse
import datetime
import fractions
import locale
import re
import sqlite3
import traceback
import typing

import dateutil.parser
import lxml.etree
import lxml.html
import lxml.html.html5parser
import tabulate
import tqdm

locale.setlocale(locale.LC_ALL, "fr_FR")


class ApartmentDetails(typing.NamedTuple):
    apartment_scrape_id: int
    headline: str
    description: str
    date_posted: str
    price: int
    raw_address: str
    num_rooms: float
    num_bathrooms: float


INSERT_DETAILS = """
INSERT INTO ApartmentDetails(
    apartment_scrape_id,
    headline,
    description,
    date_posted,
    price,
    raw_address,
    num_rooms,
    num_bathrooms
) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""


class Selector:
    def __init__(self, tree, selector):
        selector_result = tree.cssselect(selector)
        self.element = selector_result[0] if selector_result else None

    def text(self):
        return self.element.text_content() if self.element is not None else None


def get_room_element(tree, element_name: str) -> typing.Optional[str]:
    label_elements = tree.cssselect("[class^='noLabelValue']")
    rooms_elements = [
        elem for elem in label_elements if element_name in elem.text_content()
    ]

    if not rooms_elements:
        return None

    text_parts = rooms_elements[0].text_content().split()[1:]
    return " ".join(text_parts)


def select(tree, selector):
    elements = tree.cssselect(selector)
    return elements[0] if elements else None


def read_price(tree) -> typing.Optional[int]:
    price_element = select(tree, 'span[class^="currentPrice"] > span')

    if price_element is None:
        return None

    raw_price = price_element.text_content()

    valid_chars = "0123456789,"
    valid_price = "".join(c for c in raw_price if c in valid_chars)

    price_re = re.compile(r"(\d+)(?:,(\d+))?")
    match = price_re.search(valid_price)

    if not match:
        return None

    dollars = int(match.group(1))
    cents = int(match.group(2) or 0)

    return dollars * 100 + cents


def read_num_bathrooms(tree):
    raw_bathrooms = get_room_element(tree, "Salles de bain")

    if not raw_bathrooms:
        return None

    bathroom_re = re.compile(r"(\d+)(,5)?")
    if not (match := bathroom_re.search(raw_bathrooms)):
        return None

    val = float(match.group(1))
    if match.group(2) == ",5":
        val += 0.5

    return val


def read_num_rooms(tree):
    raw_fraction = get_room_element(tree, "Pièces")

    if not raw_fraction:
        return None

    raw_fraction = raw_fraction.replace("½", "1/2")
    parts = raw_fraction.split(" ")[:2]

    return float(sum(fractions.Fraction(part) for part in parts))


def read_raw_address(tree):
    if not (raw_address := Selector(tree, "span[class^='address']").text()):
        return None

    if raw_address.startswith(", "):
        raw_address = raw_address[2:]

    return raw_address.strip()


def read_date_posted(tree):
    date_posted_element = select(tree, 'div[class^="datePosted"] > time')

    if date_posted_element is not None:
        raw_date = date_posted_element.get("datetime")
        return dateutil.parser.isoparse(raw_date)

    old_date_element = select(tree, '[class^="datePosted"] [title]')
    if old_date_element is not None:
        raw_date = old_date_element.get("title")
        # 6 mai 2020 19:39
        date_format = "%d %B %Y %H:%M"
        return datetime.datetime.strptime(raw_date, date_format)

    return None


def read_description(tree):
    elements = tree.cssselect('[class*="descriptionContainer"]')

    if not elements:
        return None

    description_element = elements[0]

    description = lxml.etree.tostring(description_element, encoding="unicode")

    return description


def read_headline(tree):
    element = tree.cssselect("[class*=title]")[0]
    return "".join(element.itertext())


def process(row):
    tree = lxml.html.fromstring(row["content"])

    return ApartmentDetails(
        apartment_scrape_id=row["id"],
        headline=read_headline(tree),
        description=read_description(tree),
        date_posted=read_date_posted(tree),
        price=read_price(tree),
        raw_address=read_raw_address(tree),
        num_rooms=read_num_rooms(tree),
        num_bathrooms=read_num_bathrooms(tree),
    )


def run(limit=None, url=None, overwrite=False, disable_progress=False):
    db = sqlite3.connect("db.sqlite3")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")

    cursor = db.cursor()

    if overwrite:
        cursor.execute("DELETE FROM ApartmentDetails;")
        db.commit()

    if url is None:
        cursor.execute("SELECT * FROM ApartmentScrape")
    else:
        print(url)
        cursor.execute("SELECT * FROM ApartmentScrape WHERE url = ?", (url,))

    if limit is None:
        rows = cursor.fetchall()
    else:
        rows = cursor.fetchmany(size=limit)

    cursor.execute("BEGIN TRANSACTION;")

    results = []
    for row in tqdm.tqdm(rows, disable=disable_progress):
        try:
            details = process(dict(row))
            cursor.execute(INSERT_DETAILS, details)
            results.append(details)
        except Exception:
            print(traceback.format_exc())
            print(row["url"])
    cursor.execute("COMMIT;")
    db.close()

    table = []
    for prop in [
        "num_rooms",
        "num_bathrooms",
        "price",
        "description",
        "date_posted",
        "raw_address",
        "headline",
    ]:
        num_present = len(
            [result for result in results if getattr(result, prop) is not None]
        )
        percent_none = num_present / len(results) * 100
        table.append([prop, num_present, f"{percent_none:.2f}%"])

    print(
        tabulate.tabulate(
            table,
            headers=["property", "num present", "% present"],
            colalign=["None", "right", "right"],
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    run(args.limit)
