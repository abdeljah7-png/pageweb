import os

from django import forms

from .models import Bureau, Centre, ProfilAgent, Remarque

EXTENSIONS_OK = (".png", ".jpg", ".jpeg", ".gif", ".webp")
TAILLE_MAX = 5 * 1024 * 1024  # 5 Mo


def _arabe_ok(champs):
    """Texte libre : direction automatique (français ou arabe)."""
    for c in champs:
        c.widget.attrs.setdefault("dir", "auto")


class ProfilForm(forms.ModelForm):
    centre = forms.ModelChoiceField(
        queryset=Centre.objects.all(), label="Centre", empty_label="Choisir le centre"
    )

    class Meta:
        model = ProfilAgent
        fields = [
            "nom_agent", "centre", "bureau", "service", "dossiers_frequents",
            "volume_hebdo", "usage_a3h", "fait_a_la_main", "poste_travail",
        ]
        widgets = {
            "dossiers_frequents": forms.Textarea(attrs={"rows": 2}),
            "usage_a3h": forms.Textarea(attrs={"rows": 2}),
            "fait_a_la_main": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["bureau"].queryset = Bureau.objects.select_related("centre")
        self.fields["bureau"].empty_label = "Choisir le bureau"
        if self.instance.pk and self.instance.bureau_id:
            self.initial["centre"] = self.instance.bureau.centre_id
        _arabe_ok(self.fields.values())

    def clean(self):
        data = super().clean()
        centre, bureau = data.get("centre"), data.get("bureau")
        if centre and bureau and bureau.centre_id != centre.id:
            self.add_error("bureau", "Ce bureau n'appartient pas au centre choisi.")
        return data


class RemarqueForm(forms.ModelForm):
    class Meta:
        model = Remarque
        fields = [
            "nom_agent", "module", "type_remarque", "description", "impact",
            "code_impot", "periode", "regime", "valeurs_saisies",
            "resultat_obtenu", "resultat_attendu", "source_attendu",
            "montant_concerne", "regle_arrondi",
            "situation", "date_evenement", "date_calcul", "a3h_a_fait", "aurait_du",
            "ecran", "version_a3h", "capture",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "valeurs_saisies": forms.Textarea(attrs={"rows": 3}),
            "a3h_a_fait": forms.Textarea(attrs={"rows": 2}),
            "aurait_du": forms.Textarea(attrs={"rows": 2}),
            "date_evenement": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "date_calcul": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    # (titre, types concernés ou None pour tous, champs)
    GROUPES = [
        ("Le calcul", ["calcul", "arrondi", "situation"],
         ["code_impot", "periode", "regime", "valeurs_saisies",
          "resultat_obtenu", "resultat_attendu", "source_attendu"]),
        ("L'arrondi", ["arrondi"], ["montant_concerne", "regle_arrondi"]),
        ("La situation du dossier", ["situation"],
         ["situation", "date_evenement", "date_calcul", "a3h_a_fait", "aurait_du"]),
        ("Le formulaire", ["formulaire"], ["ecran"]),
        ("Pour finir", None, ["version_a3h", "capture"]),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["module"].empty_label = "Choisir le module"
        self.fields["type_remarque"].choices = [("", "Choisir le type")] + list(
            self.fields["type_remarque"].choices
        )[1:]
        self.fields["impact"].required = False
        self.fields["capture"].help_text = (
            "Facultative. N'affichez aucun nom ni numéro de contribuable réel : "
            "utilisez le code impôt et les montants."
        )
        self.fields["resultat_obtenu"].help_text = "Ce que A3H affiche."
        self.fields["resultat_attendu"].help_text = "Ce que vous pensez être juste."
        _arabe_ok(self.fields.values())

    def groupes(self):
        return [
            {
                "titre": titre,
                "types": ",".join(types) if types else "*",
                "champs": [self[n] for n in champs],
            }
            for titre, types, champs in self.GROUPES
        ]

    def clean_description(self):
        d = self.cleaned_data["description"].strip()
        if len(d) < 5:
            raise forms.ValidationError("Décrivez en quelques mots ce que vous avez remarqué.")
        return d

    def clean_capture(self):
        f = self.cleaned_data.get("capture")
        if f and hasattr(f, "size"):
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in EXTENSIONS_OK:
                raise forms.ValidationError("Formats acceptés : PNG, JPG, GIF, WEBP.")
            if f.size > TAILLE_MAX:
                raise forms.ValidationError("Image trop lourde (5 Mo maximum).")
        return f
