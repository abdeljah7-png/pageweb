from django.urls import path
from django.contrib.auth import views as auth_views
from .views import home, description, utilisation, download_dossier

urlpatterns = [
    path('', home, name='home'),

    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('description/', description, name='description'),
    path('utilisation/', utilisation, name='utilisation'),
    path('telecharger/', download_dossier, name='download_dossier'),
]