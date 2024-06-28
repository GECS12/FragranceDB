import os
import re
import time
import asyncio
import aiohttp
import chardet
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from classes.classes import FragranceItem
from aux_functions.db_functions import db_insert_update_remove, delete_collection
from aux_functions.data_functions import standardize_brand_names, standardize_fragrance_names, save_to_excel, \
    get_brand_from_fragrance_name
from my_flask_app.mongo import db
from dotenv import load_dotenv
import json

load_dotenv()

BASE_URL = "https://jkperfumaria.pt"
MEN_URL = f"{BASE_URL}/categoria-produto/homem/perfumes-homem/page/"
WOMEN_URL = f"{BASE_URL}/categoria-produto/mulher/perfumes-mulher/page/"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

semaphore = asyncio.Semaphore(15)  # Limit concurrent requests to 15


def clean_fragrance_names_jkperfumaria(fragrance_name):
    # Implement specific cleaning rules for JK Perfumaria
    fragrance_name = fragrance_name.lower()
    fragrance_name = fragrance_name.replace('|', '')

    if fragrance_name.startswith('marc dot'):
        return 'Marc Jacobs'
    elif fragrance_name.startswith('maroussia'):
        return 'Slava Zaitsev'
    else:
        return fragrance_name




async def fetch_page(session, url):
    retries = 5
    delay = 1
    for attempt in range(retries):
        try:
            async with session.get(url) as response:
                raw_content = await response.read()
                result = chardet.detect(raw_content)
                encoding = result['encoding'] if result['encoding'] is not None else 'utf-8'
                html = raw_content.decode(encoding, errors='ignore')
                return html
        except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
            logging.warning(f"Attempt {attempt + 1} - Failed to fetch {url}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
            else:
                logging.error(f"Failed to fetch {url} after {retries} attempts")
                return None


def get_total_pages(html):
    soup = BeautifulSoup(html, 'html.parser')
    page_numbers = soup.find('ul', class_='page-numbers')
    if not page_numbers:
        return 1
    pages = page_numbers.find_all('a', class_='page-numbers')
    # Filter out non-numeric page numbers
    numeric_pages = [page.text for page in pages if page.text.isdigit()]
    last_page = numeric_pages[-1] if numeric_pages else '1'
    return int(last_page)


async def get_fragrance_links(session, category_url, gender, page):
    retries = 5
    delay = 1
    async with semaphore:
        for attempt in range(retries):
            try:
                async with session.get(category_url) as response:
                    raw_content = await response.read()
                    result = chardet.detect(raw_content)
                    encoding = result['encoding'] if result['encoding'] is not None else 'utf-8'
                    html = raw_content.decode(encoding, errors='ignore')
                    soup = BeautifulSoup(html, 'html.parser')
                    products_list = soup.find('ul', class_='products columns-3')
                    links = []
                    if products_list:
                        product_wraps = products_list.find_all('div', class_='product-wrap')
                        for product in product_wraps:
                            link = product.find('a', href=True)['href']
                            links.append((link, gender, page))
                    if not links:
                        logging.warning(f"No links found on page {page} for {category_url}")
                    return links
            except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
                logging.warning(f"Attempt {attempt + 1} - Failed to get links from {category_url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logging.error(f"Failed to get links from {category_url} after {retries} attempts")
                    return []


async def scrape_fragrance_detail(session, url, gender, page):
    retries = 5
    delay = 1
    async with semaphore:
        for attempt in range(retries):
            try:
                async with session.get(url) as response:
                    raw_content = await response.read()
                    result = chardet.detect(raw_content)
                    encoding = result['encoding'] if result['encoding'] is not None else 'utf-8'
                    html = raw_content.decode(encoding, errors='ignore')
                    soup = BeautifulSoup(html, 'html.parser')

                    name_element = None
                    name_retries = 5
                    name_delay = 3
                    for name_attempt in range(name_retries):
                        name_element = soup.find('h1', class_='product_title entry-title')
                        if name_element:
                            break
                        logging.warning(f"Attempt {name_attempt + 1} - Product name not found for {url}")
                        if name_attempt < name_retries - 1:
                            logging.warning(f"Attempt # {attempt}. Trying to scrape {url} again")
                            await asyncio.sleep(name_delay)
                            name_delay *= 2

                    if not name_element:
                        logging.error(f"Product name not found for {url} after {name_retries} attempts")
                        return []

                    original_fragrance_name = name_element.text.strip()
                    logging.info(f"Original Fragrance Name: {original_fragrance_name}")

                    original_brand = get_brand_from_fragrance_name(original_fragrance_name)
                    logging.info(f"Original Brand: {original_brand}")

                    clean_brand = standardize_brand_names(original_brand)

                    website_clean_fragrance_name = clean_fragrance_names_jkperfumaria(original_fragrance_name)

                    final_clean_fragrance_name = standardize_fragrance_names(website_clean_fragrance_name,
                                                                             original_brand)

                    is_set_or_pack = 'coffret' in original_fragrance_name.lower()

                    form_element = soup.find('form', class_='variations_form')
                    if not form_element:
                        # Extract price and quantity from available elements if variations form is not found
                        price_element = soup.find('span', class_='woocommerce-Price-amount amount')
                        price_amount = 0.0
                        if price_element:
                            price_text = price_element.get_text()
                            price_amount = float(re.sub(r'[^\d.]', '', price_text.replace(',', '.')))

                        quantity_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*ml', original_fragrance_name, re.IGNORECASE)
                        quantity = float(quantity_match.group(1).replace(',', '.')) if quantity_match else 0

                        logging.warning(
                            f"Extracted price and quantity for {url} - Price: {price_amount}, Quantity: {quantity}")

                        fragrance = FragranceItem(
                            original_brand=original_brand,
                            clean_brand=clean_brand,
                            original_fragrance_name=original_fragrance_name,
                            website_clean_fragrance_name=website_clean_fragrance_name,
                            final_clean_fragrance_name=final_clean_fragrance_name,
                            quantity=quantity,
                            price_amount=price_amount,
                            price_currency='€',
                            link=url,
                            website="jkperfumaria.pt",
                            country=["PT"],
                            last_updated_at=datetime.now(),
                            is_set_or_pack=is_set_or_pack,
                            page=page,
                            gender=gender,
                            price_alert_threshold=None,
                            is_in_stock="Yes" if price_amount > 0 else "No"
                        )
                        return [fragrance]

                    product_variations = form_element.get('data-product_variations')
                    if not product_variations:
                        logging.error(f"Product variations not found for {url}")
                        return []

                    variations = json.loads(product_variations)

                    fragrances = []
                    for variation in variations:
                        quantity = variation['attributes'].get('attribute_tamanho') or variation['attributes'].get('attribute_tamanhos')
                        if not quantity:
                            logging.warning(f"Quantity attribute not found for variation in {url}")
                            continue
                        quantity = float(re.sub(r'[^\d.]', '', quantity.replace(',', '.')))
                        price_amount = variation['display_price']
                        is_in_stock = "Disponível por Encomenda" if variation['backorders_allowed'] else (
                            "Yes" if variation['is_in_stock'] else "No")
                        # logging.info(
                        #     f"Variation - Quantity: {quantity}, Price: {price_amount}, In Stock: {is_in_stock}")

                        fragrance = FragranceItem(
                            original_brand=original_brand,
                            clean_brand=clean_brand,
                            original_fragrance_name=original_fragrance_name,
                            website_clean_fragrance_name=website_clean_fragrance_name,
                            final_clean_fragrance_name=final_clean_fragrance_name,
                            quantity=quantity,
                            price_amount=price_amount,
                            price_currency='€',
                            link=url,
                            website="jkperfumaria.pt",
                            country=["PT"],
                            last_updated_at=datetime.now(),
                            is_set_or_pack=is_set_or_pack,
                            page=page,
                            gender=gender,
                            price_alert_threshold=None,
                            is_in_stock=is_in_stock
                        )
                        fragrances.append(fragrance)

                    if not fragrances:
                        # Handle the case where no valid variations are found
                        quantity_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*ml', original_fragrance_name, re.IGNORECASE)
                        quantity = float(quantity_match.group(1).replace(',', '.')) if quantity_match else 0
                        logging.warning(f"No valid variations found for {url}. Extracted quantity: {quantity}")

                        fragrance = FragranceItem(
                            original_brand=original_brand,
                            clean_brand=clean_brand,
                            original_fragrance_name=original_fragrance_name,
                            website_clean_fragrance_name=website_clean_fragrance_name,
                            final_clean_fragrance_name=final_clean_fragrance_name,
                            quantity=quantity,
                            price_amount=0.0,
                            price_currency='€',
                            link=url,
                            website="jkperfumaria.pt",
                            country=["PT"],
                            last_updated_at=datetime.now(),
                            is_set_or_pack=is_set_or_pack,
                            page=page,
                            gender=gender,
                            price_alert_threshold=None,
                            is_in_stock="No"
                        )
                        return [fragrance]

                    return fragrances
            except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
                logging.warning(f"Attempt {attempt + 1} - Failed to scrape {url}: {e}")
                if attempt < retries - 1:
                    logging.warning(f"Attempt # {attempt}. Trying to scrape {url} again")
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logging.error(f"Failed to scrape {url} after {retries} attempts")
                    return []


async def scrape_category(category_url, gender):
    async with aiohttp.ClientSession() as session:
        logging.info(f"Fetching initial page to determine total pages: {category_url + '1'}")
        initial_html = await fetch_page(session, category_url + "1")
        if not initial_html:
            logging.error(f"Failed to fetch initial page for {category_url}")
            return []

        total_pages = get_total_pages(initial_html)
        logging.info(f"Total pages found: {total_pages}")

        link_tasks = []
        for page in range(1, total_pages + 1):
            page_url = f"{category_url}{page}/"
            logging.info(f"Fetching links for fragrances from page {page}")
            link_tasks.append(get_fragrance_links(session, page_url, gender, page))

        all_links_results = await asyncio.gather(*link_tasks)
        all_links = []
        for links in all_links_results:
            if links:
                all_links.extend(links)
            else:
                logging.warning(f"Empty links list found for one of the pages in {category_url}")

        if not all_links:
            logging.error(f"No links found for {category_url}")
            return []

        detail_tasks = []
        for link, gender, page in all_links:
            detail_tasks.append(scrape_fragrance_detail(session, link, gender, page))

        all_fragrances_results = await asyncio.gather(*detail_tasks)
        all_fragrances = []
        for fragrances in all_fragrances_results:
            if fragrances:
                all_fragrances.extend(fragrances)
            else:
                logging.warning(f"Empty fragrance details list found for one of the links")

        return all_fragrances


async def main():
    start_time = time.time()

    collection_name = "JKPerfumaria"

    logging.info(f"Started scraping {collection_name}")

    men_fragrances = await scrape_category(MEN_URL, 'Men')
    women_fragrances = await scrape_category(WOMEN_URL, 'Women')

    all_fragrances = men_fragrances + women_fragrances

    logging.info(f"Ended scraping {collection_name}")

    logging.info(f"Total fragrances scraped: {len(all_fragrances)}")

    base_path = os.path.join(os.getcwd(), 'data')
    os.makedirs(base_path, exist_ok=True)

    try:
        save_to_excel(all_fragrances, base_path, collection_name)
    except Exception as e:
        logging.error(f"Error saving to Excel: {e}")

    end_time = time.time()
    logging.info(f"{collection_name} process took {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
