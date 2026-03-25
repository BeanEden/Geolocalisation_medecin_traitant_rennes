import os
import json
from flask import Flask, render_template, jsonify, request
import extract_local
import geocode_data

app = Flask(__name__)

def load_doctors():
    filepath = os.path.join(os.path.dirname(__file__), 'medecins_extraits.json')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/doctors')
def api_doctors():
    doctors = load_doctors()
    # On filtre les médecins qui ont des coordonnées pour la carte
    mappable = [d for d in doctors if d.get('lat') is not None and d.get('lon') is not None]
    unmappable = [d for d in doctors if d.get('lat') is None or d.get('lon') is None]
    
    return jsonify({
        'mappable': mappable,
        'unmappable_count': len(unmappable),
        'total': len(doctors)
    })

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    try:
        print("Lancement de l'extraction des médecins...")
        extract_local.main()
        print("Lancement du géocodage...")
        geocode_data.main()
        return jsonify({"status": "success", "message": "Base de données mise à jour"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/update_phone', methods=['POST'])
def update_phone():
    try:
        data = request.json
        name = data.get("name")
        address = data.get("address")
        phone = data.get("phone")
        
        if not name or not phone:
            return jsonify({"status": "error", "message": "Données manquantes"}), 400
            
        filepath = os.path.join(os.path.dirname(__file__), 'medecins_extraits.json')
        if not os.path.exists(filepath):
            return jsonify({"status": "error", "message": "Fichier introuvable"}), 404
            
        with open(filepath, 'r', encoding='utf-8') as f:
            doctors = json.load(f)
            
        updated = False
        for doc in doctors:
            if doc.get('name') == name and doc.get('address') == address:
                doc['phone'] = phone
                updated = True
                break
                
        if updated:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(doctors, f, indent=4, ensure_ascii=False)
            return jsonify({"status": "success", "message": "Téléphone mis à jour"})
        else:
            return jsonify({"status": "error", "message": "Praticien introuvable"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # On lance l'application sur le port 5000
    app.run(debug=True, port=5000)
