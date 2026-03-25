import os
import json
from bs4 import BeautifulSoup

def extract_doctors_from_file(filepath):
    doctors = []
    
    sexe = "Non renseigné"
    fname = os.path.basename(filepath).lower()
    if "femme" in fname:
        sexe = "Femme"
    elif "homme" in fname:
        sexe = "Homme"
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin1') as f:
            content = f.read()
            
    soup = BeautifulSoup(content, 'html.parser')
    
    # On sait que chaque carte commence dans une div avec certaines classes ou tag <tableau-card>
    # Mais le text dit: "chaque médecin <div class="flex h-full flex-col gradient-header-left-right..."
    cards = soup.find_all("div", class_="gradient-header-left-right")
    if not cards:
        cards = soup.find_all("tableau-card")
        
    for card in cards:
        # Noms
        name_tag = card.find("h2", class_=lambda x: x and "text-lg" in x and "text-primary" in x)
        name = name_tag.text.strip() if name_tag else "Nom Inconnu"
        
        # Spécialités et disciplines
        specs_tags = card.find_all("div", class_=lambda x: x and "text-[13px]" in x and "text-gray-900" in x)
        specialties = specs_tags[0].text.strip() if len(specs_tags) > 0 else ""
        other_disciplines = specs_tags[1].text.strip() if len(specs_tags) > 1 else ""
        
        # L'adresse et le téléphone utilisent souvent les mêmes spans class="ml-2 text-primary"
        # On va chercher tous les spans correspondants (en retirant "text-base" au cas où le site ait changé de classe)
        info_spans = card.find_all("span", class_=lambda x: x and "ml-2" in x and "text-primary" in x)
        
        address = ""
        phone = ""
        
        # Souvent, l'adresse est le premier, le tel est le 2ème. Mais distinguons les par leur contenu ou l'icône précédente
        for span in info_spans:
            text = span.text.strip()
            # Un numéro de téléphone a très peu de lettres par rapport aux chiffres
            if sum(c.isdigit() for c in text) >= 9 and sum(c.isalpha() for c in text) < 5:
                phone = text
            elif not address:
                address = text
                
        # Nettoyage de l'adresse (parfois des retours chariots)
        address = " ".join([line.strip() for line in address.split('\n') if line.strip()])
        
        # On évite les doublons si possible ou si on ne trouve rien
        if name != "Nom Inconnu":
            doctors.append({
                "name": name,
                "specialties": specialties,
                "other_disciplines": other_disciplines,
                "address": address,
                "phone": phone,
                "sexe": sexe
            })
            
    return doctors

def main():
    data_dir = r"c:\Users\JC\Documents\medecin\data"
    all_doctors = []
    
    # On trouve tous les fichiers
    for filename in os.listdir(data_dir):
        if filename.endswith(".txt") or filename.endswith(".htm") or filename.endswith(".html"):
            if filename.startswith("~$"):
                continue
            filepath = os.path.join(data_dir, filename)
            print(f"Extraction depuis {filename}...")
            doctors = extract_doctors_from_file(filepath)
            print(f"  -> {len(doctors)} médecins trouvés.")
            all_doctors.extend(doctors)
            
    # Dédoublonnage précis par nom + adresse, mais en conservant les données enrichies (téléphone, sexe)
    unique_doctors_dict = {}
    for doc in all_doctors:
        # On normalise la clé : minuscules et retrait des espaces de début/fin
        name_clean = doc['name'].strip().lower()
        addr_clean = doc['address'].strip().lower()
        identifier = f"{name_clean}_{addr_clean}"
        
        if identifier not in unique_doctors_dict:
            unique_doctors_dict[identifier] = doc
        else:
            # On met à jour si le nouveau document a plus d'informations
            if doc.get('phone') and not unique_doctors_dict[identifier].get('phone'):
                unique_doctors_dict[identifier]['phone'] = doc['phone']
            if doc.get('sexe') and doc['sexe'] != "Non renseigné" and unique_doctors_dict[identifier].get('sexe') == "Non renseigné":
                unique_doctors_dict[identifier]['sexe'] = doc['sexe']
                
    unique_doctors = list(unique_doctors_dict.values())
            
    print(f"Total médecins uniques extraits : {len(unique_doctors)}")
    
    out_path = os.path.join(os.path.dirname(__file__), "medecins_extraits.json")
    
    # 1. Récupération des anciennes coordonnées pour ne pas avoir à tout re-géocoder
    existing_coords = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as rf:
                old_docs = json.load(rf)
                for d in old_docs:
                    if d.get("lat") is not None and d.get("lon") is not None:
                        name_clean = d.get('name', '').strip().lower()
                        addr_clean = d.get('address', '').strip().lower()
                        key = f"{name_clean}_{addr_clean}"
                        existing_coords[key] = {"lat": d["lat"], "lon": d["lon"]}
        except Exception:
            pass
            
    # 2. Transfert des coordonnées existantes vers les médecins nouvellement extraits
    for doc in unique_doctors:
        name_clean = doc['name'].strip().lower()
        addr_clean = doc['address'].strip().lower()
        key = f"{name_clean}_{addr_clean}"
        if key in existing_coords:
            doc['lat'] = existing_coords[key]['lat']
            doc['lon'] = existing_coords[key]['lon']
            
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(unique_doctors, f, indent=4, ensure_ascii=False)
        
if __name__ == "__main__":
    main()
