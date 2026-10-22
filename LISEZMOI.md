# Site des remarques A3H

Projet Django complet : connexion + accueil + remarques des agents. Rien d'autre.

## Mettre en ligne sur Render (repartir de zéro)

1. Sur ton poste, dans `C:\pageweb`, supprime tout **sauf le dossier caché `.git`**
   (PowerShell : `Get-ChildItem -Force | Where-Object Name -ne ".git" | Remove-Item -Recurse -Force`).
2. Extrais ici le contenu de ce zip : `manage.py`, `pageweb/`, `remarques/`, `requirements.txt`...
3. Envoie :
   ```
   git add -A
   git status
   git commit -m "Nouveau site : accueil et remarques"
   git push
   ```
4. Dans Render, service Web, **Settings** :
   - Build Command : `pip install -r requirements.txt`
   - Start Command :
     `python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py init_admin && gunicorn pageweb.wsgi:application`
5. Dans Render, **Environment**, ajoute ces variables :

   | Variable | Valeur |
   |---|---|
   | `SECRET_KEY` | une longue suite de caractères au hasard (jamais la même qu'avant) |
   | `A3H_ADMIN_USER` | ton nom d'administrateur |
   | `A3H_ADMIN_PASSWORD` | un mot de passe long, nouveau |
   | `DATABASE_URL` | (voir « Données » plus bas) |

   Render définit lui-même `RENDER` et `RENDER_EXTERNAL_HOSTNAME` : le mode production et
   l'adresse autorisée sont donc réglés tout seuls.
6. Ouvre le site, connecte-toi, puis va dans `/admin/` : crée les **Centres**, les **Bureaux**,
   et un compte par agent (Utilisateurs). Les agents remplissent leur profil à la première visite.

## Données : à lire avant de compter sur le site

Sans `DATABASE_URL`, le site utilise SQLite, un fichier qui est **effacé à chaque mise à jour**
sur l'offre gratuite de Render : centres, bureaux, comptes et remarques disparaîtraient.
Pour garder les données, crée une base PostgreSQL (celle de Render, ou un autre service
gratuit : vérifie les durées et limites actuelles) et colle son adresse dans `DATABASE_URL`.

Ce site est un site d'essai : n'y mets pas de données de contribuables, et pas de captures
d'écran réelles. L'usage réel est prévu sur le serveur DGI avec PostgreSQL.

## Travailler en local

```
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Ouvre http://127.0.0.1:8000/ (mode développement automatique en local).

## Variables d'environnement

`SECRET_KEY` (obligatoire en production), `DEBUG` (0 ou 1), `DATABASE_URL`,
`ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `HTTPS` (mettre 0 sur un réseau interne en http),
`REMARQUES_CAPTURES_DIR`, `A3H_ADMIN_USER`, `A3H_ADMIN_PASSWORD`.

## Utilisation côté administrateur

Dans `/admin/`, section Remarques : filtres par centre, bureau, type, module, statut ;
réponse et statut visibles par l'agent ; version qui corrige ; **résumé public**
(une phrase sans donnée de contribuable, affichée dans « Ce qui a changé grâce à vous ») ;
doublons ; cas de test ; export Excel. Tableau de bord : `/tableau/`.

## Test

`python manage.py test remarques` (22 tests).
