import datetime
import re

import scrapy
from scrapy.loader import ItemLoader

from hardware_scraper.items import GPUItem
from hardware_scraper.spiders.utils import find_table
from hardware_scraper.spiders.utils import load_table_dict


class GPUSpider(scrapy.Spider):
    name = "gpu"
    allowed_domains = ["www.techpowerup.com"]
    manufacturers = ["NVIDIA", "AMD", "ATI", "Intel"]
    start_year = 2000

    def start_requests(self):
        base_url = "https://www.techpowerup.com/gpu-specs"

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
            yield response.follow(url, self.parse_gpu)

    def _find_table(self, sections, table_name):
        return find_table(sections=sections, table_name=table_name, css="h2::text")

    def _get_table_dict(self, table):
        if table is None:
            return {}

        keys = table.css("section.details dl.clearfix dt::text").getall()
        values = table.css("section.details dl.clearfix dd").getall()

        keys = [key.strip().rstrip(":") for key in keys]
        values = [value.strip() for value in values]

        table_dict = {key: value for key, value in zip(keys, values)}
        return table_dict

    def parse_gpu(self, response):
        # check if we are on the expected page (necessary if using proxies)
        if not response.css("h1.gpudb-name::text").get():
            yield scrapy.Request(url=response.url, dont_filter=True)

        gpu_full_name = response.css("h1.gpudb-name::text").get()
        manufacturer = gpu_full_name.split(" ")[0]
        gpu_name = " ".join(gpu_full_name.split(" ")[1:])

        sections = response.css("section.details")
        graphics_processor_table = self._find_table(sections, "Graphics Processor")
        graphics_card_table = self._find_table(sections, "Graphics Card")
        if graphics_card_table is None:
            graphics_card_table = self._find_table(sections, "Mobile Graphics")
        clocks_table = self._find_table(sections, "Clock Speeds")
        theoretical_performance_table = self._find_table(
            sections, "Theoretical Performance"
        )
        board_design_table = self._find_table(sections, "Board Design")
        memory_table = self._find_table(sections, "Memory")
        graphics_features_table = self._find_table(sections, "Graphics Features")
        render_config_table = self._find_table(sections, "Render Config")

        graphics_processor = self._get_table_dict(graphics_processor_table)
        graphics_card = self._get_table_dict(graphics_card_table)
        clocks = self._get_table_dict(clocks_table)
        theoretical_performance = self._get_table_dict(theoretical_performance_table)
        board_design = self._get_table_dict(board_design_table)
        memory = self._get_table_dict(memory_table)
        graphics_features = self._get_table_dict(graphics_features_table)
        render_config = self._get_table_dict(render_config_table)

        # load values
        loader = ItemLoader(item=GPUItem(), response=response)

        # load model values
        loader.add_value("gpu_full_name", gpu_full_name)
        loader.add_value("manufacturer", manufacturer)
        loader.add_value("gpu_name", gpu_name)

        # load graphics processor values
        graphics_processor_key_mapping = {
            "chip_name": "GPU Name",
            "chip_variant": "GPU Variant",
            "architecture": "Architecture",
            "process_size": "Process Size",
            "die_size": "Die Size",
        }
        load_table_dict(
            loader=loader,
            key_mapping=graphics_processor_key_mapping,
            table_dict=graphics_processor,
            full_name=gpu_full_name,
            logger=self.logger,
        )

        # load graphics card values
        graphics_card_key_mapping = {
            "release_date": "Release Date",
            "generation": "Generation",
            "production_status": "Production",
        }
        load_table_dict(
            loader=loader,
            key_mapping=graphics_card_key_mapping,
            table_dict=graphics_card,
            full_name=gpu_full_name,
            logger=self.logger,
        )

        # load clocks values
        clocks_key_mapping = {
            "frequency": ["GPU Clock", "Base Clock"],
            "turbo_frequency": "Boost Clock",
            "memory_frequency": "Memory Clock",
        }
        load_table_dict(
            loader=loader,
            key_mapping=clocks_key_mapping,
            table_dict=clocks,
            full_name=gpu_full_name,
            logger=self.logger,
        )

        # load theoretical performance values
        theoretical_performance_key_mapping = {
            "pixel_rate": "Pixel Rate",
            "texture_rate": "Texture Rate",
            "fp_16": "FP16 (half) performance",
            "fp_32": "FP32 (float) performance",
            "fp_64": "FP64 (double) performance",
        }
        load_table_dict(
            loader=loader,
            key_mapping=theoretical_performance_key_mapping,
            table_dict=theoretical_performance,
            full_name=gpu_full_name,
            logger=self.logger,
        )

        # load board design values
        board_design_key_mapping = {"tdp": "TDP"}
        load_table_dict(
            loader=loader,
            key_mapping=board_design_key_mapping,
            table_dict=board_design,
            full_name=gpu_full_name,
            logger=self.logger,
        )

        # load memory values
        memory_key_mapping = {
            "memory_size": "Memory Size",
            "memory_type": "Memory Type",
            "memory_bus": "Memory Bus",
            "memory_bandwidth": "Bandwidth",
        }
        load_table_dict(
            loader=loader,
            key_mapping=memory_key_mapping,
            table_dict=memory,
            full_name=gpu_full_name,
            logger=self.logger,
        )

        # load graphics features values
        graphics_features_key_mapping = {
            "directx": "DirectX",
            "opengl": "OpenGL",
            "opencl": "OpenCL",
            "vulkan": "Vulkan",
            "cuda": "CUDA",
            "shader_model": "Shader Model",
        }
        load_table_dict(
            loader=loader,
            key_mapping=graphics_features_key_mapping,
            table_dict=graphics_features,
            full_name=gpu_full_name,
            logger=self.logger,
        )

        # load render config values
        render_config_key_mapping = {
            "shader_units": "Shading Units",
            "tmus": "TMUs",
            "rops": "ROPs",
            "sm_count": "SM Count",
            "smm_count": "SMM Count",
            "compute_units": "Compute Units",
            "execution_units": "Execution Units",
            "tensor_cores": "Tensor Cores",
            "rt_cores": "RT Cores",
            "cache_l0": "L0 Cache",
            "cache_l1": "L1 Cache",
            "cache_l2": "L2 Cache",
            "cache_l3": "L3 Cache",
        }
        load_table_dict(
            loader=loader,
            key_mapping=render_config_key_mapping,
            table_dict=render_config,
            full_name=gpu_full_name,
            logger=self.logger,
        )

        yield loader.load_item()
