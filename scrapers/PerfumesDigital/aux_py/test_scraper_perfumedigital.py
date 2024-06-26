import os
import re
import time
import random
import logging
import asyncio
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import aiohttp
from aiohttp import ClientConnectorError, ClientPayloadError, ServerDisconnectedError
import chardet
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from aux_functions.data_functions import standardize_brand_names, standardize_fragrance_names, save_to_excel
from aux_functions.async_functions import gather_data
from aux_functions.db_functions import db_insert_update_remove, delete_collection
from classes.classes import FragranceItem
from my_flask_app.app import db

load_dotenv()

# Base URL for PerfumeDigital
BASE_URL = "https://perfumedigital.es/"
semaphore_value = 10
logging.basicConfig(level=logging.INFO)

# Initialize Motor client
motor_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
motor_db = motor_client[os.getenv("MONGO_DB_NAME")]


# Function to clean fragrance names specific to PerfumeDigital
def clean_fragrance_names_perfumedigital(fragrance_name):
    if re.search(r'(\d+)\s*regular$', fragrance_name, flags=re.IGNORECASE):
        fragrance_name = re.sub(r'(\d+)\s*regular$', r'\1 ml regular', fragrance_name, flags=re.IGNORECASE)
    if re.search(r'mlregular', fragrance_name, flags=re.IGNORECASE):
        fragrance_name = re.sub(r'mlregular', 'ml regular', fragrance_name, flags=re.IGNORECASE)
    if re.search(r'(\d+)\s*@$', fragrance_name, flags=re.IGNORECASE):
        fragrance_name = re.sub(r'(\d+)\s*@$', r'\1 ml @', fragrance_name, flags=re.IGNORECASE)

    fragrance_name = fragrance_name.lower()
    fragrance_name = re.sub(r'\(.*?\)', '', fragrance_name)
    fragrance_name = fragrance_name.replace('regular', '')
    fragrance_name = fragrance_name.replace('@', '(Tester)')
    fragrance_name = fragrance_name.replace('~', '')
    fragrance_name = fragrance_name.replace('¬∫', 'º')
    fragrance_name = fragrance_name.replace('¬≤', '²')
    fragrance_name = fragrance_name.replace('¬¥', "'")
    fragrance_name = fragrance_name.replace('√í', "ò")
    fragrance_name = fragrance_name.replace('√ë', "ñ")
    fragrance_name = fragrance_name.replace('√ç', "í")
    fragrance_name = fragrance_name.replace('√â', "é")
    fragrance_name = fragrance_name.replace('√î', "ô")
    fragrance_name = fragrance_name.replace('√©', 'é')
    fragrance_name = fragrance_name.replace('√°', 'á')
    fragrance_name = fragrance_name.replace('√≠', 'í')
    fragrance_name = fragrance_name.replace('√≥', 'ó')
    fragrance_name = fragrance_name.replace('√∂', 'ö')
    fragrance_name = fragrance_name.replace('√º', 'ü')
    fragrance_name = fragrance_name.replace('√¥', 'ô')
    fragrance_name = fragrance_name.replace('√®', 'è')
    fragrance_name = fragrance_name.replace('√ß', 'ç')
    fragrance_name = fragrance_name.replace('√±', 'ñ')
    fragrance_name = fragrance_name.replace('√∏', 'ø')
    fragrance_name = fragrance_name.replace('√´', 'ë')
    fragrance_name = fragrance_name.replace('√§', 'ä')
    fragrance_name = fragrance_name.replace('√•', 'å')
    fragrance_name = fragrance_name.replace('√Å', 'Á')
    fragrance_name = fragrance_name.replace('√∫', 'ú')
    fragrance_name = fragrance_name.replace('√ª', 'û')
    fragrance_name = fragrance_name.replace('√Ø', 'ï')
    fragrance_name = fragrance_name.replace('√â', 'É')
    fragrance_name = fragrance_name.replace('√†', 'à')
    fragrance_name = fragrance_name.replace('√¶', 'æ')
    fragrance_name = fragrance_name.replace('√Æ', 'î')
    fragrance_name = fragrance_name.replace('√¢', 'â')
    fragrance_name = fragrance_name.replace('√£', 'ã')
    fragrance_name = fragrance_name.replace('√î', 'Ô')
    fragrance_name = fragrance_name.replace('√ü', 'ß')
    fragrance_name = fragrance_name.replace('√ì', 'Ó')
    fragrance_name = fragrance_name.replace('√≤', 'ò')
    fragrance_name = fragrance_name.replace('√Ω', 'ý')
    fragrance_name = fragrance_name.replace('√ñ', 'Ö')
    fragrance_name = fragrance_name.replace('√™', 'ê')
    fragrance_name = fragrance_name.replace('√Ä', 'À')
    fragrance_name = fragrance_name.replace('√ò', 'Ø')
    fragrance_name = fragrance_name.replace('√Ö', 'Å')
    fragrance_name = fragrance_name.replace('√∞', 'ð')
    fragrance_name = fragrance_name.replace('√á', 'Ç')
    fragrance_name = fragrance_name.replace('√Ç', 'Â')
    fragrance_name = fragrance_name.replace('√π', 'ù')
    fragrance_name = fragrance_name.replace('√í', 'Ò')
    fragrance_name = fragrance_name.replace('√¨', 'ì')
    fragrance_name = fragrance_name.replace('√ú', 'Ü')
    fragrance_name = fragrance_name.replace('√à', 'È')
    return fragrance_name


