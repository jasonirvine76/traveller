import requests
import re

def preprocess_name(name):
    """
    Preprocess the input name by removing abbreviations in parentheses and converting to lowercase.
    """
    name = re.sub(r"\s*\(.*?\)", "", name)  # Remove content in parentheses
    return name.strip()

def get_wikidata_by_name(label, lang):
    endpoint_url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json"}
    processed_label = preprocess_name(label)
    query = f"""
    SELECT ?item ?image ?officialWebsite ?logo
    WHERE {{
        ?item rdfs:label "{processed_label}"@{lang}.
        OPTIONAL {{ ?item wdt:P18 ?image. }}
        OPTIONAL {{ ?item wdt:P856 ?officialWebsite. }}
        OPTIONAL {{ ?item wdt:P154 ?logo. }}
    }}
    LIMIT 1
    """
    
    
    response = requests.get(endpoint_url, params={"query": query}, headers=headers)
    if response.status_code == 200:
        data = response.json().get("results", {}).get("bindings", [])
        if data:
            result = data[0]
            image = result.get("image", {}).get("value")
            logo = result.get("logo", {}).get("value")
            return {
                "wikidata_id": result["item"]["value"].split("/")[-1],
                "image": image if image else logo,
                "official_website": result.get("officialWebsite", {}).get("value"),
            }
        return None
    else:
        raise Exception(f"Error fetching data: {response.status_code}, {response.text}")