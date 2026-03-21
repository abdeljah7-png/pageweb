from django.shortcuts import render
from django.http import FileResponse, Http404
from django.conf import settings
import os
from django.http import FileResponse, Http404, HttpResponse
def home(request):
    return render(request, 'home.html')

def description(request):
    return render(request, 'description.html')

def utilisation(request):
    return render(request, 'utilisation.html')

def download_dossier(request):
    file_path = os.path.join(settings.STATIC_ROOT, 'downloads', 'instal.zip')

    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='instal.zip')
    else:
        return HttpResponse("Fichier introuvable", status=404)