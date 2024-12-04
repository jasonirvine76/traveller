from django.urls import path
from .views import get_regency_by_name

urlpatterns = [
    path('<str:name>', get_regency_by_name, name='get_regency'),
]