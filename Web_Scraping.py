#!/usr/bin/env python
# coding: utf-8

# In[2]:


import requests
from bs4 import BeautifulSoup
import time
import datetime
import re

def clean_price(price_text):
    try:
        found = re.search(r"(\d+\.\d+)", price_text)
        return float(found.group(1)) if found else 0.0
    except:
        return 0.0

def clean_unit_data(unit_text):
    try:
        price_match = re.search(r"(\d+\.\d+)", unit_text)
        price_val = float(price_match.group(1)) if price_match else 0.0
        
        measure_match = re.search(r"per\s.*", unit_text)
        measure_val = measure_match.group(0) if measure_match else "unknown"
        
        return price_val, measure_val
    except:
        return 0.0, "error"

def scrape_trolley(item_name):
    url = f"https://www.trolley.co.uk/search/?q={item_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"--- Scraping {item_name} ---")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to access site. Status: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    products = soup.find_all('div', class_='product-item')
    
    scraped_data = []

    for product in products[:10]:
        try:
            brand = product.find('div', class_='_brand').get_text(strip=True)
            desc = product.find('div', class_='_desc').get_text(strip=True)
            
            price_div = product.find('div', class_='_price')
            total_price = clean_price(price_div.get_text(strip=True))
            
            unit_raw = product.find('div', class_='_per-item').get_text(strip=True)
            unit_price_val, unit_measure = clean_unit_data(unit_raw)

            scraped_data.append({
                "store": brand,
                "product_name": desc,
                "category": item_name,
                "total_price": total_price,
                "unit_price_val": unit_price_val,
                "unit_measure": unit_measure
            })
            
        except AttributeError:
            continue

    return scraped_data

# Main Logic
items_to_check = ["milk", "bread", "eggs"]
final_results = []

for item in items_to_check:
    data = scrape_trolley(item)
    final_results.extend(data)
    time.sleep(3) #

# Print results
print(f"\n{'STORE':<15} | {'PRODUCT':<40} | {'PRICE':<8} | {'UNIT RATE'}")
print("-" * 85)
for entry in final_results:
    print(f"{entry['store']:<15} | {entry['product_name'][:40]:<40} | £{entry['total_price']:<7} | £{entry['unit_price_val']} {entry['unit_measure']}")

print(f"\nSuccessfully collected {len(final_results)} items with ONS unit metrics.")

# In[3]:


from supabase import create_client, Client

SUPABASE_URL = "https://leabwcbbpxbrttwiqpqa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxlYWJ3Y2JicHhicnR0d2lxcHFhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA5OTU1MDMsImV4cCI6MjA4NjU3MTUwM30.FkD4PVsk_i8IEspRrJsjvFwLoZk3d3jQKZEAthCPcPY"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_to_supabase(data_list):
    if not data_list:
        print("No data to upload.")
        return

    try:
        response = supabase.table("grocery_inflation_tracker").insert(data_list).execute()
        print(f"Successfully uploaded {len(data_list)} items to the cloud!")
    except Exception as e:
        print(f"Database Error: {e}")

upload_to_supabase(final_results)
