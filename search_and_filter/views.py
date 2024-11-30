from django.shortcuts import render
from rdfstore.views import query_graphdb

def search_from_desc(request):
    search_term = request.GET.get('search', '').lower()
    selected_categories = request.GET.getlist('categories')
    results = None

    sparql_query = f"""
    PREFIX data: <http://tourism-2024.org/data/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?tourismArea ?name ?category ?city ?price ?rating
    WHERE {{
        ?tourismArea data:description ?description ;
                    rdfs:label ?name ;
                    data:category ?category ;
                    data:atCity ?city ;
                    data:price ?price ;
                    data:rating ?rating .
        
        FILTER(CONTAINS(LCASE(?description), "{search_term}"))
    
    """

    if selected_categories:
        categories_filter = "FILTER (?category IN (" + ",".join([f'"{category}"' for category in selected_categories]) + "))"
        sparql_query += f"    {categories_filter}"
    
    sparql_query += "}"

    results = query_graphdb(sparql_query)

    result_list = []
    if results and "results" in results:
        for row in results["results"]["bindings"]:
            result_list.append({
                "tourismArea": _get_value(row, "tourismArea"),
                "name": _get_value(row, "name"),
                "description": _get_value(row, "description"),
                "category": _get_value(row, "category"),
                "city": _get_value(row, "city", lambda v: v.split("/")[-1]),  # Extract after slash
                "price": _get_value(row, "price"),
                "rating": _get_value(row, "rating"),
            })
    else:
        print("No results found or error in query execution.")

    return render(request, 'search-page.html', {
        'results': result_list,
        'search_term': search_term,
        'selected_categories': selected_categories  
    })

def _get_value(row, key, transform=None):
    value = row.get(key, {}).get("value", "-")
    return transform(value) if transform and value != "-" else value