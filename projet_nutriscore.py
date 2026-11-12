"""
projet_nutriscore.py : l'algorithme du Nutri-Score de 2023, tous ses cas (question 3.2).

Le Nutri-Score note un aliment à partir de sept composantes, pour 100 g :
- quatre composantes « négatives », dont la consommation doit être limitée : l'énergie (en),
  les acides gras saturés (sa), les sucres (su) et le sel (so) ;
- trois composantes « positives » : les protéines (pr), les fibres (fi), et les fruits,
  légumes et légumineuses (fr).
Chaque composante reçoit des points selon les barèmes des fig. 2 et 3 du sujet. Le score
vaut N − P, où N est la somme des points négatifs (de 0 à 55) et P celle des points
positifs (de 0 à 17). Plus le score est bas, meilleur est l'aliment ; la fig. 5 le
convertit en label, de A à E.

C'est l'algorithme que le sujet appelle « version de mars 2025 » : la version actualisée du
Nutri-Score, que Santé publique France nomme « Nutri-Score actualisé en 2023 », entrée en
vigueur en France le 16 mars 2025 (FAQ officielle, version du 17 mars 2025). Ses maximums,
55 points négatifs et 17 positifs, le distinguent de l'algorithme de 2017 (40 et 15). Le
code l'appelle « l'algorithme de 2023 ».

Choix d'interprétation du sujet (README, « Choix de conception ») :
1. La règle des protéines est celle de l'algorithme de 2023 : à partir de 11 points
   négatifs, les protéines ne comptent plus (FAQ officielle du 17 mars 2025, p. 29 et 30,
   et calculs d'Open Food Facts). La fig. 4 du sujet reprend la règle de 2017, qui gardait les
   protéines au-delà de 80 % de fruits, légumes et légumineuses : l'option
   exceptionFruits=True l'applique, pour mesurer l'écart sur la base.
2. Le sel est en grammes, comme dans les barèmes de 2023 (fig. 3) ; le sodium vaut sel / 2,5.
3. La composante fr est celle de 2023 : fruits, légumes et légumineuses, sans les fruits à
   coque ni les huiles (en-tête de la fig. 2).
4. Un seuil doit être strictement dépassé : une valeur égale au seuil reçoit les points du
   bas (« ≤ 335 » vaut 0 point, « > 335 » vaut 1 point).
5. La base reste au cas général, mais le calcul couvre tous les cas de 2023 (FAQ, p. 17-20
   et 28-34), que l'interface propose pour un produit cherché sur OFF :
   - fromage : les protéines comptent toujours ;
   - viande rouge : au plus 2 points de protéines ;
   - matières grasses, fruits à coque et graines : l'énergie des acides gras saturés
     (sa × 37 kJ) et le ratio AGS / lipides remplacent l'énergie et les AGS, les protéines
     ne comptent plus dès 7 points négatifs, et la classe A va jusqu'à −6 ;
   - boissons (pour 100 mL) : leurs propres barèmes d'énergie, de sucres, de protéines et de
     fruits, 4 points si elles contiennent des édulcorants non nutritifs, et des classes
     propres (B jusqu'à 2, C jusqu'à 6, D jusqu'à 9) ;
   - eaux : classe A, sans calcul.
   Le type d'un produit ne se devine pas à ses sept valeurs : il vient de sa fiche OFF
   (categorieDepuisOff) ou du choix de l'utilisateur.

Commande :
    python3 projet_nutriscore.py   # les exemples du sujet, puis la vérification sur la base, les cas
                                   # particuliers et, s'il est construit, le vivier de la base étendue
"""

import random
from pathlib import Path

from projet_base import DOSSIER, FICHIER_BASE, enregistrerResultats, lireBase


# --- Question 3.2 : barèmes du Nutri-Score de 2023 (fig. 2 et 3 du sujet) ---

# Chaque barème donne les seuils successifs : une valeur qui dépasse strictement k seuils reçoit k points.
SEUILS_ENERGIE = [335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350]                 # kJ/100 g, 0 à 10
SEUILS_AGS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]                                               # g/100 g, 0 à 10
SEUILS_SUCRES = [3.4, 6.8, 10, 14, 17, 20, 24, 27, 31, 34, 37, 41, 44, 48, 51]             # g/100 g, 0 à 15
SEUILS_SEL = [0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2,
              2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4]                                 # g/100 g, 0 à 20
SEUILS_PROTEINES = [2.4, 4.8, 7.2, 9.6, 12, 14, 17]                                        # g/100 g, 0 à 7
SEUILS_FIBRES = [3.0, 4.1, 5.2, 6.3, 7.4]                                                  # g/100 g, 0 à 5

