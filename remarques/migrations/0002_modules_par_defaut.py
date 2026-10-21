from django.db import migrations

MODULES = [
    "Pointage impôts", "Calcul impôts mensuels", "Calcul forfait", "Calcul réel",
    "Calcul société", "Déclaration", "Vérification",
    "Taxation d'office : défauts", "Taxation d'office : préliminaires",
    "Taxation d'office : ponctuelles", "Taxation d'office : approfondies",
    "Données : bureau", "Données : impôts", "Données : contribuables",
    "Données : obligation fiscale", "Dashboard",
    "Application Forfait", "Application Réel", "Application Vérification",
    "Installation ou mise à jour", "Autre",
]


def creer_modules(apps, schema_editor):
    Module = apps.get_model("remarques", "Module")
    for i, nom in enumerate(MODULES, start=1):
        Module.objects.get_or_create(nom=nom, defaults={"ordre": i * 10})


class Migration(migrations.Migration):
    dependencies = [("remarques", "0001_initial")]
    operations = [migrations.RunPython(creer_modules, migrations.RunPython.noop)]
