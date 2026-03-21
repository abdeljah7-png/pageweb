from django.urls import path
from .views import home, description, utilisation, download_dossier
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('', home, name='home'),  # page d'accueil principale
    path('description/', description, name='description'),
    path('utilisation/', utilisation, name='utilisation'),
    path('telecharger/', download_dossier, name='download_dossier'),
]

