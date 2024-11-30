from django.shortcuts import render
from rdfstore.views import query_graphdb


def get_destination_by_id(request, id):
    sparql_query = f"""
    PREFIX data: <http://tourism-2024.org/data/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?name ?description ?category ?city ?price ?rating ?latitude ?longitude ?timeSpent
    WHERE {{
        data:{id} rdfs:label ?name ;
                 data:description ?description ;
                 data:category ?category ;
                 data:atCity ?city ;
                 data:price ?price ;
                 data:rating ?rating ;
                 data:latitude ?latitude ;
                 data:longitude ?longitude .
        OPTIONAL {{ data:{id} data:timeSpentInMinutes ?timeSpent . }}
    }}
    """
    results = query_graphdb(sparql_query)

    destination_data = None
    if results and "results" in results:
        bindings = results["results"]["bindings"]
        if bindings:
            row = bindings[0] 
            destination_data = {
                "name": _get_value(row, "name"),
                "description": _get_value(row, "description"),
                "category": _get_value(row, "category"),
                "city": _get_value(row, "city", lambda v: v.split("/")[-1]),  # Extract after slash
                "price": _get_value(row, "price"),
                "rating": _get_value(row, "rating"),
                "timeSpent": _get_value(row, "timeSpent"),
                "latitude": _get_value(row, "latitude", float),
                "longitude": _get_value(row, "longitude", float),
            }
    else:
        print(f"No results found for destination ID: {id}")
    return render(request, 'destination-page.html', {'destination': destination_data, 'destination_id': id})


def _get_value(row, key, transform=None):
    value = row.get(key, {}).get("value", "-")
    return transform(value) if transform and value != "-" else value