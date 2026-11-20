"""Tests du SuperNutri-score (question 3.4) : ses critères, ses poids, ses profils et le classement de la base."""

import openpyxl
import pytest

import projet_base
import projet_supernutri as sn
from projet_mrsort import affecter, nomDeClasse


baseConstruite = pytest.mark.skipif(not projet_base.FICHIER_BASE.exists(), reason="la base n'est pas encore construite")

LIMITER = ["en", "sa", "su", "so"]
FAVORISER = ["pr", "fi", "fr"]
TRANSFORMATION = ["nova", "additifs", "aRisque", "bio"]


def platAuNiveauDeAPrime():
    """Un plat qui vaut le profil de A′ (b5) sur les onze critères : il le franchit avec une concordance de 1."""
    return {"en": 300, "sa": 1.0, "su": 2.0, "so": 0.2, "pr": 15.0, "fi": 7.0, "fr": 80.0,
            "nova": 3, "additifs": 0, "listeAdditifs": None, "bio": "oui"}


# --- Les poids ---

def test_les_onze_criteres_dans_l_ordre():
    """Les sept composantes du Nutri-Score, puis la transformation et la production."""
    assert sn.CRITERES_SUPER == LIMITER + FAVORISER + TRANSFORMATION


def test_les_poids_suivent_les_trois_piliers():
    """À limiter 0,40, à favoriser 0,30, transformation et production 0,30 ; la somme fait 1."""
    poids = sn.MODELE_SUPER["poids"]
    assert sum(poids.values()) == pytest.approx(1)
    assert sum(poids[c] for c in LIMITER) == pytest.approx(0.40)
    assert sum(poids[c] for c in FAVORISER) == pytest.approx(0.30)
    assert sum(poids[c] for c in TRANSFORMATION) == pytest.approx(0.30)


def test_dans_un_pilier_nutritionnel_les_poids_suivent_les_points_maximaux():
    """Le sel (20 points au plus) pèse deux fois l'énergie (10 points) ; les protéines (7) pèsent 7/5 des fibres (5)."""
    poids = sn.MODELE_SUPER["poids"]
    assert poids["so"] == pytest.approx(2 * poids["en"])
    assert poids["pr"] == pytest.approx(7 / 5 * poids["fi"])


def test_les_poids_de_la_transformation_et_de_la_production():
    """NOVA 0,10 ; nombre d'additifs et additifs à risque 0,075 chacun ; bio 0,05, le plus faible."""
    poids = sn.MODELE_SUPER["poids"]
    assert (poids["nova"], poids["additifs"], poids["aRisque"], poids["bio"]) == pytest.approx((0.10, 0.075, 0.075, 0.05))
    assert poids["bio"] == min(poids.values())


# --- Les profils ---

def test_les_profils_sont_ordonnes():
    """De b2 (D′) à b5 (A′), chaque profil est au moins aussi exigeant que le précédent, dans le sens du critère."""
    profils = sn.MODELE_SUPER["profils"]
    for critere in sn.CRITERES_SUPER:
        valeurs = [profil[critere] for profil in profils]
        if sn.MODELE_SUPER["sens"][critere] == "min":
            assert valeurs == sorted(valeurs, reverse=True), critere
        else:
            assert valeurs == sorted(valeurs), critere


def test_les_seuils_de_a_prime_viennent_des_allegations():
    """Règlement CE 1924/2006 : « faible teneur » en AGS (1,5 g), en sucres (5 g) et en sel (0,3 g) ; « riche en fibres » (6 g)."""
    a, b = sn.MODELE_SUPER["profils"][3], sn.MODELE_SUPER["profils"][2]
    assert (a["sa"], a["su"], a["so"], a["fi"]) == (1.5, 5, 0.3, 6)
    assert b["fi"] == 3                                        # « source de fibres » pour B′


def test_lambda_vaut_0_7():
    assert sn.MODELE_SUPER["lam"] == 0.7


