import os
import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from aux_functions.db_functions import *
from classes.classes import FragranceItem
from my_flask_app.mongo import db
from dotenv import load_dotenv
from aux_functions.async_functions import gather_data
from aux_functions.data_functions import *
import chardet

load_dotenv()

# Base URLs for men's and women's fragrances
BASE_URL = "https://www.perfume-clique.pt"
MEN_URL = f"{BASE_URL}/c/Para-Ele/?l=144"
WOMEN_URL = f"{BASE_URL}/c/Para-Ela/?l=144"


# Function to clean fragrance names specific to PerfumeClique
def clean_fragrance_name_perfumeclique(fragrance_name):
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
def parse(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    fragrances = []
    price_currency = '€'

    for div in soup.find_all('div', class_='skuResult'):
        product_box = div.find('div', class_='productBox')
        if product_box:
            brand_tag = product_box.find('div', class_='brand')
            brand = brand_tag.get_text(strip=True) if brand_tag else None

            img_tag = product_box.find('img', itemprop='image')
            fragrance_name = img_tag['alt'].strip() if img_tag and 'alt' in img_tag.attrs else None

            price_tag = product_box.find('div', class_='price')
            price_amount = float(
                price_tag.get_text(strip=True).replace('€', '').replace(',', '.')) if price_tag else None

            link_tag = product_box.find('a', href=True)
            link = BASE_URL + link_tag['href'] if link_tag else None

            is_set_or_pack = any(
                keyword in fragrance_name.lower() for keyword in
                ['set', ' + ', 'balm', 'lotion', 'deodorant', ' & ', 'soap'])

            # Clean fragrance name
            cleaned_fragrance_name = standardize_fragrance_names(clean_fragrance_name_perfumeclique(fragrance_name),
                                                                 brand)

            if is_set_or_pack:
                quantity = 0
            else:
                quantity_match = re.search(r'(\d+(\.\d+)?)\s*ml', fragrance_name, re.IGNORECASE)
                if quantity_match:
                    quantity = float(quantity_match.group(1))
                    # Remove the quantity part from cleaned_fragrance_name
                    cleaned_fragrance_name = re.sub(r'\b\d+(\.\d+)?\s*ml\b', '', cleaned_fragrance_name,
                                                    flags=re.IGNORECASE).strip()

            gender = 'Men' if 'Para-Ele' in url else 'Women'

            fragrance = FragranceItem(
                brand=standardize_brand_names(brand),
                original_fragrance_name=fragrance_name,
                clean_fragrance_name=cleaned_fragrance_name,
                quantity=quantity,
                price_amount=price_amount,
                price_currency=price_currency,
                link=link,
                website="PerfumeClique.pt",
                country=["PT"],
                last_updated_at=datetime.now(),
                is_set_or_pack=is_set_or_pack,
                gender=gender,
                price_alert_threshold=None
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
        #total_pages = 3
        urls = [f"{category_url}&p={i}" for i in range(1, total_pages + 1)]
        html_pages = await gather_data(urls, parse)

    all_fragrances = [fragrance for page in html_pages for fragrance in page]
    return all_fragrances


# Main function to orchestrate the scraping process
async def main():
    start_time = time.time()

    men_fragrances = await scrape_category(MEN_URL)
    women_fragrances = await scrape_category(WOMEN_URL)

    all_fragrances = men_fragrances + women_fragrances

    base_path = os.path.join(os.getcwd(), 'data')  # Update this path as necessary
    os.makedirs(base_path, exist_ok=True)

    collection_name = "PerfumeClique"

    try:
        save_to_excel(all_fragrances, base_path, collection_name)
    except Exception as e:
        print(e)

    try:
        delete_collection(collection_name)
    except Exception as e:
        print(e)

    collection = db[collection_name]

    print(f"Start: Inserting/Updating/Removing fragrances in MongoDB for {collection_name}")
    try:
        db_insert_update_remove(collection, all_fragrances)
    except Exception as e:
        print("Error Occurred on Insert/Update/Remove")
        print(e)

    print(f"End: Inserting/Updating/Removing fragrances from MongoDB for {collection_name}")

    end_time = time.time()
    print(f"{collection_name} process took {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    test_mongo_connection()
    asyncio.run(main())
