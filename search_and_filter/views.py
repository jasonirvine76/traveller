from django.shortcuts import render
from rdfstore.views import query_graphdb

def search_from_desc(request):
    search_term = request.GET.get('search', '').lower()
    selected_categories = request.GET.getlist('categories')
    from_price = request.GET.get('from_price')
    to_price = request.GET.get('to_price')
    sort_name = request.GET.get('sort_name')
    sort_rating = request.GET.get('sort_rating')
    sort_price = request.GET.get('sort_price')

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
        
        FILTER(CONTAINS(LCASE(?description), "{search_term}") || CONTAINS(LCASE(?name), "{search_term}"))
    
    """

    if selected_categories:
        categories_filter = "FILTER (?category IN (" + ",".join([f'"{category}"' for category in selected_categories]) + "))"
        sparql_query += f"    {categories_filter}"

    if from_price:
        sparql_query += f"    FILTER (?price >= {from_price})\n"

    if to_price:
        sparql_query += f"    FILTER (?price <= {to_price})\n"

    sparql_query += "}"

    if sort_name or sort_rating or sort_price:
        sparql_query += "ORDER BY"
        if sort_name:
            sparql_query += f"{'ASC' if sort_name == 'asc' else 'DESC'}(?name)\n"

        if sort_price:
            sparql_query += f"{'ASC' if sort_price == 'asc' else 'DESC'}(?price)\n"

        if sort_rating:
            sparql_query += f"{'ASC' if sort_rating == 'asc' else 'DESC'}(?rating)\n"

    results = query_graphdb(sparql_query)

    result_list = []
    if results and "results" in results:
        for row in results["results"]["bindings"]:
            result_list.append({
                "id": _get_value(row, "tourismArea", lambda v: v.split("/")[-1]), # Extract after slash
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
        'selected_categories': selected_categories,
        'from_price': from_price,
        'to_price': to_price,
        'sort_name': sort_name,
        'sort_rating': sort_rating,
        'sort_price': sort_price
    })

def _get_value(row, key, transform=None):
    value = row.get(key, {}).get("value", "-")
    return transform(value) if transform and value != "-" else value