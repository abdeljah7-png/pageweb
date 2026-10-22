from django.urls import path

from . import views

app_name = "remarques"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("nouvelle/", views.nouvelle, name="nouvelle"),
    path("mes/", views.mes_remarques, name="mes"),
    path("profil/", views.profil, name="profil"),
    path("idees/", views.idees, name="idees"),
    path("idees/<int:pk>/moi-aussi/", views.moi_aussi, name="moi_aussi"),
    path("nouveautes/", views.nouveautes, name="nouveautes"),
    path("tableau/", views.tableau, name="tableau"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/capture/", views.capture, name="capture"),
]
