import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Crée le compte administrateur à partir des variables A3H_ADMIN_USER et "
        "A3H_ADMIN_PASSWORD, s'il n'existe pas. Ne modifie jamais un compte existant."
    )

    def handle(self, *args, **options):
        nom = os.environ.get("A3H_ADMIN_USER", "").strip()
        mdp = os.environ.get("A3H_ADMIN_PASSWORD", "")
        if not nom or not mdp:
            self.stdout.write("init_admin : variables absentes, rien à faire.")
            return
        User = get_user_model()
        if User.objects.filter(username=nom).exists():
            self.stdout.write("init_admin : le compte « %s » existe déjà." % nom)
            return
        User.objects.create_superuser(username=nom, password=mdp)
        self.stdout.write(self.style.SUCCESS("init_admin : compte « %s » créé." % nom))
