import pathlib
import shutil
import json
from http import HTTPStatus
from collections import Counter

from loguru import logger

CACHE_PATH = pathlib.Path(__file__).parent.resolve().parent.joinpath(".scrapy").joinpath("httpcache").joinpath("cpu")
OK_STATUS_CODES = {HTTPStatus.OK}


def main():
    counter = Counter()
    for directory in CACHE_PATH.iterdir():
        for subdirectory in directory.iterdir():
            meta_filename = subdirectory.joinpath("meta")
            meta_contents = meta_filename.read_text()
            meta_contents = meta_contents.replace("'", '"')
            meta_info = json.loads(meta_contents)
            url = meta_info["url"].strip("'")
            if url.startswith("https://www.techpowerup.com/cpu-specs/?mfgr=Intel"):
                counter["list_page"] += 1
                logger.info(f"Removing cache on url: {meta_info['url']}")
                shutil.rmtree(subdirectory)


if __name__ == "__main__":
    main()
