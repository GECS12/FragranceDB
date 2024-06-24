import os
import re
import time
import hashlib
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
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

# Base URL for Perfumes24h
BASE_URL = "https://perfumes24h.com/perfumes/"


# Function to scroll to load all content on the page using Selenium
def scroll_to_load_all(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # Wait for new content to load
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height


# Function to fetch HTML content using Selenium
def fetch_html_with_selenium(url):
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    scroll_to_load_all(driver)

    html = driver.page_source
    driver.quit()
    return html


# Function to parse the HTML content to extract fragrance information
def parse(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    fragrances = []
    price_currency = '€'

    for div in soup.find_all('div', class_='item_producto'):
        brand_tag = div.find('div', class_='nombre_marca')
        brand = brand_tag.get_text(strip=True) if brand_tag else None

        name_tag = div.find('div', class_='nombre_grupo')
        fragrance_name = name_tag.get_text(strip=True) if name_tag else None

        link_tags = div.find_all('a', href=True)
        link = link_tags[1]['href'] if len(link_tags) > 1 else (link_tags[0]['href'] if link_tags else None)

        price_tag = div.find('div', class_='txt_precio_venta')
        price_amount = float(price_tag.get_text(strip=True).replace('€', '').replace(',', '.')) if price_tag else None

        aux_type_tag = div.find('div', class_='tipo_producto')
        aux_type = aux_type_tag.get_text(strip=True) if aux_type_tag else ""

        clean_fragrance_name = standardize_fragrance_names(fragrance_name + " " + aux_type, brand)

        gender_tag = div.find('div', class_='sexo')
        gender = gender_tag.get_text(strip=True) if gender_tag else ""
        gender = 'Men' if 'Hombre' in gender else 'Women'

        for variant in div.find_all('div', class_='item_tamanyo'):
            variant_price = float(variant['data-pp'].replace(',', '.'))
            quantity_match = re.search(r'(\d+)', variant.get_text(strip=True))
            variant_quantity = int(quantity_match.group(1)) if quantity_match else 0
            is_set_or_pack = True if not quantity_match else False

            fragrance = FragranceItem(
                brand=standardize_brand_names(brand),
                original_fragrance_name=fragrance_name,
                clean_fragrance_name=clean_fragrance_name,
                quantity=variant_quantity,
                price_amount=variant_price,
                price_currency=price_currency,
                link=link,
                website="Perfumes24h.com",
                country=["PT", "ES"],
                last_updated_at=datetime.now(),
                is_set_or_pack=is_set_or_pack,
                gender=gender,
                price_alert_threshold=None
            )
            if fragrance.get_id() not in [f.get_id() for f in fragrances]:  # Ensure no duplicate IDs
                fragrances.append(fragrance)

    return fragrances


# Main function to orchestrate the scraping process
def main():

    collection_name = "Perfumes24h"

    print(f"Started scraping {collection_name}")

    html = fetch_html_with_selenium(BASE_URL)
    parsed_data = parse(html, BASE_URL)

    all_fragrances = parsed_data

    print(f"Ended scraping {collection_name}")

    base_path = os.path.join(os.getcwd(), 'data')  # Update this path as necessary
    os.makedirs(base_path, exist_ok=True)

    try:
        save_to_excel(all_fragrances, base_path, collection_name)
    except Exception as e:
        print(e)


    # try:
    #     delete_collection(collection_name)
    # except Exception as e:
    #     print(e)

    collection = db[collection_name]

    print(f"Start: Inserting/Updating/Removing fragrances in MongoDB for {collection_name}")
    try:
        db_insert_update_remove(collection, all_fragrances)
    except Exception as e:
        print("Error Occurred on Insert/Update/Remove")
        print(e)

    print(f"End: Inserting/Updating/Removing fragrances from MongoDB for {collection_name}")


if __name__ == "__main__":
    main()
