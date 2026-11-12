"""Tests de l'algorithme du Nutri-Score de 2023 (question 3.2)."""

import json
from pathlib import Path

import pytest

import projet_base
import projet_nutriscore as ns


FIXTURES = Path(__file__).parent / "fixtures"


def produit(en=0, sa=0, su=0, so=0, pr=0, fi=0, fr=0):
    """Fabrique un produit à partir de ses sept composantes."""
    return {"en": en, "sa": sa, "su": su, "so": so, "pr": pr, "fi": fi, "fr": fr}


# --- Les deux exemples du sujet (fig. 6 et 7) ---

def test_exemple_figure_6_cruesli_melange_de_noix():
    """Fig. 6 : 9 points négatifs, 8 positifs, les protéines comptent : score 1, label B."""
    resultat = ns.scoreNutriscore(ns.EXEMPLES_SUJET["figure 6"]["produit"])
    assert (resultat["N"], resultat["P"], resultat["score"], resultat["label"]) == (9, 8, 1, "B")
    assert resultat["proteinesComptees"]
    assert resultat["points"] == {"en": 5, "sa": 1, "su": 3, "so": 0, "pr": 3, "fi": 5, "fr": 0}


def test_exemple_figure_7_sesame_gerble():
    """Fig. 7 : 11 points négatifs, les protéines ne comptent pas : 11 − 2 = 9, label C."""
    resultat = ns.scoreNutriscore(ns.EXEMPLES_SUJET["figure 7"]["produit"])
    assert (resultat["N"], resultat["P"], resultat["score"], resultat["label"]) == (11, 2, 9, "C")
    assert not resultat["proteinesComptees"]


# --- Les quatre produits gardés du projet de 2025 ---

@pytest.mark.parametrize("code, score, label", [
    ("3168930010906", 10, "C"),   # Cruesli chocolat noir
    ("5010029000016", -3, "A"),   # Weetabix
    ("5010029202410", -3, "A"),   # Weetabix, autre format
    ("7613036669146", 7, "C"),    # Chocapic bio
])
def test_produits_off_de_2025(code, score, label):
    """Notre calcul retrouve le score et le label qu'OFF donne pour ces produits."""
    reponse = json.loads((FIXTURES / f"{code}.json").read_text(encoding="utf-8"))
    valeurs = projet_base.valeursDuCalculOff(reponse["product"])
    resultat = ns.scoreNutriscore(valeurs)
    assert (resultat["score"], resultat["label"]) == (score, label)


# --- Les barèmes (fig. 2 et 3) ---

def test_une_valeur_egale_au_seuil_recoit_les_points_du_bas():
    """Choix de conception n° 4 : un seuil doit être strictement dépassé."""
    assert ns.pointsDepuisSeuils(335, ns.SEUILS_ENERGIE) == 0
    assert ns.pointsDepuisSeuils(335.1, ns.SEUILS_ENERGIE) == 1
    assert ns.pointsDepuisSeuils(1, ns.SEUILS_AGS) == 0
    assert ns.pointsDepuisSeuils(3.4, ns.SEUILS_SUCRES) == 0
    assert ns.pointsDepuisSeuils(0.2, ns.SEUILS_SEL) == 0
    assert ns.pointsDepuisSeuils(2.4, ns.SEUILS_PROTEINES) == 0
    assert ns.pointsDepuisSeuils(3.0, ns.SEUILS_FIBRES) == 0


def test_points_maximaux_de_chaque_composante():
    """Les maximums du sujet : 10, 10, 15 et 20 points négatifs, 7, 5 et 5 positifs."""
    resultat = ns.scoreNutriscore(produit(en=4000, sa=50, su=90, so=9, pr=40, fi=20, fr=100))
    assert resultat["points"] == {"en": 10, "sa": 10, "su": 15, "so": 20, "pr": 7, "fi": 5, "fr": 5}
    assert resultat["points"] == ns.POINTS_MAX
    assert sum(ns.POINTS_MAX[c] for c in ns.NEGATIFS) == 55
    assert sum(ns.POINTS_MAX[c] for c in ns.POSITIFS) == 17


