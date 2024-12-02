from django.shortcuts import render, HttpResponse
from SPARQLWrapper import SPARQLWrapper, JSON
from rdfstore.views import query_graphdb
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests

# Create your views here.
def search_package(request):
    search_term = request.GET.get('search', '').lower()  

    sparql_query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX data: <http://localhost:7200/data/>

        SELECT 
            ?PKGID 
            ?firstPlaceID ?secondPlaceID ?thirdPlaceID ?fourthPlaceID ?fifthPlaceID 
            ?Place1 ?Place2 ?Place3 ?Place4 ?Place5 ?location ?locationLabel
        WHERE {{
            optional {{
                ?PKGID data:location ?location .
                ?location rdfs:label ?locationLabel
            }}

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
            first_place_iri = row["firstPlaceID"]["value"]
            second_place_iri = row["secondPlaceID"]["value"]
            third_place_iri = row["thirdPlaceID"]["value"]
            fourth_place_iri = row["fourthPlaceID"]["value"]
            fifth_place_iri = row["fifthPlaceID"]["value"]
            temp_dict = {
                "package": pkg_id,
                "place1": row["Place1"]["value"],
                "place2": row["Place2"]["value"],
                "place3": row["Place3"]["value"],
                "place4": row["Place4"]["value"],
                "place5": row["Place5"]["value"],
                "place1_iri": first_place_iri,
                "place2_iri": second_place_iri,
                "place3_iri": third_place_iri,
                "place4_iri": fourth_place_iri,
                "place5_iri": fifth_place_iri,
                "place1_code" : first_place_iri.rsplit('/', 1)[-1],
                "place2_code" : second_place_iri.rsplit('/', 1)[-1],
                "place3_code" : third_place_iri.rsplit('/', 1)[-1],
                "place4_code" : fourth_place_iri.rsplit('/', 1)[-1],
                "place5_code" : fifth_place_iri.rsplit('/', 1)[-1],
            }
            if "location" in row.keys():
                temp_dict["location"] = row["locationLabel"]["value"]
                temp_dict["location_iri"] = row["location"]["value"]
            result_list.append(temp_dict)
    else:
        print("No results found or error in query execution.")

    return render(request, 'package_data.html', {'results': result_list, 'search_term': search_term})

@csrf_exempt
def fetch_rdf_data(request):
    if request.method == "POST":
        place_iri = request.POST.get("place_iri")
        endpoint = "http://localhost:7200/repositories/traveller"
        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX data: <http://localhost:7200/data/>

            SELECT ?wst ?desc ?category ?rating ?cityLabel
            WHERE {{
                ?wst a <https://www.wikidata.org/wiki/Q1200957> .
                FILTER(?wst = <{place_iri}>) .
                OPTIONAL {{?wst data:description ?desc .}}
                OPTIONAL {{?wst data:category ?category .}}
                OPTIONAL {{?wst data:rating ?rating .}}
                OPTIONAL {{
                    ?wst data:atCity ?city .
                    ?city rdfs:label ?cityLabel .
                    }}
            }}
        """
        headers = {"Accept": "application/sparql-results+json"}
        response = requests.get(endpoint, params={"query": query}, headers=headers)

        if response.status_code == 200:
            rdf_data = response.json()
            bindings = rdf_data.get("results", {}).get("bindings", [{}])[0]
            return JsonResponse({
                "description": bindings.get("desc", {}).get("value", "No description available."),
                "category": bindings.get("category", {}).get("value", "No category available."),
                "rating": bindings.get("rating", {}).get("value", "No rating available."),
                "cityLabel": bindings.get("cityLabel", {}).get("value", "No city available."),
            })
        else:
            return JsonResponse({"error": "Failed to fetch data from RDF store."}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method."}, status=405)