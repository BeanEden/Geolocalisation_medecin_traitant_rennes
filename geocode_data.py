import os
import json
import requests
import concurrent.futures
import time

def geocode_address(doc):
    addr = doc.get("address", "")
    if not addr:
        doc['lat'] = None
        doc['lon'] = None
        return doc

    clean_addr = addr.replace('\n', ', ')
    url = "https://api-adresse.data.gouv.fr/search/"
    
    try:
        response = requests.get(url, params={'q': clean_addr, 'limit': 1}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            if features:
                # API Adresse renvoie [lon, lat]
                coords = features[0]["geometry"]["coordinates"]
                doc['lon'] = coords[0]
                doc['lat'] = coords[1]
                return doc
                
        # En cas d'échec de l'adresse complète, on tente avec le code postal + ville (la fin de la chaine)
        parts = clean_addr.split(",")
        if len(parts) > 1:
            fallback_addr = parts[-1].strip()
            response = requests.get(url, params={'q': fallback_addr, 'limit': 1}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                if features:
                    coords = features[0]["geometry"]["coordinates"]
                    doc['lon'] = coords[0]
                    doc['lat'] = coords[1]
                    return doc

    except Exception as e:
        print(f"Erreur HTTP pour {doc.get('name')}: {e}")

    doc['lat'] = None
    doc['lon'] = None
    return doc

def main():
    print("Chargement des médecins extraits...")
    json_path = os.path.join(os.path.dirname(__file__), "medecins_extraits.json")
    
    if not os.path.exists(json_path):
        print(f"Erreur : le fichier {json_path} n'existe pas.")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        doctors = json.load(f)
        
    docs_to_geocode = [d for d in doctors if not d.get("lat") or not d.get("lon")]
    print(f"{len(doctors)} médecins au total.")
    print(f"-> {len(docs_to_geocode)} médecins seront géocodés avec l'API Adresse (Multithreading)...")
    
    if not docs_to_geocode:
        print("Tous les médecins sont déjà géocodés !")
        return

    start_time = time.time()
    
    # Processus asynchrone multithread (20 workers pour respecter les limites et le CPU)
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(geocode_address, doc): doc for doc in docs_to_geocode}
        
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            if completed % 50 == 0 or completed == len(docs_to_geocode):
                print(f"  [{completed}/{len(docs_to_geocode)}] requêtes traitées...")

    # Sauvegarde finale
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(doctors, f, indent=4, ensure_ascii=False)
        
    elapsed = time.time() - start_time
    
    # Bilan global
    success_count = sum(1 for d in doctors if d.get('lat') is not None)
    print(f"\nGéocodage terminé en {elapsed:.2f} secondes !")
    print(f"Bilan : {success_count} médecins désormais sur la carte (sur {len(doctors)} au total).")

if __name__ == "__main__":
    main()
