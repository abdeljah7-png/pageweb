import datetime

from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Bureau, Centre, MoiAussi, Module, ProfilAgent, Remarque, VersionA3H,
)


@admin.action(description="Exporter la sélection en Excel (.xlsx)")
def exporter_excel(modeladmin, request, queryset):
    try:
        from openpyxl import Workbook
    except ImportError:
        modeladmin.message_user(request, "Installez openpyxl : pip install openpyxl", level="error")
        return None
    wb = Workbook()
    ws = wb.active
    ws.title = "Remarques"
    champs = [
        f for f in Remarque._meta.get_fields()
        if getattr(f, "concrete", False) and not f.many_to_many and f.name not in ("auteur", "capture")
    ]
    ws.append([f.verbose_name for f in champs] + ["Demandes identiques"])
    qs = queryset.select_related("bureau__centre", "module", "version_correction", "doublon_de")
    qs = qs.annotate(_nb=Count("doublons", distinct=True) + Count("moi_aussi", distinct=True))
    for r in qs:
        ligne = []
        for f in champs:
            if f.choices:
                v = getattr(r, "get_%s_display" % f.name)()
            else:
                v = getattr(r, f.name)
            if f.name == "bureau" and v is not None:
                v = "%s / %s" % (v.centre.nom, v.nom)
            elif hasattr(v, "tzinfo") and v is not None:
                v = v.replace(tzinfo=None) if v.tzinfo else v
            elif v is not None and not isinstance(v, (str, int, float, bool, datetime.date, datetime.datetime)):
                v = str(v)
            ligne.append(v)
        ligne.append(r._nb)
        ws.append(ligne)
    ws.freeze_panes = "A2"
    rep = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    rep["Content-Disposition"] = 'attachment; filename="remarques_a3h.xlsx"'
    wb.save(rep)
    return rep


@admin.action(description="Marquer comme étudiée")
def marquer_etudiee(modeladmin, request, queryset):
    queryset.filter(statut="nouvelle").update(statut="etudiee")


@admin.action(description="Marquer comme cas de test")
def marquer_cas_test(modeladmin, request, queryset):
    queryset.update(cas_de_test=True)


@admin.register(Remarque)
class RemarqueAdmin(admin.ModelAdmin):
    list_display = (
        "id", "created_at", "centre", "bureau", "nom_agent", "module",
        "type_remarque", "impact", "apercu", "statut", "demandes", "cas_de_test",
    )
    list_display_links = ("id", "apercu")
    list_filter = (
        "statut", "type_remarque", "module", "impact", "cas_de_test",
        "bureau__centre", "bureau", "version_correction",
    )
    search_fields = ("description", "nom_agent", "code_impot", "valeurs_saisies", "reponse", "id")
    date_hierarchy = "created_at"
    list_select_related = ("bureau__centre", "module")
    autocomplete_fields = ("doublon_de",)
    actions = [exporter_excel, marquer_etudiee, marquer_cas_test]
    readonly_fields = ("auteur", "nom_agent", "bureau", "created_at", "updated_at", "lien_capture")
    fieldsets = (
        ("Suivi : votre décision", {
            "fields": ("statut", "reponse", "version_correction", "cas_de_test", "doublon_de", "note_interne"),
        }),
        ("Qui et quand", {"fields": ("auteur", "nom_agent", "bureau", "created_at", "updated_at")}),
        ("La remarque", {"fields": ("module", "type_remarque", "impact", "description")}),
        ("Calcul", {"classes": ("collapse",), "fields": (
            "code_impot", "periode", "regime", "valeurs_saisies",
            "resultat_obtenu", "resultat_attendu", "source_attendu",
            "montant_concerne", "regle_arrondi")}),
        ("Situation particulière", {"classes": ("collapse",), "fields": (
            "situation", "date_evenement", "date_calcul", "a3h_a_fait", "aurait_du")}),
        ("Formulaire et divers", {"classes": ("collapse",), "fields": (
            "ecran", "version_a3h", "capture", "lien_capture")}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_nb=Count("doublons", distinct=True) + Count("moi_aussi", distinct=True))

    @admin.display(description="Centre", ordering="bureau__centre__nom")
    def centre(self, obj):
        return obj.bureau.centre.nom

    @admin.display(description="Remarque")
    def apercu(self, obj):
        return obj.titre

    @admin.display(description="Demandes identiques", ordering="_nb")
    def demandes(self, obj):
        return 1 + obj._nb

    @admin.display(description="Capture")
    def lien_capture(self, obj):
        if not obj.pk or not obj.capture:
            return "Aucune"
        return format_html('<a href="{}" target="_blank">Voir la capture</a>',
                           reverse("remarques:capture", args=[obj.pk]))


@admin.register(Centre)
class CentreAdmin(admin.ModelAdmin):
    search_fields = ("nom",)


@admin.register(Bureau)
class BureauAdmin(admin.ModelAdmin):
    list_display = ("nom", "centre")
    list_filter = ("centre",)
    search_fields = ("nom", "centre__nom")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("nom", "ordre")
    list_editable = ("ordre",)


@admin.register(VersionA3H)
class VersionAdmin(admin.ModelAdmin):
    list_display = ("numero", "date", "nb_remarques")

    @admin.display(description="Remarques traitées")
    def nb_remarques(self, obj):
        return obj.remarques_traitees.count()


@admin.register(ProfilAgent)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ("nom_agent", "bureau", "service", "volume_hebdo", "user")
    list_filter = ("bureau__centre", "bureau", "volume_hebdo")
    search_fields = ("nom_agent", "service", "user__username")


admin.site.register(MoiAussi)
