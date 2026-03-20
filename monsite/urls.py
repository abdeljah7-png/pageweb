from django.urls import path
from .views import home, description, utilisation, download_dossier

urlpatterns = [
    path('', home, name='home'),
    path('description/', description, name='description'),
    path('utilisation/', utilisation, name='utilisation'),  # <-- slash ajouté
    path('telecharger/', download_dossier, name='download_dossier'),
]