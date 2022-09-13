import pathlib
import shutil
import json
from http import HTTPStatus
from collections import Counter

from loguru import logger

CACHE_PATH = pathlib.Path(__file__).parent.resolve().parent.joinpath(".scrapy").joinpath("httpcache").joinpath("cpu")
OK_STATUS_CODES = {HTTPStatus.OK}


def main():
    status_counter = Counter()
    for directory in CACHE_PATH.iterdir():
        for subdirectory in directory.iterdir():
            meta_filename = subdirectory.joinpath("meta")
            meta_contents = meta_filename.read_text()
            meta_contents = meta_contents.replace("'", '"')
            meta_info = json.loads(meta_contents)
            status = meta_info["status"]
            status_counter[status] += 1
            if status not in OK_STATUS_CODES:
                logger.info(f"Removing cache on url: {meta_info['url']} with status code: {status}")
                shutil.rmtree(subdirectory)


if __name__ == "__main__":
    main()