def test_points_des_fruits_legumes_et_legumineuses():
    """Fig. 2 : 0 point jusqu'à 40 %, 1 au-delà, 2 au-delà de 60 %, 5 au-delà de 80 %."""
    for pourcentage, points in [(0, 0), (40, 0), (40.1, 1), (60, 1), (60.1, 2), (80, 2), (80.1, 5), (100, 5)]:
        assert ns.pointsFruits(pourcentage) == points


def test_label_depuis_score():
    """Fig. 5 : A jusqu'à 0, B de 1 à 2, C de 3 à 10, D de 11 à 18, E à partir de 19."""
    for score, label in [(-15, "A"), (0, "A"), (1, "B"), (2, "B"), (3, "C"), (10, "C"),
                         (11, "D"), (18, "D"), (19, "E"), (40, "E")]:
        assert ns.labelDepuisScore(score) == label


# --- La règle des protéines (choix de conception n° 1) ---

def test_les_proteines_comptent_sous_11_points_negatifs():
    """10 points négatifs : les protéines comptent."""
    resultat = ns.scoreNutriscore(produit(en=1700, sa=2.5, su=10.5, pr=20))   # 5 + 2 + 3 + 0 = 10
    assert resultat["N"] == 10 and resultat["proteinesComptees"]
    assert resultat["P"] == 7


def test_les_proteines_ne_comptent_plus_a_11_points_negatifs():
    """11 points négatifs : les protéines ne comptent plus."""
    resultat = ns.scoreNutriscore(produit(en=1700, sa=2.5, su=10.5, so=0.3, pr=20))   # 5 + 2 + 3 + 1 = 11
    assert resultat["N"] == 11 and not resultat["proteinesComptees"]
    assert resultat["P"] == 0


def test_exception_des_fruits_de_la_figure_4():
    """
    La fig. 4 garde les protéines au-delà de 80 % de fruits, légumes et légumineuses (règle
    de 2017) ; la règle officielle de 2023 ne les garde pas. Les deux scores diffèrent.
    """
    plat = produit(en=1700, sa=2.5, su=10.5, so=0.3, pr=20, fr=85)
    officiel = ns.scoreNutriscore(plat)
    figure4 = ns.scoreNutriscore(plat, exceptionFruits=True)
    assert not officiel["proteinesComptees"] and figure4["proteinesComptees"]
    assert officiel["score"] == 11 - 5 and figure4["score"] == 11 - 12


# --- La base de plats préparés ---

@pytest.mark.skipif(not projet_base.FICHIER_BASE.exists(), reason="la base n'est pas encore construite")
def test_la_base_est_reproduite():
    """Notre calcul retrouve le score et le label d'OFF pour chaque plat de la base."""
    verification = ns.verifierNutriscoreBase(projet_base.lireBase())
    assert verification["reproduits"] == verification["total"], verification["ecarts"]


def test_les_maximums_sont_ceux_de_l_algorithme_actualise():
    """
    Le sujet (§1.2, « version de mars 2025 ») annonce de 0 à 55 points négatifs et de 0 à 17
    positifs : ce sont les maximums de l'algorithme actualisé en 2023, et non ceux de 2017 (40 et 15).
    """
    assert sum(ns.POINTS_MAX[composante] for composante in ns.NEGATIFS) == 55
    assert sum(ns.POINTS_MAX[composante] for composante in ns.POSITIFS) == 17


# --- Les cas particuliers de l'algorithme de 2023 (FAQ du 17 mars 2025, p. 17-20 et 28-34) ---

def test_la_viande_rouge_plafonne_les_proteines_a_2_points():
    """Viande rouge : 20 g de protéines valent 7 points au cas général, mais 2 seulement (P ≤ 12)."""
    steak = produit(en=600, sa=3, so=0.3, pr=20)                       # N = 1 + 2 + 0 + 1 = 4
    general = ns.scoreNutriscore(steak)
    rouge = ns.scoreNutriscore(steak, categorie="viandeRouge")
    assert general["points"]["pr"] == 7 and rouge["points"]["pr"] == 2
    assert rouge["maximums"]["pr"] == 2
    assert (general["score"], general["label"]) == (-3, "A")
    assert (rouge["score"], rouge["label"]) == (2, "B")


