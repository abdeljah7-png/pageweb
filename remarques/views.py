from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, F, Prefetch, Q
from django.utils import timezone
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ProfilForm, RemarqueForm
from .models import (
    STATUTS, TYPES, Bureau, MoiAussi, ProfilAgent, Remarque, VersionA3H,
)

staff_requis = user_passes_test(lambda u: u.is_active and u.is_staff)


def _profil(user):
    try:
        return user.profil_remarques
    except ProfilAgent.DoesNotExist:
        return None


def _suite_sure(request, defaut):
    cible = request.POST.get("next") or request.GET.get("next") or ""
    if cible and url_has_allowed_host_and_scheme(cible, allowed_hosts={request.get_host()}):
        return cible
    return defaut


STATUTS_UTILES = ["planifiee", "corrigee"]

# Une couleur par type, reprise des boutons d'A3H. Le texte aide l'agent à reconnaître son cas.
TUILES = [
    ("calcul", "#27ae60", "Un montant ne correspond pas à ce que vous attendiez."),
    ("arrondi", "#3498db", "Un écart d'un millime ou d'un dinar sur une ligne ou un total."),
    ("situation", "#f39c12", "Fermeture, cessation, décès : un cas que le calcul ne gère pas."),
    ("formulaire", "#8e44ad", "Un champ, un libellé ou une impression à corriger."),
    ("bug", "#c0392b", "Un plantage, un blocage ou une lenteur."),
    ("idee", "#17a2a0", "Ce qui vous ferait gagner du temps."),
]

# Étapes de la frise d'avancement : statut -> (position atteinte, libellé de l'étape finale)
ETAPES = {
    "nouvelle": (0, "Terminée"),
    "etudiee": (1, "Terminée"),
    "reproduite": (1, "Terminée"),
    "a_clarifier": (1, "Terminée"),
    "planifiee": (2, "Terminée"),
    "corrigee": (3, "Corrigée"),
    "calcul_correct": (3, "Explication donnée"),
    "refusee": (3, "Non retenue"),
}


def _frise(statut):
    position, final = ETAPES.get(statut, (0, "Terminée"))
    noms = ["Reçue", "Étudiée", "Planifiée", final]
    sortie = []
    for i, nom in enumerate(noms):
        etat = "fait" if i < position else ("courant" if i == position else "a_venir")
        if i == 3 and position == 3:
            etat = "fait"
        sortie.append({"nom": nom, "etat": etat})
    return sortie


def _non_lues(qs):
    return qs.filter(reponse_modifiee_le__isnull=False).filter(
        Q(vue_par_agent_le__isnull=True) | Q(vue_par_agent_le__lt=F("reponse_modifiee_le"))
    )


RETENUES = ("reproduite", "planifiee", "corrigee")


def _stats_agent(user):
    mes = Remarque.objects.filter(auteur=user)
    total = mes.count()
    traitees = mes.exclude(statut="nouvelle").count()
    retenues = mes.filter(statut__in=RETENUES).count()
    corrigees = mes.filter(statut="corrigee").count()
    badges = [
        {"titre": "Première remarque", "texte": "Vous avez pris la parole.", "ok": total >= 1},
        {"titre": "Observateur attentif", "texte": "5 remarques envoyées.", "ok": total >= 5},
        {"titre": "Œil de lynx", "texte": "Une de vos remarques a été retenue.", "ok": retenues >= 1},
        {"titre": "A3H grâce à vous", "texte": "Une de vos remarques est corrigée dans A3H.", "ok": corrigees >= 1},
    ]
    if total == 0:
        message = "Votre première remarque compte : chaque écart de calcul ou idée signalé rend A3H plus juste pour tous."
    elif corrigees:
        message = ("Une de vos remarques a déjà fait évoluer A3H. Bravo !" if corrigees == 1
                   else "%d de vos remarques ont déjà fait évoluer A3H. Bravo !" % corrigees)
    elif retenues:
        message = ("Une de vos remarques a été retenue : elle est prise au sérieux." if retenues == 1
                   else "Vos remarques sont prises au sérieux : %d ont été retenues." % retenues)
    else:
        message = "Vos remarques sont en cours d'étude. Vous serez informé ici dès qu'elles avancent."
    return {
        "nb_total": total, "nb_traitees": traitees, "nb_retenues": retenues,
        "badges": badges, "nb_badges": sum(1 for b in badges if b["ok"]),
        "message": message,
    }