# --- Les additifs à risque et les valeurs d'un plat ---

def test_les_additifs_a_risque():
    """Nitrites et nitrates (E249 à E252), phosphates, carraghénanes ; l'acide citrique (E330) n'en est pas un."""
    assert sn.additifsARisque("E250, E330, E451, E407a") == 3
    assert sn.additifsARisque("E14XX, E330, E415") == 0
    assert sn.additifsARisque(None) == 0
    assert sn.additifsARisque("e252") == 1


def test_les_valeurs_d_un_plat():
    """Le bio vaut 1 ou 0, et les additifs à risque se comptent dans la liste des additifs."""
    valeurs = sn.valeursDuPlat(dict(platAuNiveauDeAPrime(), listeAdditifs="E250, E330", bio="non"))
    assert (valeurs["bio"], valeurs["aRisque"], valeurs["additifs"]) == (0, 1, 0)
    assert sn.valeursDuPlat(platAuNiveauDeAPrime())["bio"] == 1


def test_une_valeur_absente_ne_vote_pas_pour_le_plat():
    """Sans groupe NOVA, le plat perd la voix de NOVA (0,10) face à chaque profil, mais garde les autres."""
    detail = affecter(sn.valeursDuPlat(dict(platAuNiveauDeAPrime(), nova=None)), sn.MODELE_SUPER)
    assert detail["concordances"][3] == pytest.approx(0.90)
    assert nomDeClasse(detail["classe"]) == "A′"


# --- Le seuil majoritaire ---

def test_rater_toute_la_transformation_laisse_a_prime_possible():
    """Ultra-transformé, plein d'additifs, non bio, mais au niveau de A′ sur les sept composantes : 0,70, soit λ."""
    plat = dict(platAuNiveauDeAPrime(), nova=4, additifs=8, listeAdditifs="E250, E451", bio="non")
    detail = affecter(sn.valeursDuPlat(plat), sn.MODELE_SUPER)
    assert detail["concordances"][3] == pytest.approx(0.70)
    assert nomDeClasse(detail["classe"]) == "A′"


def test_rater_aussi_un_critere_nutritionnel_fait_perdre_a_prime():
    """Le même plat, avec 3 g de fibres au lieu de 7 : il perd la voix des fibres et tombe sous λ face à A′."""
    plat = dict(platAuNiveauDeAPrime(), nova=4, additifs=8, listeAdditifs="E250, E451", bio="non", fi=3.0)
    detail = affecter(sn.valeursDuPlat(plat), sn.MODELE_SUPER)
    assert detail["concordances"][3] < 0.7
    assert nomDeClasse(detail["classe"]) != "A′"


# --- La base ---

@baseConstruite
def test_la_poelee_fermiere_est_c_prime():
    """
    La Poêlée Fermière (B au Nutri-Score) : 1,6 g de protéines, sous le seuil de D′ (2,4 g) ; NOVA 4 et 3 additifs
    lui ferment B′. Face à C′, elle ne rate que les protéines : 1 − 0,124 ≥ 0,7.
    """
    plat = [p for p in projet_base.lireBase() if p["code"] == "3257982125116"][0]
    assert sn.classerPlat(plat)["lettre"] == "C′"


@baseConstruite
def test_le_super_nutri_score_range_toute_la_base_et_ecrit_l_excel(tmp_path):
    """Chaque plat reçoit une classe ; l'Excel a une ligne par plat, avec sa classe et son Nutri-Score."""
    sortie = tmp_path / "supernutri.xlsx"
    resultat = sn.superNutriScore(projet_base.FICHIER_BASE, sortie=sortie, afficher=False)
    assert len(resultat["plats"]) == 125
    assert sum(resultat["repartition"].values()) == 125
    feuille = openpyxl.load_workbook(sortie).worksheets[0]
    entetes = [cellule.value for cellule in feuille[1]]
    assert "SuperNutri-score" in entetes and "Nutri-Score" in entetes
    assert feuille.max_row == 126