# Fruits, légumes et légumineuses : 1 point au-delà de 40 %, 2 au-delà de 60 %, 5 au-delà de 80 %
POINTS_FRUITS = [(80, 5), (60, 2), (40, 1)]

NEGATIFS = ["en", "sa", "su", "so"]
POSITIFS = ["pr", "fi", "fr"]
POINTS_MAX = {"en": 10, "sa": 10, "su": 15, "so": 20, "pr": 7, "fi": 5, "fr": 5}

LIBELLES = {
    "en": "Énergie", "sa": "Acides gras saturés", "su": "Sucres", "so": "Sel",
    "pr": "Protéines", "fi": "Fibres", "fr": "Fruits, légumes et légumineuses",
    "enAgs": "Énergie des acides gras saturés", "ratioAgs": "Acides gras saturés / lipides",
    "edulcorants": "Édulcorants non nutritifs",
}
UNITES = {"en": "kJ", "sa": "g", "su": "g", "so": "g", "pr": "g", "fi": "g", "fr": "%",
          "enAgs": "kJ", "ratioAgs": "%", "edulcorants": ""}

# À partir de ce nombre de points négatifs, les protéines ne comptent plus
SEUIL_PROTEINES = 11

# Fig. 5 : la plus grande valeur du score pour chaque label ; au-delà de 18, le label est E
BORNES_LABELS = [(0, "A"), (2, "B"), (10, "C"), (18, "D")]


# --- Question 3.2 : les cas particuliers de 2023 (FAQ du 17 mars 2025, p. 17-20 et 28-34) ---

# Les types de produits : chacun a ses règles. Le cas général est celui de la base.
CATEGORIES = {
    "general": "Aliment (cas général)",
    "fromage": "Fromage",
    "viandeRouge": "Viande rouge",
    "matieresGrasses": "Matière grasse, fruit à coque ou graine",
    "boisson": "Boisson",
    "eau": "Eau",
}

# Viande rouge : les protéines rapportent au plus 2 points (FAQ, p. 29)
PROTEINES_MAX_VIANDE_ROUGE = 2

# Matières grasses, fruits à coque et graines (tableaux 7 et 8, p. 30-31)
KJ_PAR_GRAMME_AGS = 37                                                          # énergie des AGS = sa × 37 kJ
SEUILS_ENERGIE_AGS = [120, 240, 360, 480, 600, 720, 840, 960, 1080, 1200]     # kJ/100 g, 0 à 10
SEUILS_RATIO_AGS = [10, 16, 22, 28, 34, 40, 46, 52, 58, 64]                   # % AGS / lipides, 0 à 10, comptés avec « ≥ »
SEUIL_PROTEINES_MATIERES_GRASSES = 7

# Boissons, pour 100 mL (tableaux 9 et 10, p. 32-33)
SEUILS_ENERGIE_BOISSONS = [30, 90, 150, 210, 240, 270, 300, 330, 360, 390]     # kJ, 0 à 10
SEUILS_SUCRES_BOISSONS = [0.5, 2, 3.5, 5, 6, 7, 8, 9, 10, 11]                  # g, 0 à 10
SEUILS_PROTEINES_BOISSONS = [1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.0]                # g, 0 à 7
POINTS_FRUITS_BOISSONS = [(80, 6), (60, 4), (40, 2)]                           # au-delà de 40, 60 et 80 %
POINTS_EDULCORANTS = 4                                                          # présence d'édulcorants non nutritifs

# Les composantes négatives de chaque type (les positives sont toujours pr, fi et fr), et leurs maximums
COMPOSANTES_NEGATIVES = {
    "general": NEGATIFS, "fromage": NEGATIFS, "viandeRouge": NEGATIFS,
    "matieresGrasses": ["enAgs", "ratioAgs", "su", "so"],
    "boisson": NEGATIFS + ["edulcorants"],
}
MAXIMUMS = {
    "general": dict(POINTS_MAX),
    "fromage": dict(POINTS_MAX),
    "viandeRouge": dict(POINTS_MAX, pr=PROTEINES_MAX_VIANDE_ROUGE),
    "matieresGrasses": {"enAgs": 10, "ratioAgs": 10, "su": 15, "so": 20, "pr": 7, "fi": 5, "fr": 5},
    "boisson": {"en": 10, "sa": 10, "su": 10, "so": 20, "edulcorants": POINTS_EDULCORANTS, "pr": 7, "fi": 5, "fr": 6},
}

