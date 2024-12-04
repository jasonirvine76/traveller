from django.shortcuts import render
from .query import get_wikidata_by_name

def get_regency_by_name(request, name):
    regency_data = get_wikidata_by_name(name, lang="id")

    if not regency_data:
        return render(request, 'regency-page.html', {'error': 'Regency not found.'})

    regency_details = {
        "wikidata_id": regency_data.get("wikidata_id", "-"),
        "image": regency_data.get("image", "-"),
        "coordinates": regency_data.get("coordinates", "-"),
        "country": regency_data.get("country", "-"),
        "located_in": regency_data.get("located_in", "-"),
        "contains_entity": regency_data.get("contains_entity", "-"),
    }
    print(regency_details)
    return render(request, 'regency-page.html', {'regency_data': regency_details})
