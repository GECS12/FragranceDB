from dotenv import load_dotenv
import os
import re
import time
import aiohttp
import chardet
from datetime import datetime
from aux_functions.db_functions import *
from classes.classes import FragranceItem
from aux_functions.async_functions import gather_data
from my_flask_app.mongo import db
from aux_functions.data_functions import *
import asyncio
from aiohttp import ClientConnectorError, ClientPayloadError, ServerDisconnectedError
from bs4 import BeautifulSoup
import random

load_dotenv()

# Base URL for PerfumeDigital
BASE_URL = "https://perfumedigital.es/"
semaphore_value = 15
retries_value = 5
initial_delay_value = 3


# Function to extract quantity from the fragrance name
# def extract_quantity(fragrance_name):
#     fragrance_name = re.sub(r'(?<=\d),(?=\d)', '.', fragrance_name, re.IGNORECASE)
#     match = re.search(r'(\d+\.?\d*)\s*ml\b|\bml\s*(\d+\.?\d*)\b|(\d+\.?\d*)ml\b', fragrance_name, re.IGNORECASE)
#     if match:
#         return float(match.group(1) or match.group(2) or match.group(3))
#     return 0

# Function to clean fragrance names specific to PerfumeDigital
def clean_fragrance_name_perfumedigital(fragrance_name):
    #Adds ml if missing before regular i.e ARMANI IN LOVE WITH YOU FREEZE EDP 50 REGULAR, Modified: ARMANI IN LOVE WITH YOU FREEZE EDP 50 ml regular
    if re.search(r'(\d+)\s*regular$', fragrance_name, flags=re.IGNORECASE):
        fragrance_name = re.sub(r'(\d+)\s*regular$', r'\1 ml regular', fragrance_name, flags=re.IGNORECASE)

    #separates ml from the word regular i.e Original: CHARLIE REVLON SILVER EDT 100 MLREGULAR, Modified: CHARLIE REVLON SILVER EDT 100 ml regular
    if re.search(r'mlregular', fragrance_name, flags=re.IGNORECASE):
        fragrance_name = re.sub(r'mlregular', 'ml regular', fragrance_name, flags=re.IGNORECASE)

    #removes quicne militros i.e LA VIE EST BELLE EDP 15 (QUINCE MILILITROS) ML @, Modified: LA VIE EST BELLE EDP 15  ML @
    #if re.search(r'\(quince mililitros\)', fragrance_name, flags=re.IGNORECASE):
    #fragrance_name = re.sub(r'\(quince mililitros\)', '', fragrance_name, flags=re.IGNORECASE)

    #adds ml if msising before @ i.e ARMANI IN LOVE WITH YOU EDP 100 @, Modified: ARMANI IN LOVE WITH YOU EDP 100 ml @
    if re.search(r'(\d+)\s*@$', fragrance_name, flags=re.IGNORECASE):
        fragrance_name = re.sub(r'(\d+)\s*@$', r'\1 ml @', fragrance_name, flags=re.IGNORECASE)

    #if re.search(r'\(tapon roto\)', fragrance_name, flags=re.IGNORECASE):
    #fragrance_name = re.sub(r'\(tapon roto\)', '', fragrance_name, flags=re.IGNORECASE)

    fragrance_name = fragrance_name.lower()
    fragrance_name = re.sub(r'\(.*?\)', '', fragrance_name)
    fragrance_name = fragrance_name.replace('regular', '')
    fragrance_name = fragrance_name.replace('¬∫', 'º')
    fragrance_name = fragrance_name.replace('@', '(Tester)')

    return fragrance_name


