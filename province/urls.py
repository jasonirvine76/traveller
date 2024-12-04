from django.urls import path
from .views import get_province_by_name

urlpatterns = [
    path('<str:name>', get_province_by_name, name='get_province'),
]