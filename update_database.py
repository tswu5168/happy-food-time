# -*- coding: utf-8 -*-
"""
HappyFoodTime: One-Click Automatic Database Synchronization & Resolution (Multi-Theme)
This script integrates both scraping the list items and resolving their addresses/GPS coordinates
for multiple map themes: Food, Stay, Play, and Camping.
"""

import os
import sys
import time
import json
import re
import subprocess
import urllib.request
import urllib.parse

# Set stdout to UTF-8 to prevent Windows terminal CP950 coding issues
sys.stdout.reconfigure(encoding='utf-8')

# Theme Configurations mapped to Google Maps Shared List URLs
THEME_CONFIG = {
    "food": "https://maps.app.goo.gl/ATKdxosP9QKedy868",  # 我想吃的
    "stay": "https://maps.app.goo.gl/m94jZFN4p3gonovZ6",  # 我想住的
    "play": "https://maps.app.goo.gl/6LVvtti4PYB7xqVk6",  # 我想去的
    "camp": ""  # 我的露營區 (暫無 URL)
}

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPED_JSON_PATH = os.path.join(PROJECT_DIR, "scraped_raw_stores.json")
RESOLVED_JSON_PATH = os.path.join(PROJECT_DIR, "fully_resolved_stores.json")
JS_OUTPUT_PATH = os.path.join(PROJECT_DIR, "stores_data.js")

TAIWAN_REGIONS = ["宜蘭", "台北", "新北", "花蓮", "台東", "台南", "台中", "彰化", "嘉義", "高雄", "基隆", "苗栗", "南投", "屏東", "桃園", "新竹", "雲林"]

def install_dependencies():
    print("=" * 60)
    print("[1/4] Checking and installing Python dependencies...")
    print("=" * 60)
    required = {"selenium", "webdriver-manager", "geopy"}
    for package in required:
        pkg_name = package.replace("-", "_")
        try:
            __import__(pkg_name)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    print("All dependencies checked and ready!\n")

def scrape_gmaps_list(url, theme_name):
    if not url:
        print(f"No URL configured for theme '{theme_name}'. Skipping scrape.")
        return []
        
    print("=" * 60)
    print(f"[2/4] Scraping Google Maps List items for Theme: '{theme_name}'...")
    print("=" * 60)
    
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--lang=zh-TW")
    
    print("Initializing Chrome Driver...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        print(f"Navigating to shared list URL: {url}")
        driver.get(url)
        print("Waiting for page redirection and initial loading (12 seconds)...")
        time.sleep(12)
        
        js_find_scroll_container = """
            let divs = document.querySelectorAll('div');
            for (let div of divs) {
                let style = window.getComputedStyle(div);
                if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
                    if (div.scrollHeight > 500) return div;
                }
            }
            return null;
        """
        scrollable_container = driver.execute_script(js_find_scroll_container)
        
        scroll_attempts = 0
        max_scroll_attempts = 150
        last_item_count = 0
        no_change_count = 0
        
        while scroll_attempts < max_scroll_attempts:
            items = driver.find_elements(By.CLASS_NAME, "fontHeadlineSmall")
            current_count = len(items)
            print(f"  Scroll {scroll_attempts+1}: Loaded {current_count} items in DOM.")
            
            if current_count == last_item_count:
                no_change_count += 1
                if no_change_count >= 8:
                    print("  List size stabilized. Reached the bottom.")
                    break
            else:
                no_change_count = 0
                
            last_item_count = current_count
            
            if scrollable_container:
                driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scrollable_container)
            else:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
            scroll_attempts += 1
            time.sleep(2.5)
            
        # Extract items
        items_elements = driver.find_elements(By.CLASS_NAME, "fontHeadlineSmall")
        raw_data = []
        for el in items_elements:
            name = el.text.strip()
            if not name:
                continue
                
            raw_data.append({
                "name": name,
                "region": "未知",
                "cuisine": "未知", 
                "address": "地址請至導航地圖查看",
                "time": "",
                "lat": "",
                "lon": "",
                "theme": theme_name
            })
            
        # De-duplicate by name within this theme
        seen = set()
        unique_data = []
        for d in raw_data:
            if d['name'] not in seen:
                seen.add(d['name'])
                unique_data.append(d)
                
        print(f"Scrape completed! Total unique items found for '{theme_name}': {len(unique_data)}\n")
        driver.quit()
        return unique_data
    except Exception as e:
        print(f"Error scraping list: {e}")
        driver.quit()
        return []

