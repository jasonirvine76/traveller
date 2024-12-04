import re
import requests

def preprocess_name(name):
    """
    Preprocess the regency name by:
    - Removing abbreviations in parentheses.
    - Replacing underscores with spaces (e.g., 'Jakarta_Barat' -> 'Jakarta Barat').
    """
    # Remove content in parentheses
    name = re.sub(r"\s*\(.*?\)", "", name)
    
    # Replace underscores with spaces for regency names
    name = name.replace("_", " ")
    
    return name.strip()

def parse_coordinates(coordinate_str):
    """
    Parse coordinates from WKT format 'Point(longitude latitude)' to a tuple of floats (longitude, latitude).
    """
    match = re.match(r"Point\(([-+]?\d*\.?\d+) ([-+]?\d*\.?\d+)\)", coordinate_str)
    if match:
        longitude = float(match.group(1))
        latitude = float(match.group(2))
        return longitude, latitude
    return None, None

def fetch_label_for_entity(entity_uri):
    """
    Fetch the human-readable label for an entity (e.g., country, located in).
    """
    endpoint_url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json"}
    query = f"""
    SELECT ?label
    WHERE {{
        <{entity_uri}> rdfs:label ?label.
        FILTER(LANG(?label) = "id")  # Adjust this to match the language of the label (e.g., Indonesian).
    }}
    """
    response = requests.get(endpoint_url, params={"query": query}, headers=headers)
    if response.status_code == 200:
        data = response.json().get("results", {}).get("bindings", [])
        if data:
            return data[0].get("label", {}).get("value")
    return None

def get_wikidata_by_name(label, lang="id"):
    endpoint_url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json"}
    processed_label = preprocess_name(label)  # Preprocess the name
    query = f"""
    SELECT ?regencyName ?image ?coordinate ?country ?locatedIn ?containsEntity
    WHERE {{
        
        ?regencyName rdfs:label "{processed_label}"@{lang}.
        
        OPTIONAL {{ ?regencyName wdt:P18 ?image . }}  # Image
        OPTIONAL {{ ?regencyName wdt:P625 ?coordinate . }}  # Coordinates (geolocation)
        OPTIONAL {{ ?regencyName wdt:P17 ?country . }}  # Country
        OPTIONAL {{ ?regencyName wdt:P131 ?locatedIn . }}  # Located in the administrative territorial entity
        OPTIONAL {{ ?regencyName wdt:P150 ?containsEntity . }}  # Contains the administrative territorial entity
        
    }}
    LIMIT 1
    """
    response = requests.get(endpoint_url, params={"query": query}, headers=headers)
    if response.status_code == 200:
        data = response.json().get("results", {}).get("bindings", [])
        if data:
            result = data[0]
            image = result.get("image", {}).get("value")
            coordinates = result.get("coordinate", {}).get("value")
            country_uri = result.get("country", {}).get("value")
            located_in = result.get("locatedIn", {}).get("value")
            contains_entity = result.get("containsEntity", {}).get("value")

            longitude, latitude = parse_coordinates(coordinates) if coordinates else (None, None)

            # Fetch labels for country, located_in, and contains_entity (if applicable)
            country_label = fetch_label_for_entity(country_uri) if country_uri else None
            located_in_label = fetch_label_for_entity(located_in) if located_in else None
            contains_entity_label = fetch_label_for_entity(contains_entity) if contains_entity else None
            
            return {
                "wikidata_id": result["regencyName"]["value"].split("/")[-1],
                "image": image,
                "coordinates": {"longitude": longitude, "latitude": latitude},
                "country": country_label,
                "located_in": located_in_label,
                "contains_entity": contains_entity_label,
            }
        return None
    else:
        raise Exception(f"Error fetching data: {response.status_code}, {response.text}")
