import argparse
import inspect
import logging
import os

import requests
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

import kijiji_v2.frontend
import kijiji_v2.geocode
import kijiji_v2.process
import kijiji_v2.upload


def crawl():
    """For each city configured in `scrape_config.py`, crawl through Kijiji's
    apartments listings and save the raw HTML in the `ApartmentScrape` table.
    """
    crawler = CrawlerProcess(get_project_settings())
    crawler.crawl("apartments")
    crawler.start()


def process(url=None, limit=None, overwrite=False):
    """Parse the raw HTML from the crawl phase into the values we wish to
    display on the site - price, number of bathrooms, etc.
    """
    kijiji_v2.process.run(url=url, limit=limit, overwrite=overwrite)


def geocode():
    """Go through the rows of `ApartmentDetails` and attempt to geocode the
    addresses into `ApartmentAddress`. Expects the geocoding server to be
    running on http://localhost:5000.
    """
    kijiji_v2.geocode.run()


def frontend():
    """Flatten the data into a format suitable for generating a frontend site,
    and save it to a sqlite3 db named `frontend.sqlite3`. The schema for the
    frontend data is specified in `frontend-schema.sql`.
    """
    kijiji_v2.frontend.run()


def upload():
    """GZIP `db.sqlite3` and `frontend.sqlite3`, and upload them to the bucket
    `kijiji-apartments`. The uploaded file name will contain the current date in
    ISO-8601 format.
    """
    kijiji_v2.upload.upload()


def deploy():
    """Triggers a rebuild of the site in Netlify by sending a post request to
    the url specified by NETLIFY_REBUILD_ENDPOINT."""
    rebuild_endpoint = os.environ["NETLIFY_REBUILD_ENDPOINT"]
    requests.post(rebuild_endpoint, {})


def do_all(deploy_site=False):
    """Run `crawl`, `process`, and `geocode` in sequence. If `--deploy` is set,
    additionally run `upload` and `deploy`. Make sure the geocoding server is
    accessible at http://localhost:5000 before running this command.
    """
    urllib3_logger = logging.getLogger("urllib3")
    urllib3_logger.setLevel(logging.CRITICAL)

    crawl()
    process()
    geocode()
    frontend()

    if deploy_site:
        upload()
        deploy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    commands = {
        "crawl": crawl,
        "geocode": geocode,
        "frontend": frontend,
        "upload": upload,
        "deploy": deploy,
    }

    subparsers = parser.add_subparsers(dest="command", required=True)
    for command_name in commands.keys():
        command = commands[command_name]
        docstring = inspect.getdoc(command)
        subparsers.add_parser(command_name, help=docstring)

    process_parser = subparsers.add_parser("process", help=inspect.getdoc(process))
    process_parser.add_argument("--url")
    process_parser.add_argument("--limit", type=int)
    process_parser.add_argument("--overwrite", action="store_true")

    all_parser = subparsers.add_parser("all", help=inspect.getdoc(do_all))
    all_parser.add_argument("--deploy", action="store_true")

    args = parser.parse_args()

    if args.command == "process":
        process(args.url, args.limit, args.overwrite)
    elif args.command == "all":
        do_all(args.deploy)
    else:
        commands[args.command]()
