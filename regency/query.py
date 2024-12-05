import re
import requests

def preprocess_name(name):
    name = re.sub(r"\s*\(.*?\)", "", name)
    
    name = name.replace("_", " ")
    
    return name.strip()

def parse_coordinates(coordinate_str):
    match = re.match(r"Point\(([-+]?\d*\.?\d+) ([-+]?\d*\.?\d+)\)", coordinate_str)
    if match:
        longitude = float(match.group(1))
        latitude = float(match.group(2))
        return longitude, latitude
    return None, None

def fetch_label_for_entity(entity_uri):
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
    SELECT ?regencyName ?image ?coatOfArms ?coordinate ?country ?locatedIn ?containsEntity
    WHERE {{
        ?regencyName rdfs:label "{processed_label}"@{lang}.
        OPTIONAL {{ ?regencyName wdt:P18 ?image . }}  
        OPTIONAL {{ ?regencyName wdt:P94 ?coatOfArms . }} 
        OPTIONAL {{ ?regencyName wdt:P625 ?coordinate . }}  
        OPTIONAL {{ ?regencyName wdt:P17 ?country . }} 
        OPTIONAL {{ ?regencyName wdt:P131 ?locatedIn . }}  
        OPTIONAL {{ ?regencyName wdt:P150 ?containsEntity . }}  
    }}
    """
    response = requests.get(endpoint_url, params={"query": query}, headers=headers)
    
    if response.status_code == 200:
        data = response.json().get("results", {}).get("bindings", [])
        
        if data:
            image, coat_of_arms, coordinates, country_uri, located_in, longitude, latitude = None, None, None, None, None, None, None
            contains_entities = []
            
            for result in data:
                if not image: 
                    image = result.get("image", {}).get("value")
                if not coat_of_arms:
                    coat_of_arms = result.get("coatOfArms", {}).get("value")
                if not coordinates:
                    coordinates = result.get("coordinate", {}).get("value")
                if not country_uri:
                    country_uri = result.get("country", {}).get("value")
                if not located_in:
                    located_in = result.get("locatedIn", {}).get("value")
                
                contains_entity = result.get("containsEntity", {}).get("value")
                if contains_entity and contains_entity not in contains_entities:
                    contains_entities.append(contains_entity)
            
            if coordinates:
                longitude, latitude = parse_coordinates(coordinates)
            
            # Fetch labels for URIs
            country_label = fetch_label_for_entity(country_uri) if country_uri else None
            located_in_label = fetch_label_for_entity(located_in) if located_in else None
            contains_entity_labels = [
                fetch_label_for_entity(entity) for entity in contains_entities 
            ]
            contains_entity_labels = [label for label in contains_entity_labels if label]
            
            return {
                "wikidata_id": data[0]["regencyName"]["value"],
                "image": image,
                "coat_of_arms": coat_of_arms,  
                "coordinates": {"longitude": longitude, "latitude": latitude},
                "country": country_label,
                "located_in": located_in_label,
                "contains_entities": contains_entity_labels,
            }
        return None
    else:
        raise Exception(f"Error fetching data: {response.status_code}, {response.text}")