def test_les_proteines_du_fromage_comptent_toujours():
    """Fromage : même à 11 points négatifs ou plus, les protéines comptent (FAQ, p. 29)."""
    fromage = produit(en=1500, sa=18, so=1.6, pr=25)                   # N = 4 + 10 + 0 + 7 = 21
    general = ns.scoreNutriscore(fromage)
    resultat = ns.scoreNutriscore(fromage, categorie="fromage")
    assert general["N"] == 21 and not general["proteinesComptees"]
    assert resultat["proteinesComptees"]
    assert (general["score"], general["label"]) == (21, "E")
    assert (resultat["score"], resultat["label"]) == (14, "D")


def test_l_huile_d_olive_est_classee_B():
    """
    Matières grasses : l'énergie des acides gras saturés (sa × 37 kJ) et le ratio AGS / lipides
    remplacent l'énergie et les AGS. Huile d'olive : 4 + 1 = 5 points négatifs, 5 positifs, score 0, B.
    """
    huile = dict(produit(en=3378, sa=14, fr=100), lipides=100)
    resultat = ns.scoreNutriscore(huile, categorie="matieresGrasses")
    assert resultat["valeurs"]["enAgs"] == 518 and resultat["points"]["enAgs"] == 4
    assert resultat["valeurs"]["ratioAgs"] == 14 and resultat["points"]["ratioAgs"] == 1
    assert (resultat["N"], resultat["P"], resultat["score"], resultat["label"]) == (5, 5, 0, "B")


def test_le_ratio_des_graisses_compte_l_egalite():
    """Le barème du ratio AGS / lipides se lit « < 10 » pour 0 point : 10 % tout juste vaut déjà 1 point."""
    assert ns.pointsDepuisSeuils(9.99, ns.SEUILS_RATIO_AGS, inclusif=True) == 0
    assert ns.pointsDepuisSeuils(10, ns.SEUILS_RATIO_AGS, inclusif=True) == 1
    assert ns.pointsDepuisSeuils(64, ns.SEUILS_RATIO_AGS, inclusif=True) == 10


def test_les_matieres_grasses_ecartent_les_proteines_a_7_points_negatifs():
    """
    Matières grasses : les protéines ne comptent plus à partir de 7 points négatifs (et non 11),
    et la classe A va jusqu'à −6. Cacahuètes nature : 4 − 12 = −8, A ; salées : 9 − 5 = 4, C.
    """
    nature = dict(produit(en=2400, sa=7, su=4, so=0.02, pr=26, fi=8.5), lipides=49)
    sale = dict(nature, so=1.2)
    resultat = ns.scoreNutriscore(nature, categorie="matieresGrasses")
    assert (resultat["N"], resultat["proteinesComptees"], resultat["score"], resultat["label"]) == (4, True, -8, "A")
    resultat = ns.scoreNutriscore(sale, categorie="matieresGrasses")
    assert (resultat["N"], resultat["proteinesComptees"], resultat["score"], resultat["label"]) == (9, False, 4, "C")


def test_les_boissons_ont_leurs_baremes_et_leurs_classes():
    """Boissons : un soda (180 kJ, 10,6 g de sucres) prend 3 + 9 points, soit 12 : E, dès 10 points."""
    resultat = ns.scoreNutriscore(produit(en=180, su=10.6), categorie="boisson")
    assert (resultat["points"]["en"], resultat["points"]["su"]) == (3, 9)
    assert (resultat["score"], resultat["label"]) == (12, "E")


def test_les_edulcorants_ajoutent_4_points_aux_boissons():
    """Un soda sans sucre mais édulcoré : 4 points, C ; sans édulcorant, 0 point, B (A est réservé aux eaux)."""
    resultat = ns.scoreNutriscore(dict(produit(en=1.3), edulcorants=True), categorie="boisson")
    assert resultat["points"]["edulcorants"] == 4
    assert (resultat["score"], resultat["label"]) == (4, "C")
    assert ns.scoreNutriscore(produit(en=1.3), categorie="boisson")["label"] == "B"


