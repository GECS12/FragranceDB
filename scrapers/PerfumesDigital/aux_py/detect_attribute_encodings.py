import aiohttp
import asyncio
import chardet
import logging
from bs4 import BeautifulSoup
import codecs

BASE_URL = "https://perfumedigital.es/"

logging.basicConfig(level=logging.INFO)


# Function to fetch the page content
async def fetch_page_content(url, session):
    try:
        async with session.get(url, timeout=15) as response:
            raw_content = await response.read()
            result = chardet.detect(raw_content)
            encoding = result['encoding'] if result['encoding'] is not None else 'utf-8'
            logging.info(f"Detected encoding for {url}: {encoding}")
            return raw_content, encoding
    except Exception as e:
        logging.error(f"Error fetching page content: {e}")
        return None, None


# Function to parse HTML and print the encoding of original_brand and original_fragrance_name
def detect_encoding(raw_content, encoding):
    if encoding.lower() == 'macroman':
        html = codecs.decode(raw_content, 'mac_roman')
    else:
        html = raw_content.decode(encoding, errors='ignore')

    soup = BeautifulSoup(html, 'html.parser')

    for td in soup.find_all('td', align='center', style='width:33%;'):
        table = td.find('table')
        if table:
            brand_tag = table.find('i')
            if brand_tag:
                original_brand = brand_tag.get_text(strip=True)
                logging.info(f"Original brand: {original_brand} | Encoding used: {encoding}")

            link_tag = table.find('a', href=True)
            img_tag = link_tag.find('img') if link_tag else None
            if img_tag and 'alt' in img_tag.attrs:
                original_fragrance_name = img_tag['alt'].strip()
                logging.info(f"Original fragrance name: {original_fragrance_name} | Encoding used: {encoding}")


# Main function to fetch and detect encoding
async def main():
    tasks = []
    async with aiohttp.ClientSession() as session:
        for page in (15, 26):  # Adjust the range as needed for the number of pages
            pase = (page - 1) * 15
            url = f"{BASE_URL}index.php?PASE={pase}&marca=&buscado=&ID_CATEGORIA=&ORDEN=&precio1=&precio2=#PRODUCTOS"
            tasks.append(fetch_page_content(url, session))

        results = await asyncio.gather(*tasks)

        for raw_content, encoding in results:
            if raw_content:
                detect_encoding(raw_content, encoding)


if __name__ == "__main__":
    asyncio.run(main())