# Function to clean brands names specific to PerfumeDigital
def clean_brands_perfumedigital(brand):
    brand = brand.lower()
    brand = brand.replace('√®', 'è')

    return brand


# Function to parse the HTML content to extract fragrance information
def parse(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    fragrances = []
    price_currency = '€'
    price_amount = 0.0
    quantity = 0.0

    # Extract the page number from the URL and get page
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    pase = int(query_params.get('PASE', [0])[0])
    page = (pase // 15) + 1

    for td in soup.find_all('td', align='center', style='width:33%;'):
        table = td.find('table')
        if table:
            # Get Brand and Clean Brand
            brand_tag = table.find('i')
            original_brand = brand_tag.get_text(strip=True) if brand_tag else None

            clean_brand = clean_brands_perfumedigital(original_brand)
            clean_brand = standardize_brand_names(clean_brand)

            # Get Link
            link_tag = table.find('a', href=True)
            link = BASE_URL + link_tag['href'] if link_tag else None

            # Get Original Fragrance Name
            img_tag = link_tag.find('img') if link_tag else None
            original_fragrance_name = img_tag['alt'].strip() if img_tag and 'alt' in img_tag.attrs else None

            # Get Price
            price_info_tag = table.find('span', class_='productSpecialPrice')
            if price_info_tag:
                price_text = price_info_tag.get_text().split()
                if len(price_text) > 1:
                    price_amount = float(price_text[-2].replace('€', ''))

            # Get Set_Pack
            is_set_or_pack = any(
                keyword in original_fragrance_name.lower() for keyword in
                ['lote', 'pack', 'packs', 'set', 'seis con 5', ' + '])

            # Get website_clean and final_clean
            website_clean_fragrance_name = clean_fragrance_names_perfumedigital(original_fragrance_name)
            final_clean_fragrance_name = standardize_fragrance_names(website_clean_fragrance_name, clean_brand)

            if is_set_or_pack:
                quantity = 0
            else:
                quantity_match = re.search(r'(\d+(\.\d+)?)\s*ml', final_clean_fragrance_name, re.IGNORECASE)
                if quantity_match:
                    quantity = float(quantity_match.group(1))
                    final_clean_fragrance_name = re.sub(r'\b\d+(\.\d+)?\s*ml\b', '', final_clean_fragrance_name,
                                                        flags=re.IGNORECASE).strip()
                else:
                    logging.warning(f"Couldn't find quantity for original fragrance:{original_fragrance_name}")

            fragrance = FragranceItem(
                original_brand=original_brand,
                clean_brand=clean_brand,
                original_fragrance_name=original_fragrance_name,
                website_clean_fragrance_name=website_clean_fragrance_name,
                final_clean_fragrance_name=final_clean_fragrance_name,
                quantity=quantity,
                price_amount=price_amount,
                price_currency=price_currency,
                link=link,
                website="PerfumeDigital.es",
                country=["PT", "ES"],
                last_updated_at=datetime.now(),
                is_set_or_pack=is_set_or_pack,
                page=page,
                gender=None,
                price_alert_threshold=None,
                is_in_stock=True
            )
            if fragrance.get_id() not in [f.get_id() for f in fragrances]:  # Ensure no duplicate IDs
                fragrances.append(fragrance)

    return fragrances


# Function to fetch gender information for a fragrance
async def fetch_gender_perfumedigital(fragrance, semaphore, session, collection, retries=10, delay=3):
    async with semaphore:
        await asyncio.sleep(random.uniform(1, 2))  # Small initial delay before fetching

        # Check if the gender information is already stored in the database
        stored_fragrance = await collection.find_one({"_id": fragrance.get_id()}, {"gender": 1})
        if stored_fragrance and stored_fragrance.get("gender"):
            fragrance.gender = stored_fragrance["gender"]
            logging.info(
                f"Gender found for {fragrance.get_final_clean_fragrance_name()} at {fragrance.get_link()}")
            return fragrance
        else:
            logging.info(f"Couldn't find gender for {fragrance.get_final_clean_fragrance_name()} at {fragrance.get_link()}")

        for attempt in range(retries):
            try:
                async with session.get(fragrance.link, timeout=15) as response:
                    raw_content = await response.read()
                    result = chardet.detect(raw_content)
                    encoding = result['encoding'] if result['encoding'] is not None else 'utf-8'
                    html = raw_content.decode(encoding, errors='ignore')
                    soup = BeautifulSoup(html, 'html.parser')

                    if len(html.strip()) == 0:
                        raise ValueError("Empty HTML content")

                    gender_tag = soup.find('i', string=re.compile(r'Perfumes (Mujer|Hombre)', re.IGNORECASE))

                    if gender_tag:
                        if 'Mujer' in gender_tag.text:
                            fragrance.gender = 'Women'
                        elif 'Hombre' in gender_tag.text:
                            fragrance.gender = 'Men'

                        # Store the gender information in the database
                        await collection.update_one({"_id": fragrance.get_id()}, {"$set": {"gender": fragrance.gender}},
                                              upsert=True)
                        return fragrance

                    fragrance.gender = None
                    return fragrance

            except (aiohttp.ClientConnectorError, aiohttp.ClientPayloadError, ServerDisconnectedError,
                    asyncio.TimeoutError) as e:
                logging.error(f"Network error ({type(e).__name__}) fetching gender for {fragrance.link}: {e}")
            except ValueError as e:
                logging.error(f"ValueError fetching gender for {fragrance.link}: {e}")
            except Exception as e:
                logging.error(f"Unexpected error ({type(e).__name__}) fetching gender for {fragrance.link}: {e}")

            backoff_delay = delay * (2 ** attempt) + random.uniform(0, 1)
            logging.info(f"Retrying in {backoff_delay:.2f} seconds...")
            await asyncio.sleep(backoff_delay)

        fragrance.gender = None
        return fragrance


# Main function to orchestrate the scraping process
async def main():
    start_time = time.time()

    collection_name = "PerfumesDigital"
    logging.info(f"Started scraping {collection_name}")

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL) as response:
            raw_content = await response.read()
            result = chardet.detect(raw_content)
            encoding = result['encoding']
            html = raw_content.decode(encoding, errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            page_info = soup.find('td', class_='padd_33').find('font', face='arial', size='1')
            if page_info:
                total_pages = int(re.search(r'de (\d+)', page_info.get_text()).group(1))
                logging.info(f"Total pages: {total_pages}")
            else:
                logging.info("Total pages info not found, defaulting to 1.")
                total_pages = 1

    selected_pages = total_pages
    selected_pages = 5
    urls = [
        (f"https://perfumedigital.es/index.php?PASE={i * 15}&marca=&buscado=&ID_CATEGORIA=&ORDEN=&precio1=&precio2"
         f"=#PRODUCTOS")
        for i in range(selected_pages)
    ]

    html_pages = await gather_data(urls, parse)

    all_fragrances = []
    failed_pages = []

    for i, parsed_data in enumerate(html_pages):
        if parsed_data:
            all_fragrances.extend(parsed_data)
            logging.info(f"Scraped page: {i + 1}")
        else:
            failed_pages.append(i + 1)

    logging.info(f"Total fragrances scraped: {len(all_fragrances)}. Fetching gender information...")

    if failed_pages:
        logging.info(f"Failed to scrape the following pages: {failed_pages}")

    semaphore = asyncio.Semaphore(semaphore_value)
    collection = motor_db[collection_name]

    async with aiohttp.ClientSession() as session:
        all_fragrances = await asyncio.gather(
            *[fetch_gender_perfumedigital(fragrance, semaphore, session, collection) for fragrance in all_fragrances])

    logging.info(f"Ended scraping {collection_name}")

    base_path = os.path.join(os.getcwd(), 'data')  # Update this path as necessary
    os.makedirs(base_path, exist_ok=True)

    try:
        save_to_excel(all_fragrances, base_path, collection_name)
    except Exception as e:
        logging.error(f"Error saving to Excel: {e}")

    # try:
    #     delete_collection(collection_name)
    # except Exception as e:
    #     logging.info(e)

    # logging.info(f"Start: Inserting/Updating/Removing fragrances in MongoDB for {collection_name}")
    # collection = db[collection_name]
    # try:
    #     db_insert_update_remove(collection, all_fragrances)
    # except Exception as e:
    #     logging.info("Error Occurred on Insert/Update/Remove")
    #     logging.info(e)
    # logging.info(f"End: Inserting/Updating/Removing fragrances from MongoDB for {collection_name}")

    end_time = time.time()
    logging.info(f"{collection_name} process took {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
