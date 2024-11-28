from django.shortcuts import render
from SPARQLWrapper import SPARQLWrapper, JSON

GRAPHDB_ENDPOINT = "http://localhost:7200/repositories/traveller"

def query_graphdb(query):
    sparql = SPARQLWrapper(GRAPHDB_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)  

    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        print(f"Error querying GraphDB: {e}")
        return None

def traveller_data_view(request):
    search_term = request.GET.get('search', '').lower()  

    sparql_query = f"""
    PREFIX data: <http://tourism-2024.org/data/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?tourismArea ?description
    WHERE {{
        ?tourismArea data:description ?description .
        FILTER(CONTAINS(LCASE(?description), "{search_term}"))
    }}
    """

    results = query_graphdb(sparql_query)

    result_list = []
    if results and "results" in results:
        for row in results["results"]["bindings"]:
            result_list.append({
                "tourismArea": row["tourismArea"]["value"],
                "description": row["description"]["value"]
            })
    else:
        print("No results found or error in query execution.")

    print(result_list)
    return render(request, 'traveller_data.html', {'results': result_list, 'search_term': search_term})
