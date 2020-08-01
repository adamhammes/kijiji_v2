import dataclasses

import scrapy

import kijiji_v2.scrape_config


@dataclasses.dataclass
class ApartmentScrape:
    url: str
    content: str
    origin: kijiji_v2.scrape_config.ScrapeOrigin


class ApartmentSpider(scrapy.Spider):
    base_url = "https://www.kijiji.ca"
    name = "apartments"

    def start_requests(self):

        for origin in kijiji_v2.scrape_config.enabled_origins:
            url = "".join(
                [
                    ApartmentSpider.base_url,
                    "/b-appartement-condo/",
                    origin.kijiji_name,
                    "c37",
                    origin.kijiji_id,
                ]
            )

            yield scrapy.Request(
                url, callback=self.listing, meta={"dont_cache": True, "origin": origin},
            )

    def listing(self, response):
        apartment_paths = response.css(".info-container a.title::attr(href)").extract()

        next_path = response.css('[title~="Suivante"]::attr(href)').extract_first()

        if next_path:
            next_url = ApartmentSpider.base_url + next_path
            yield scrapy.Request(
                url=next_url, callback=self.listing, meta=response.meta
            )

        for apartment in apartment_paths:
            url = ApartmentSpider.base_url + apartment
            meta = response.meta.copy()
            del meta["dont_cache"]

            yield scrapy.Request(url, callback=self.apartment_details, meta=meta)

    def apartment_details(self, response):
        yield ApartmentScrape(
            origin=response.meta["origin"],
            url=response.request.url,
            content=response.text,
        )
