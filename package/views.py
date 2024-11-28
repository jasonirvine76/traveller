from django.shortcuts import render, HttpResponse
from SPARQLWrapper import SPARQLWrapper, JSON
from rdfstore.views import query_graphdb

GRAPHDB_ENDPOINT = "http://localhost:7200/repositories/traveller"

# Create your views here.
def search_package(request):
    search_term = request.GET.get('search', '').lower()  

    sparql_query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX data: <http://tourism-2024.org/data/>
        PREFIX onto: <http://www.ontotext.com/>

        SELECT 
            ?PKGID 
            ?firstPlaceID ?secondPlaceID ?thirdPlaceID ?fourthPlaceID ?fifthPlaceID 
            ?Place1 ?Place2 ?Place3 ?Place4 ?Place5
        WHERE {{
            ?PKGID data:hasFirstPlace ?firstPlaceID .
            OPTIONAL {{?firstPlaceID rdfs:label ?firstPlaceLabel . }}
            BIND(COALESCE(?firstPlaceLabel, "") AS ?Place1)
            
            ?PKGID data:hasSecondPlace ?secondPlaceID .
            OPTIONAL {{ ?secondPlaceID rdfs:label ?secondPlaceLabel . }}
            BIND(COALESCE(?secondPlaceLabel, "") AS ?Place2)
            
            ?PKGID data:hasThirdPlace ?thirdPlaceID .
            OPTIONAL {{ ?thirdPlaceID rdfs:label ?thirdPlaceLabel . }}
            BIND(COALESCE(?thirdPlaceLabel, "") AS ?Place3)
            
            ?PKGID data:hasFourthPlace ?fourthPlaceID .
            OPTIONAL {{ ?fourthPlaceID rdfs:label ?fourthPlaceLabel . }}
            BIND(COALESCE(?fourthPlaceLabel, "") AS ?Place4)
            
            ?PKGID data:hasFifthPlace ?fifthPlaceID .
            OPTIONAL {{ ?fifthPlaceID rdfs:label ?fifthPlaceLabel . }}
            BIND(COALESCE(?fifthPlaceLabel, "") AS ?Place5)

            FILTER (
                CONTAINS(LCASE(?Place1), "{search_term}") ||
                CONTAINS(LCASE(?Place2), "{search_term}") ||
                CONTAINS(LCASE(?Place3), "{search_term}") ||
                CONTAINS(LCASE(?Place4), "{search_term}") ||
                CONTAINS(LCASE(?Place5), "{search_term}")
            )
        }}
    """

    results = query_graphdb(sparql_query)

    result_list = []
    if results and "results" in results:
        for row in results["results"]["bindings"]:
            pkg_id = row["PKGID"]["value"].rsplit('/', 1)[-1]
            result_list.append({
                "package": pkg_id,
                "place1": row["Place1"]["value"],
                "place2": row["Place2"]["value"],
                "place3": row["Place3"]["value"],
                "place4": row["Place4"]["value"],
                "place5": row["Place5"]["value"],
            })
    else:
        print("No results found or error in query execution.")

    print(result_list)
    return render(request, 'package_data.html', {'results': result_list, 'search_term': search_term})