from django.urls import path
from . import views

urlpatterns = [
    path("test/", views.home, name="home"),
    path("", views.search_from_desc, name="search_from_desc")
]