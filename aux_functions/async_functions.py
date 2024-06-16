import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import chardet

async def gather_data(urls, parse_function, max_concurrent_requests=5):
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_parse(session, url, parse_function, semaphore) for url in urls]
        return await asyncio.gather(*tasks)

async def fetch_and_parse(session, url, parse, semaphore, retries=5, delay=10):
    async with semaphore:
        page_number = (int(url.split('PASE=')[1].split('&')[0]) // 15) + 1
        for attempt in range(retries):
            try:
                print(f"Scraping page: {page_number}")
                async with session.get(url) as response:
                    raw_content = await response.read()
                    result = chardet.detect(raw_content)
                    encoding = result['encoding']
                    try:
                        html = raw_content.decode(encoding, errors='ignore')  # Handle decoding errors gracefully
                    except UnicodeDecodeError as e:
                        print(f"UnicodeDecodeError at {url} - {e}")
                        print(f"Problematic byte position: {e.start}")
                        return []
                    return parse(html, url)
            except aiohttp.ClientConnectorError as e:
                print(f"ClientConnectorError fetching URL {url}: {e}")
            except aiohttp.ClientPayloadError as e:
                print(f"ClientPayloadError fetching URL {url}: {e}")
            except aiohttp.ServerDisconnectedError as e:
                print(f"ServerDisconnectedError fetching URL {url}: {e}")
            except Exception as e:
                print(f"Error fetching URL {url}: {e}")
            if attempt < retries - 1:
                print(f"Retrying {url} in {delay} seconds...")
                await asyncio.sleep(delay)
    print(f"Failed to fetch URL {url} after {retries} attempts.")
    return []


