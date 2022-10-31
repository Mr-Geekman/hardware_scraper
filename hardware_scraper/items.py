# Define here the models for your crawled items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import re
from typing import Any
from typing import Dict
from typing import Optional

import scrapy
from bs4 import BeautifulSoup
from dateutil import parser
from itemloaders.processors import MapCompose
from itemloaders.processors import TakeFirst
from scrapy import Field


def extract_text_from_tags(value: str) -> str:
    soup = BeautifulSoup(value, "html.parser")
    return soup.text


def extract_by_regexp(pattern: str, special_values: Optional[Dict[str, Any]] = None):
    if special_values is None:
        special_values = {}

    def wrapped(value: str) -> str:
        for key, value_to_return in special_values.items():
            if value == key:
                return value_to_return
        matches = re.findall(pattern, value)
        if len(matches) > 1:
            raise ValueError(
                f"There should be exactly one value in matching by pattern: {pattern}"
            )
        return matches[0]

    return wrapped


def extract_unit_value(
    pattern: str, value_name: str, unit_factors: Dict[str, float], value: str
):
    matches = re.findall(pattern, value)
    if len(matches) > 1:
        raise ValueError(
            f"There should be exactly one {value_name} in match by pattern: {pattern}"
        )
    if len(matches) == 0:
        if value == "N/A":
            return None
        else:
            raise ValueError(f"Unknown {value_name}: {value}")

    value, unit = matches[0]
    value = float(value)
    factor = unit_factors.get(unit, None)
    if factor is None:
        raise ValueError(f"Unknown unit of {value_name}: {unit}")
    value *= factor
    return value


def extract_frequency(value: str) -> Optional[float]:
    if value == "System Shared":
        return None

    pattern = r"((?:\d*[.])?\d+)\s*(MHz|GHz)"
    value_name = "frequency"
    unit_factors = {"GHz": 1000, "MHz": 1}
    return extract_unit_value(
        pattern=pattern, value_name=value_name, unit_factors=unit_factors, value=value
    )


def extract_pixel_rate(value: str) -> Optional[float]:
    pattern = r"((?:\d*[.])?\d+)\s*(MPixel/s|GPixel/s)"
    value_name = "pixel rate"
    unit_factors = {"GPixel/s": 1000, "MPixel/s": 1}
    return extract_unit_value(
        pattern=pattern, value_name=value_name, unit_factors=unit_factors, value=value
    )


def extract_texture_rate(value: str) -> Optional[float]:
    pattern = r"((?:\d*[.])?\d+)\s*(MTexel/s|GTexel/s)"
    value_name = "texture rate"
    unit_factors = {"GTexel/s": 1000, "MTexel/s": 1}
    return extract_unit_value(
        pattern=pattern, value_name=value_name, unit_factors=unit_factors, value=value
    )


def extract_flops(value: str) -> Optional[float]:
    pattern = r"((?:\d*[.])?\d+)\s*(GFLOPS|TFLOPS)"
    value_name = "flops"
    unit_factors = {"TFLOPS": 1000, "GFLOPS": 1}
    return extract_unit_value(
        pattern=pattern, value_name=value_name, unit_factors=unit_factors, value=value
    )


def extract_cache_size(value: str) -> Optional[float]:
    pattern = r"((?:\d*[.])?\d+)\s?(KB|MB)"
    value_name = "cache size"
    unit_factors = {"MB": 1000, "KB": 1}
    return extract_unit_value(
        pattern=pattern, value_name=value_name, unit_factors=unit_factors, value=value
    )


def extract_memory_size(value: str) -> Optional[float]:
    if value == "System Shared":
        return None

    pattern = r"((?:\d*[.])?\d+)\s?(MB|GB)"
    value_name = "memory size"
    unit_factors = {"GB": 1000, "MB": 1}
    return extract_unit_value(
        pattern=pattern, value_name=value_name, unit_factors=unit_factors, value=value
    )


