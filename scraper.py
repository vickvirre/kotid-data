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
                # --- DATA TVÄTT ---
                raw_rent = str(apt.get("hyra", "0")).replace(" ", "").replace("\xa0", "")
                
                # Hämta intresse-strängen, ex: "277 (10st)"
                raw_interest = str(apt.get("antalIntresse", "0"))
                
                # 1. Hitta ANTAL SÖKANDE (Siffran inuti parentesen)
                applicants_match = re.search(r"\((\d+)", raw_interest)
                if applicants_match:
                    applicants_count = int(applicants_match.group(1))
                else:
                    applicants_count = 0

                # 2. Hitta KÖDAGAR (Om det finns 'poang', annars gissa 0)
                # Ibland är poängen null i listan och syns bara på detaljsidan
                raw_points = apt.get("poang")
                if raw_points:
                    queue_days = int(raw_points) 
                else:
                    queue_days = 0 

                parsed_apt = {
                    "last_seen": datetime.now().strftime("%Y-%m-%d"),
                    "published": apt.get("publiceratDatum", ""),
                    "area": apt.get("omrade", "Okänt"),
                    "address": apt.get("adress", ""),
                    "type": apt.get("typ", "Okänt"),
                    "sqm": int(apt.get("yta", 0)),
                    "rent": int(raw_rent) if raw_rent.isdigit() else 0,
                    "queue_days": queue_days,
                    "applicants": applicants_count,  # <--- HÄR ÄR NYA DATAN!
                    "floor": apt.get("vaning", ""),
                    "id": apt.get("objektNr", ""),
                    "is_active": True
                }
                parsed_apartments.append(parsed_apt)
            except Exception as loop_error:
                # print(f"Hoppade över en rad pga fel: {loop_error}") 
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

        # --- STÄDPATRULLEN ---
        # Fixar gamla objekt som saknar 'applicants' så inte koden kraschar
        for old_item in history:
            if "applicants" not in old_item:
                old_item["applicants"] = 0

        # 1. Skapa dictionary av all historik
        history_dict = {f"{item['id']}_{item.get('published', '')}": item for item in history}

        # 2. VIKTIGT: Nollställ status! Utgå från att ingen är aktiv längre.
        for key in history_dict:
            history_dict[key]['is_active'] = False

        count_new = 0
        count_updated = 0
        
        # 3. Uppdatera med ny data
        for apt in new_data:
            unique_key = f"{apt['id']}_{apt['published']}"
            
            if unique_key in history_dict:
                history_dict[unique_key].update(apt) # Uppdaterar poäng, applicants OCH sätter is_active = True
                count_updated += 1
            else:
                history_dict[unique_key] = apt
                count_new += 1
        
        final_list = list(history_dict.values())
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(final_list, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Sparat! {count_new} nya, {count_updated} uppdaterade.")
        print(f"   Totalt i databasen: {len(final_list)}")