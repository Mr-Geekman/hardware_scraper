import pathlib
import shutil
import json
from http import HTTPStatus
from collections import Counter

from loguru import logger

CACHE_PATH = pathlib.Path(__file__).parent.resolve().parent.joinpath(".scrapy").joinpath("httpcache")
OK_STATUS_CODES = {HTTPStatus.OK}


def main():
    status_counter = Counter()
    for hardware_directory in CACHE_PATH.iterdir():
        to_remove = []
        logger.info(f"Processing {hardware_directory.name}")
        for directory in hardware_directory.iterdir():
            for subdirectory in directory.iterdir():
                meta_filename = subdirectory.joinpath("meta")
                meta_contents = meta_filename.read_text()
                meta_contents = meta_contents.replace("'", '"')
                meta_info = json.loads(meta_contents)
                status = meta_info["status"]
                status_counter[status] += 1
                if status not in OK_STATUS_CODES:
                    logger.info(f"Removing cache on url: {meta_info['url']} with status code: {status}")
                    to_remove.append(subdirectory)

        answer = input("Do you want to remove listed subdirectories with cache: Y/N [N]: ")
        if answer == "Y":
            logger.info("Removing")
            for subdirectory in to_remove:
                shutil.rmtree(subdirectory)
        else:
            logger.info("Not removing")


if __name__ == "__main__":
    main()