# Les bornes des classes de chaque type (FAQ, p. 34) ; les fromages et les viandes rouges suivent le cas général
BORNES_PAR_CATEGORIE = {
    "general": BORNES_LABELS,
    "matieresGrasses": [(-6, "A"), (2, "B"), (10, "C"), (18, "D")],
    "boisson": [(2, "B"), (6, "C"), (9, "D")],                                  # A est réservé aux eaux
}

# Les marqueurs du calcul de 2023 d'OFF, dans l'ordre où on les lit, et le type qu'ils désignent
MARQUEURS_OFF = [("is_water", "eau"), ("is_beverage", "boisson"), ("is_fat_oil_nuts_seeds", "matieresGrasses"),
                 ("is_cheese", "fromage"), ("is_red_meat_product", "viandeRouge")]

# Les deux exemples du sujet (fig. 6 et 7), relevés sur Open Food Facts
EXEMPLES_SUJET = {
    "figure 6": {
        "nom": "Cruesli mélange de noix, Quaker, 450 g",
        "produit": {"en": 1913, "sa": 2, "su": 12, "so": 0, "pr": 8.5, "fi": 10, "fr": 0},
        "attendu": (1, "B"),
    },
    "figure 7": {
        "nom": "Sésame, Gerblé, 230 g",
        "produit": {"en": 1961, "sa": 2, "su": 17, "so": 0.38, "pr": 10, "fi": 4.6, "fr": 0},
        "attendu": (9, "C"),
    },
}

FICHIER_VERIFICATION = DOSSIER / "resultats" / "nutriscore_base.xlsx"

# Les échantillons qui vérifient les cas particuliers contre OFF : (nom, catégorie d'OFF, nombre de
# fiches). Pour chacun, une page de l'index d'OFF est tirée au hasard, avec la graine de la base.
ECHANTILLONS = [
    ("boissons", "en:beverages", 50),
    ("fromages", "en:cheeses", 50),
    ("matieres-grasses", "en:fats", 50),
    ("fruits-a-coque", "en:nuts", 30),
    ("eaux", "en:waters", 20),
]
RESULTATS_MAX_INDEX = 10000           # l'index de recherche d'OFF ne sert pas plus de 10 000 résultats


