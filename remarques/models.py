import os
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone


def stockage_captures():
    """Les captures sont stockées hors de tout dossier public.
    Elles ne sont servies que par la vue protégée `capture`."""
    dossier = getattr(settings, "REMARQUES_CAPTURES_DIR", None) or os.path.join(
        str(getattr(settings, "BASE_DIR", ".")), "captures_privees"
    )
    return FileSystemStorage(location=str(dossier))


def chemin_capture(instance, nom_fichier):
    ext = os.path.splitext(nom_fichier)[1].lower()
    return "%s/%s%s" % (timezone.now().strftime("%Y/%m"), uuid.uuid4().hex, ext)


TYPES = [
    ("calcul", "Erreur de calcul"),
    ("arrondi", "Écart d'arrondi"),
    ("situation", "Situation particulière d'un dossier"),
    ("formulaire", "Défaillance d'un formulaire"),
    ("bug", "Bug, plantage ou lenteur"),
    ("idee", "Idée pour gagner du temps"),
]

STATUTS = [
    ("nouvelle", "Nouvelle"),
    ("etudiee", "Étudiée"),
    ("reproduite", "Reproduite"),
    ("a_clarifier", "Règle à clarifier"),
    ("planifiee", "Planifiée"),
    ("corrigee", "Corrigée"),
    ("calcul_correct", "Calcul correct (explication donnée)"),
    ("refusee", "Non retenue"),
]

IMPACTS = [
    ("bloquant", "Bloquant : je ne peux pas continuer"),
    ("genant", "Gênant : je contourne"),
    ("mineur", "Mineur"),
]

SITUATIONS = [
    ("fermeture", "Fermeture de dossier"),
    ("cessation", "Cessation d'activité"),
    ("deces", "Décès"),
    ("transfert", "Transfert"),
    ("fusion", "Fusion"),
    ("faillite", "Faillite / liquidation"),
    ("redressement", "Redressement"),
    ("changement_regime", "Changement de régime en cours d'année"),
    ("autre", "Autre"),
]

SOURCES = [
    ("manuel", "Calcul manuel"),
    ("ancien_dossier", "Ancien dossier"),
    ("texte_loi", "Texte de loi"),
    ("collegue", "Collègue"),
    ("autre", "Autre"),
]

ARRONDIS = [
    ("dinar", "Au dinar"),
    ("millime", "Au millime"),
    ("superieur", "Au supérieur"),
    ("inferieur", "À l'inférieur"),
    ("inconnu", "Je ne sais pas"),
]

MONTANTS = [
    ("principal", "Principal"),
    ("pen_fix", "Pénalité fixe"),
    ("pen_var", "Pénalité variable"),
    ("total", "Total"),
]

VOLUMES = [
    ("moins10", "Moins de 10 dossiers par semaine"),
    ("10_30", "10 à 30"),
    ("30_100", "30 à 100"),
    ("plus100", "Plus de 100"),
]


