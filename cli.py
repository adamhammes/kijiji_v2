import argparse
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
    crawler = CrawlerProcess(get_project_settings())
    crawler.crawl("apartments")
    crawler.start()


def process(url=None, limit=None, overwrite=False):
    kijiji_v2.process.run(url=url, limit=limit, overwrite=overwrite)


def geocode():
    kijiji_v2.geocode.run()


def frontend():
    kijiji_v2.frontend.run()


def upload():
    kijiji_v2.upload.upload()


def do_all():
def deploy():
    rebuild_endpoint = os.environ["NETLIFY_REBUILD_ENDPOINT"]
    requests.post(rebuild_endpoint, {})


    urllib3_logger = logging.getLogger("urllib3")
    urllib3_logger.setLevel(logging.CRITICAL)

    crawl()
    process()
    geocode()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    commands = {
        "crawl": crawl,
        "geocode": geocode,
        "all": do_all,
        "frontend": frontend,
        "upload": upload,
        "deploy": deploy,
    }

    subparsers = parser.add_subparsers(dest="command", required=True)
    for command_name in commands.keys():
        subparsers.add_parser(command_name)

    process_parser = subparsers.add_parser("process")
    process_parser.add_argument("--url")
    process_parser.add_argument("--limit", type=int)
    process_parser.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()

    if args.command == "process":
        process(args.url, args.limit, args.overwrite)
    else:
        commands[args.command]()
