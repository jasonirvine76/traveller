from django.urls import path
from . import views

urlpatterns = [
    path("", views.traveller_data_view, name="traveller_data_view")
]