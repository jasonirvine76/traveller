from django.shortcuts import render
from rdfstore.views import query_graphdb
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import datetime

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
            ?price1 ?price1WD ?price1WN
            ?price2 ?price2WD ?price2WN
            ?price3 ?price3WD ?price3WN
            ?price4 ?price4WD ?price4WN
            ?price5 ?price5WD ?price5WN
        WHERE {{
            OPTIONAL {{
                ?PKGID data:location ?location .
                ?location rdfs:label ?locationLabel
            }}

            ?PKGID data:hasFirstPlace ?firstPlaceID .
            OPTIONAL {{ ?firstPlaceID rdfs:label ?firstPlaceLabel . }}
            OPTIONAL {{ ?firstPlaceID data:price ?price1 }}
            OPTIONAL {{ ?firstPlaceID data:weekdayPrice ?price1WD }}
            OPTIONAL {{ ?firstPlaceID data:weekendHolidayPrice ?price1WN }}
            BIND(COALESCE(?firstPlaceLabel, "") AS ?Place1)
            
            ?PKGID data:hasSecondPlace ?secondPlaceID .
            OPTIONAL {{ ?secondPlaceID rdfs:label ?secondPlaceLabel . }}
            OPTIONAL {{ ?secondPlaceID data:price ?price2 }}
            OPTIONAL {{ ?secondPlaceID data:weekdayPrice ?price2WD }}
            OPTIONAL {{ ?secondPlaceID data:weekendHolidayPrice ?price2WN }}
            BIND(COALESCE(?secondPlaceLabel, "") AS ?Place2)
            
            ?PKGID data:hasThirdPlace ?thirdPlaceID .
            OPTIONAL {{ ?thirdPlaceID rdfs:label ?thirdPlaceLabel . }}
            OPTIONAL {{ ?thirdPlaceID data:price ?price3 }}
            OPTIONAL {{ ?thirdPlaceID data:weekdayPrice ?price3WD }}
            OPTIONAL {{ ?thirdPlaceID data:weekendHolidayPrice ?price3WN }}
            BIND(COALESCE(?thirdPlaceLabel, "") AS ?Place3)
            
            ?PKGID data:hasFourthPlace ?fourthPlaceID .
            OPTIONAL {{ ?fourthPlaceID rdfs:label ?fourthPlaceLabel . }}
            OPTIONAL {{ ?fourthPlaceID data:price ?price4 }}
            OPTIONAL {{ ?fourthPlaceID data:weekdayPrice ?price4WD }}
            OPTIONAL {{ ?fourthPlaceID data:weekendHolidayPrice ?price4WN }}
            BIND(COALESCE(?fourthPlaceLabel, "") AS ?Place4)
            
            ?PKGID data:hasFifthPlace ?fifthPlaceID .
            OPTIONAL {{ ?fifthPlaceID rdfs:label ?fifthPlaceLabel . }}
            OPTIONAL {{ ?fifthPlaceID data:price ?price5 }}
            OPTIONAL {{ ?fifthPlaceID data:weekdayPrice ?price5WD }}
            OPTIONAL {{ ?fifthPlaceID data:weekendHolidayPrice ?price5WN }}
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
            temp_dict = {
                "package": pkg_id,
                "place1": row.get("Place1", {}).get("value", ""),
                "place2": row.get("Place2", {}).get("value", ""),
                "place3": row.get("Place3", {}).get("value", ""),
                "place4": row.get("Place4", {}).get("value", ""),
                "place5": row.get("Place5", {}).get("value", ""),
                "place1_iri": row.get("firstPlaceID", {}).get("value", ""),
                "place2_iri": row.get("secondPlaceID", {}).get("value", ""),
                "place3_iri": row.get("thirdPlaceID", {}).get("value", ""),
                "place4_iri": row.get("fourthPlaceID", {}).get("value", ""),
                "place5_iri": row.get("fifthPlaceID", {}).get("value", ""),
                "place1_code": row.get("firstPlaceID", {}).get("value", "").rsplit('/', 1)[-1],
                "place2_code": row.get("secondPlaceID", {}).get("value", "").rsplit('/', 1)[-1],
                "place3_code": row.get("thirdPlaceID", {}).get("value", "").rsplit('/', 1)[-1],
                "place4_code": row.get("fourthPlaceID", {}).get("value", "").rsplit('/', 1)[-1],
                "place5_code": row.get("fifthPlaceID", {}).get("value", "").rsplit('/', 1)[-1],
            }

            cumulative_price = 0
            today = datetime.datetime.today()
            is_weekend = today.weekday() >= 5  # Saturday (5) or Sunday (6)

            # Helper function to process a place's price
            def add_price(row, base_key):
                price = row.get(f"{base_key}", {}).get("value")
                price_wd = row.get(f"{base_key}WD", {}).get("value")
                price_wn = row.get(f"{base_key}WN", {}).get("value")

                if price:
                    return int(float(price))
                elif is_weekend and price_wn:
                    return int(float(price_wn))
                elif not is_weekend and price_wd:
                    return int(float(price_wd))
                return 0
            
            # Calculate cumulative price
            cumulative_price += add_price(row, "price1")
            cumulative_price += add_price(row, "price2")
            cumulative_price += add_price(row, "price3")
            cumulative_price += add_price(row, "price4")
            cumulative_price += add_price(row, "price5")

            temp_dict["total_price"] = cumulative_price
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