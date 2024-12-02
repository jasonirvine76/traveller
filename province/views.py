import re
from django.shortcuts import render
from rdfstore.views import query_graphdb
import requests

def get_province_by_name(request, name):
    sparql_query = f"""
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX data: <http://localhost:7200/data/>

        SELECT *
        WHERE{{
            ?provinceName rdf:type <https://www.wikidata.org/wiki/Q34876> .
            ?provinceName foaf:isPrimaryTopicOf ?wikidataIRI .
            ?provinceName rdfs:label ?label .
            FILTER(?provinceName = data:{name})
        }}
    """
    results = query_graphdb(sparql_query)

    province_data = dict()
    external_link = None
    if results and "results" in results:
        bindings = results["results"]["bindings"]
        if bindings:
            row = bindings[0] 
            external_link = _get_value(row, "wikidataIRI")
            province_data["externalLink"] = external_link
    else:
        print(f"No results found for Province name: {name}")
    external_data = _fetch_province_data(external_link)
    if external_data and "results" in external_data:
        bindings = external_data["results"]["bindings"]
        if bindings:
            row = bindings[0]
            coordinates = _get_value(row, "coordinate")
            longitude, latitude = _extract_coordinate(coordinates)
            province_data["longitude"] = longitude
            province_data["latitude"] = latitude
            province_data["population"] = _get_value(row, "population")
            province_data["inceptionDate"] = _get_value(row, "inceptionDate")
            province_data["area"] = _get_value(row, "area")
            province_data["label"] = _get_value(row, "label")
        list_of_cityreg = []
        for row in bindings:
            cityreg_dict = dict()
            cityreg_label = _get_value(row, "cityregLabel")
            cityreg_iri = _get_value(row, "cityreg")
            cityreg_dict['label'] = cityreg_label
            cityreg_dict['iri'] = cityreg_iri
            list_of_cityreg.append(cityreg_dict)
        province_data['cityregs'] = list_of_cityreg
    else:
        print(f"No results found for Province name: {name}")
    return render(request, 'province-page.html', {'province_data': province_data})

def _extract_coordinate(point_str):
    match = re.match(r"Point\(([-+]?\d*\.?\d+) ([-+]?\d*\.?\d+)\)", point_str)
    if match:
        longitude = float(match.group(1))
        latitude = float(match.group(2))
        return (longitude, latitude)
    else:
        return (None, None)

def _get_value(row, key, transform=None):
    value = row.get(key, {}).get("value", "-")
    return transform(value) if transform and value != "-" else value

def _fetch_province_data(province_code):
    if not province_code:
        return None
    
    province_code = province_code.split("/")[-1]
    query = f"""
    SELECT ?coordinate ?label ?cityreg ?cityregLabel ?population ?inceptionDate ?area
    WHERE {{
        wd:{province_code} wdt:P625 ?coordinate .
        wd:{province_code} wdt:P150 ?cityreg .
        wd:{province_code} rdfs:label ?label .
        wd:{province_code} wdt:P1082 ?population .
        wd:{province_code} wdt:P571 ?inceptionDate .
        wd:{province_code} wdt:P2046 ?area .
        ?cityreg rdfs:label ?cityregLabel
        FILTER(LANG(?label) = "id")
        FILTER(LANG(?cityregLabel) = "id")
    }}
    """
    endpoint_url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json"}

    response = requests.get(endpoint_url, params={"query": query}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        raise Exception(f"Error fetching data: {response.status_code}, {response.text}")