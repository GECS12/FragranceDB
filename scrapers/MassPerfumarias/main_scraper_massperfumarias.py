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
from aux_functions.data_functions import save_to_excel, standardize_brand_names, standardize_fragrance_names
from my_flask_app.mongo import db
from dotenv import load_dotenv

load_dotenv()

# Base URLs for men's and women's fragrances
BASE_URL = "https://mass-perfumarias.pt"
MEN_URL = f"{BASE_URL}/perfumes/homem.html?product_list_limit=72"
WOMEN_URL = f"{BASE_URL}/perfumes/senhora.html?product_list_limit=72"

logging.basicConfig(level=logging.INFO)

def clean_fragrance_names_massperfumarias(fragrance_name):

    fragrance_name = fragrance_name.lower()
    fragrance_name = fragrance_name.replace('vap', 'ml')

    return fragrance_name

async def fetch_page(session, url):
    #logging.info(f"Fetching page: {url}")
    async with session.get(url) as response:
        raw_content = await response.read()
        result = chardet.detect(raw_content)
        encoding = result['encoding'] if result['encoding'] is not None else 'utf-8'
        html = raw_content.decode(encoding, errors='ignore')
        return html

def extract_brands(html):
    soup = BeautifulSoup(html, 'html.parser')
    marca_span = soup.find('span', text='Marca')
    if not marca_span:
        logging.warning("Marca span not found in the HTML.")
        return []

    # Find the next sibling after the <span>Marca</span> that contains the list of brands
    filter_section = marca_span.find_parent('div', class_='filter-options-item')
    if not filter_section:
        logging.warning("Filter section containing 'Marca' not found.")
        return []

    brand_list = filter_section.find_next('ol', class_='items list')
    if not brand_list:
        logging.warning("Brand list not found after 'Marca' span.")
        return []

    brand_items = brand_list.find_all('li', class_='item')
    brands = []
    for item in brand_items:
        link_element = item.find('a', class_='swissup-aln-item')
        if link_element:
            brand_name = link_element.find('span', class_='swissup-option-label').text.strip()
            brand_url = link_element['href']
            brands.append((brand_name, brand_url))
            #logging.info(f"Found brand: {brand_name} with URL: {brand_url}")
    return brands

def parse_fragrances(html, gender, page, original_brand):
    soup = BeautifulSoup(html, 'html.parser')
    products = soup.find_all('li', class_='item product product-item')
    fragrances = []
    price_currency = '€'

    #logging.info(f"Parsing {len(products)} products for brand {original_brand} on page {page}")

    for product in products:
        try:
            link = product.find('a', class_='product-item-link')['href']
            original_fragrance_name = product.find('a', class_='product-item-link').text.strip()

            price_span = product.find('span', class_='price')
            if price_span:
                price_text = price_span.text.strip().replace('€', '').replace(',', '.')
                price_amount = float(price_text) if price_text else None
            else:
                #logging.warning(f"No price found for product: {original_fragrance_name} on link {link}")
                price_amount = None

            clean_brand = standardize_brand_names(original_brand)
            website_clean_fragrance_name = clean_fragrance_names_massperfumarias(original_fragrance_name)
            final_clean_fragrance_name = standardize_fragrance_names(website_clean_fragrance_name, original_brand)

            # Check stock availability
            stock_div = product.find('div', class_='stock unavailable')
            is_in_stock = stock_div is None  # If 'stock unavailable' class is not found, assume it's in stock


            quantity_match = re.search(r'(\d+(\.\d+)?)\s*ml', final_clean_fragrance_name, re.IGNORECASE)
            if quantity_match:
                quantity = float(quantity_match.group(1))
                final_clean_fragrance_name = re.sub(r'\b\d+(\.\d+)?\s*ml\b', '', final_clean_fragrance_name,
                                                    flags=re.IGNORECASE).strip()
            else:
                #logging.warning(f"No quantity found for product: {original_fragrance_name}")
                continue

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
                is_in_stock=is_in_stock,
                website="mass-perfumarias.pt",
                country=["PT"],
                last_updated_at=datetime.now(),
                is_set_or_pack=False,
                page=page,
                gender=gender,
                price_alert_threshold=None
            )

            fragrances.append(fragrance)
        except Exception as e:
            logging.error(f"Error parsing product: {product}. Error: {e}")

    return fragrances

async def scrape_brand(session, brand_name, brand_url, gender):
    #logging.info(f"Scraping brand: {brand_name} at URL: {brand_url}")
    brand_html = await fetch_page(session, brand_url)
    return parse_fragrances(brand_html, gender, 1, brand_name)  # Assume one page for simplicity

async def scrape_category(category_url, gender):
    async with aiohttp.ClientSession() as session:
        # Fetch the initial category page
        initial_html = await fetch_page(session, category_url)
        brands = extract_brands(initial_html)

        tasks = [scrape_brand(session, brand_name, brand_url, gender) for brand_name, brand_url in brands]
        all_fragrances = await asyncio.gather(*tasks)
        return [fragrance for sublist in all_fragrances for fragrance in sublist]

async def main():
    start_time = time.time()

    collection_name = "MassPerfumarias"

    logging.info(f"Started scraping {collection_name}")

    men_fragrances = await scrape_category(MEN_URL, 'Men')
    women_fragrances = await scrape_category(WOMEN_URL, 'Women')

    all_fragrances = men_fragrances + women_fragrances

    logging.info(f"Ended scraping {collection_name}")

    logging.info(f"Total fragrances scraped: {len(all_fragrances)}. Fetching gender information...")

    base_path = os.path.join(os.getcwd(), 'data')
    os.makedirs(base_path, exist_ok=True)

    try:
        save_to_excel(all_fragrances, base_path, collection_name)
    except Exception as e:
        logging.error(f"Error saving fragrances to Excel: {e}")

    try:
        delete_collection(collection_name)
    except Exception as e:
        logging.info(e)

    collection = db[collection_name]

    logging.info(f"Start: Inserting/Updating/Removing fragrances in MongoDB for {collection_name}")
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
