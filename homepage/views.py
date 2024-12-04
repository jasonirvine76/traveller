from django.shortcuts import render
import requests

def show_homepage(request):
    endpoint = "http://localhost:7200/repositories/traveller"
    query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX data: <http://localhost:7200/data/>

        SELECT ?wst ?rating ?label ?description
        WHERE {
            ?wst a <https://www.wikidata.org/wiki/Q1200957> .
            OPTIONAL {?wst data:rating ?rating .}
            OPTIONAL {?wst data:description ?description .}
            OPTIONAL {?wst rdfs:label ?label .}
        }
        ORDER BY DESC(?rating)
        LIMIT 3
    """
    headers = {"Accept": "application/sparql-results+json"}
    response = requests.get(endpoint, params={"query": query}, headers=headers)

    if response.status_code == 200:
        rdf_data = response.json()
        destinations = []
        for binding in rdf_data.get("results", {}).get("bindings", []):
            destinations.append({
                "iri": "destination/"+binding.get("wst", {}).get("value", "").rsplit('/', 1)[-1],
                "description": binding.get("description", {}).get("value", "No description available."),
                "rating": float(binding.get("rating", {}).get("value", "No rating available.")),
                "label": binding.get("label", {}).get("value", "-"),
            })
    else:
        destinations = []

    # Pass the destinations to the template
    return render(request, 'homepage.html', {"destinations": destinations})
