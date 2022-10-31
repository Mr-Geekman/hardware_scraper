import datetime
import re

import scrapy
from scrapy.loader import ItemLoader

from hardware_scraper.items import CPUItem
from hardware_scraper.spiders.utils import find_table
from hardware_scraper.spiders.utils import load_table_dict


class CPUSpider(scrapy.Spider):
    name = "cpu"
    allowed_domains = ["www.techpowerup.com"]
    manufacturers = ["Intel", "AMD"]
    start_year = 2000

    def start_requests(self):
        base_url = "https://www.techpowerup.com/cpu-specs"

        for manufacturer in self.manufacturers:
            for release_year in range(self.start_year, datetime.date.today().year + 1):
                # get generations for each release year,
                # this is necessary because otherwise we can't get all the items of the page, there is a limit
                release_date_url = (
                    f"{base_url}/?mfgr={manufacturer}&released={release_year}&sort=name"
                )
                yield scrapy.Request(release_date_url, self.parse_manufacturer_year)

    def parse_manufacturer_year(self, response):
        # check if we are on the expected page (necessary if using proxies)
        if not response.css("select#generation").get():
            yield scrapy.Request(url=response.url, dont_filter=True)

        generations = response.css("select#generation option::text").getall()
        generations = [
            re.findall(r"(.*) \(\d+\)$", x)[0] for x in generations if x != "All"
        ]

        for generation in sorted(generations):
            url = f"{response.url}&generation={generation}"
            yield scrapy.Request(url, self.parse_generation)

    def parse_generation(self, response):
        # check if we are on the expected page (necessary if using proxies)
        if not response.css("select#generation").get():
            yield scrapy.Request(url=response.url, dont_filter=True)

        urls = response.css("table.processors tr td a::attr(href)").getall()
        for url in sorted(urls):
            yield response.follow(url, self.parse_cpu)

    def _find_table(self, sections, table_name):
        return find_table(sections=sections, table_name=table_name, css="h1::text")

    def _get_table_dict(self, table):
        if table is None:
            return {}

        keys = table.css("section.details table th::text").getall()
        values = table.css("section.details table td").getall()

        keys = [key.strip().rstrip(":") for key in keys]
        values = [value.strip() for value in values]

        table_dict = {key: value for key, value in zip(keys, values)}
        return table_dict

    def parse_cpu(self, response):
        # check if we are on the expected page (necessary if using proxies)
        if not response.css("h1.cpuname::text").get():
            yield scrapy.Request(url=response.url, dont_filter=True)

        cpu_full_name = response.css("h1.cpuname::text").get()
        manufacturer = cpu_full_name.split(" ")[0]
        cpu_name = " ".join(cpu_full_name.split(" ")[1:])

        sections = response.css("section.details")
        physical_table = self._find_table(sections, "Physical")
        performance_table = self._find_table(sections, "Performance")
        architecture_table = self._find_table(sections, "Architecture")
        cores_table = self._find_table(sections, "Cores")
        cache_table = self._find_table(sections, "Cache")
        features_table = self._find_table(sections, "Features")
        notes_table = self._find_table(sections, "Notes")

        details = self._get_table_dict(physical_table)
        performance = self._get_table_dict(performance_table)
        architecture = self._get_table_dict(architecture_table)
        cores = self._get_table_dict(cores_table)
        cache = self._get_table_dict(cache_table)
        if features_table is not None:
            features = features_table.css("ul.clearfix li").getall()
        else:
            features = None
        if notes_table is not None:
            notes = notes_table.css("td.p").get()
        else:
            notes = None

        # load values
        loader = ItemLoader(item=CPUItem(), response=response)

        # load model values
        loader.add_value("cpu_full_name", cpu_full_name)
        loader.add_value("manufacturer", manufacturer)
        loader.add_value("cpu_name", cpu_name)

        # load details values
        details_key_mapping = {
            "socket": "Socket",
            "process_size": "Process Size",
            "die_size": "Die Size",
        }
        load_table_dict(
            loader=loader,
            key_mapping=details_key_mapping,
            table_dict=details,
            full_name=cpu_full_name,
            logger=self.logger,
        )

        # load performance values
        performance_key_mapping = {
            "frequency": "Frequency",
            "turbo_frequency": "Turbo Clock",
            "unlocked_multiplier": "Multiplier Unlocked",
            "tdp": "TDP",
        }
        load_table_dict(
            loader=loader,
            key_mapping=performance_key_mapping,
            table_dict=performance,
            full_name=cpu_full_name,
            logger=self.logger,
        )

        # load architecture values
        architecture_key_mapping = {
            "market": "Market",
            "production_status": "Production Status",
            "release_date": "Release Date",
            "codename": "Codename",
            "generation": "Generation",
        }
        load_table_dict(
            loader=loader,
            key_mapping=architecture_key_mapping,
            table_dict=architecture,
            full_name=cpu_full_name,
            logger=self.logger,
        )

        # load cores values
        cores_key_mapping = {
            "number_of_cores": "# of Cores",
            "number_of_threads": "# of Threads",
            "integrated_graphics": "Integrated Graphics",
        }
        load_table_dict(
            loader=loader,
            key_mapping=cores_key_mapping,
            table_dict=cores,
            full_name=cpu_full_name,
            logger=self.logger,
        )

        # load cache values
        cache_key_mapping = {
            "cache_l1": "Cache L1",
            "cache_l1_type": "Cache L1",
            "cache_l2": "Cache L2",
            "cache_l2_type": "Cache L2",
            "cache_l3": "Cache L3",
            "cache_l3_type": "Cache L3",
        }
        load_table_dict(
            loader=loader,
            key_mapping=cache_key_mapping,
            table_dict=cache,
            full_name=cpu_full_name,
            logger=self.logger,
        )

        # load features
        if features is not None:
            for feature in features:
                loader.add_value("features", feature)

        # load notes
        if notes is not None:
            loader.add_value("notes", notes)

        yield loader.load_item()
