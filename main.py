import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests
import concurrent.futures
import folium

async def scrape_doctors():
    url = "https://tableau.ordre.medecin.fr/recherche-avancee?specialite=120&discipline=&titre=&nom=&prenom=&civilite=i&region=53&departement=35&ville=Rennes&rue="
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigation vers la page de l'Ordre des Médecins...")
        await page.goto(url)
        
        print("Attente du chargement des résultats...")
        try:
            # Attend que le premier élément "tableau-card" s'affiche (max 15s)
            await page.wait_for_selector("tableau-card", timeout=15000)
        except Exception as e:
            print("Aucun résultat ou erreur lors du chargement :", e)
        
        # Le chargement d'une SPA avec Angular peut parfois avoir des animations
        await page.wait_for_timeout(2000) 
        
        # Scroller jusqu'en bas pour s'assurer que tous les scripts/lazy-loading soient finis
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        
        content = await page.content()
        await browser.close()
        
    # Analyse de la page via BeautifulSoup
    soup = BeautifulSoup(content, "html.parser")
    cards = soup.find_all("tableau-card")
    doctors = []
    
    for card in cards:
        # Noms
        name_tag = card.find("h2", class_=lambda x: x and "text-lg" in x and "text-primary" in x)
        name = name_tag.text.strip() if name_tag else "Nom Inconnu"
        
        # Adresse et Téléphone
        info_spans = card.find_all("span", class_=lambda x: x and "text-primary" in x and "ml-2" in x)
        address = ""
        phone = ""
        for span in info_spans:
            text = span.text.strip()
            if sum(c.isdigit() for c in text) >= 9 and sum(c.isalpha() for c in text) < 5:
                phone = text
            elif not address:
                address = text
                
        # Spécialités et disciplines
        specs_tags = card.find_all("div", class_=lambda x: x and "text-[13px]" in x and "text-gray-900" in x)
        specialties = specs_tags[0].text.strip() if len(specs_tags) > 0 else "Généraliste (ou non spécifié)"
        other_disciplines = specs_tags[1].text.strip() if len(specs_tags) > 1 else ""
        
        doctors.append({
            "name": name,
            "specialties": specialties,
            "other_disciplines": other_disciplines,
            "address": address,
            "phone": phone
        })
        
    print(f"{len(doctors)} médecins récupérés.")
    return doctors

def __geocode_single_address_main(doc):
    addr = doc.get('address', '')
    if not addr:
        doc['lat'], doc['lon'] = None, None
        return doc
        
    clean_addr = addr.replace('\n', ', ')
    url = "https://api-adresse.data.gouv.fr/search/"
    try:
        response = requests.get(url, params={'q': clean_addr, 'limit': 1}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                coords = data["features"][0]["geometry"]["coordinates"]
                doc['lon'], doc['lat'] = coords[0], coords[1]
                return doc
                
        # Fallback avec la fin de l'adresse
        parts = clean_addr.split(",")
        if len(parts) > 1:
            fallback = parts[-1].strip()
            response = requests.get(url, params={'q': fallback, 'limit': 1}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("features"):
                    coords = data["features"][0]["geometry"]["coordinates"]
                    doc['lon'], doc['lat'] = coords[0], coords[1]
                    return doc
    except Exception as e:
        print(f"    Erreur HTTP pour {doc.get('name')} : {e}")
        
    doc['lat'], doc['lon'] = None, None
    return doc

def geocode_addresses(doctors):
    print("\nGéocodage rapide en cours avec l'API Adresse (Multithreading)...")
    
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(__geocode_single_address_main, doc): doc for doc in doctors}
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            if completed % 50 == 0 or completed == len(doctors):
                print(f"  [{completed}/{len(doctors)}] requêtes traitées...")
            
    return doctors

def create_map(doctors, output_file="carte_medecins.html"):
    print(f"\nGénération de la carte ({output_file})...")
    # Initialisation de la carte au centre de Rennes
    m = folium.Map(location=[48.117266, -1.6777926], zoom_start=13)
    
    meds_mapped = 0
    for doc in doctors:
        if doc.get('lat') and doc.get('lon'):
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; min-width: 200px;">
                <h4 style="color: #0056b3; margin-bottom: 5px;">{doc['name']}</h4>
                <p style="margin: 0; font-size: 13px; font-weight: bold;">{doc['specialties']}</p>
                <p style="margin: 0; font-size: 12px; color: #555;">{doc['other_disciplines']}</p>
                <hr style="margin: 8px 0;">
                <p style="margin: 0; font-size: 12px;">{doc['address'].replace(chr(10), '<br>')}</p>
                {f'<p style="margin: 5px 0 0 0; font-size: 12px; font-weight: bold; color: #d9534f;">📞 {doc["phone"]}</p>' if doc.get('phone') else ''}
            </div>
            """
            folium.Marker(
                location=[doc['lat'], doc['lon']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=doc['name'],
                icon=folium.Icon(color='blue', icon='user-md', prefix='fa') # Icon de médecin "FontAwesome"
            ).add_to(m)
            meds_mapped += 1
            
    m.save(output_file)
    print(f"Succès ! {meds_mapped} médecins ont été placés sur la carte.")
    print(f"Ouvrez le fichier '{output_file}' dans votre navigateur.")

async def main():
    doctors = await scrape_doctors()
    
    # Stockons une sauvegarde JSON au cas où 
    with open("medecins_data.json", "w", encoding="utf-8") as f:
        json.dump(doctors, f, indent=4, ensure_ascii=False)
        
    doctors = geocode_addresses(doctors)
    create_map(doctors)

if __name__ == "__main__":
    asyncio.run(main())
