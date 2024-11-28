from django.shortcuts import render, HttpResponse
from SPARQLWrapper import SPARQLWrapper, JSON
from rdfstore.views import query_graphdb

GRAPHDB_ENDPOINT = "http://localhost:7200/repositories/traveller"

# Create your views here.
def home(request):
    return HttpResponse("hello world!")

def search_from_desc(request):
    search_term = request.GET.get('search', '').lower()  

    sparql_query = f"""
    PREFIX data: <http://tourism-2024.org/data/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?tourismArea ?name ?description
    WHERE {{
        ?tourismArea data:description ?description .
        FILTER(CONTAINS(LCASE(?description), "{search_term}"))
        BIND(?tourismArea AS ?entity)
        BIND(STRAFTER(STR(?entity), "http://tourism-2024.org/data/") AS ?name)
    }}
    """

    results = query_graphdb(sparql_query)

    result_list = []
    if results and "results" in results:
        for row in results["results"]["bindings"]:
            result_list.append({
                "tourismArea": row["tourismArea"]["value"],
                "name": row["name"]["value"],
                "description": row["description"]["value"]
            })
    else:
        print("No results found or error in query execution.")

    print(result_list)
    return render(request, 'traveller_data.html', {'results': result_list, 'search_term': search_term})