class Centre(models.Model):
    nom = models.CharField("Centre", max_length=150, unique=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Bureau(models.Model):
    centre = models.ForeignKey(Centre, on_delete=models.PROTECT, related_name="bureaux")
    nom = models.CharField("Bureau", max_length=150)

    class Meta:
        ordering = ["centre__nom", "nom"]
        unique_together = [("centre", "nom")]

    def __str__(self):
        return "%s (%s)" % (self.nom, self.centre.nom)


class Module(models.Model):
    nom = models.CharField("Module ou écran", max_length=120, unique=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom


class VersionA3H(models.Model):
    numero = models.CharField("Numéro de version", max_length=30, unique=True)
    date = models.DateField("Date", default=timezone.localdate)
    notes = models.TextField("Ce que contient cette version", blank=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "version d'A3H"
        verbose_name_plural = "versions d'A3H"

    def __str__(self):
        return self.numero


class ProfilAgent(models.Model):
    """Rempli une seule fois par agent ; s'attache à toutes ses remarques."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profil_remarques"
    )
    nom_agent = models.CharField("Nom et prénom", max_length=120)
    bureau = models.ForeignKey(Bureau, on_delete=models.PROTECT, verbose_name="Bureau")
    service = models.CharField(
        "Poste ou service", max_length=120, blank=True,
        help_text="Par exemple : taxation, vérification, recouvrement.",
    )
    dossiers_frequents = models.TextField(
        "Types de dossiers traités le plus souvent", blank=True
    )
    volume_hebdo = models.CharField(
        "Volume approximatif", max_length=10, choices=VOLUMES, blank=True
    )
    usage_a3h = models.TextField("Ce que je fais le plus dans A3H", blank=True)
    fait_a_la_main = models.TextField(
        "Ce que je fais encore à la main ou sur Excel", blank=True
    )
    poste_travail = models.CharField(
        "Mon poste de travail", max_length=200, blank=True,
        help_text="Windows, taille d'écran, imprimante, qualité de la connexion.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "profil d'agent"
        verbose_name_plural = "profils d'agents"

    def __str__(self):
        return "%s - %s" % (self.nom_agent, self.bureau)


# Champs facultatifs affichés dans le détail d'une remarque.
CHAMPS_DETAIL = [
    "ecran", "code_impot", "periode", "regime", "montant_concerne",
    "valeurs_saisies", "resultat_obtenu", "resultat_attendu", "source_attendu",
    "regle_arrondi", "situation", "date_evenement", "date_calcul",
    "a3h_a_fait", "aurait_du", "version_a3h",
]


class Remarque(models.Model):
    # Qui
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="remarques",
    )
    nom_agent = models.CharField("Agent", max_length=120)
    bureau = models.ForeignKey(Bureau, on_delete=models.PROTECT, related_name="remarques")

    # Les trois champs obligatoires
    module = models.ForeignKey(Module, on_delete=models.PROTECT, verbose_name="Module concerné")
    type_remarque = models.CharField("Type de remarque", max_length=12, choices=TYPES)
    description = models.TextField("Description")

    impact = models.CharField("Impact sur mon travail", max_length=10, choices=IMPACTS, blank=True)

    # Calcul
    code_impot = models.CharField("Code impôt concerné", max_length=40, blank=True)
    periode = models.CharField("Période ou exercice", max_length=60, blank=True)
    regime = models.CharField("Régime ou type de contribuable", max_length=80, blank=True)
    valeurs_saisies = models.TextField("Valeurs saisies", blank=True)
    resultat_obtenu = models.CharField("Résultat obtenu avec A3H", max_length=120, blank=True)
    resultat_attendu = models.CharField("Résultat attendu", max_length=120, blank=True)
    source_attendu = models.CharField(
        "D'où vient le résultat attendu", max_length=15, choices=SOURCES, blank=True
    )
    # Arrondi
    montant_concerne = models.CharField("Montant concerné", max_length=10, choices=MONTANTS, blank=True)
    regle_arrondi = models.CharField("Règle d'arrondi attendue", max_length=10, choices=ARRONDIS, blank=True)
    # Situation particulière
    situation = models.CharField("Situation du contribuable", max_length=20, choices=SITUATIONS, blank=True)
    date_evenement = models.DateField("Date de l'événement", null=True, blank=True)
    date_calcul = models.DateField("Date de calcul", null=True, blank=True)
    a3h_a_fait = models.TextField("Ce que A3H a fait", blank=True)
    aurait_du = models.TextField("Ce qu'il aurait dû faire", blank=True)
    # Formulaire
    ecran = models.CharField("Formulaire ou écran concerné", max_length=150, blank=True)
    # Autre
    version_a3h = models.CharField("Version d'A3H", max_length=30, blank=True)
    capture = models.FileField(
        "Capture d'écran", upload_to=chemin_capture, storage=stockage_captures, blank=True
    )

    # Suivi (rempli par l'administrateur)
    statut = models.CharField("Statut", max_length=15, choices=STATUTS, default="nouvelle")
    reponse = models.TextField("Réponse visible par l'agent", blank=True)
    version_correction = models.ForeignKey(
        VersionA3H, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="remarques_traitees", verbose_name="Version qui traite cette remarque",
    )
    cas_de_test = models.BooleanField(
        "Cas de test à rejouer avant chaque version", default=False
    )
    doublon_de = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="doublons", verbose_name="Même demande que la remarque n°",
    )
    note_interne = models.TextField("Note interne (non visible par l'agent)", blank=True)

    created_at = models.DateTimeField("Reçue le", auto_now_add=True)
    updated_at = models.DateTimeField("Mise à jour le", auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return "#%s %s" % (self.pk, self.titre)

    @property
    def titre(self):
        texte = " ".join(self.description.split())
        return texte if len(texte) <= 80 else texte[:77] + "..."

    def champs_renseignes(self):
        sortie = []
        for nom in CHAMPS_DETAIL:
            champ = self._meta.get_field(nom)
            valeur = getattr(self, nom)
            if valeur in (None, ""):
                continue
            if champ.choices:
                valeur = getattr(self, "get_%s_display" % nom)()
            sortie.append((champ.verbose_name, valeur))
        return sortie


class MoiAussi(models.Model):
    remarque = models.ForeignKey(Remarque, on_delete=models.CASCADE, related_name="moi_aussi")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("remarque", "user")]