def extract_region(text):
    if not text:
        return "未知"
    for r in TAIWAN_REGIONS:
        if r in text:
            return r
    if "臺北" in text: return "台北"
    if "臺中" in text: return "台中"
    if "臺南" in text: return "台南"
    if "臺東" in text: return "台東"
    return "未知"

def is_in_taiwan(lat, lon):
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        return (21.8 <= lat_f <= 26.5) and (119.3 <= lon_f <= 122.3)
    except ValueError:
        return False

def resolve_addresses(stores, theme_name, resolved_map):
    if not stores:
        return resolved_map
        
    print("=" * 60)
    print(f"[3/4] Resolving addresses and coordinates for Theme: '{theme_name}'...")
    print("=" * 60)
    
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from geopy.geocoders import ArcGIS
    
    geolocator = ArcGIS()
    
    # Setup Selenium for Google Maps searching
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--lang=zh-TW")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    def query_google_maps(name):
        query = urllib.parse.quote(name)
        url = f"https://www.google.com/maps/search/{query}?hl=zh-TW"
        try:
            driver.get(url)
            time.sleep(4.5)
            
            if "偵測到您的電腦網路送出的流量有異常情況" in driver.page_source:
                print("    [Google Maps query blocked]")
                return None
                
            curr_url = driver.current_url
            lat, lon = "", ""
            coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', curr_url)
            if coord_match:
                lat, lon = coord_match.group(1), coord_match.group(2)
                
            address = None
            try:
                addr_element = driver.find_element(By.CSS_SELECTOR, "[data-item-id='address']")
                if addr_element:
                    aria = addr_element.get_attribute("aria-label")
                    if aria:
                        address = aria.replace("地址:", "").replace("地址：", "").strip()
            except Exception:
                pass
                
            if address or (lat and lon):
                if lat and lon and not is_in_taiwan(lat, lon):
                    lat, lon = "", ""
                return {
                    "address": address or "地址請至導航地圖查看",
                    "lat": lat,
                    "lon": lon,
                    "region": extract_region(address or name)
                }
        except Exception as e:
            print(f"    Google Maps query error for {name}: {e}")
        return None
        
    def query_arcgis_fallback(name):
        try:
            location = geolocator.geocode(f"{name}, 臺灣", timeout=5)
            if location:
                lat, lon = location.latitude, location.longitude
                if not is_in_taiwan(lat, lon):
                    return None
                reverse_loc = geolocator.reverse((lat, lon), timeout=5)
                addr = reverse_loc.address if reverse_loc else location.address
                clean_addr = addr.replace(", TWN", "").strip()
                if clean_addr == name:
                    clean_addr = "地址請至導航地圖查看"
                return {
                    "address": clean_addr,
                    "lat": str(lat),
                    "lon": str(lon),
                    "region": extract_region(addr)
                }
        except Exception:
            pass
        return None
        
    for idx, store in enumerate(stores):
        name = store['name']
        store['theme'] = theme_name
        
        # Deduce cuisine / category based on name keywords & theme
        category = "未知"
        if theme_name == "food":
            category = "台式"
            if "燒肉" in name or "拉麵" in name or "丼飯" in name or "壽司" in name:
                category = "日式"
            elif "海鮮" in name or "萬里蟹" in name or "海產" in name or "魚湯" in name:
                category = "海鮮"
            elif "披薩" in name or "義式" in name or "義式" in name:
                category = "歐美"
            elif "客家" in name:
                category = "客家"
            elif "素食" in name or "蔬食" in name:
                category = "素食"
        elif theme_name == "stay":
            category = "民宿"
            if "飯店" in name or "酒店" in name or "Hotel" in name or "會館" in name:
                category = "飯店"
            elif "營" in name or "露營" in name:
                category = "營地"
            elif "青旅" in name or "背包" in name:
                category = "青年旅館"
        elif theme_name == "play":
            category = "景點"
            if "步道" in name or "山" in name or "古道" in name or "瀑布" in name:
                category = "自然景觀"
            elif "老街" in name or "夜市" in name or "商圈" in name:
                category = "市集老街"
            elif "博物館" in name or "美術館" in name or "觀光工廠" in name:
                category = "藝文觀光"
            elif "公園" in name or "牧場" in name or "農場" in name:
                category = "休閒公園"
        elif theme_name == "camp":
            category = "露營區"
            if "野營" in name:
                category = "野營地"
                
        store['cuisine'] = category
        
        # Check if already resolved in checkpoint (must be high quality: no commas in address and valid GPS)
        already_resolved = False
        if name in resolved_map:
            existing = resolved_map[name]
            addr = existing.get('address', '')
            lat = existing.get('lat', '')
            lon = existing.get('lon', '')
            reg = existing.get('region', '')
            
            has_real_addr = addr and "地址請至" not in addr and ("," not in addr)
            has_real_coords = lat and lon and is_in_taiwan(lat, lon)
            has_real_region = reg and reg != "未知"
            
            if has_real_addr and has_real_coords and has_real_region:
                already_resolved = True
                store['address'] = addr
                store['lat'] = lat
                store['lon'] = lon
                store['region'] = reg
                
        if already_resolved:
            resolved_map[name] = store
            continue
            
        print(f"  [{idx+1}/{len(stores)}] Resolving: {name}")
        
        # 1. Google Maps geocoding
        result = query_google_maps(name)
        time.sleep(1.5)
        
        # 2. Fallback to ArcGIS
        if not result:
            print("    Google Maps failed. Trying ArcGIS geocoder...")
            result = query_arcgis_fallback(name)
            time.sleep(1.0)
            
        if result:
            store['address'] = result['address']
            store['lat'] = result['lat']
            store['lon'] = result['lon']
            store['region'] = result['region']
            print(f"    Success: {store['region']} | {store['address']} (GPS: {store['lat']},{store['lon']})")
        else:
            store['region'] = extract_region(name)
            print(f"    Fallback: Region deduced from name: {store['region']}")
            
        resolved_map[name] = store
        
        # Checkpoint incremental updates every 20 stores
        if (idx + 1) % 20 == 0 or (idx + 1) == len(stores):
            checkpoint_data = list(resolved_map.values())
            with open(RESOLVED_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
                
    driver.quit()
    return resolved_map

def load_env():
    env_vars = {}
    env_path = os.path.join(PROJECT_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        env_vars[parts[0].strip()] = parts[1].strip()
    return env_vars

def upsert_to_supabase(stores_list, env_vars):
    supabase_url = env_vars.get("SUPABASE_URL")
    service_key = env_vars.get("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not service_key or "your-project" in supabase_url:
        print("[Warning] Supabase URL or Service Key not configured in .env. Skipping cloud upload.")
        return False
        
    print("=" * 60)
    print("[4/5] Upserting database records to Supabase...")
    print("=" * 60)
    
    # Fields: name, region, cuisine, address, time, lat, lon, theme
    payload = []
    for s in stores_list:
        payload.append({
            "name": s.get("name"),
            "region": s.get("region", "未知"),
            "cuisine": s.get("cuisine", "未知"),
            "address": s.get("address", "地址請至導航地圖查看"),
            "time": s.get("time", ""),
            "lat": s.get("lat", ""),
            "lon": s.get("lon", ""),
            "theme": s.get("theme", "food")
        })
        
    try:
        url = f"{supabase_url.rstrip('/')}/rest/v1/stores"
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.status
            if status in (200, 201, 204):
                print(f"Successfully upserted {len(payload)} stores to Supabase!")
                return True
            else:
                print(f"Failed to upsert. Status code: {status}")
                return False
    except Exception as e:
        print(f"Error during Supabase upsert: {e}")
        return False

def write_js_database(stores_list):
    # Fallback region deduction for any missing regions
    for s in stores_list:
        if not s.get('region') or s['region'] == "未知":
            s['region'] = extract_region(s['address'] or s['name'])
            
    with open(JS_OUTPUT_PATH, "w", encoding="utf-8") as out:
        out.write("// Auto-generated data file containing user's custom maps list (sanitized)\n")
        out.write("const STORES_DATA = ")
        json.dump(stores_list, out, ensure_ascii=False, indent=2)
        out.write(";\n")

def finalize_sync(total_count, uploaded=False):
    print("=" * 60)
    print("[5/5] Finalizing Database Sync...")
    print("=" * 60)
    print(f"Total synchronized items: {total_count}")
    if uploaded:
        print("Database successfully synchronized to SUPABASE cloud node!")
    else:
        print("Database written successfully to local backup!")
    print(f"Local backup database written to: {JS_OUTPUT_PATH}")
    print("Done! Refresh http://localhost:8080 in your browser to view updates!")
    print("=" * 60)

def main():
    start_time = time.time()
    
    install_dependencies()
    
    # Load previously resolved checkpoint to avoid recalculating
    resolved_map = {}
    if os.path.exists(RESOLVED_JSON_PATH):
        try:
            with open(RESOLVED_JSON_PATH, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            resolved_map = {}
            for x in checkpoint:
                if 'theme' not in x:
                    x['theme'] = 'food'
                resolved_map[x['name']] = x
            print(f"Loaded {len(checkpoint)} resolved stores from checkpoint.")
        except Exception as e:
            print(f"Could not load checkpoint: {e}")
            
    # List to collect all stores from all themes
    all_theme_scraped_stores = []
    
    # Loop through configs and scrape/resolve
    for theme, url in THEME_CONFIG.items():
        if url:
            # Step 1: Scrape
            scraped_theme_stores = scrape_gmaps_list(url, theme)
            
            # Step 2: Resolve and merge into resolved_map
            if scraped_theme_stores:
                resolved_map = resolve_addresses(scraped_theme_stores, theme, resolved_map)
                all_theme_scraped_stores.extend(scraped_theme_stores)
        else:
            # If no URL is configured for a theme, preserve any existing resolved items of this theme
            print(f"Preserving existing resolved items for unconfigured theme: '{theme}'")
            existing_theme_items = [v for v in resolved_map.values() if v.get('theme') == theme]
            all_theme_scraped_stores.extend(existing_theme_items)
            print(f"  Preserved {len(existing_theme_items)} items.")
            
    # Combine final records from resolved_map for all active scraped/preserved stores
    final_stores_list = []
    seen_names = set()
    for store in all_theme_scraped_stores:
        name = store['name']
        if name not in seen_names:
            seen_names.add(name)
            # Fetch resolved details (or fallback to original scraped data)
            final_stores_list.append(resolved_map.get(name, store))
            
    # Load environment variables
    env_vars = load_env()
    
    # Upsert to Supabase
    uploaded = upsert_to_supabase(final_stores_list, env_vars)
    
    # Write local fallback JS file
    write_js_database(final_stores_list)
    
    finalize_sync(len(final_stores_list), uploaded)
    
    end_time = time.time()
    print(f"Database Synchronizer completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