def codesDesEchantillons(depuisCache=True):
    """
    Les codes-barres des échantillons de vérification des cas particuliers. Pour chaque
    catégorie d'OFF, on tire une page de l'index au hasard (graine de la base), parmi les
    produits vendus en France. Les réponses sont gardées dans donnees/brut/recherche/.
    Renvoie un dictionnaire : nom de l'échantillon → liste de codes-barres.
    """
    from projet_base import DOSSIER_BRUT, GRAINE, PAUSE_RECHERCHE, URL_RECHERCHE, lireJson

    hasard = random.Random(GRAINE)
    codes = {}
    for nom, categorie, taille in ECHANTILLONS:
        requete = f'categories_tags:"{categorie}" AND countries_tags:"en:france"'
        compte = lireJson(URL_RECHERCHE, {"q": requete, "page_size": 1, "fields": "code"},
                          DOSSIER_BRUT / "recherche" / f"{nom}_compte.json", PAUSE_RECHERCHE, depuisCache)
        pages = max(1, min(RESULTATS_MAX_INDEX // taille, (compte.get("count", 0) + taille - 1) // taille))
        page = hasard.randint(1, pages)
        reponse = lireJson(URL_RECHERCHE, {"q": requete, "page_size": taille, "page": page, "fields": "code"},
                           DOSSIER_BRUT / "recherche" / f"{nom}_page{page:03d}.json", PAUSE_RECHERCHE, depuisCache)
        codes[nom] = [str(resultat["code"]) for resultat in reponse.get("hits", []) if resultat.get("code")]
    return codes


# --- Question 3.2 : calcul des points et du score ---

def pointsDepuisSeuils(valeur, seuils, inclusif=False):
    """
    Compte les seuils que la valeur dépasse strictement : c'est le nombre de points. Avec
    inclusif=True, un seuil atteint compte aussi : c'est la lecture du barème du ratio
    AGS / lipides des matières grasses (« < 10 » pour 0 point, « ≥ 64 » pour 10 points).
    """
    points = 0
    for seuil in seuils:
        if valeur > seuil or (inclusif and valeur == seuil):
            points += 1
    return points


def pointsFruits(pourcentage, bareme=POINTS_FRUITS):
    """
    Points des fruits, légumes et légumineuses : 0, 1, 2 ou 5 (fig. 2), ou, pour les
    boissons, 0, 2, 4 ou 6 (bareme=POINTS_FRUITS_BOISSONS).
    """
    for seuil, points in bareme:
        if pourcentage > seuil:
            return points
    return 0


def labelDepuisScore(score, categorie="general"):
    """
    Convertit un score en label, selon la fig. 5 du sujet pour le cas général, ou selon les
    bornes du type de produit (matières grasses, boissons : FAQ, p. 34).
    """
    for borne, label in BORNES_PAR_CATEGORIE.get(categorie, BORNES_LABELS):
        if score <= borne:
            return label
    return "E"


def typesMarquesParOff(donnees):
    """
    Tous les types que désignent les marqueurs du calcul de 2023 d'OFF (nutriscore.2023.data :
    is_water, is_beverage, is_fat_oil_nuts_seeds, is_cheese, is_red_meat_product), dans l'ordre
    de MARQUEURS_OFF. Une eau est aussi marquée boisson : on ne garde alors que l'eau. Plus d'un
    type veut dire qu'OFF cumule leurs règles, ce que la FAQ ne fait jamais.
    """
    types = [categorie for marqueur, categorie in MARQUEURS_OFF if donnees.get(marqueur)]
    if "eau" in types and "boisson" in types:
        types.remove("boisson")
    return types


def categorieDepuisOff(donnees):
    """
    Le type de produit que propose Open Food Facts : le premier que désignent les marqueurs de
    son calcul de 2023 (typesMarquesParOff). Sans marqueur, c'est le cas général.
    """
    types = typesMarquesParOff(donnees)
    return types[0] if types else "general"


def composantesDeLaCategorie(categorie="general"):
    """
    Les lignes du tableau des points d'un type de produit, dans l'ordre : pour chacune, un
    dictionnaire (cle, libelle, unite, maximum, groupe), où groupe vaut « negatif » ou
    « positif ». La liste est vide pour l'eau, classée A sans calcul.
    """
    if categorie == "eau":
        return []
    lignes = []
    for groupe, composantes in (("negatif", COMPOSANTES_NEGATIVES[categorie]), ("positif", POSITIFS)):
        for cle in composantes:
            lignes.append({"cle": cle, "libelle": LIBELLES[cle], "unite": UNITES[cle],
                           "maximum": MAXIMUMS[categorie][cle], "groupe": groupe})
    return lignes


def valeursDuCalcul(produit, categorie):
    """
    Les valeurs que le calcul note, pour chaque composante du type de produit. Pour les
    matières grasses, l'énergie des AGS (sa × 37 kJ) et le ratio AGS / lipides (en %, 0 si les
    lipides manquent) se calculent à partir de sa et de lipides. Pour les boissons, les
    édulcorants valent 1 s'il y en a, 0 sinon.
    """
    valeurs = {cle: produit[cle] for cle in NEGATIFS + POSITIFS}
    if categorie == "matieresGrasses":
        lipides = produit.get("lipides") or 0
        valeurs["enAgs"] = produit["sa"] * KJ_PAR_GRAMME_AGS
        valeurs["ratioAgs"] = 100 * produit["sa"] / lipides if lipides > 0 else 0.0
        del valeurs["en"], valeurs["sa"]
    if categorie == "boisson":
        valeurs["edulcorants"] = 1 if produit.get("edulcorants") else 0
    return valeurs


def pointsDuCalcul(valeurs, categorie):
    """Les points de chaque composante, avec les barèmes du type de produit."""
    if categorie == "boisson":
        points = {"en": pointsDepuisSeuils(valeurs["en"], SEUILS_ENERGIE_BOISSONS),
                  "sa": pointsDepuisSeuils(valeurs["sa"], SEUILS_AGS),
                  "su": pointsDepuisSeuils(valeurs["su"], SEUILS_SUCRES_BOISSONS),
                  "so": pointsDepuisSeuils(valeurs["so"], SEUILS_SEL),
                  "edulcorants": POINTS_EDULCORANTS * valeurs["edulcorants"],
                  "pr": pointsDepuisSeuils(valeurs["pr"], SEUILS_PROTEINES_BOISSONS),
                  "fi": pointsDepuisSeuils(valeurs["fi"], SEUILS_FIBRES),
                  "fr": pointsFruits(valeurs["fr"], POINTS_FRUITS_BOISSONS)}
        return points
    if categorie == "matieresGrasses":
        points = {"enAgs": pointsDepuisSeuils(valeurs["enAgs"], SEUILS_ENERGIE_AGS),
                  "ratioAgs": pointsDepuisSeuils(valeurs["ratioAgs"], SEUILS_RATIO_AGS, inclusif=True)}
    else:
        points = {"en": pointsDepuisSeuils(valeurs["en"], SEUILS_ENERGIE),
                  "sa": pointsDepuisSeuils(valeurs["sa"], SEUILS_AGS)}
    points["su"] = pointsDepuisSeuils(valeurs["su"], SEUILS_SUCRES)
    points["so"] = pointsDepuisSeuils(valeurs["so"], SEUILS_SEL)
    points["pr"] = pointsDepuisSeuils(valeurs["pr"], SEUILS_PROTEINES)
    points["fi"] = pointsDepuisSeuils(valeurs["fi"], SEUILS_FIBRES)
    points["fr"] = pointsFruits(valeurs["fr"])
    if categorie == "viandeRouge":
        points["pr"] = min(points["pr"], PROTEINES_MAX_VIANDE_ROUGE)
    return points


def regleDesProteines(N, produit, categorie, exceptionFruits):
    """Dit si les protéines comptent, et pourquoi : renvoie (proteinesComptees, raison)."""
    if categorie == "fromage":
        return True, "les protéines comptent toujours pour un fromage"
    if categorie == "boisson":
        return True, "les protéines comptent toujours pour une boisson"
    seuil = SEUIL_PROTEINES_MATIERES_GRASSES if categorie == "matieresGrasses" else SEUIL_PROTEINES
    if N < seuil:
        return True, f"les protéines comptent : moins de {seuil} points négatifs"
    if exceptionFruits and produit["fr"] > 80:
        return True, "les protéines comptent : plus de 80 % de fruits, légumes et légumineuses (fig. 4)"
    return False, f"les protéines ne comptent pas : au moins {seuil} points négatifs"


def scoreNutriscore(produit, exceptionFruits=False, categorie="general"):
    """
    Calcule le Nutri-Score d'un produit (dictionnaire de clés en, sa, su, so, pr, fi, fr ;
    plus lipides pour les matières grasses et edulcorants pour les boissons).

    categorie : le type de produit (CATEGORIES), le cas général par défaut. Avec
    exceptionFruits=True, on applique la fig. 4 du sujet telle qu'elle est écrite : au-delà de
    80 % de fruits, légumes et légumineuses, les protéines comptent même à partir de 11 points
    négatifs (règle de 2017).

    Renvoie un dictionnaire : score, label, points (le détail par composante), N, P,
    proteinesComptees, raison (pourquoi les protéines comptent ou non), categorie, valeurs
    (les valeurs notées) et maximums (les points maximaux de chaque composante). Une eau est
    classée A sans calcul : son score vaut None.
    """
    if categorie == "eau":
        return {"score": None, "label": "A", "points": {}, "N": 0, "P": 0, "proteinesComptees": False,
                "raison": "les eaux sont classées A, sans calcul", "categorie": categorie,
                "valeurs": {}, "maximums": {}}
    valeurs = valeursDuCalcul(produit, categorie)
    points = pointsDuCalcul(valeurs, categorie)
    N = sum(points[composante] for composante in COMPOSANTES_NEGATIVES[categorie])
    proteinesComptees, raison = regleDesProteines(N, produit, categorie, exceptionFruits)
    if categorie == "viandeRouge":
        raison += f" ; viande rouge : au plus {PROTEINES_MAX_VIANDE_ROUGE} points de protéines"

    P = points["fi"] + points["fr"]
    if proteinesComptees:
        P += points["pr"]
    score = N - P
    return {"score": score, "label": labelDepuisScore(score, categorie), "points": points, "N": N, "P": P,
            "proteinesComptees": proteinesComptees, "raison": raison, "categorie": categorie,
            "valeurs": valeurs, "maximums": MAXIMUMS[categorie]}


# --- Question 3.2 : vérification sur la base ---

def verifierNutriscoreBase(produits):
    """
    Recalcule le Nutri-Score de chaque plat et le compare au score et au label donnés par OFF.
    Calcule aussi le score selon la fig. 4, pour repérer les plats où les deux règles divergent.

    Renvoie un dictionnaire : total, reproduits (score et label identiques à ceux d'OFF),
    ecarts (les plats qui diffèrent), divergencesFigure4 (les plats dont le label change avec
    la règle de la fig. 4) et lignes (le détail de chaque plat, pour l'Excel).
    """
    lignes, ecarts, divergences = [], [], []
    for plat in produits:
        calcul = scoreNutriscore(plat)
        figure4 = scoreNutriscore(plat, exceptionFruits=True)
        identique = calcul["score"] == plat["score"] and calcul["label"] == plat["label"]
        ligne = {"code": plat["code"], "nom": plat["nom"], "scoreOff": plat["score"], "labelOff": plat["label"],
                 "points": calcul["points"], "N": calcul["N"], "P": calcul["P"],
                 "proteinesComptees": calcul["proteinesComptees"], "score": calcul["score"],
                 "label": calcul["label"], "identique": identique,
                 "scoreFigure4": figure4["score"], "labelFigure4": figure4["label"]}
        lignes.append(ligne)
        if not identique:
            ecarts.append(f"{plat['code']} {plat['nom']} : OFF {plat['score']} {plat['label']}, "
                          f"calcul {calcul['score']} {calcul['label']}")
        if figure4["label"] != calcul["label"]:
            divergences.append(f"{plat['code']} {plat['nom']} : {calcul['label']} en 2023, "
                               f"{figure4['label']} selon la fig. 4")
    return {"total": len(produits), "reproduits": len(produits) - len(ecarts), "ecarts": ecarts,
            "divergencesFigure4": divergences, "lignes": lignes}


def verifierCasParticuliers():
    """
    Vérifie notre calcul des cas particuliers contre Open Food Facts. Chaque fiche du cache
    que le calcul de 2023 d'OFF marque (fromage, viande rouge, matière grasse, boisson, eau)
    est recalculée avec ce type, puis comparée au score et au label d'OFF (au label seul pour
    les eaux, classées A sans score). Les fiches viennent des plats préparés écartés de la
    base et des échantillons de vérification (ECHANTILLONS).
    Renvoie un dictionnaire : type → {total, reproduits, ecarts}.
    """
    import json
    from projet_base import DOSSIER_BRUT, produitDepuisFiche

    resultats = {categorie: {"total": 0, "reproduits": 0, "ecarts": []} for categorie in CATEGORIES if categorie != "general"}
    for chemin in sorted((DOSSIER_BRUT / "produits").glob("*.json")):
        reponse = json.loads(chemin.read_text(encoding="utf-8"))
        if reponse.get("status") != 1 or not reponse.get("product"):
            continue
        produit = produitDepuisFiche(reponse)
        off = produit["nutriscoreOff"]
        if produit["categorie"] == "general" or off is None:
            continue
        calcul = scoreNutriscore(produit, categorie=produit["categorie"])
        bilan = resultats[produit["categorie"]]
        bilan["total"] += 1
        if calcul["label"] == off["label"] and (calcul["score"] is None or calcul["score"] == off["score"]):
            bilan["reproduits"] += 1
        else:
            bilan["ecarts"].append(f"{produit['code']} {produit['nom']} : OFF {off['score']} {off['label']}, "
                                   f"calcul {calcul['score']} {calcul['label']}{explicationDeLEcart(reponse['product'])}")
    return resultats


# Les barèmes du cas général, par composante du calcul d'OFF, pour contrôler la lecture des seuils
SEUILS_DES_COMPOSANTES_OFF = {"energy": SEUILS_ENERGIE, "saturated_fat": SEUILS_AGS, "sugars": SEUILS_SUCRES,
                              "salt": SEUILS_SEL, "proteins": SEUILS_PROTEINES, "fiber": SEUILS_FIBRES}


# Les composantes du calcul d'OFF, sous les noms du sujet (pour écrire les explications des écarts)
CLES_DES_COMPOSANTES_OFF = {"energy": "en", "saturated_fat": "sa", "sugars": "su", "salt": "so",
                            "proteins": "pr", "fiber": "fi"}


def valeursPileDeLaFiche(fiche):
    """
    Les valeurs que le calcul de 2023 d'OFF note pile sur un seuil, pour une fiche du cas
    général (avec la valeur exacte du tableau nutritionnel quand elle existe). Renvoie une liste
    de (composante d'OFF, valeur, lecture) : lecture vaut « strict » quand OFF donne les points
    du bas, « inclusif » quand il en donne un de plus. Les protéines plafonnées d'une viande
    rouge ne comptent pas.
    """
    from projet_base import CHAMPS_NUTRIMENTS, valeurExacte

    calcul = (fiche.get("nutriscore") or {}).get("2023") or {}
    donnees = calcul.get("data") or {}
    if calcul.get("nutriscore_computed") != 1 or categorieDepuisOff(donnees) not in ("general", "fromage", "viandeRouge"):
        return []
    pile = []
    for cote in ("negative", "positive"):
        for composante in (donnees.get("components") or {}).get(cote, []):
            seuils, valeur = SEUILS_DES_COMPOSANTES_OFF.get(composante.get("id")), composante.get("value")
            if seuils is None or valeur is None:
                continue
            valeur = valeurExacte(valeur, fiche.get("nutriments") or {}, CHAMPS_NUTRIMENTS[composante["id"]][1])
            if valeur not in seuils or (composante["id"] == "proteins" and donnees.get("is_red_meat_product")):
                continue
            if composante.get("points") == pointsDepuisSeuils(valeur, seuils):
                pile.append((composante["id"], valeur, "strict"))
            elif composante.get("points") == pointsDepuisSeuils(valeur, seuils) + 1:
                pile.append((composante["id"], valeur, "inclusif"))
    return pile


def explicationDeLEcart(fiche):
    """
    Ce qui explique, d'après sa fiche, qu'OFF ne trouve pas notre résultat : il marque le
    produit de deux types à la fois et cumule leurs règles, ou il compte un point de plus pour
    une valeur pile sur un seuil. Renvoie la phrase, entre parenthèses, ou une chaîne vide.
    """
    donnees = ((fiche.get("nutriscore") or {}).get("2023") or {}).get("data") or {}
    types = typesMarquesParOff(donnees)
    if len(types) > 1:
        return f" (OFF le marque à la fois {' et '.join(CATEGORIES[t].lower() for t in types)}, et cumule leurs règles)"
    for identifiant, valeur, lecture in valeursPileDeLaFiche(fiche):
        if lecture == "inclusif":
            cle = CLES_DES_COMPOSANTES_OFF[identifiant]
            texte = f"{valeur:g}".replace(".", ",")
            return f" (OFF compte un point de plus pour une valeur pile sur un seuil : {LIBELLES[cle].lower()}, {texte} {UNITES[cle]})"
    return ""


def valeursPileSurUnSeuil(fiches=None):
    """
    Contrôle la lecture des seuils (choix 4 : un seuil doit être strictement dépassé) sur les
    calculs de 2023 d'OFF, au cas général. Pour chaque valeur notée par OFF qui tombe pile sur
    un seuil, on compte les fois où OFF lui donne les points du bas (« > », notre lecture) et
    celles où il lui en donne un de plus (« ≥ »). La valeur est la valeur exacte du tableau
    nutritionnel quand elle existe (valeurExacte, choix 13) : OFF affiche 0,4 g de sel mais
    compte 0,4043 g, qui n'est pas pile sur le seuil. Les protéines plafonnées d'une viande
    rouge ne comptent pas.
    fiches : des réponses de l'API produit (par défaut, toutes les fiches du cache).
    Renvoie un dictionnaire : composante d'OFF → {"strict": n, "inclusif": m, "exemples": codes « ≥ »}.
    """
    import json
    from projet_base import DOSSIER_BRUT

    if fiches is None:
        fiches = (json.loads(chemin.read_text(encoding="utf-8")) for chemin in sorted((DOSSIER_BRUT / "produits").glob("*.json")))
    controle = {}
    for reponse in fiches:
        fiche = reponse.get("product") or {}
        for identifiant, valeur, lecture in valeursPileDeLaFiche(fiche):
            bilan = controle.setdefault(identifiant, {"strict": 0, "inclusif": 0, "exemples": []})
            bilan[lecture] += 1
            if lecture == "inclusif":
                bilan["exemples"].append(str(fiche.get("code")))
    return controle


def ecrireVerification(verification, chemin=FICHIER_VERIFICATION, casParticuliers=None):
    """
    Écrit le détail de la vérification dans un classeur Excel, au style du projet ; avec
    casParticuliers (verifierCasParticuliers), une feuille de plus pour les cas particuliers.
    """
    from openpyxl import Workbook
    from projet_design import mettreEnFormeFeuille

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "vérification"
    feuille.append(["Code-barres", "Nom", "Score OFF", "Label OFF"]
                   + [f"Points {LIBELLES[c].lower()}" for c in NEGATIFS + POSITIFS]
                   + ["N", "P", "Protéines comptées", "Score calculé", "Label calculé", "Identique à OFF",
                      "Score selon la fig. 4", "Label selon la fig. 4"])
    for ligne in verification["lignes"]:
        feuille.append([ligne["code"], ligne["nom"], ligne["scoreOff"], ligne["labelOff"]]
                       + [ligne["points"][c] for c in NEGATIFS + POSITIFS]
                       + [ligne["N"], ligne["P"], "oui" if ligne["proteinesComptees"] else "non",
                          ligne["score"], ligne["label"], "oui" if ligne["identique"] else "non",
                          ligne["scoreFigure4"], ligne["labelFigure4"]])
    largeurs = [15, 42, 9, 9] + [11] * 7 + [6, 6, 11, 10, 10, 10, 11, 11]
    mettreEnFormeFeuille(feuille, largeurs, colonnesClasses=(4, 16, 19))

    if casParticuliers:
        feuilleCas = classeur.create_sheet("cas particuliers")
        feuilleCas.append(["Type de produit", "Fiches vérifiées", "Reproduites", "Écarts"])
        for categorie, bilan in casParticuliers.items():
            feuilleCas.append([CATEGORIES[categorie], bilan["total"], bilan["reproduits"], " ; ".join(bilan["ecarts"])])
        mettreEnFormeFeuille(feuilleCas, [38, 15, 12, 90])
    chemin.parent.mkdir(parents=True, exist_ok=True)
    classeur.save(chemin)


def afficherCalcul(nom, produit):
    """Affiche le calcul du Nutri-Score d'un produit, composante par composante."""
    resultat = scoreNutriscore(produit)
    print(nom)
    for composante in NEGATIFS + POSITIFS:
        print(f"  {LIBELLES[composante]:<33} {produit[composante]:>7g} {UNITES[composante]:<3}"
              f"{resultat['points'][composante]:>3} / {POINTS_MAX[composante]}")
    print(f"  N = {resultat['N']}, P = {resultat['P']} ({resultat['raison']})")
    print(f"  score = {resultat['score']}, label {resultat['label']}")


def main():
    """Affiche les deux exemples du sujet, puis vérifie le calcul sur la base de plats préparés."""
    for exemple in EXEMPLES_SUJET.values():
        afficherCalcul(exemple["nom"], exemple["produit"])
        print(f"  attendu : score {exemple['attendu'][0]}, label {exemple['attendu'][1]}\n")

    if not FICHIER_BASE.exists():
        print("La base n'est pas encore construite : lancer d'abord projet_base.py.")
        return
    verification = verifierNutriscoreBase(lireBase())
    casParticuliers = verifierCasParticuliers()
    ecrireVerification(verification, casParticuliers=casParticuliers)
    print(f"Base : {verification['reproduits']}/{verification['total']} plats reproduits (score et label d'OFF)")
    for ecart in verification["ecarts"]:
        print(f"  écart : {ecart}")
    print(f"Règle de la fig. 4 : {len(verification['divergencesFigure4'])} plat(s) changent de label")
    for divergence in verification["divergencesFigure4"]:
        print(f"  {divergence}")
    resultats = {
        "total": verification["total"],
        "reproduits": verification["reproduits"],
        "ecarts": verification["ecarts"],
        "divergencesFigure4": verification["divergencesFigure4"],
        "casParticuliers": casParticuliers,
        "seuilsPile": valeursPileSurUnSeuil(),
    }
    for composante, bilan in resultats["seuilsPile"].items():
        print(f"Valeurs pile sur un seuil, {composante} : {bilan['strict']} lues « > » par OFF, {bilan['inclusif']} « ≥ »")
    for categorie, bilan in casParticuliers.items():
        print(f"Cas particulier, {CATEGORIES[categorie].lower()} : {bilan['reproduits']}/{bilan['total']} fiches reproduites")
        for ecart in bilan["ecarts"]:
            print(f"  écart : {ecart}")

    from projet_base import FICHIER_BASE_ETENDUE, construireBaseEtendue, ficheEnDirect
    if FICHIER_BASE_ETENDUE.exists():
        etendue, entonnoir, infos = construireBaseEtendue(depuisCache=True, afficher=False)
        vivier = verifierNutriscoreBase(infos["vivier"])
        # chaque écart reçoit son explication, lue dans la fiche d'OFF gardée dans le cache
        ecarts = [ecart + explicationDeLEcart(ficheEnDirect(ecart.split(" ")[0], reseau=False)[0]["product"])
                  for ecart in vivier["ecarts"]]
        vivier["ecarts"] = ecarts
        resultats["vivierEtendu"] = {"total": vivier["total"], "reproduits": vivier["reproduits"], "ecarts": ecarts}
        print(f"Vivier étendu : {vivier['reproduits']}/{vivier['total']} plats reproduits")
        for ecart in vivier["ecarts"]:
            print(f"  écart : {ecart}")
    print(f"Détail : {FICHIER_VERIFICATION.relative_to(DOSSIER)}")
    enregistrerResultats("nutriscore", resultats)


if __name__ == "__main__":
    main()
