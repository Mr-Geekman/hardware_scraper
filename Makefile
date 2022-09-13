lint: isort-check black-check

isort-check:
	isort --sl -c hardware_scraper/

black-check:
	black --check hardware_scraper/

format:
	isort --sl hardware_scraper/
	black hardware_scraper/
