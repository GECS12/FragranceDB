import os
import re
import time
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from classes.classes import FragranceItem
from aux_functions.db_functions import db_insert_update_remove, delete_collection
from aux_functions.data_functions import standardize_brand_names, standardize_fragrance_names, save_to_excel
from my_flask_app.mongo import db
import chardet
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)

# Base URLs for men's and women's fragrances
BASE_URL = "https://www.perfume-clique.pt"
MEN_URL = f"{BASE_URL}/c/Para-Ele/?l=144"
WOMEN_URL = f"{BASE_URL}/c/Para-Ela/?l=144"


# Function to clean fragrance names specific to PerfumeClique
def clean_fragrance_names_perfumeclique(fragrance_name):
    fragrance_name = fragrance_name.lower()
    fragrance_name = fragrance_name.replace('spray', '')
    return fragrance_name


# Function to extract the total number of pages to scrape
def get_total_pages(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    paging = soup.find('div', class_='paging')
    if paging:
        num_pages = paging.find_all('a', class_='pageNum')
        if num_pages:
            return int(num_pages[-1].text)
    return 1


# Function to parse the HTML content to extract fragrance information
def parse(html, url, page):
    soup = BeautifulSoup(html, 'html.parser')
    fragrances = []
    price_currency = '€'
    quantity = 0.0

    for div in soup.find_all('div', class_='skuResult'):
        product_box = div.find('div', class_='productBox')
        if product_box:
            # Original brand
            brand_tag = product_box.find('div', class_='brand')
            original_brand = brand_tag.get_text(strip=True) if brand_tag else None

            # Original Fragrance Name
            img_tag = product_box.find('img', itemprop='image')
            original_fragrance_name = img_tag['alt'].strip() if img_tag and 'alt' in img_tag.attrs else None

            price_tag = product_box.find('div', class_='price')
            price_amount = float(
                price_tag.get_text(strip=True).replace('€', '').replace(',', '.')) if price_tag else None

            link_tag = product_box.find('a', href=True)
            link = BASE_URL + link_tag['href'] if link_tag else None

            is_set_or_pack = any(
                keyword in original_fragrance_name.lower() for keyword in
                ['set', ' + ', 'balm', 'lotion', 'deodorant', 'soap'])

            # Clean brand
            clean_brand = standardize_brand_names(original_brand)

            # Clean fragrance name
            website_clean_fragrance_name = clean_fragrance_names_perfumeclique(original_fragrance_name)
            final_clean_fragrance_name = standardize_fragrance_names(website_clean_fragrance_name, original_brand)

            if is_set_or_pack:
                quantity = 0
            else:
                quantity_match = re.search(r'(\d+(\.\d+)?)\s*ml', original_fragrance_name, re.IGNORECASE)
                if quantity_match:
                    quantity = float(quantity_match.group(1))
                    # Remove the quantity part from cleaned_fragrance_name
                    final_clean_fragrance_name = re.sub(r'\b\d+(\.\d+)?\s*ml\b', '', final_clean_fragrance_name,
                                                        flags=re.IGNORECASE).strip()

            gender = 'Men' if 'Para-Ele' in url else 'Women'

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
                website="perfume-clique.pt",
                country=["PT"],
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


# Function to fetch the initial page to determine the total number of pages
async def fetch_initial_page(session, url):
    async with session.get(url) as response:
        raw_content = await response.read()
        result = chardet.detect(raw_content)
        encoding = result['encoding'] if result['encoding'] is not None else 'utf-8'
        html = raw_content.decode(encoding, errors='ignore')
        return html


# Function to scrape all pages in a category
async def scrape_category(category_url):
    async with aiohttp.ClientSession() as session:
        initial_html = await fetch_initial_page(session, category_url)
        total_pages = get_total_pages(initial_html, category_url)
        urls = [f"{category_url}&p={i}" for i in range(1, total_pages + 1)]
        tasks = [fetch_data_from_page(session, url, i) for i, url in enumerate(urls, 1)]
        html_pages = await asyncio.gather(*tasks)

    all_fragrances = [fragrance for page in html_pages for fragrance in page]
    return all_fragrances


# Function to fetch data from each page
async def fetch_data_from_page(session, url, page):
    async with session.get(url) as response:
        raw_content = await response.read()
        result = chardet.detect(raw_content)
        encoding = result['encoding'] if result['encoding'] is not None else 'utf-8'
        html = raw_content.decode(encoding, errors='ignore')
        return parse(html, url, page)


# Main function to orchestrate the scraping process
async def main():
    start_time = time.time()
    collection_name = "PerfumeClique"

    logging.info(f"Started scraping {collection_name}")

    men_fragrances = await scrape_category(MEN_URL)
    women_fragrances = await scrape_category(WOMEN_URL)

    all_fragrances = men_fragrances + women_fragrances

    base_path = os.path.join(os.getcwd(), 'data')  # Update this path as necessary
    os.makedirs(base_path, exist_ok=True)

    logging.info(f"Ended scraping {collection_name}")

    logging.info(f"Total fragrances scraped: {len(all_fragrances)}. Fetching gender information...")

    try:
        save_to_excel(all_fragrances, base_path, collection_name)
    except Exception as e:
        logging.info(e)

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
