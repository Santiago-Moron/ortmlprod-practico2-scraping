import json
import os
import re
from typing import Dict, List
import sys

sys.path.append(os.getcwd())

from playwright.sync_api import Browser, Page, sync_playwright
import requests
from src.database.database_connection import insert_properties
from src.settings import custom_logger
from src.structs import PropertyType, Property, PropertyDetails


VALID_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
ID_DIGITS=8

class PropertyScraper:
    def __init__(
        self, output_dir: str = "data/scraped_data", max_properties: int = 60, log_level=10
    ) -> None:
        """
        Initialize the PropertyScraper

        Args:
            output_dir (str): The directory to store scraped data
            max_properties (int): The maximum number of properties to scrape
        """

        self.logger = custom_logger(self.__class__.__name__, log_level)


        self.output_dir = output_dir
        self.images_dir = os.path.join(self.output_dir, "images")
        self.properties_dir = os.path.join(self.output_dir, "properties")


        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.properties_dir, exist_ok=True)


        self.possible_types = {
            "casa": PropertyType.HOUSE,
            "apartamento": PropertyType.APARTMENT,
        }

        # Vamos a guardar cuáles son las ids de las propiedades ya procesadas para no guardarlas dos veces
        self.processed_properties = set()
        self._load_processed_properties()

        self.properties_processed = len(self.processed_properties)
        self.max_properties = max_properties
        self.logger.info(
            "PropertyScraper initialized. Output directory: %s", self.output_dir
        )

    def _load_processed_properties(self) -> None:
        """Load already processed properties from existing JSONL files"""

        for filename in os.listdir(self.properties_dir):
            if filename.endswith(".jsonl"):
                property_id = filename.replace(".jsonl", "")
                self.processed_properties.add(property_id)
        self.logger.info(
            f"Found {len(self.processed_properties)} previously processed properties"
        )

    def run(self, base_url: str, validation_url: str) -> None:
        """
        Run the property scraper.

        Args:
            base_url (str): The base URL for property listings.
            validation_url (str): The URL to validate property links.
        """

        self.logger.info("Starting scraper run")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            page = context.new_page()
            current_page = 1

            while True:
                if self.properties_processed >= self.max_properties:
                    self.logger.info(
                        f"Reached maximum number of new properties ({self.max_properties})"
                    )
                    break

                page_url = f"{base_url}/pagina{current_page}"
                self.logger.info(f"Processing page {current_page}, URL: {page_url}")

                page.goto(page_url)

                property_links = self._get_property_links(page, validation_url)
                self.logger.info(
                    f"Found {len(property_links)} unique property links on page {current_page}"
                )

                self._process_properties(page, property_links, browser)

                # Si no hay más páginas, terminamos
                if not self.has_next_page(page):
                    self.logger.info("No more pages to process")
                    break

                current_page += 1
            self.logger.info("Finished processing all properties across all pages")
            browser.close()

    def has_next_page(self, page) -> bool:
        next_button = page.locator("ul.list li.ant-pagination-item:last-child a")
        
        if next_button.count() == 0:
            return False
        
        href = next_button.get_attribute("href")
        return href is not None

    def _get_property_links(self, page: Page, validation_url: str) -> List[str]:
        """
        Get property links from the current page

        Args:
            page (Page): The page object to get property links from
            validation_url (str): The URL to validate property links

        Returns:
            List[str]: A list of property links
        """

        property_links = []

        # Find all links and filter for property listings (ending in 8 digits)
        all_links = page.locator("a.lc-data").all()
        # Extract href attributes and filter for valid property links
        for link in all_links:
            href = link.get_attribute("href")
            # Only include links that end with 9 digits (property IDs)
            if (
                href
                and re.search(r"/\d+$", href)
                and (href not in property_links)
            ):
                property_links.append(validation_url+href)

        # Remove duplicates while preserving order
        property_links = list(dict.fromkeys(property_links))
        return property_links

    def _process_properties(
        self,
        page: Page,
        property_links: List[str],
        browser: Browser,
    ) -> None:
        """
        Process each property link found on the page

        Args:
            page (Page): The page object to process property links from
            property_links (List[str]): A list of property links to process
            browser (Browser): The browser object to use for processing
        """
        properties_details = []
        for i, link in enumerate(property_links, 1):
            try:

                property = Property(
                    id=link.split("-")[-1][-ID_DIGITS:],
                    type=PropertyType.UNKNOWN,
                    link=link,
                    images=[],
                    details=None,
                )
                if property.id in self.processed_properties:
                    self.logger.info(
                        f"Skipping already processed property {property.id} ({i}/{len(property_links)})"
                    )
                    continue

                self.logger.info(
                    f"Processing property {i}/{len(property_links)}: {link}"
                )
                processed_property = self._process_property(page, property)
                properties_details.append(processed_property)
                # Guardamos la id de la propiedad para no procesarla de nuevo en el futuro
                self.processed_properties.add(processed_property.id)
                self.properties_processed += 1
                self.logger.info(
                    f"Processed {self.properties_processed}/{self.max_properties} properties"
                )
                

                if self.properties_processed >= self.max_properties:
                    break

            except Exception as e:
                self.logger.error(f"Error processing property {link}: {str(e)}")
                continue
        insert_properties(properties_details)

    def _process_property(self, page: Page, property: Property) -> Property | None:
        """
        Process a property by navigating to its URL and extracting its ID and image URLs

        Args:
            page (Page): The page object to use for processing
            property (Property): The property to process
        """


        self.logger.debug("Navigating to property URL: %s", property.link)
        page.goto(property.link)

        self.logger.debug("Processing property ID: %s", property.id)
        try:
            # .property_details_cover es la referencia a las imágenes en el caso de InfoCasas. 
            image_element = page.locator(".property_details_cover img")
            if not image_element.count():
                raise ValueError("Could not find image container #divInner_Galeria on page")

            img_urls = [img.get_attribute("src") for img in image_element.all()]
            self.logger.debug(
                "Successfully extracted %d image URLs from property page", len(img_urls)
            )

        except Exception as e:
            self.logger.error("Error retrieving image URLs: %s", str(e))
            img_urls = []

        # Obtenemos los detalles de la propiedad buscando el identificador div.iconoDatos
        try:
            details = self.scrape_property_details(page)



            property.details = PropertyDetails(
                        is_office=bool(details.get("Apto para Oficina", False)),
                        neighborhood=details.get("Zona"),
                        n_rooms=self._parse_rooms(details.get("Dormitorios")),
                        n_bathrooms=int(details["Baños"]) if details.get("Baños") else None,
                        square_meters=self._parse_m2(details.get("M² edificados"))
                    )
            
        except Exception as e:
            self.logger.error("Error retrieving property details: %s", str(e))
            return None

        # Guardamos localmente las imágenes, creando un directorio si todavía no existe
        property_img_dir = os.path.join(self.images_dir, property.id)
        os.makedirs(property_img_dir, exist_ok=True)

        jsonlines_data = []

        for i, img_url in enumerate(img_urls, 1):
            if any(img_url.endswith(ext) for ext in VALID_IMAGE_EXTENSIONS):

                img_filename = img_url.split("/")[-1]
                img_path = os.path.join(property_img_dir, img_filename)
                self.logger.debug(
                    f"Downloading image {i}/{len(img_urls)} for property {property.id}: {img_filename}"
                )

                # Aquí se descarga y se guarda la imagen
                try:
                    img_data = requests.get(img_url).content
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                except Exception as e:
                    self.logger.error(f"Failed to download image {img_url}: {str(e)}")
                    continue

                image_info = {
                    "source": "gallito",
                    "id": property.id,
                    "link": property.link,
                    "type": property.type.value,
                    "local_image_path": img_path,
                    "image_url": img_url,
                    "details": (
                        {
                            "is_office": property.details.is_office,
                            "neighborhood": property.details.neighborhood,
                            "n_rooms": property.details.n_rooms,
                            "n_bathrooms": property.details.n_bathrooms,
                            "square_meters": property.details.square_meters,
                        }
                        if property.details
                        else None
                    ),
                }
                jsonlines_data.append(image_info)

        self.logger.debug("Saving property data to JSONL")
        self.save_to_jsonl(property, jsonlines_data)
        return property
    

    def scrape_property_details(self, page)->Dict:
        rows = page.locator(".technical-sheet .ant-row").all()
        data = {}
        for row in rows:
            label = row.locator(".ant-space-item span.ant-typography").last.inner_text().strip()
            value_el = row.locator("strong")
            
            if value_el.count() > 0:
                data[label] = value_el.inner_text().strip()
            else:
                data[label] = None 
        
        return data
    
    def _parse_m2(self, value: str | None) -> float | None:
        if not value:
            return None
        return float(value.replace("m2", "").strip())
    
    def _parse_rooms(self, value: str | None) -> int | None:
        if not value:
            return None
        if value.strip().lower() == "monoambiente":
            return 1
        try:
            return int(value)
        except ValueError:
            return None

    def save_to_jsonl(self, property: Property, jsonlines_data: List[Dict]):
        """
        Save the property data to a JSONL file

        Args:
            property (Property): The property to save
            jsonlines_data (List[Dict]): The data to save
        """
        jsonl_path = os.path.join(self.properties_dir, f"{property.id}.jsonl")
        self.logger.debug("Saving data for property %s to %s", property.id, jsonl_path)

        try:
            with open(jsonl_path, "a", encoding="utf-8") as f:
                for item in jsonlines_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            self.logger.debug("Successfully saved data for property %s", property.id)
        except Exception as e:
            self.logger.error(
                "Failed to save data for property %s: %s", property.id, str(e)
            )