# Function to parse the HTML content to extract fragrance information
def parse(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    fragrances = []
    price_currency = '€'

    for td in soup.find_all('td', align='center', style='width:33%;'):
        table = td.find('table')
        if table:
            brand_tag = table.find('i')
            brand = brand_tag.get_text(strip=True) if brand_tag else None

            link_tag = table.find('a', href=True)
            img_tag = link_tag.find('img') if link_tag else None
            fragrance_name = img_tag['alt'].strip() if img_tag and 'alt' in img_tag.attrs else None

            price_info_tag = table.find('span', class_='productSpecialPrice')
            if price_info_tag:
                price_text = price_info_tag.get_text().split()
                if len(price_text) > 1:
                    price_amount = float(price_text[-2].replace('€', ''))

            link = BASE_URL + link_tag['href'] if link_tag else None

            is_set_or_pack = any(
                keyword in fragrance_name.lower() for keyword in
                ['lote', 'pack', 'packs', 'set', 'seis con 5', ' + ', 'caja'])

            #Specific perufmedigital name cleaning
            cleaned_fragrance_name = standardize_fragrance_names(clean_fragrance_name_perfumedigital(fragrance_name),
                                                                 brand)

            if is_set_or_pack:
                quantity = 0
            else:
                quantity_match = re.search(r'(\d+(\.\d+)?)\s*ml', cleaned_fragrance_name, re.IGNORECASE)
                if quantity_match:
                    quantity = float(quantity_match.group(1))
                    # Remove the quantity part from cleaned_fragrance_name
                    cleaned_fragrance_name = re.sub(r'\b\d+(\.\d+)?\s*ml\b', '', cleaned_fragrance_name,
                                                    flags=re.IGNORECASE).strip()
                else:
                    print(f"Couldn't find quantity for pattern: {quantity_match}, fragrance: {cleaned_fragrance_name}")

            # Standardize the fragrance name, ensuring the brand is included at the beginning if not already present
            cleaned_fragrance_name = standardize_fragrance_names(cleaned_fragrance_name, brand)

            fragrance = FragranceItem(
                brand=standardize_brand_names(brand),
                original_fragrance_name=fragrance_name,
                clean_fragrance_name=cleaned_fragrance_name,
                quantity=quantity,
                price_amount=price_amount,
                price_currency=price_currency,
                link=link,
                website="PerfumeDigital.es",
                country=["PT", "ES"],
                last_updated_at=datetime.now(),
                is_set_or_pack=is_set_or_pack,
                gender=None,
                price_alert_threshold=None
            )
            if fragrance.get_id() not in [f.get_id() for f in fragrances]:  # Ensure no duplicate IDs
                fragrances.append(fragrance)

    return fragrances


# Function to fetch gender information for a fragrance
async def fetch_gender_perfumedigital(fragrance, semaphore, session, retries=10, delay=2):
    async with semaphore:
        await asyncio.sleep(random.uniform(2, 3))  # Small initial delay before fetching
        for attempt in range(retries):
            try:
                async with session.get(fragrance.link, timeout=15) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    if len(html.strip()) == 0:
                        raise ValueError("Empty HTML content")

                    gender_tag = soup.find('i', string=re.compile(r'Perfumes (Mujer|Hombre)', re.IGNORECASE))

                    if gender_tag:
                        if 'Mujer' in gender_tag.text:
                            fragrance.gender = 'Women'
                        elif 'Hombre' in gender_tag.text:
                            fragrance.gender = 'Men'
                        # print(f"Found gender: {fragrance.gender} for {fragrance.link}")
                        return fragrance

                    fragrance.gender = None
                    return fragrance

            except (ClientConnectorError, ClientPayloadError, ServerDisconnectedError, asyncio.TimeoutError) as e:
                print(f"Network error ({type(e).__name__}) fetching gender for {fragrance.link}: {e}")
            except ValueError as e:
                print(f"ValueError fetching gender for {fragrance.link}: {e}")
            except Exception as e:
                print(f"Unexpected error ({type(e).__name__}) fetching gender for {fragrance.link}: {e}")

            backoff_delay = delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"Retrying in {backoff_delay:.2f} seconds...")
            await asyncio.sleep(backoff_delay)

        fragrance.gender = None
        return fragrance


# Main function to orchestrate the scraping process
async def main():
    start_time = time.time()

    collection_name = "PerfumesDigital"

    print(f"Started scraping {collection_name}")

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL) as response:
            raw_content = await response.read()
            result = chardet.detect(raw_content)
            encoding = result['encoding']
            html = raw_content.decode(encoding)
            soup = BeautifulSoup(html, 'html.parser')
            page_info = soup.find('td', class_='padd_33').find('font', face='arial', size='1')
            if page_info:
                total_pages = int(re.search(r'de (\d+)', page_info.get_text()).group(1))
                print(f"Total pages: {total_pages}")
            else:
                print("Total pages info not found, defaulting to 1.")
                quit()
    selected_pages = total_pages
    #selected_pages = 3
    urls = [
        f"https://perfumedigital.es/index.php?PASE={i * 15}&marca=&buscado=&ID_CATEGORIA=&ORDEN=&precio1=&precio2=#PRODUCTOS"
        for i in range(selected_pages)
    ]

    html_pages = await gather_data(urls, parse)

    all_fragrances = []
    failed_pages = []

    for i, parsed_data in enumerate(html_pages):
        if parsed_data:
            all_fragrances.extend(parsed_data)
            print(f"Scraped page: {i + 1}")
        else:
            failed_pages.append(i + 1)

    print(f"Total fragrances scraped: {len(all_fragrances)}. Fetching gender information...")

    if failed_pages:
        print(f"Failed to scrape the following pages: {failed_pages}")

    semaphore = asyncio.Semaphore(semaphore_value)
    async with aiohttp.ClientSession() as session:
        all_fragrances = await asyncio.gather(
            *[fetch_gender_perfumedigital(fragrance, semaphore, session) for fragrance in all_fragrances])

    print(f"Ended scraping {collection_name}")

    base_path = os.path.join(os.getcwd(), 'data')  # Update this path as necessary
    os.makedirs(base_path, exist_ok=True)

    try:
        save_to_excel(all_fragrances, base_path, collection_name)
    except Exception as e:
        print(e)

    try:
        delete_collection(collection_name)
    except Exception as e:
        print(e)

    print(f"Start: Inserting/Updating/Removing fragrances in MongoDB for {collection_name}")
    collection = db[collection_name]
    try:
        db_insert_update_remove(collection, all_fragrances)
    except Exception as e:
        print("Error Occurred on Insert/Update/Remove")
        print(e)
    print(f"End: Inserting/Updating/Removing fragrances from MongoDB for {collection_name}")

    end_time = time.time()
    print(f"{collection_name} process took {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
