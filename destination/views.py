from django.shortcuts import render
from destination.query import get_wikidata_by_name
from rdfstore.views import query_graphdb


def get_destination_by_id(request, id):
    sparql_query = f"""
    PREFIX data: <http://localhost:7200/data/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?name ?description ?category ?city ?price ?rating ?latitude ?longitude ?timeSpent ?user ?userRating ?userFrom ?userAge ?userId ?alamat ?weekendHolidayPrice ?weekdayPrice
    WHERE {{
        data:{id} rdfs:label ?name ;
                 data:description ?description ;
                 data:category ?category ;
                 data:atCity ?city ;
                 data:rating ?rating ;
                 data:latitude ?latitude ;
                 data:longitude ?longitude .
        OPTIONAL {{ data:{id} data:price ?price . }}
        OPTIONAL {{ data:{id} data:alamat ?alamat . }}
        OPTIONAL {{ data:{id} data:weekendHolidayPrice ?weekendHolidayPrice . }}
        OPTIONAL {{ data:{id} data:weekdayPrice ?weekdayPrice . }}
        OPTIONAL {{ data:{id} data:timeSpentInMinutes ?timeSpent . }}
        OPTIONAL {{
            data:{id} data:hasRating ?userRatingNode .
            ?userRatingNode data:user ?user ;
                            data:rating ?userRating .
            OPTIONAL {{ ?user data:from ?userFrom . }}
            OPTIONAL {{ ?user data:hasAge ?userAge . }}
            OPTIONAL {{ ?user data:hasId ?userId . }}
        }}
    }}
    """
    results = query_graphdb(sparql_query)
    destination_data = None
    user_ratings = []
    if results and "results" in results:
        bindings = results["results"]["bindings"]
        if bindings:
            row = bindings[0]
            wikidata_data = get_wikidata_by_name(_get_value(row, "name"), "id")
            if not wikidata_data:
                wikidata_data = get_wikidata_by_name(_get_value(row, "name"), "en")
            print(wikidata_data)
            destination_data = {
                "name": _get_value(row, "name"),
                "description": _get_value(row, "description"),
                "category": _get_value(row, "category"),
                "city": _get_value(row, "city", lambda v: v.split("/")[-1]),
                "price": _get_value(row, "price") if row.get("price") else (
                    f"Weekend: {_get_value(row, 'weekendHolidayPrice')} / Weekday: {_get_value(row, 'weekdayPrice')}"
                    if row.get("weekendHolidayPrice") or row.get("weekdayPrice")
                    else "-"
                ),
                "rating": _get_value(row, "rating"),
                "timeSpent": _get_value(row, "timeSpent"),
                "latitude": _get_value(row, "latitude", float),
                "longitude": _get_value(row, "longitude", float),
                "alamat": _get_value(row, "alamat"),
                "image": wikidata_data.get("image") if wikidata_data else None,
                "official_website":wikidata_data.get("official_website") if wikidata_data else None,
            }

            for binding in bindings:
                user = binding.get("user", {}).get("value", "-").split("/")[-1]
                user_rating = binding.get("userRating", {}).get("value", "-")
                user_from = binding.get("userFrom", {}).get("value", "-").split("/")[-1]  
                user_age = binding.get("userAge", {}).get("value", "-")
                user_id = binding.get("userId", {}).get("value", "-")

                if user != "-" and user_rating != "-":
                    user_ratings.append({
                        "user": user,
                        "rating": user_rating,
                        "from": user_from,  
                        "age": user_age,
                        "id": user_id,
                    })

    return render(request, 'destination-page.html', {'destination': destination_data, 'user_ratings': user_ratings, 'destination_id': id})


def _get_value(row, key, transform=None):
    value = row.get(key, {}).get("value", "-")
    return transform(value) if transform and value != "-" else value