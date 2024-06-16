import aiohttp
from bs4 import BeautifulSoup
import asyncio
from aux_functions.data_functions import *

async def fetch_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            return html

async def extract_brands_from_url(url):
    html = await fetch_html(url)
    return extract_brands_from_html(html)

def extract_brands_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    brands = []

    select_tag = soup.find('select', {'name': 'marca'})
    if select_tag:
        options = select_tag.find_all('option')
        for option in options:
            brand = option.get('value')
            if brand and brand.strip() != "":
                brands.append(brand.strip())

    return brands

if __name__ == "__main__":
    url = "https://perfumedigital.es/"  # Replace with the actual URL
    brands = asyncio.run(extract_brands_from_url(url))
    corrected_brands = []
    print(f"Extracted brands: {brands}")
    for brand in brands:
        corrected_brands.append(standardize_strings(standardize_brand_name(brand)))
    print(f'Corrected brands: {corrected_brands}')
