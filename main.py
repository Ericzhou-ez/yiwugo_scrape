import time
import random
import os
import csv
import threading
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:114.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
]

def start_driver():
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    return uc.Chrome(options=options)


def get_listing_urls(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.tile-item"))
        )
    except Exception as e:
        print("Timeout waiting for listing elements:", e)
        return []
    soup = BeautifulSoup(driver.page_source, "html.parser")
    listings = soup.find_all("a", class_="tile-item")
    urls = []
    for listing in listings:
        link = listing.get("href")
        if link:
            urls.append("https://www.yiwugo.com" + link)
    return urls


def go_to_next_page(driver):
    """Clicks the '下一页' button and waits for the next page to load."""
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "下一页"))
        )
        next_button.click()
        time.sleep(5)
        return True
    except Exception as e:
        print("No next page found or error:", e)
        return False

driver = start_driver()
# change base url for product catagory here
base_url = ("https://www.yiwugo.com/classification/index.html?"
            "typeaId=21&typea=%E7%99%BE%E8%B4%A7&spm=eWl3dWdvLmNvbS8=.ZW4ueWl3dWdvLmNvbS8."
            "d3d3Lnlpd3Vnby5jb20v.d3d3Lnlpd3Vnby5jb20vY2xhc3NpZmljYXRpb24vaW5kZXguaHRtbA==.d3d3Lnlpd3Vnby5jb20vaW5kZXguaHRtbA==")
driver.get(base_url)
time.sleep(5)

all_listing_urls = set()
while True:
    urls = get_listing_urls(driver)
    all_listing_urls.update(urls)
    print(f"✅ Found {len(urls)} listings on page. Total so far: {len(all_listing_urls)}")
    if len(urls) <= 10:
        break
    if not go_to_next_page(driver):
        break

print(f"🎯 Finished collecting listings. Total listings found: {len(all_listing_urls)}")
driver.quit()

class UserProfile:
    def __init__(self):
        self.driver = start_driver()


profiles_queue = Queue()
NUM_AGENTS = 10
for _ in range(NUM_AGENTS):
    profiles_queue.put(UserProfile())

data_lock = threading.Lock()
unique_records = set()
output_file = "yiwugo_factories.csv"
if not os.path.exists(output_file):
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Factory Name", "Owner Name", "Phone Number", "Address"])


def save_result(record):
    """Save a record to CSV if it’s unique."""
    with data_lock:
        if record not in unique_records:
            unique_records.add(record)
            with open(output_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(record)
            print(f"Saved: {record}")


def scrape_listing(url, max_retries=3):
    profile = profiles_queue.get()
    retries = 0
    record = None

    print(f"🌍 Scraping URL: {url}")
    while retries < max_retries:
        try:
            profile.driver.get(url)
            time.sleep(3)
            WebDriverWait(profile.driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.title-link.fb"))
            )
            soup = BeautifulSoup(profile.driver.page_source, "html.parser")
            factory_tag = soup.find("a", class_="title-link fb")
            owner_tag = soup.find("span", class_="c666 owner-name")
            phone_tag = soup.find("p", class_="c666")
            address_tag = soup.find("span", class_="c666 f-break")

            factory_name = factory_tag.get_text(strip=True) if factory_tag else ""
            owner_name = owner_tag.get_text(strip=True) if owner_tag else ""
            phone = phone_tag.get_text(strip=True) if phone_tag else ""
            address = address_tag.get_text(strip=True) if address_tag else ""

            if all([factory_name, owner_name, phone, address]):
                record = (factory_name, owner_name, phone, address)
                print(f"✅ Scraped record: {record}")
                break  # Exit retry loop
            else:
                print(f"⚠️ Incomplete data for {url}, retrying...")
                retries += 1
                time.sleep(3)

        except (TimeoutException, NoSuchElementException) as e:
            retries += 1
            print(f"🔄 Retry {retries}/{max_retries} for {url} due to: {e}")
            time.sleep(3)

        except Exception as e:
            print(f"🚨 Fatal error scraping {url}: {e}")
            break

    if not record:
        print(f"❌ Failed after {max_retries} retries. Reinitializing agent.")
        try:
            profile.driver.quit()
        except:
            pass
        profile = UserProfile()

    profiles_queue.put(profile)
    return record if record else None


# Saving as I go
with ThreadPoolExecutor(max_workers=50) as executor:
    future_to_url = {executor.submit(scrape_listing, url): url for url in all_listing_urls}
    for future in as_completed(future_to_url):
        result = future.result()
        if result:
            save_result(result)

# Clean up: Quit all agent drivers.
while not profiles_queue.empty():
    profile = profiles_queue.get()
    try:
        profile.driver.quit()
    except Exception:
        pass

df = pd.read_csv(output_file)
print(f"✅ Scraped {len(df)} unique records and saved to CSV!")
