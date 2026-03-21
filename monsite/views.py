from django.shortcuts import render
from django.http import FileResponse, Http404
from django.conf import settings
import os
from django.http import FileResponse, Http404, HttpResponse



@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def description(request):
    return render(request, 'description.html')

@login_required
def utilisation(request):
    return render(request, 'utilisation.html')

@login_required
def download_dossier(request):
    file_path = os.path.join(settings.STATIC_ROOT, 'downloads', 'instal.zip')

    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='instal.zip')
    else:
        return HttpResponse("Fichier introuvable", status=404)