def test_le_lait_et_le_jus_d_orange_sont_des_boissons():
    """Lait demi-écrémé : 6 − 7 = −1, B ; jus d'orange : 10 − 6 = 4, C (protéines et fruits des boissons)."""
    lait = ns.scoreNutriscore(produit(en=194, sa=1.0, su=4.8, so=0.1, pr=3.3), categorie="boisson")
    assert (lait["N"], lait["points"]["pr"], lait["score"], lait["label"]) == (6, 7, -1, "B")
    jus = ns.scoreNutriscore(produit(en=180, su=9, pr=0.7, fr=100), categorie="boisson")
    assert (jus["N"], jus["points"]["fr"], jus["score"], jus["label"]) == (10, 6, 4, "C")


def test_l_eau_est_classee_A_sans_calcul():
    """Les eaux sont classées A, sans score (FAQ, p. 18 et 34)."""
    resultat = ns.scoreNutriscore(produit(), categorie="eau")
    assert resultat["label"] == "A" and resultat["score"] is None


def test_les_classes_suivent_la_categorie():
    """Les bornes des classes (FAQ, p. 34) : aliments, matières grasses (A jusqu'à −6), boissons (B dès le minimum)."""
    assert [ns.labelDepuisScore(s) for s in (0, 1, 2, 3, 10, 11, 18, 19)] == list("ABBCCDDE")
    assert [ns.labelDepuisScore(s, "matieresGrasses") for s in (-6, -5, 2, 3, 10, 11, 18, 19)] == list("ABBCCDDE")
    assert [ns.labelDepuisScore(s, "boisson") for s in (-3, 2, 3, 6, 7, 9, 10)] == list("BBCCDDE")


def test_composantes_de_la_categorie():
    """Les lignes du tableau des points suivent la catégorie : libellés, groupes et maximums."""
    general = ns.composantesDeLaCategorie("general")
    assert [ligne["cle"] for ligne in general] == ns.NEGATIFS + ns.POSITIFS
    boisson = ns.composantesDeLaCategorie("boisson")
    assert "edulcorants" in [ligne["cle"] for ligne in boisson]
    for categorie, negatifs, positifs in [("general", 55, 17), ("viandeRouge", 55, 12), ("fromage", 55, 17),
                                          ("matieresGrasses", 55, 17), ("boisson", 54, 18)]:
        lignes = ns.composantesDeLaCategorie(categorie)
        assert sum(l["maximum"] for l in lignes if l["groupe"] == "negatif") == negatifs, categorie
        assert sum(l["maximum"] for l in lignes if l["groupe"] == "positif") == positifs, categorie
    assert [ligne["cle"] for ligne in ns.composantesDeLaCategorie("matieresGrasses")][:2] == ["enAgs", "ratioAgs"]
    assert ns.composantesDeLaCategorie("eau") == []


def test_categorie_depuis_les_marqueurs_d_off():
    """Le type que propose Open Food Facts, d'après les marqueurs de son calcul de 2023."""
    assert ns.categorieDepuisOff({"is_beverage": 1, "is_water": 1}) == "eau"
    assert ns.categorieDepuisOff({"is_beverage": 1}) == "boisson"
    assert ns.categorieDepuisOff({"is_fat_oil_nuts_seeds": 1}) == "matieresGrasses"
    assert ns.categorieDepuisOff({"is_cheese": 1}) == "fromage"
    assert ns.categorieDepuisOff({"is_red_meat_product": 1}) == "viandeRouge"
    assert ns.categorieDepuisOff({"is_beverage": 0, "is_cheese": 0}) == "general"
    assert set(ns.CATEGORIES) == {"general", "fromage", "viandeRouge", "matieresGrasses", "boisson", "eau"}