def _apports(qs):
    """Corrections citables : seulement celles qui ont un résumé public écrit par l'administrateur."""
    return qs.filter(statut__in=STATUTS_UTILES).exclude(resume_public="").select_related("bureau")


@login_required
def accueil(request):
    ctx = _stats_agent(request.user)
    toutes = Remarque.objects.all()
    libelles = dict(TYPES)
    ctx.update({
        "profil": _profil(request.user),
        "nb_non_lues": _non_lues(Remarque.objects.filter(auteur=request.user)).count(),
        "tuiles": [{"code": c, "titre": libelles[c], "couleur": col, "texte": t} for c, col, t in TUILES],
        "apports": _apports(toutes).order_by("-updated_at")[:6],
        "communaute": {
            "remarques": toutes.count(),
            "corrigees": toutes.filter(statut="corrigee").count(),
            "agents": toutes.exclude(auteur=None).values("auteur").distinct().count(),
        },
        "derniere_version": VersionA3H.objects.first(),
    })
    return render(request, "remarques/accueil.html", ctx)


@login_required
def nouveautes(request):
    """Ce que les remarques ont changé, version par version. Seuls les résumés publics
    écrits par l'administrateur sont montrés, jamais le texte brut d'un agent."""
    versions = list(VersionA3H.objects.all())
    for v in versions:
        traitees = v.remarques_traitees.filter(statut="corrigee")
        v.nb_traitees = traitees.count()
        v.apports = _apports(traitees).order_by("pk")
    return render(request, "remarques/nouveautes.html", {"versions": versions})


@login_required
def profil(request):
    instance = _profil(request.user)
    form = ProfilForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        p = form.save(commit=False)
        p.user = request.user
        p.save()
        messages.success(request, "Votre profil est enregistré.")
        return redirect(_suite_sure(request, reverse("remarques:accueil")))
    bureaux = {}
    for b in Bureau.objects.all():
        bureaux.setdefault(str(b.centre_id), []).append([b.id, b.nom])
    return render(request, "remarques/profil.html", {
        "form": form, "bureaux_par_centre": bureaux,
        "next": request.GET.get("next", ""),
    })


@login_required
def nouvelle(request):
    p = _profil(request.user)
    if p is None:
        messages.info(request, "Avant votre première remarque, indiquez votre bureau (une seule fois).")
        return redirect("%s?next=%s" % (reverse("remarques:profil"), request.path))
    initial = {"nom_agent": p.nom_agent}
    if request.GET.get("type") in dict(TYPES):  # tuile cliquée sur l'accueil
        initial["type_remarque"] = request.GET["type"]
    form = RemarqueForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        r = form.save(commit=False)
        r.auteur = request.user
        r.bureau = p.bureau
        r.save()
        messages.success(
            request,
            "Merci ! Votre remarque n°%s est enregistrée. Vous verrez ici même quand elle sera "
            "étudiée : un badge « nouvelle réponse » vous préviendra." % r.pk,
        )
        return redirect("remarques:detail", pk=r.pk)
    return render(request, "remarques/nouvelle.html", {"form": form})


@login_required
def mes_remarques(request):
    liste = Remarque.objects.filter(auteur=request.user).select_related(
        "module", "version_correction"
    )
    return render(request, "remarques/mes.html", {"remarques": liste})


