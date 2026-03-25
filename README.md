# GéoDoc - Carte des Médecins de la Région de Rennes

GéoDoc est une application Web intuitive permettant de localiser et visualiser l'ensemble des praticiens (médecins généralistes, spécialistes, médecins du travail, etc.) enregistrés sur le secteur de Rennes.

L'objectif est d'offrir une carte interactive très rapide avec des capacités de ciblage et de filtre poussées, tout en fonctionnant à la fois en version logicielle locale (avec extracteur) ou en version hébergée de type statique (GitHub Pages).

## 🚀 Fonctionnalités Clés
- **Carte Interactive** propulsée par *Leaflet* avec clusters de données.
- **Moteur de Recherche par Adresse** : Rentrez votre adresse sur Rennes, l'outil centre la vue et calcule instantanément la distance vers chaque professionnel !
- **Itinéraires Automatiques** : Cliquez sur un praticien pour tracer immédiatement la route (en utilisant Leaflet Routing Machine).
- **Filtres Multicritères** : Triez dynamiquement par **Spécialité Médico-chirurgicale** et par **Genre** (Hommes / Femmes).
- **Data Scraping** : Inclut des scripts Python d'extraction de données depuis les annuaires et de géocodage multithread natif basé sur *l'API Adresse du Gouvernement*. Plus rapide et sans limitation drastique par rapport à Nominatim.

## 🛠️ Stack Technique
- **Front-end** : Vanilla JS, Leaflet.js, API Nominatim (pour la recherche d'adresse locale), FontAwesome, CSS Grid/Flexbox modernes (UI Glassmorphism).
- **Back-end** : Flask (Dev server et déclencheur d'extraction), Python (Multi-threading `concurrent.futures`, `BeautifulSoup4` pour extraire l'enveloppe HTML du DOM).
- **Hébergement Web** : Prêt pour déploiement via GitHub Pages en architecture Statique 100% Client.

## 📦 Comment utiliser la version locale (Extraction Live)
Le projet est fourni avec un système permettant d'ingérer vos propres extractions "brutes" (par exemple : `medecin_femme.txt` en HTML brut et `medecin_homme.txt`).
1. Lancez l'application avec `python app.py`
2. Ouvrez `http://127.0.0.1:5000`
3. Cliquez sur **"Actualiser les données (.txt)"**. Le système va dédoublonner, récupérer les numéros de téléphones fraîchement grattés, envoyer les requêtes croisées multithread à l'API Data Gouv, et actualiser l'interface instantanément.

## 🌐 Consultation de la Carte Statique
L'application Front-End à la racine (`index.html`) de ce dépôt GitHub est configurée pour fonctionner de façon autonome avec les données pré-récoltées de l'auteur (`medecins_extraits.json`). Déployable immédiatement via **GitHub Pages**.
