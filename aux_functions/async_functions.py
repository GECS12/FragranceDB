import asyncio
import aiohttp
import chardet
import random


# Function to gather data concurrently with a semaphore to limit max concurrent requests
async def gather_data(urls, parse_function, max_concurrent_requests=5):
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_parse(session, url, parse_function, semaphore) for url in urls]
        return await asyncio.gather(*tasks)


# Function to fetch and parse data with retries and backoff delay
async def fetch_and_parse(session, url, parse, semaphore, retries=5, delay=5):
    async with semaphore:
        for attempt in range(retries):
            try:
                await asyncio.sleep(random.uniform(1, 2))  # Add a longer, random delay between requests
                print(f"Scraping URL: {url}")
                async with session.get(url) as response:
                    if response.status == 429:
                        # Handle rate limit exceeded
                        print(f"Rate limit exceeded for URL: {url}. Retrying after delay...")
                        await asyncio.sleep(10)  # Specific delay for 429 status
                        continue
                    raw_content = await response.read()
                    result = chardet.detect(raw_content)
                    encoding = result['encoding'] if result['encoding'] is not None else 'utf-8'
                    html = raw_content.decode(encoding, errors='ignore')
                    return parse(html, url)
            except (aiohttp.ClientConnectorError, aiohttp.ClientPayloadError, aiohttp.ServerDisconnectedError,
                    aiohttp.ClientResponseError, asyncio.TimeoutError) as e:
                # Handle different types of network errors
                if response.status == 429:
                    print(f"Rate limit exceeded for URL: {url}. Retrying after delay...")
                    await asyncio.sleep(10)  # Specific delay for 429 status
                elif attempt < retries - 1:
                    backoff_delay = delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying URL: {url} in {backoff_delay:.2f} seconds due to error: {e}")
                    await asyncio.sleep(backoff_delay)
                else:
                    print(f"Failed to fetch URL {url} after {retries} attempts: {e}")
                    return []

    print(f"Failed to fetch URL {url} after {retries} attempts.")
    return []
