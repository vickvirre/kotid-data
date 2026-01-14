import requests
import json
import re
import time
import random
from datetime import datetime

def scrape_sssb_api():
    # --- ANTI-BAN STRATEGI ---
    wait_time = random.randint(10, 60)
    print(f"😴 Väntar {wait_time} sekunder...")
    time.sleep(wait_time)
    
    # URL som hämtar 1000 objekt
    api_url = "https://minasidor.sssb.se/widgets/?callback=jQuery17206685519131474844_1768388791300&widgets%5B%5D=alert&widgets%5B%5D=objektsummering%40lagenheter&widgets%5B%5D=objektfilter%40lagenheter&widgets%5B%5D=objektsortering%40lagenheter&widgets%5B%5D=objektlistabilder%40lagenheter&widgets%5B%5D=paginering%40lagenheter&widgets%5B%5D=pagineringgofirst%40lagenheter&widgets%5B%5D=pagineringgonew%40lagenheter&widgets%5B%5D=pagineringlista%40lagenheter&widgets%5B%5D=pagineringgoold%40lagenheter&widgets%5B%5D=pagineringgolast%40lagenheter&pagination=1&paginationantal=1000"

    print(f"📡 Kontaktar SSSB...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Referer": "https://minasidor.sssb.se/lediga-bostader/"
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        
        content = response.text
        start_index = content.find('{')
        end_index = content.rfind('}') + 1
        
        if start_index == -1: return []
            
        data_package = json.loads(content[start_index:end_index])
        apartments_list = data_package.get("data", {}).get("objektlistabilder@lagenheter", [])
        
        print(f"🔍 Hittade {len(apartments_list)} bostäder.")
        
        parsed_apartments = []
        for apt in apartments_list:
            try:
                # Hämta hyra
                raw_rent = str(apt.get("hyra", "0")).replace(" ", "").replace("\xa0", "")
                
                # Hämta ködagar
                raw_queue = str(apt.get("antalIntresse", "0"))
                queue_match = re.search(r"(\d+)", raw_queue)
                queue_days = int(queue_match.group(1)) if queue_match else 0
                
                parsed_apt = {
                    "last_seen": datetime.now().strftime("%Y-%m-%d"),
                    "published": apt.get("publiceratDatum", ""),
                    "area": apt.get("omrade", "Okänt"),
                    "address": apt.get("adress", ""),
                    "type": apt.get("typ", "Okänt"),      # <--- NYHET! Här sparas typen
                    "sqm": int(apt.get("yta", 0)),
                    "rent": int(raw_rent) if raw_rent.isdigit() else 0,
                    "queue_days": queue_days,
                    "floor": apt.get("vaning", ""),
                    "id": apt.get("objektNr", "")
                }
                parsed_apartments.append(parsed_apt)
            except:
                continue
                
        return parsed_apartments

    except Exception as e:
        print(f"❌ Fel: {e}")
        return []

if __name__ == "__main__":
    new_data = scrape_sssb_api()
    
    if new_data:
        filename = "history.json"
        try:
            with open(filename, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []

        # ID + Datum som unik nyckel
        history_dict = {f"{item['id']}_{item.get('published', '')}": item for item in history}

        count_new = 0
        count_updated = 0
        
        for apt in new_data:
            unique_key = f"{apt['id']}_{apt['published']}"
            
            if unique_key in history_dict:
                # Uppdatera (detta lägger till 'type' på befintliga rader!)
                history_dict[unique_key] = apt
                count_updated += 1
            else:
                history_dict[unique_key] = apt
                count_new += 1
        
        final_list = list(history_dict.values())
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(final_list, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Sparat! {count_new} nya, {count_updated} uppdaterade.")