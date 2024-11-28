from django.urls import path
from .views import get_destination_by_id

urlpatterns = [
    path('<str:id>', get_destination_by_id, name='destination_detail'),
]