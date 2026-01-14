import requests
import json
import re
import time
import random
from datetime import datetime

def scrape_sssb_api():
    # --- ANTI-BAN STRATEGI ---
    # Vänta slumpmässigt mellan 10 sekunder och 4 minuter
    wait_time = random.randint(10, 240)
    print(f"😴 Väntar {wait_time} sekunder för att se mänsklig ut...")
    time.sleep(wait_time)
    # -------------------------

    # Din API-länk
    api_url = "https://minasidor.sssb.se/widgets/?callback=jQuery17206685519131474844_1768388791300&widgets%5B%5D=alert&widgets%5B%5D=objektsummering%40lagenheter&widgets%5B%5D=objektfilter%40lagenheter&widgets%5B%5D=objektsortering%40lagenheter&widgets%5B%5D=objektlistabilder%40lagenheter&widgets%5B%5D=paginering%40lagenheter&widgets%5B%5D=pagineringgofirst%40lagenheter&widgets%5B%5D=pagineringgonew%40lagenheter&widgets%5B%5D=pagineringlista%40lagenheter&widgets%5B%5D=pagineringgoold%40lagenheter&widgets%5B%5D=pagineringgolast%40lagenheter&pagination=1&paginationantal=1000"
    
    print(f"📡 Kontaktar SSSB:s databas...")

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
        
        if start_index == -1 or end_index == -1:
            print("❌ Kunde inte tolka svaret.")
            return []
            
        json_text = content[start_index:end_index]
        data_package = json.loads(json_text)
        
        apartments_list = data_package.get("data", {}).get("objektlistabilder@lagenheter", [])
        print(f"🔍 Hittade {len(apartments_list)} bostäder.")
        
        parsed_apartments = []
        
        for apt in apartments_list:
            try:
                raw_queue = apt.get("antalIntresse", "0")
                queue_match = re.search(r"(\d+)", str(raw_queue))
                queue_days = int(queue_match.group(1)) if queue_match else 0
                
                raw_rent = apt.get("hyra", "0")
                rent = int(str(raw_rent).replace(" ", "").replace("\xa0", ""))
                
                parsed_apt = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "area": apt.get("omrade", "Okänt"),
                    "address": apt.get("adress", ""),
                    "sqm": int(apt.get("yta", 0)),
                    "rent": rent,
                    "queue_days": queue_days,
                    "floor": apt.get("vaning", ""),
                    "id": apt.get("objektNr", "")
                }
                parsed_apartments.append(parsed_apt)
            except Exception:
                continue
                
        return parsed_apartments

    except Exception as e:
        print(f"❌ Ett fel uppstod: {e}")
        return []

if __name__ == "__main__":
    data = scrape_sssb_api()
    
    if data:
        filename = "history.json"
        
        # 1. Läs in den gamla listan (om den finns)
        try:
            with open(filename, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []

        # 2. Skapa ett "register" där vi enkelt kan hitta bostäder via deras ID
        # Detta gör att vi kan kolla "finns den här redan?"
        history_dict = {item['id']: item for item in history}

        # 3. Gå igenom de nya bostäderna vi just hämtade
        count_new = 0
        count_updated = 0
        
        for apt in data:
            if apt['id'] in history_dict:
                # Den fanns redan! Uppdatera med de senaste siffrorna (högre ködagar)
                history_dict[apt['id']] = apt
                count_updated += 1
            else:
                # Helt ny bostad! Lägg till den.
                history_dict[apt['id']] = apt
                count_new += 1
        
        # 4. Gör om registret till en lista igen så vi kan spara det
        updated_history = list(history_dict.values())

        # 5. Spara ner till filen
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(updated_history, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Klart! {count_new} nya bostäder tillagda, {count_updated} uppdaterade.")
        print(f"   Totalt i din databas: {len(updated_history)} unika bostäder.")