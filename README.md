# Fulcrums Web Scraper

## Overview
This script scrapes **YiwuGo** for **supplier and distributor data**, including **factory names, owner names, phone numbers, and addresses**. The extracted data is stored in a CSV file.

## Purpose
- **Auto-populate** the sourcing team’s database.  
- **Categorize distributors** by product type.  
- **Enable autocomplete** for supplier entries.  
- **Facilitate product searches** with stored data.  

## Installation
Ensure you have Python installed, then install the required dependencies:

```bash
pip install selenium undetected-chromedriver beautifulsoup4 pandas
```

## How It Works

### 1. Collect Listing URLs
- Visits YiwuGo’s category pages.
- Extracts **product listing URLs** from multiple pages.

### 2. Scrape Factory Data
- Uses **headless undetected Chrome drivers** to avoid detection.
- Parses each page using **BeautifulSoup**.
- Extracts **factory details** (name, owner, phone, address).
- Retries failed pages automatically up to 3 times.

### 3. Store Data
- Saves records **as they are scraped** into `yiwugo_factories.csv`.

## Running the Script

```bash
python main.py
```

## Avoiding Detection
- Uses **rotating user-agents** to mimic real users.
- Multi-threaded execution with **ThreadPoolExecutor** for efficiency.

## Output
The scraped data is saved in:

```plaintext
yiwugo_factories.csv
```

Each row contains:

```csv
Factory Name, Owner Name, Phone Number, Address
```

## Notes
- Update `base_url` in `main.py` to scrape different product categories.
- Adjust the number of concurrent scraping agents (`NUM_AGENTS`) for performance tuning.