def extract_memory_bandwidth(value: str) -> Optional[float]:
    if value == "System Dependent":
        return None

    pattern = r"((?:\d*[.])?\d+)\s?(MB/s|GB/s)"
    value_name = "memory bandwidth"
    unit_factors = {"MB/s": 1 / 1000, "GB/s": 1}
    return extract_unit_value(
        pattern=pattern, value_name=value_name, unit_factors=unit_factors, value=value
    )


def extract_cache_type(value: str) -> Optional[str]:
    pattern = r".*\((.*)\)"
    matches = re.findall(pattern, value)
    if len(matches) > 1:
        raise ValueError(
            f"There should be exactly one value in match by pattern: {pattern}"
        )
    if len(matches) == 0:
        return None

    match = matches[0]
    return match


def extract_multiplier(value: str) -> bool:
    if value == "Yes":
        return True
    elif value == "No":
        return False
    else:
        raise ValueError(f"Unknown value for multiplier: {value}")


def extract_release_date(value: str) -> Optional[str]:
    if value == "Unknown" or value == "Never Released":
        return value
    else:
        return parser.parse(value).date().isoformat()


def extract_generation(value: str) -> str:
    soup = BeautifulSoup(value, "html.parser")
    text = soup.text.strip()
    value_1, value_2 = text.split("\n", 1)
    return value_1


class CPUItem(scrapy.Item):
    # Physical section
    cpu_full_name = Field(
        input_processor=MapCompose(str.strip), output_processor=TakeFirst()
    )
    manufacturer = Field(
        input_processor=MapCompose(str.strip), output_processor=TakeFirst()
    )
    cpu_name = Field(
        input_processor=MapCompose(str.strip), output_processor=TakeFirst()
    )

    socket = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    # in nm
    process_size = Field(
        input_processor=MapCompose(
            extract_text_from_tags,
            str.strip,
            extract_by_regexp(r"((?:\d*[.])?\d+)\s*nm"),
            int,
        ),
        output_processor=TakeFirst(),
    )
    # in mm^2
    die_size = Field(
        input_processor=MapCompose(
            extract_text_from_tags,
            str.strip,
            extract_by_regexp(r"((?:\d*[.])?\d+)\s*mm²"),
            float,
        ),
        output_processor=TakeFirst(),
    )

    # Performance section
    # in MHz
    frequency = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_frequency
        ),
        output_processor=TakeFirst(),
    )
    # in MHz
    turbo_frequency = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_frequency
        ),
        output_processor=TakeFirst(),
    )
    unlocked_multiplier = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_multiplier
        ),
        output_processor=TakeFirst(),
    )
    # in Wats
    tdp = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_by_regexp(r"(\d+)\s*W"), float
        ),
        output_processor=TakeFirst(),
    )

    # Architecture section
    market = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    production_status = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    release_date = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_release_date
        ),
        output_processor=TakeFirst(),
    )
    codename = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    generation = Field(
        input_processor=MapCompose(extract_generation),
        output_processor=TakeFirst(),
    )

    # Cores section
    number_of_cores = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, int),
        output_processor=TakeFirst(),
    )
    number_of_threads = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, int),
        output_processor=TakeFirst(),
    )
    integrated_graphics = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )

    # Cache section
    cache_l1 = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_size
        ),
        output_processor=TakeFirst(),
    )
    cache_l1_type = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_type
        ),
        output_processor=TakeFirst(),
    )
    cache_l2 = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_size
        ),
        output_processor=TakeFirst(),
    )
    cache_l2_type = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_type
        ),
        output_processor=TakeFirst(),
    )
    cache_l3 = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_size
        ),
        output_processor=TakeFirst(),
    )
    cache_l3_type = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_type
        ),
        output_processor=TakeFirst(),
    )

    # Features section
    features = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
    )

    # Notes section
    notes = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )


