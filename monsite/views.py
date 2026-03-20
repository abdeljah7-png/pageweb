from django.shortcuts import render
from django.http import FileResponse, Http404
from django.conf import settings
import os

def home(request):
    return render(request, 'home.html')

def description(request):
    return render(request, 'description.html')

def utilisation(request):
    return render(request, 'utilisation.html')

def download_dossier(request):
    file_path = os.path.join(settings.MEDIA_ROOT, 'downloads/instal.zip')
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='instal.zip')
    else:
        raise Http404("Fichier introuvable")

def download_dossier(request):
    file_path = os.path.join(settings.MEDIA_ROOT, 'downloads/INSTAL.zip')
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='INSTAL.zip')
    else:
        return HttpResponse("Le fichier ZIP n'a pas été trouvé sur le serveur.", status=404)