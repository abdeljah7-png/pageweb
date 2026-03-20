from django.urls import path
from .views import home,description,utilisation
from . import views


urlpatterns = [
    path('', home, name='home'),
    path('description', description, name='description'),
    path('utilisation', utilisation, name='utilisation'),
    path('telecharger/', views.download_dossier, name='download_dossier'),
]