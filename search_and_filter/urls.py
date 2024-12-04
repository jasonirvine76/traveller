from django.urls import path
from . import views

urlpatterns = [
    path("", views.search_from_desc, name="search_from_desc")
]