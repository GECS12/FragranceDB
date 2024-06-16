# main_scraper_perfumedigital.py
from dotenv import load_dotenv
import os
load_dotenv()

from classes.classes import FragranceItem
from aux_functions.async_functions import *
import re
import aiohttp
import chardet
import time
from aux_functions.db_functions import insert_or_update_fragrances
from bs4 import BeautifulSoup
from my_flask_app.mongo import db
from aux_functions.data_functions import *




BASE_URL = "https://perfumedigital.es/"
semaphore_value = 15
retries_value = 3
delays_value = 1

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

            if not fragrance_name:
                print("Fragrance name not found!")
                continue

            quantity = extract_quantity(fragrance_name)

            price_info_tag = table.find('span', class_='productSpecialPrice')
            if price_info_tag:
                price_text = price_info_tag.get_text().split()
                if len(price_text) > 1:
                    price_amount = float(price_text[-2].replace('€', ''))

            link = BASE_URL + link_tag['href'] if link_tag else None

            is_set_or_pack = 'Y' if any(keyword in fragrance_name.lower() for keyword in ['lote', 'pack', 'packs']) else 'N'
            if is_set_or_pack == 'Y':
                quantity = 0

            fragrance = FragranceItem(
                brand=standardize_strings(standardize_brand_name(brand)),
                fragrance_name=fragrance_name,
                quantity=quantity,
                price_amount=float(price_amount) if price_amount else None,
                price_currency=price_currency,
                link=link,
                website="PerfumeDigital.es",
                country=["PT", "ES"],
                last_updated_at=datetime.now(),
                is_set_or_pack=is_set_or_pack,
                gender=None,
                price_alert_threshold=None  # Set initial threshold, can be updated later
            )
            fragrances.append(fragrance)

    return fragrances

def extract_quantity(fragrance_name):
    match = re.search(r'\b(\d+)\s*ML\b', fragrance_name, re.IGNORECASE)
    return int(match.group(1)) if match else None

async def fetch_gender_perfumedigital(fragrance, semaphore, retries=retries_value, delay=delays_value):
    async with semaphore:
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(fragrance.link) as response:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        gender_tag = soup.find('i', string=re.compile(r'Perfumes (Mujer|Hombre)', re.IGNORECASE))
                        if gender_tag:
                            if 'Mujer' in gender_tag.text:
                                fragrance.gender = 'Women'
                            elif 'Hombre' in gender_tag.text:
                                fragrance.gender = 'Men'
                            return fragrance
            except aiohttp.ClientConnectorError as e:
                print(f"ClientConnectorError fetching gender for {fragrance.link}: {e}")
            except aiohttp.ClientPayloadError as e:
                print(f"ClientPayloadError fetching gender for {fragrance.link}: {e}")
            except aiohttp.ServerDisconnectedError as e:
                print(f"ServerDisconnectedError fetching gender for {fragrance.link}: {e}")
            except Exception as e:
                print(f"Error fetching gender for {fragrance.link}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    return fragrance

async def main():
    start_time = time.time()
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
    urls = [
        f"https://perfumedigital.es/index.php?PASE={i * 15}&marca=&buscado=&ID_CATEGORIA=&ORDEN=&precio1=&precio2=#PRODUCTOS"
        for i in range(selected_pages)
    ]

    print("Starting to scrape pages...")

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

    semaphore = asyncio.Semaphore(semaphore_value)
    all_fragrances = await asyncio.gather(*[fetch_gender_perfumedigital(fragrance, semaphore) for fragrance in all_fragrances])

    # Define the collection
    collection = db["PerfumeDigital"]

    insert_or_update_fragrances(collection, all_fragrances)

    print("Insert/Update/Remove Fragrances to DB Mongo Complete.")

    if failed_pages:
        print(f"Failed to scrape the following pages: {failed_pages}")

    end_time = time.time()
    print(f"Scraping completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    asyncio.run(main())