@login_required
def detail(request, pk):
    r = get_object_or_404(Remarque.objects.select_related("module", "bureau", "version_correction"), pk=pk)
    proprietaire = r.auteur_id == request.user.id
    if not (proprietaire or request.user.is_staff or r.type_remarque == "idee"):
        raise Http404
    etait_non_lue = proprietaire and r.non_lue
    if proprietaire and r.reponse_modifiee_le:
        # update() pour ne pas toucher à « Mise à jour le »
        Remarque.objects.filter(pk=r.pk).update(vue_par_agent_le=timezone.now())
    return render(request, "remarques/detail.html", {
        "r": r,
        "frise": _frise(r.statut),
        "etait_non_lue": etait_non_lue,
        "proprietaire": proprietaire,
        "voir_details": proprietaire or request.user.is_staff,
        "a_vote": r.moi_aussi.filter(user=request.user).exists(),
    })


@login_required
def capture(request, pk):
    r = get_object_or_404(Remarque, pk=pk)
    if not r.capture or not (request.user.is_staff or r.auteur_id == request.user.id):
        raise Http404
    rep = FileResponse(r.capture.open("rb"))
    rep["X-Content-Type-Options"] = "nosniff"
    return rep


@login_required
def idees(request):
    liste = (
        Remarque.objects.filter(type_remarque="idee", doublon_de__isnull=True)
        .exclude(statut="refusee")
        .select_related("module")
        .annotate(nb_votes=Count("moi_aussi", distinct=True), nb_doublons=Count("doublons", distinct=True))
    )
    liste = sorted(liste, key=lambda r: (-(1 + r.nb_votes + r.nb_doublons), -r.pk))
    deja = set(
        MoiAussi.objects.filter(user=request.user).values_list("remarque_id", flat=True)
    )
    for r in liste:
        r.demandes = 1 + r.nb_votes + r.nb_doublons
        r.a_vote = r.pk in deja
        r.est_la_mienne = r.auteur_id == request.user.id
    return render(request, "remarques/idees.html", {"idees": liste})


@login_required
@require_POST
def moi_aussi(request, pk):
    r = get_object_or_404(Remarque, pk=pk, type_remarque="idee")
    if r.auteur_id != request.user.id:
        vote, cree = MoiAussi.objects.get_or_create(remarque=r, user=request.user)
        if not cree:
            vote.delete()
    return redirect(_suite_sure(request, reverse("remarques:idees")))


def _compte(qs, *champs, libelles=None):
    lignes = qs.values(*champs).annotate(n=Count("id")).order_by("-n")
    sortie = []
    for l in lignes:
        etiquette = " / ".join(str((libelles or {}).get(l[c], l[c])) for c in champs)
        sortie.append({"libelle": etiquette, "n": l["n"]})
    return sortie


@staff_requis
def tableau(request):
    qs = Remarque.objects.all()
    top = (
        Remarque.objects.filter(type_remarque="idee", doublon_de__isnull=True)
        .exclude(statut__in=["refusee", "corrigee"])
        .annotate(nb_votes=Count("moi_aussi", distinct=True), nb_doublons=Count("doublons", distinct=True))
    )
    top = sorted(top, key=lambda r: -(1 + r.nb_votes + r.nb_doublons))[:10]
    for r in top:
        r.demandes = 1 + r.nb_votes + r.nb_doublons
    return render(request, "remarques/tableau.html", {
        "total": qs.count(),
        "a_traiter": qs.filter(statut="nouvelle").count(),
        "nb_cas_test": qs.filter(cas_de_test=True).count(),
        "par_statut": _compte(qs, "statut", libelles=dict(STATUTS)),
        "par_type": _compte(qs, "type_remarque", libelles=dict(TYPES)),
        "par_module": _compte(qs, "module__nom"),
        "par_centre": _compte(qs, "bureau__centre__nom"),
        "par_bureau": _compte(qs, "bureau__nom", "bureau__centre__nom"),
        "idees_top": top,
        "recentes": qs.select_related("module", "bureau")[:10],
    })
