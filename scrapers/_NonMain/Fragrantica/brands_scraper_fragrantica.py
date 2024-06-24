from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

BASE_URL = "https://www.fragrantica.com/designers/"

def fetch_html(url):
    options = Options()
    options.headless = True  # Run in headless mode
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    html = driver.page_source
    driver.quit()
    return html

def extract_brands_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    brands = []

    designer_divs = soup.find_all('div', class_='designerlist cell small-6 large-4')
    for designer_div in designer_divs:
        img_tag = designer_div.find('img')
        if img_tag and 'alt' in img_tag.attrs:
            brand = img_tag['alt'].strip()
            if brand:
                brands.append(brand)

    return brands

def main():
    url = BASE_URL
    html = fetch_html(url)
    brands = extract_brands_from_html(html)
    print(f"Extracted brands: {brands}")
    return brands

if __name__ == "__main__":
    brands = main()
    # Save the brands to a file or print t
