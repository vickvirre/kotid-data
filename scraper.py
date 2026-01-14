import requests
import json
import re
from datetime import datetime

def scrape_sssb_api():
    # ---------------------------------------------------------
    # STEG 1: Klistra in din "Guld-länk" här mellan citattecknen!
    # Den ska börja på https://minasidor.sssb.se/widgets/....
    # ---------------------------------------------------------
    api_url = "https://minasidor.sssb.se/widgets/?callback=jQuery17206685519131474844_1768388791300&widgets%5B%5D=alert&widgets%5B%5D=objektsummering%40lagenheter&widgets%5B%5D=objektfilter%40lagenheter&widgets%5B%5D=objektsortering%40lagenheter&widgets%5B%5D=objektlistabilder%40lagenheter&widgets%5B%5D=paginering%40lagenheter&widgets%5B%5D=pagineringgofirst%40lagenheter&widgets%5B%5D=pagineringgonew%40lagenheter&widgets%5B%5D=pagineringlista%40lagenheter&widgets%5B%5D=pagineringgoold%40lagenheter&widgets%5B%5D=pagineringgolast%40lagenheter&pagination=1&paginationantal=1000"
    
    # Om länken saknas, varna användaren
    if "PASTE_YOUR" in api_url:
        print("❌ DU MÅSTE KLISTRA IN LÄNKEN I SCRIPTET FÖRST! (Se rad 8)")
        return []

    print(f"📡 Kontaktar SSSB:s databas...")

    # Vi låtsas vara en vanlig besökare
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Referer": "https://minasidor.sssb.se/lediga-bostader/"
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status() # Larmar om länken är fel
        
        # SSSB svarar med "JSONP" (kod), vi måste städa bort det för att få ren JSON.
        # Vi letar efter första "{" och sista "}"
        content = response.text
        start_index = content.find('{')
        end_index = content.rfind('}') + 1
        
        if start_index == -1 or end_index == -1:
            print("❌ Kunde inte tolka svaret från SSSB. Är länken rätt?")
            # Printa lite av svaret för felsökning
            print(f"Svar från servern: {content[:100]}...") 
            return []
            
        json_text = content[start_index:end_index]
        data_package = json.loads(json_text)
        
        # Nu gräver vi oss ner till listan med lägenheter
        # Baserat på din kodsnutt ligger de under "data" -> "objektlistabilder@lagenheter"
        apartments_list = data_package.get("data", {}).get("objektlistabilder@lagenheter", [])
        
        print(f"🔍 Hittade {len(apartments_list)} bostäder i databasen.")
        
        parsed_apartments = []
        
        for apt in apartments_list:
            try:
                # 1. Hämta ködagar (formatet är "1009 (14st)")
                raw_queue = apt.get("antalIntresse", "0")
                queue_match = re.search(r"(\d+)", str(raw_queue))
                queue_days = int(queue_match.group(1)) if queue_match else 0
                
                # 2. Hämta hyra (ta bort mellanslag, t.ex. "7 594" -> 7594)
                raw_rent = apt.get("hyra", "0")
                # Ibland är hyran ett tal, ibland text, vi säkrar upp:
                rent = int(str(raw_rent).replace(" ", "").replace("\xa0", ""))
                
                # 3. Bygg objektet
                parsed_apt = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "area": apt.get("omrade", "Okänt"),     # T.ex. "Jerum"
                    "address": apt.get("adress", ""),       # T.ex. "Studentbacken 21"
                    "sqm": int(apt.get("yta", 0)),          # T.ex. 41
                    "rent": rent,
                    "queue_days": queue_days,
                    "floor": apt.get("vaning", ""),
                    "id": apt.get("objektNr", "")           # Unikt ID från SSSB
                }
                
                parsed_apartments.append(parsed_apt)
                
            except Exception as e:
                # print(f"⚠️ Hoppade över en rad: {e}") # Avkommentera om du vill se fel
                continue
                
        return parsed_apartments

    except Exception as e:
        print(f"❌ Ett fel uppstod: {e}")
        return []

if __name__ == "__main__":
    data = scrape_sssb_api()
    
    if data:
        print(f"✅ Succé! Samlade in {len(data)} bostäder.")
        print("Exempel på första bostaden:", data[0])
        
        # Spara till history.json
        filename = "history.json"
        try:
            with open(filename, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []
            
        history.extend(data)
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print("💾 Sparat till history.json")