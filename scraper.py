import requests
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime

def scrape_sssb_safe():
    all_apartments = []
    page = 1
    has_results = True
    
    # Vi låtsas vara en vanlig webbläsare (Chrome)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0 Safari/537.36"
    }

    print("🤖 Startar SSSB-roboten...")

    while has_results:
        # Vi bygger URL:en för nuvarande sida
        url = f"https://minasidor.sssb.se/lediga-bostader/?pagination={page}"
        print(f"📄 Läser in sida {page}...", end="")
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status() # Larmar om sidan är nere
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Vi letar efter "Ködagar:" för att hitta bostäderna (samma säkra metod som förut)
            queue_labels = soup.find_all(string=re.compile(r"Ködagar:"))
            
            if not queue_labels:
                print(" -> Inga bostäder hittades. Vi är klara! ✅")
                has_results = False
                break
            
            count_on_page = 0
            for label in queue_labels:
                # Logik för att hitta datan runt "Ködagar"-etiketten
                try:
                    # Gå upp till containern för hela bostadskortet
                    # Vi testar att hitta föräldern som heter "ObjektList-item" eller går upp 3 steg
                    container = label.find_parent("div", class_="ObjektList-item")
                    if not container:
                        container = label.parent.parent.parent
                    
                    text = container.get_text(" ", strip=True)

                    # Regex för att plocka ut värden
                    area_match = re.search(r"Område:\s*(\w+)", text)
                    rent_match = re.search(r"Hyra:\s*([\d\s]+)\s*kr", text)
                    sqm_match = re.search(r"Boyta:\s*(\d+)\s*m²", text)
                    days_match = re.search(r"Ködagar:\s*(\d+)", text)

                    if days_match:
                        apt = {
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "area": area_match.group(1) if area_match else "Okänt",
                            "rent": int(rent_match.group(1).replace(" ", "")) if rent_match else 0,
                            "sqm": int(sqm_match.group(1)) if sqm_match else 0,
                            "queue_days": int(days_match.group(1)),
                            # Unikt ID för att undvika dubbletter
                            "id": f"{area_match.group(1)}-{days_match.group(1)}-{rent_match.group(1)}"
                        }
                        all_apartments.append(apt)
                        count_on_page += 1
                        
                except Exception:
                    continue

            print(f" -> Hittade {count_on_page} st.")
            
            # VIKTIGT: Pausa lite så vi inte blir flaggade
            time.sleep(1.5) 
            page += 1

        except Exception as e:
            print(f"\n❌ Något gick fel på sida {page}: {e}")
            break

    return all_apartments

if __name__ == "__main__":
    data = scrape_sssb_safe()
    
    print(f"\n🎯 Totalt insamlat: {len(data)} bostäder")
    
    if data:
        # Spara/Uppdatera history.json
        filename = "history.json"
        
        # 1. Läs in gammal data (om den finns)
        try:
            with open(filename, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []
            
        # 2. Lägg till ny data
        # (Här lägger vi bara till allt, senare kan vi filtrera dubbletter om vi vill)
        history.extend(data)
        
        # 3. Spara filen
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Sparat data i {filename}")