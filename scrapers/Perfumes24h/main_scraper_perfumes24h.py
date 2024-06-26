import os
import re
from datetime import datetime
import time
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from classes.classes import FragranceItem
from aux_functions.data_functions import standardize_fragrance_names, standardize_brand_names, save_to_excel
from aux_functions.db_functions import db_insert_update_remove, delete_collection
from my_flask_app.app import db

load_dotenv()

logging.basicConfig(level=logging.INFO)

# Base URL for AJAX endpoint
AJAX_URL = "https://perfumes24h.com/ajax/buscador.filtros_v2.php"

# Headers for the request
HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": "nmc_analytics=false; nmc_marketing=false; nmc_mostrado=true; tokenc=uTqmDNx7gq4bfdv3FjsB1KoKKWpqeNCNAAD2T4zHTGzwJMuVXTIycz8j5QIykESokiDz3E6ET9oOYWc8T63rh6ymiemyHJ017mdx; PHPSESSID=3de860e36ae9f6dd2cad24cd91e2b95b",
    "Referer": "https://perfumes24h.com/perfumes/",
    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

# Function to fetch data from the AJAX endpoint with retry mechanism
async def fetch_data_from_ajax(session, url, page, retries=3, delay=5):
    params = {
        "ofertas": 0,
        "fid": 1,
        "sid": 0,
        "ssid": 0,
        "g": 0,
        "m": 0,
        "sets": 0,
        "pag": page,
        "q": 0,
        "pid": 0,
        "orden": "",
        "novedades": 0,
        "promociones_especiales": 0,
        "promocion": 0,
        "id_promocion_unida": 0,
        "nuevo": 0,
        "pmin": 0,
        "pmax": 2000,
        "tp": 0,
        "ajax": 1
    }
    for attempt in range(retries):
        try:
            async with session.get(url, headers=HEADERS, params=params) as response:
                if response.status == 200:
                    logging.info(f"Scraping page {page}")
                    response_text = await response.text()
                    if response_text == "-1":
                        return None
                    return response_text
                else:
                    logging.info(f"Failed to fetch data for page {page}, status code: {response.status}")
        except Exception as e:
            logging.info(f"Error fetching page {page}: {e}")
        await asyncio.sleep(delay)
    logging.info(f"Failed to fetch data for page {page} after {retries} retries")
    return None

# Function to determine the total number of pages
async def get_total_pages(session, url):
    page = 82
    while page > 0:
        response = await fetch_data_from_ajax(session, url, page)
        if response is not None:
            return page
        page -= 1
    return 1

# Function to parse the fetched data
def parse_ajax_data(html, url, page):
    soup = BeautifulSoup(html, 'html.parser')
    fragrances = []
    price_currency = '€'

    for div in soup.find_all('div', class_='item_producto'):
        # Original brand
        brand_tag = div.find('div', class_='nombre_marca')
        original_brand = brand_tag.get_text(strip=True) if brand_tag else None

        # Clean Brand
        clean_brand = standardize_brand_names(original_brand)

        # Original Fragrance Name
        name_tag = div.find('div', class_='nombre_grupo')
        aux_fragrance_name = name_tag.get_text(strip=True) if name_tag else None

        aux_type_tag = div.find('div', class_='tipo_producto')
        aux_type = aux_type_tag.get_text(strip=True) if aux_type_tag else ""

        original_fragrance_name = (aux_fragrance_name + " " + aux_type)

        # Link
        link_tags = div.find_all('a', href=True)
        link = link_tags[1]['href'] if len(link_tags) > 1 else (link_tags[0]['href'] if link_tags else None)

        # Gender
        gender_tag = div.find('div', class_='sexo')
        gender = gender_tag.get_text(strip=True) if gender_tag else ""
        gender = 'Men' if 'Hombre' in gender else 'Women'

        # Full Clean Fragrance Name
        final_clean_fragrance_name = standardize_fragrance_names(original_fragrance_name, original_brand)

        for variant in div.find_all('div', class_='item_tamanyo'):
            price_amount = float(variant['data-pp'].replace(',', '.'))
            quantity_match = re.search(r'(\d+)', variant.get_text(strip=True))
            quantity = int(quantity_match.group(1)) if quantity_match else 0
            is_set_or_pack = True if not quantity_match else False

            fragrance = FragranceItem(
                original_brand=original_brand,
                clean_brand=clean_brand,
                original_fragrance_name=original_fragrance_name,
                website_clean_fragrance_name=original_fragrance_name,
                final_clean_fragrance_name=final_clean_fragrance_name,
                quantity=quantity,
                price_amount=price_amount,
                price_currency=price_currency,
                link=link,
                website="perfumes24h.com",
                country=["PT", "ES"],
                last_updated_at=datetime.now(),
                is_set_or_pack=is_set_or_pack,
                page=page,
                gender=gender,
                price_alert_threshold=None,
                is_in_stock=True

            )
            if fragrance.get_id() not in [f.get_id() for f in fragrances]:  # Ensure no duplicate IDs
                fragrances.append(fragrance)

    return fragrances

# Main function to orchestrate the scraping process
async def main():
    start_time = time.time()

    collection_name = "Perfumes24h"

    logging.info(f"Started scraping {collection_name}")

    async with aiohttp.ClientSession() as session:
        total_pages = await get_total_pages(session, AJAX_URL)
        logging.info(f"Total pages to scrape: {total_pages}")

        tasks = [fetch_data_from_ajax(session, AJAX_URL, page) for page in range(1, total_pages + 1)]
        responses = await asyncio.gather(*tasks)

    all_fragrances = []
    for page, response in enumerate(responses, start=1):
        if response:
            parsed_data = parse_ajax_data(response, AJAX_URL, page)
            all_fragrances.extend(parsed_data)

    logging.info(f"Ended scraping {collection_name}")

    logging.info(f"Total fragrances scraped: {len(all_fragrances)}. Fetching gender information...")

    base_path = os.path.join(os.getcwd(), 'data')  # Update this path as necessary
    os.makedirs(base_path, exist_ok=True)

    try:
        save_to_excel(all_fragrances, base_path, collection_name)
    except Exception as e:
        logging.info(e)

    try:
        delete_collection(collection_name)
    except Exception as e:
        logging.info(e)

    logging.info(f"Start: Inserting/Updating/Removing fragrances in MongoDB for {collection_name}")

    collection = db[collection_name]

    try:
        db_insert_update_remove(collection, all_fragrances)
    except Exception as e:
        logging.info("Error Occurred on Insert/Update/Remove")
        logging.info(e)
    logging.info(f"End: Inserting/Updating/Removing fragrances from MongoDB for {collection_name}")

    end_time = time.time()

    logging.info(f"{collection_name} process took {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    asyncio.run(main())