class GPUItem(scrapy.Item):
    # Graphics Processor section
    gpu_full_name = Field(
        input_processor=MapCompose(str.strip), output_processor=TakeFirst()
    )
    manufacturer = Field(
        input_processor=MapCompose(str.strip), output_processor=TakeFirst()
    )
    gpu_name = Field(
        input_processor=MapCompose(str.strip), output_processor=TakeFirst()
    )
    chip_name = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    chip_variant = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    architecture = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    # in nm
    process_size = Field(
        input_processor=MapCompose(
            extract_text_from_tags,
            str.strip,
            extract_by_regexp(r"((?:\d*[.])?\d+)\s*nm"),
            int,
        ),
        output_processor=TakeFirst(),
    )
    # in mm^2
    die_size = Field(
        input_processor=MapCompose(
            extract_text_from_tags,
            str.strip,
            extract_by_regexp(
                r"((?:\d*[.])?\d+)\s*mm²", special_values={"unknown": None}
            ),
            float,
        ),
        output_processor=TakeFirst(),
    )

    # Graphics Card section
    release_date = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_release_date
        ),
        output_processor=TakeFirst(),
    )
    generation = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    production_status = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )

    # Clock Speeds section
    # in MHz
    frequency = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_frequency
        ),
        output_processor=TakeFirst(),
    )
    # in MHz
    turbo_frequency = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_frequency
        ),
        output_processor=TakeFirst(),
    )
    # in MHz
    memory_frequency = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_frequency
        ),
        output_processor=TakeFirst(),
    )

    # Theoretical Performance section
    # in MPixes/s
    pixel_rate = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_pixel_rate
        ),
        output_processor=TakeFirst(),
    )
    # in MTexel/s
    texture_rate = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_texture_rate
        ),
        output_processor=TakeFirst(),
    )
    # in GFlops
    fp_16 = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, extract_flops),
        output_processor=TakeFirst(),
    )
    # in GFlops
    fp_32 = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, extract_flops),
        output_processor=TakeFirst(),
    )
    # in GFlops
    fp_64 = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, extract_flops),
        output_processor=TakeFirst(),
    )

    # Board Design section
    # in Wats
    tdp = Field(
        input_processor=MapCompose(
            extract_text_from_tags,
            str.strip,
            extract_by_regexp(r"(\d+)\s*W", special_values={"unknown": None}),
            lambda x: None if x is None else float(x),
        ),
        output_processor=TakeFirst(),
    )

    # Memory section
    # in MB
    memory_size = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_memory_size
        ),
        output_processor=TakeFirst(),
    )
    memory_type = Field(
        input_processor=MapCompose(
            extract_text_from_tags,
            str.strip,
            lambda x: None if x == "System Shared" else x,
        ),
        output_processor=TakeFirst(),
    )
    # in bits
    memory_bus = Field(
        input_processor=MapCompose(
            extract_text_from_tags,
            str.strip,
            extract_by_regexp(r"(\d+)\s*bit", special_values={"System Shared": None}),
            lambda x: None if x is None else int(x),
        ),
        output_processor=TakeFirst(),
    )
    # in GB/s
    memory_bandwidth = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_memory_bandwidth
        ),
        output_processor=TakeFirst(),
    )

    # Graphics Features section
    directx = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    opengl = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    opencl = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    vulkan = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    cuda = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
    shader_model = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )

    # Render Config section
    shader_units = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, int),
        output_processor=TakeFirst(),
    )
    tmus = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, int),
        output_processor=TakeFirst(),
    )
    rops = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, int),
        output_processor=TakeFirst(),
    )
    sm_count = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, int),
        output_processor=TakeFirst(),
    )
    smm_count = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, int),
        output_processor=TakeFirst(),
    )
    compute_units = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, int),
        output_processor=TakeFirst(),
    )
    execution_units = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, int),
        output_processor=TakeFirst(),
    )
    tensor_cores = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, int),
        output_processor=TakeFirst(),
    )
    rt_cores = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, int),
        output_processor=TakeFirst(),
    )
    cache_l0 = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_size
        ),
        output_processor=TakeFirst(),
    )
    cache_l1 = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_size
        ),
        output_processor=TakeFirst(),
    )
    cache_l2 = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_size
        ),
        output_processor=TakeFirst(),
    )
    cache_l3 = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_size
        ),
        output_processor=TakeFirst(),
    )

    # TODO: add notes section
