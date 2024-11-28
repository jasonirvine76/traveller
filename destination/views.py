from django.shortcuts import render
from rdfstore.views import query_graphdb


def get_destination_by_id(request, id):
    sparql_query = f"""
    PREFIX data: <http://tourism-2024.org/data/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?name ?description ?category ?city ?price ?rating ?timeSpent ?latitude ?longitude
    WHERE {{
        data:{id} rdfs:label ?name ;
                              data:description ?description ;
                              data:category ?category ;
                              data:atCity ?city ;
                              data:price ?price ;
                              data:rating ?rating ;
                              data:timeSpentInMinutes ?timeSpent ;
                              data:latitude ?latitude ;
                              data:longitude ?longitude .
    }}
    """
    results = query_graphdb(sparql_query)

    destination_data = None
    if results and "results" in results:
        bindings = results["results"]["bindings"]
        if bindings:
            row = bindings[0] 
            destination_data = {
                "name": row["name"]["value"],
                "description": row["description"]["value"],
                "category": row["category"]["value"],
                "city": row["city"]["value"].split("/")[-1],  
                "price": row["price"]["value"],
                "rating": row["rating"]["value"],
                "timeSpent": row["timeSpent"]["value"],
                "latitude": float(row["latitude"]["value"]),
                "longitude": float(row["longitude"]["value"]),
            }
    else:
        print(f"No results found for destination ID: {id}")

    return render(request, 'destination-page.html', {'destination': destination_data, 'destination_id': id})
