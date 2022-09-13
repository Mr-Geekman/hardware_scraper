# Define here the models for your crawled items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import re
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


def extract_by_regexp(pattern: str):
    def wrapped(value: str) -> str:
        matches = re.findall(pattern, value)
        if len(matches) > 1:
            raise ValueError(
                f"There should be exactly one value in matching by pattern: {pattern}"
            )
        return matches[0]

    return wrapped


def extract_frequency(value: str) -> Optional[int]:
    pattern = r"((?:\d*[.])?\d+)\s*(MHz|GHz)"
    matches = re.findall(pattern, value)
    if len(matches) > 1:
        raise ValueError(
            f"There should be exactly one frequency in match by pattern: {pattern}"
        )
    if len(matches) == 0:
        if value == "N/A":
            return None
        else:
            raise ValueError(f"Unknown frequency: {value}")

    value, unit = matches[0]
    value = float(value)
    if unit == "GHz":
        value = value * 1000
    elif unit == "MHz":
        pass
    else:
        raise ValueError(f"Unknown unit of frequency: {unit}")
    return int(value)


def extract_cache(value: str) -> Optional[int]:
    pattern = r"((?:\d*[.])?\d+)\s?(K|MB)"
    matches = re.findall(pattern, value)
    if len(matches) > 1:
        raise ValueError(
            f"There should be exactly one cache in match by pattern: {pattern}"
        )
    if len(matches) == 0:
        if value == "N/A":
            return None
        else:
            raise ValueError(f"Unknown cache: {value}")

    value, unit = matches[0]
    value = float(value)
    if unit == "MB":
        value = value * 1000
    elif unit == "K":
        pass
    else:
        raise ValueError(f"Unknown unit of cache: {unit}")
    return int(value)


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


class CpuItem(scrapy.Item):
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
    # TODO: fix
    #   It results in answer 96 on page: https://www.techpowerup.com/cpu-specs/atom-230.c1395
    die_size = Field(
        input_processor=MapCompose(
            extract_text_from_tags,
            str.strip,
            extract_by_regexp(r"((?:\d*[.])?\d+)\s*mm²"),
            float,
        ),
        output_processor=TakeFirst(),
    )

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
    tdp = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_by_regexp(r"(\d+)\s*W"), float
        ),
        output_processor=TakeFirst(),
    )

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

    cache_l1 = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, extract_cache),
        output_processor=TakeFirst(),
    )
    cache_l1_type = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_type
        ),
        output_processor=TakeFirst(),
    )
    cache_l2 = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, extract_cache),
        output_processor=TakeFirst(),
    )
    cache_l2_type = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_type
        ),
        output_processor=TakeFirst(),
    )
    cache_l3 = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip, extract_cache),
        output_processor=TakeFirst(),
    )
    cache_l3_type = Field(
        input_processor=MapCompose(
            extract_text_from_tags, str.strip, extract_cache_type
        ),
        output_processor=TakeFirst(),
    )

    features = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
    )
    notes = Field(
        input_processor=MapCompose(extract_text_from_tags, str.strip),
        output_processor=TakeFirst(),
    )