@pytest.mark.skipif(not projet_base.FICHIER_RESULTATS.exists(), reason="les résultats ne sont pas encore calculés")
def test_les_cas_particuliers_reproduisent_off():
    """
    Notre calcul des cas particuliers, contre OFF, sur les fiches du cache : les chiffres du
    JSON sont ceux que l'on recalcule, et chaque écart a son explication. Soit OFF marque le
    produit de deux types à la fois et applique les deux règles, ce que la FAQ ne fait jamais
    (la Piada Speck et Fromage, fromage et viande rouge) ; soit OFF compte un point de plus pour
    une valeur pile sur un seuil (voir test_valeurs_pile_sur_un_seuil_chez_off).
    """
    resultats = json.loads(projet_base.FICHIER_RESULTATS.read_text(encoding="utf-8"))["nutriscore"]
    if "casParticuliers" not in resultats:
        pytest.skip("les cas particuliers ne sont pas encore vérifiés")
    assert resultats["casParticuliers"] == ns.verifierCasParticuliers()
    ecarts = [ecart for bilan in resultats["casParticuliers"].values() for ecart in bilan["ecarts"]]
    assert "8032484861879" in [ecart.split(" ")[0] for ecart in ecarts]            # Piada Speck et Fromage
    assert all("à la fois" in ecart or "pile sur un seuil" in ecart for ecart in ecarts), ecarts
    for categorie in ("boisson", "eau", "matieresGrasses", "viandeRouge"):
        assert resultats["casParticuliers"][categorie]["total"] > 0


def test_les_marqueurs_d_off_qui_se_cumulent():
    """Une boisson marquée viande rouge garde ses deux types ; une eau n'est pas aussi une boisson."""
    assert ns.typesMarquesParOff({"is_beverage": 1, "is_red_meat_product": 1}) == ["boisson", "viandeRouge"]
    assert ns.typesMarquesParOff({"is_beverage": 1, "is_water": 1}) == ["eau"]
    assert ns.typesMarquesParOff({}) == []


def ficheAvecSel(code, sel, points):
    """Une réponse d'OFF dont le calcul de 2023 note le sel à `sel` g avec `points` points (cas général)."""
    composantes = {"negative": [{"id": "salt", "value": sel, "points": points}], "positive": []}
    return {"status": 1, "product": {"code": code, "nutriscore": {"2023": {
        "nutriscore_computed": 1, "data": {"is_beverage": 0, "components": composantes}}}}}


def test_valeurs_pile_sur_un_seuil_chez_off():
    """
    Contrôle du choix 4 sur les calculs d'OFF : une valeur pile sur un seuil (0,8 g de sel) qui
    reçoit les points du bas compte comme « > » ; un point de plus, comme « ≥ ». Les autres
    valeurs ne comptent pas, ni une valeur affichée pile (0,4 g) dont la valeur exacte du
    tableau nutritionnel dépasse le seuil (0,4043 g : choix 13).
    """
    soupe = ficheAvecSel("4", 0.4, 2)                       # OFF affiche 0,4 g, mais compte 0,4043 g
    soupe["product"]["nutriments"] = {"salt_100g": 0.4043}
    fiches = [ficheAvecSel("1", 0.8, 3), ficheAvecSel("2", 0.8, 4), ficheAvecSel("3", 0.85, 4), soupe]
    controle = ns.valeursPileSurUnSeuil(fiches)
    assert controle["salt"] == {"strict": 1, "inclusif": 1, "exemples": ["2"]}


@pytest.mark.skipif(not projet_base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")
def test_les_ecarts_du_vivier_etendu_sont_expliques():
    """Sur tous les plats retenus de la base étendue, chaque écart avec OFF a son explication (OFF, pas notre calcul)."""
    resultats = json.loads(projet_base.FICHIER_RESULTATS.read_text(encoding="utf-8"))["nutriscore"]
    vivier = resultats["vivierEtendu"]
    assert vivier["total"] - vivier["reproduits"] == len(vivier["ecarts"])
    assert all("pile sur un seuil" in ecart or "à la fois" in ecart for ecart in vivier["ecarts"]), vivier["ecarts"]
