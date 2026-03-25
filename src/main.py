from scrapers.gallito import PropertyScraper
from settings.settings import load_settings
from settings.logger import custom_logger
from src.database.database_connection import create_tables


if __name__ == "__main__":
    create_tables()
    settings = load_settings(key="Scraper")
    LOG_LEVEL = settings["LogLevel"]
    BASE_URL = settings["BaseUrl"]
    VALIDATION_URL = settings["ValidationUrl"]
    AMOUNT_OF_PROPERTIES = settings["AmountOfProperties"]


    scraper = PropertyScraper(
        max_properties=AMOUNT_OF_PROPERTIES,
        log_level=LOG_LEVEL
    )

    scraper.run(
        base_url=BASE_URL,
        validation_url=VALIDATION_URL,
    )
