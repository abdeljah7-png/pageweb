from django.urls import path
from .views import home,description,utilisation
from . import views


urlpatterns = [
    path('utilisation', views.utilisation, name='utilisation'),
    path('', views.home, name='home'),
    path('description/', views.description, name='description'),
    path('telecharger/', views.download_dossier, name='download_dossier'),

]

