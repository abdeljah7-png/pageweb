import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ProfilForm, RemarqueForm
from .models import (
    STATUTS, TYPES, Bureau, MoiAussi, ProfilAgent, Remarque,
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


@login_required
def accueil(request):
    profil = _profil(request.user)
    mes = Remarque.objects.filter(auteur=request.user)
    return render(request, "remarques/accueil.html", {
        "profil": profil,
        "nb_total": mes.count(),
        "nb_reponses": mes.exclude(statut="nouvelle").count(),
    })


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
    form = RemarqueForm(
        request.POST or None, request.FILES or None, initial={"nom_agent": p.nom_agent}
    )
    if request.method == "POST" and form.is_valid():
        r = form.save(commit=False)
        r.auteur = request.user
        r.bureau = p.bureau
        r.save()
        messages.success(request, "Merci ! Votre remarque n°%s est enregistrée." % r.pk)
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
    return render(request, "remarques/detail.html", {
        "r": r,
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
