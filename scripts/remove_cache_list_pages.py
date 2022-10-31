import pathlib
import shutil
import json
from http import HTTPStatus
from collections import Counter

from loguru import logger

CACHE_PATH = pathlib.Path(__file__).parent.resolve().parent.joinpath(".scrapy").joinpath("httpcache")
OK_STATUS_CODES = {HTTPStatus.OK}


def main():
    counter = Counter()
    for hardware_directory in CACHE_PATH.iterdir():
        to_remove = []
        logger.info(f"Processing {hardware_directory.name}")
        for directory in hardware_directory.iterdir():
            for subdirectory in directory.iterdir():
                meta_filename = subdirectory.joinpath("meta")
                meta_contents = meta_filename.read_text()
                meta_contents = meta_contents.replace("'", '"')
                meta_info = json.loads(meta_contents)
                url = meta_info["url"].strip("'")
                cpu_list_prefix = "https://www.techpowerup.com/cpu-specs/?mfgr="
                gpu_list_prefix = "https://www.techpowerup.com/gpu-specs/?mfgr="
                if url.startswith(cpu_list_prefix) or url.startswith(gpu_list_prefix):
                    counter["list_page"] += 1
                    logger.info(f"Removing cache on url: {meta_info['url']}")
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
