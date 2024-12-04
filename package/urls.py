from django.urls import path
from . import views

urlpatterns = [
    path("", views.search_package, name="search_package"),
    path('fetch_rdf_data/', views.fetch_rdf_data, name='fetch_rdf_data')
]