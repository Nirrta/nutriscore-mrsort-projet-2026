"""
projet_base.py : constitution de la base de plats préparés (question 3.1).

La base vient d'Open Food Facts (OFF), la base collaborative des produits alimentaires,
publiée sous licence ODbL. Elle contient 125 plats préparés vendus en France, 25 par
classe du Nutri-Score (A à E). Pour chaque plat, elle donne les sept composantes du
Nutri-Score, son score et son label, ainsi que les informations du SuperNutri-score
(groupe NOVA, nombre d'additifs) et le Green-Score.

La méthode, en quatre étapes :

1. Repérage. L'index de recherche d'OFF (search.openfoodfacts.org) donne des codes-barres
   de plats préparés vendus en France. Cet index range encore les produits selon le
   Nutri-Score de 2021 : il sert seulement à repérer des candidats de chaque classe. On y
   tire des pages au hasard, pour ne pas prendre que les plats les plus populaires, que
   d'autres groupes pourraient choisir aussi.
2. Détail. Pour chaque candidat, l'API produit d'OFF donne le calcul du Nutri-Score de 2023
   avec ses composantes. C'est la seule source retenue pour le score et le label.
3. Filtres. On garde les plats dont le Nutri-Score de 2023 est calculé, qui relèvent du cas
   général de l'algorithme (ni boisson, ni fromage, ni matière grasse, ni viande rouge),
   dont les sept composantes, le groupe NOVA et les additifs sont connus, et dont les
   valeurs sont plausibles. Notre propre calcul du Nutri-Score n'est pas un filtre : sinon,
   la vérification de la question 3.2 serait circulaire.
4. Tirage. On tire 25 plats par classe, au hasard, avec une graine fixée.

Toutes les réponses d'OFF sont gardées dans donnees/brut/. Avec --depuis-cache, le script
reconstruit exactement la même base, sans réseau.

La base étendue (--etendue) ajoute 50 plats par classe tirés hors de la base, avec les mêmes
filtres et la même graine : 375 plats, 75 par classe. Elle mesure les modèles sur des plats
qu'ils n'ont pas vus, puis sert à apprendre le modèle final.

L'interface lit aussi une fiche à la demande, par code-barres, lien ou nom (ficheEnDirect,
rechercherParNom, produitDepuisFiche) : sans filtre, pour n'importe quel produit.

Commandes :
    python3 projet_base.py                 # repérage et téléchargement (une quinzaine de minutes la première fois)
    python3 projet_base.py --depuis-cache  # la même base, sans réseau, en quelques secondes
    python3 projet_base.py --etendue       # la base étendue (375 plats ; environ une heure la première fois)
"""

import argparse
import json
import os
import random
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path


# --- Paramètres de la base ---

CATEGORIE = "en:meals"       # les plats préparés, dans la classification d'OFF
PAYS = "en:france"           # les produits vendus en France
CLASSES = ["a", "b", "c", "d", "e"]
PAR_CLASSE = 25              # plats tirés par classe : 125 en tout
GRAINE = 2026                # graine du hasard, choisie une fois pour toutes

# Pages de 100 candidats tirées au départ pour chaque classe de l'index (Nutri-Score de 2021).
# On en prend plus pour A et E : les classes de 2023 sont plus sévères, et c'est dans les
# classes extrêmes que les candidats risquent de manquer.
PAGES_PAR_CLASSE = {"a": 2, "b": 1, "c": 1, "d": 1, "e": 2}
TAILLE_PAGE = 100
PAGES_MAX = 100              # l'index ne sert pas plus de 10 000 résultats
TOURS_SUPPLEMENTAIRES = 6    # repérages complémentaires au plus, si une classe manque de plats

# La base étendue : la base, plus PAR_CLASSE_AJOUT plats par classe tirés hors de la base, soit 75 par classe.
# Elle sert à mesurer les modèles sur des plats qu'ils n'ont pas vus, puis à apprendre le modèle final.
PAR_CLASSE_AJOUT = 50
TOURS_ETENDUE = 12           # pages ajoutées au plus, classe par classe, pour la base étendue
LOT_BASE = "base du 30/10"   # la colonne « Lot » de la base étendue : d'où vient chaque plat
LOT_AJOUT = "ajout du 07/11"

# --- Accès à Open Food Facts ---

URL_RECHERCHE = "https://search.openfoodfacts.org/search"
URL_PRODUIT = "https://world.openfoodfacts.org/api/v2/product/{code}"
AGENT = "ProjetTransparenceM2MIAGE/1.0 (Universite Paris Dauphine-PSL)"
PAUSE_RECHERCHE = 2.0        # secondes entre deux recherches
PAUSE_PRODUIT = 1.0          # secondes entre deux fiches : OFF accepte au plus 100 fiches par minute
ESSAIS = 8                   # essais par requête avant d'abandonner
DELAI_DIRECT = 10            # secondes : une recherche depuis l'interface n'attend pas plus, et ne relance pas
RESULTATS_PAR_NOM = 10       # résultats au plus d'une recherche par nom
PREMIERE_ATTENTE = 30        # secondes d'attente après un refus, doublées à chaque nouvel essai (au plus 240)
CHAMPS_PRODUIT = ",".join([
    "code", "product_name", "product_name_fr", "brands", "quantity",
    "categories_tags", "countries_tags", "labels_tags",
    "nutriscore", "nutriments", "nova_group", "additives_n", "additives_tags",
    "environmental_score_score", "environmental_score_grade", "ecoscore_score", "ecoscore_grade",
    "last_modified_t",
])

# --- Fichiers ---

DOSSIER = Path(__file__).resolve().parent
DOSSIER_BRUT = DOSSIER / "donnees" / "brut"
FICHIER_BASE = DOSSIER / "donnees" / "base_plats_prepares.xlsx"
FICHIER_BASE_ETENDUE = DOSSIER / "donnees" / "base_etendue_plats_prepares.xlsx"
FICHIER_RESULTATS = DOSSIER / "resultats" / "resultats_projet.json"

# Les colonnes de la feuille « base », dans l'ordre : (clé utilisée dans le code, en-tête Excel).
# Les sept composantes portent les noms du sujet (§1.4) : en, sa, su, so, pr, fi, fr.
# « so » contient le sel en grammes, car les barèmes de 2023 sont en sel ; le sodium
# (sel / 2,5) est donné à part, en milligrammes.
COLONNES = [
    ("code", "Code-barres"),
    ("nom", "Nom"),
    ("marque", "Marque"),
    ("quantite", "Quantité"),
    ("url", "Fiche Open Food Facts"),
    ("en", "Énergie (kJ/100 g)"),
    ("kcal", "Énergie (kcal/100 g)"),
    ("sa", "Acides gras saturés (g/100 g)"),
    ("su", "Sucres (g/100 g)"),
    ("so", "Sel (g/100 g)"),
    ("sodium", "Sodium (mg/100 g)"),
    ("pr", "Protéines (g/100 g)"),
    ("fi", "Fibres (g/100 g)"),
    ("fr", "Fruits, légumes et légumineuses (%)"),
    ("score", "Score Nutri-Score"),
    ("label", "Label Nutri-Score"),
    ("nova", "Groupe NOVA"),
    ("additifs", "Nombre d'additifs"),
    ("listeAdditifs", "Additifs"),
    ("green", "Green-Score (/100)"),
    ("labelGreen", "Label Green-Score"),
    ("bio", "Bio"),
    ("modifie", "Fiche modifiée le"),
]
# La base étendue a une colonne de plus : le lot d'où vient chaque plat (LOT_BASE ou LOT_AJOUT)
COLONNES_ETENDUE = COLONNES + [("lot", "Lot")]
CLES_OBLIGATOIRES = ["label", "score", "en", "sa", "su", "so", "pr", "fi", "fr"]

# Les étapes de l'entonnoir, dans l'ordre où les filtres s'appliquent
ETAPES = [
    "fiche disponible",
    "plat préparé vendu en France",
    "Nutri-Score 2023 calculé",
    "cas général du Nutri-Score",
    "sept composantes connues",
    "NOVA et additifs connus",
    "valeurs plausibles",
]


# --- Question 3.1 : accès à Open Food Facts, avec un cache ---

def lireJson(url, parametres, fichierCache, pause, depuisCache):
    """
    Renvoie la réponse JSON d'OFF à une requête. La réponse est lue dans le cache si elle y
    est déjà ; sinon elle est demandée à OFF puis rangée dans le cache.

    OFF répond 503 quand il est surchargé et 429 quand on va trop vite : on attend alors de
    plus en plus longtemps avant de réessayer, ou le délai qu'OFF indique (en-tête
    Retry-After). Un produit inconnu (404) est mis en cache comme les autres réponses.
    """
    if fichierCache.exists():
        return json.loads(fichierCache.read_text(encoding="utf-8"))
    if depuisCache:
        raise FileNotFoundError(f"{fichierCache} manque dans le cache : relancer sans --depuis-cache.")

    adresse = url + "?" + urllib.parse.urlencode(parametres)
    attente = PREMIERE_ATTENTE
    for essai in range(ESSAIS):
        try:
            requete = urllib.request.Request(adresse, headers={"User-Agent": AGENT})
            with urllib.request.urlopen(requete, timeout=60) as reponse:
                donnees = json.loads(reponse.read().decode("utf-8"))
        except urllib.error.HTTPError as erreur:
            if erreur.code != 404:
                delaiIndique = valeurNombre(erreur.headers.get("Retry-After"))
                time.sleep(delaiIndique if delaiIndique else attente)
                attente = min(attente * 2, 240)
                continue
            donnees = {"status": 0, "status_verbose": "product not found"}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(attente)
            attente = min(attente * 2, 240)
            continue
        fichierCache.parent.mkdir(parents=True, exist_ok=True)
        fichierCache.write_text(json.dumps(donnees, ensure_ascii=False), encoding="utf-8")
        time.sleep(pause)
        return donnees
    raise RuntimeError(f"OFF ne répond pas à {adresse}")


def requeteRecherche(classe2021):
    """Renvoie la requête de l'index : plats préparés vendus en France, d'une classe de 2021."""
    return f'categories_tags:"{CATEGORIE}" AND countries_tags:"{PAYS}" AND nutrition_grades:"{classe2021}"'


def nombreDePages(classe2021, depuisCache):
    """Renvoie le nombre de pages de 100 candidats que l'index propose pour une classe de 2021."""
    reponse = lireJson(URL_RECHERCHE, {"q": requeteRecherche(classe2021), "page_size": 1, "fields": "code"},
                       DOSSIER_BRUT / "recherche" / f"{classe2021}_compte.json", PAUSE_RECHERCHE, depuisCache)
    nombre = reponse.get("count", 0)
    return min(PAGES_MAX, (nombre + TAILLE_PAGE - 1) // TAILLE_PAGE)


def codesDeLaPage(classe2021, page, depuisCache):
    """Renvoie les codes-barres d'une page de l'index de recherche."""
    reponse = lireJson(URL_RECHERCHE,
                       {"q": requeteRecherche(classe2021), "page_size": TAILLE_PAGE, "page": page, "fields": "code"},
                       DOSSIER_BRUT / "recherche" / f"{classe2021}_page{page:03d}.json", PAUSE_RECHERCHE, depuisCache)
    return [str(resultat["code"]) for resultat in reponse.get("hits", []) if resultat.get("code")]


def ficheProduit(code, depuisCache):
    """Renvoie la réponse de l'API produit d'OFF pour un code-barres."""
    return lireJson(URL_PRODUIT.format(code=code), {"fields": CHAMPS_PRODUIT},
                    DOSSIER_BRUT / "produits" / f"{code}.json", PAUSE_PRODUIT, depuisCache)


def dateExtraction(depuisCache, nomFichier="extraction.json"):
    """
    Renvoie la date du premier téléchargement, rangée dans le cache. Ainsi, une base
    reconstruite depuis le cache garde la date des données, et non celle du jour.
    La base étendue a sa propre date, dans extraction_etendue.json.
    """
    fichier = DOSSIER_BRUT / nomFichier
    if fichier.exists():
        return json.loads(fichier.read_text(encoding="utf-8"))["date"]
    if depuisCache:
        raise FileNotFoundError(f"{fichier} manque dans le cache : relancer sans --depuis-cache.")
    fichier.parent.mkdir(parents=True, exist_ok=True)
    jour = date.today().isoformat()
    fichier.write_text(json.dumps({"date": jour}), encoding="utf-8")
    return jour


# --- Question 3.1 : lecture d'une fiche et filtres ---

def valeurNombre(valeur):
    """Convertit une valeur d'OFF en nombre décimal, ou renvoie None si elle manque."""
    if valeur is None or valeur == "":
        return None
    try:
        return float(valeur)
    except (TypeError, ValueError):
        return None


def valeursPlausibles(valeurs, graisses, glucides):
    """
    Écarte les fiches visiblement fausses et les produits à reconstituer (en poudre) :
    - énergie entre 0 et 3 800 kJ pour 100 g ;
    - acides gras saturés, sucres, protéines et fibres entre 0 et 100 g ;
    - sel entre 0 et 10 g : au-delà, c'est une erreur ou un concentré ;
    - fruits, légumes et légumineuses entre 0 et 100 % ;
    - acides gras saturés au plus égaux aux graisses, sucres au plus égaux aux glucides ;
    - graisses, glucides, protéines, fibres et sel ensemble au plus égaux à 105 g.
    Les graisses et les glucides ne servent qu'à ces contrôles ; ils peuvent manquer (None).
    """
    if not 0 <= valeurs["en"] <= 3800:
        return False
    for cle in ("sa", "su", "pr", "fi"):
        if not 0 <= valeurs[cle] <= 100:
            return False
    if not 0 <= valeurs["so"] <= 10:
        return False
    if not 0 <= valeurs["fr"] <= 100:
        return False
    if graisses is not None and valeurs["sa"] > graisses + 0.1:
        return False
    if glucides is not None and valeurs["su"] > glucides + 0.1:
        return False
    if graisses is not None and glucides is not None:
        if graisses + glucides + valeurs["pr"] + valeurs["fi"] + valeurs["so"] > 105:
            return False
    return True


# Pour chaque composante du calcul d'OFF : sa clé dans le sujet et ses champs du tableau nutritionnel
CHAMPS_NUTRIMENTS = {
    "energy": ("en", ["energy-kj_100g"]),
    "saturated_fat": ("sa", ["saturated-fat_100g"]),
    "sugars": ("su", ["sugars_100g"]),
    "salt": ("so", ["salt_100g"]),
    "proteins": ("pr", ["proteins_100g"]),
    "fiber": ("fi", ["fiber_100g"]),
    "fruits_vegetables_legumes": ("fr", ["fruits-vegetables-legumes_100g",
                                         "fruits-vegetables-legumes-estimate-from-ingredients_100g"]),
}


def valeurExacte(arrondie, nutriments, champs):
    """
    OFF affiche dans son calcul des valeurs arrondies (0,4 g de sel), mais compte les points
    avec la valeur exacte du tableau nutritionnel (0,4043 g, donc au-dessus du seuil de 0,4).
    On reprend la valeur exacte quand elle correspond à la valeur arrondie, à 1 % ou 0,01 près ;
    sinon, on garde la valeur du calcul.
    """
    for champ in champs:
        exacte = valeurNombre(nutriments.get(champ))
        if exacte is not None and (arrondie is None or abs(exacte - arrondie) <= max(0.01, 0.01 * abs(arrondie))):
            return exacte
    return arrondie


def valeursDuCalculOff(fiche):
    """
    Renvoie les sept composantes qu'OFF a utilisées pour calculer le Nutri-Score de 2023
    d'une fiche, sous les noms du sujet (en, sa, su, so, pr, fi, fr), avec leur valeur
    exacte (valeurExacte). Une composante inconnue vaut None. Les fibres ne sont retenues
    que si elles sont déclarées dans le tableau nutritionnel.

    Quand OFF ne compte pas les protéines (au moins 11 points négatifs), elles manquent dans
    son calcul : on les lit alors dans le tableau nutritionnel.
    """
    calcul = (fiche.get("nutriscore") or {}).get("2023") or {}
    composantes = {}
    for cote in ("negative", "positive"):
        for composante in ((calcul.get("data") or {}).get("components") or {}).get(cote, []):
            composantes[composante.get("id")] = valeurNombre(composante.get("value"))
    nutriments = fiche.get("nutriments") or {}

    valeurs = {}
    for identifiant, (cle, champs) in CHAMPS_NUTRIMENTS.items():
        if identifiant in composantes:
            valeurs[cle] = valeurExacte(composantes[identifiant], nutriments, champs)
        else:
            valeurs[cle] = None
    if valeurs["pr"] is None:
        valeurs["pr"] = valeurNombre(nutriments.get("proteins_100g"))
    fibresDeclarees = valeurNombre(nutriments.get("fiber_100g"))
    if fibresDeclarees is None:
        valeurs["fi"] = None
    elif valeurs["fi"] is None:
        valeurs["fi"] = fibresDeclarees
    return valeurs


def extraireProduit(reponse):
    """
    Lit la réponse de l'API produit d'OFF. Renvoie (produit, None) si le plat passe tous les
    filtres, ou (None, étape) avec la première étape de l'entonnoir (ETAPES) qu'il ne passe pas.
    """
    fiche = reponse.get("product")
    if reponse.get("status") != 1 or not fiche:
        return None, "fiche disponible"

    if CATEGORIE not in (fiche.get("categories_tags") or []) or PAYS not in (fiche.get("countries_tags") or []):
        return None, "plat préparé vendu en France"

    calcul = (fiche.get("nutriscore") or {}).get("2023") or {}
    if calcul.get("nutriscore_computed") != 1 or calcul.get("grade") not in CLASSES:
        return None, "Nutri-Score 2023 calculé"

    donnees = calcul.get("data") or {}
    for casParticulier in ["is_beverage", "is_water", "is_cheese", "is_fat_oil_nuts_seeds", "is_red_meat_product"]:
        if donnees.get(casParticulier):
            return None, "cas général du Nutri-Score"

    valeurs = valeursDuCalculOff(fiche)
    nutriments = fiche.get("nutriments") or {}
    nom = (fiche.get("product_name_fr") or fiche.get("product_name") or "").strip()
    if not nom or None in valeurs.values():
        return None, "sept composantes connues"

    nova = valeurNombre(fiche.get("nova_group"))
    additifs = valeurNombre(fiche.get("additives_n"))
    if nova not in (1, 2, 3, 4) or additifs is None:
        return None, "NOVA et additifs connus"

    graisses = valeurNombre(nutriments.get("fat_100g"))
    glucides = valeurNombre(nutriments.get("carbohydrates_100g"))
    if not valeursPlausibles(valeurs, graisses, glucides):
        return None, "valeurs plausibles"

    # Le plat est retenu : on rassemble sa ligne de la base
    code = str(fiche.get("code") or reponse.get("code"))
    kcal = valeurNombre(nutriments.get("energy-kcal_100g"))
    produit = dict(valeurs)
    produit.update(champsDeLaFiche(fiche, code))
    produit.update({
        "kcal": kcal if kcal is not None else valeurs["en"] / 4.184,
        "sodium": valeurs["so"] * 400,          # 1 g de sel contient 0,4 g de sodium
        "score": int(calcul["score"]),
        "label": calcul["grade"].upper(),
    })
    return produit, None


def champsDeLaFiche(fiche, code):
    """
    Les champs descriptifs d'une fiche d'OFF : nom, marque, quantité, lien, groupe NOVA (None
    s'il est inconnu), nombre et liste des additifs, Green-Score, bio, date de modification.
    """
    nova = valeurNombre(fiche.get("nova_group"))
    additifs = valeurNombre(fiche.get("additives_n"))
    green = valeurNombre(fiche.get("environmental_score_score"))
    if green is None:
        green = valeurNombre(fiche.get("ecoscore_score"))
    labelGreen = fiche.get("environmental_score_grade") or fiche.get("ecoscore_grade")
    labelsBio = {"en:organic", "en:eu-organic", "fr:ab-agriculture-biologique"}
    return {
        "code": code,
        "nom": (fiche.get("product_name_fr") or fiche.get("product_name") or "").strip(),
        "marque": (fiche.get("brands") or "").split(",")[0].strip(),
        "quantite": (fiche.get("quantity") or "").strip(),
        "url": f"https://fr.openfoodfacts.org/produit/{code}",
        "nova": int(nova) if nova in (1, 2, 3, 4) else None,
        "additifs": int(additifs) if additifs is not None else None,
        "listeAdditifs": ", ".join(tag.split(":")[-1].upper() for tag in fiche.get("additives_tags") or []),
        "green": green,
        "labelGreen": labelGreen.upper().replace("-PLUS", "+") if labelGreen in ("a-plus", "a", "b", "c", "d", "e", "f") else "",
        "bio": "oui" if labelsBio & set(fiche.get("labels_tags") or []) else "non",
        "modifie": datetime.fromtimestamp(fiche["last_modified_t"]).date().isoformat() if fiche.get("last_modified_t") else "",
    }


def sansDoublon(produits):
    """
    Retire les doublons : deux fiches qui ont le même nom et la même marque (souvent deux
    formats d'un même plat) n'en font qu'une. On garde celle dont le code-barres est le plus petit.
    """
    gardes = {}
    for produit in sorted(produits, key=lambda p: p["code"]):
        cle = (produit["nom"].lower(), produit["marque"].lower())
        if cle not in gardes:
            gardes[cle] = produit
    return sorted(gardes.values(), key=lambda p: p["code"])


def construireVivier(codes, depuisCache, afficher=True):
    """
    Lit la fiche de chaque candidat et applique les filtres dans l'ordre.
    Renvoie (vivier, entonnoir) : les plats retenus, et pour chaque étape le nombre de
    candidats qui la passent.
    """
    entonnoir = {"candidats repérés": len(codes)}
    for etape in ETAPES:
        entonnoir[etape] = 0
    retenus = []
    for numero, code in enumerate(codes, start=1):
        produit, echec = extraireProduit(ficheProduit(code, depuisCache))
        for etape in ETAPES:          # chaque étape passée avant l'échec est comptée
            if etape == echec:
                break
            entonnoir[etape] += 1
        if produit:
            retenus.append(produit)
        if afficher and numero % 100 == 0:
            print(f"  {numero}/{len(codes)} fiches lues")
    vivier = sansDoublon(retenus)
    entonnoir["sans doublon"] = len(vivier)
    return vivier, entonnoir


def vivierParClasse(vivier):
    """Compte les plats retenus dans chaque classe du Nutri-Score de 2023."""
    return {classe.upper(): sum(1 for p in vivier if p["label"] == classe.upper()) for classe in CLASSES}


# --- Question 3.1 : repérage des candidats et tirage ---

def ajouterPage(classe2021, pagesRestantes, pagesTirees, codes, depuisCache):
    """
    Tire la prochaine page au hasard pour une classe de 2021 et ajoute ses codes-barres
    à la liste des candidats (sans doublon). Renvoie False s'il n'y a plus de page à tirer.
    """
    if not pagesRestantes[classe2021]:
        return False
    page = pagesRestantes[classe2021].pop(0)
    pagesTirees[classe2021].append(page)
    for code in codesDeLaPage(classe2021, page, depuisCache):
        if code not in codes:
            codes.append(code)
    return True


def tirerEchantillon(vivier, parClasse=PAR_CLASSE, graine=GRAINE):
    """
    Tire au hasard parClasse plats de chaque classe du Nutri-Score de 2023, avec une graine
    fixée. Les candidats sont d'abord rangés par code-barres, pour que le tirage ne dépende
    pas de l'ordre de lecture.
    """
    hasard = random.Random(graine)
    echantillon = []
    for classe in CLASSES:
        candidats = sorted((p for p in vivier if p["label"] == classe.upper()), key=lambda p: p["code"])
        if len(candidats) < parClasse:
            raise ValueError(f"Seulement {len(candidats)} plats de classe {classe.upper()} : il en faut {parClasse}.")
        tires = hasard.sample(candidats, parClasse)
        echantillon += sorted(tires, key=lambda p: p["nom"].lower())
    return echantillon


def ordreDesPages(graine, depuisCache):
    """
    Les pages de l'index pour chaque classe de 2021, dans un ordre tiré au hasard avec la
    graine. La base prend les premières ; la base étendue reprend là où la base s'est arrêtée.
    """
    hasardPages = random.Random(graine)
    ordre = {}
    for classe in CLASSES:
        pages = list(range(1, nombreDePages(classe, depuisCache) + 1))
        hasardPages.shuffle(pages)
        ordre[classe] = pages
    return ordre


def construireBase(graine=GRAINE, depuisCache=False, afficher=True):
    """
    Enchaîne le repérage, les filtres et le tirage. Renvoie (base, entonnoir, infos) :
    les 125 plats tirés, l'entonnoir des filtres et les informations de la notice
    (graine, pages tirées, vivier par classe, date d'extraction).
    """
    jour = dateExtraction(depuisCache)

    # Les pages de chaque classe de 2021, dans un ordre tiré au hasard
    pagesRestantes = ordreDesPages(graine, depuisCache)
    pagesTirees = {classe: [] for classe in CLASSES}

    # Premier repérage
    codes = []
    for classe in CLASSES:
        for _ in range(PAGES_PAR_CLASSE[classe]):
            ajouterPage(classe, pagesRestantes, pagesTirees, codes, depuisCache)
    if afficher:
        print(f"{len(codes)} candidats repérés, lecture des fiches…")
    vivier, entonnoir = construireVivier(codes, depuisCache, afficher)

    # Repérages complémentaires : une page de plus dans la même lettre, tant qu'une classe manque de plats
    for _ in range(TOURS_SUPPLEMENTAIRES):
        manquantes = [classe for classe in CLASSES if vivierParClasse(vivier)[classe.upper()] < PAR_CLASSE]
        if not manquantes:
            break
        if afficher:
            print(f"Classes à compléter : {', '.join(c.upper() for c in manquantes)}")
        for classe in manquantes:
            ajouterPage(classe, pagesRestantes, pagesTirees, codes, depuisCache)
        vivier, entonnoir = construireVivier(codes, depuisCache, afficher)

    base = tirerEchantillon(vivier, PAR_CLASSE, graine)
    infos = {
        "graine": graine,
        "dateExtraction": jour,
        "pagesTirees": {classe.upper(): sorted(pages) for classe, pages in pagesTirees.items()},
        "vivierParClasse": vivierParClasse(vivier),
    }
    return base, entonnoir, infos


def horsDeLaBase(plats, base):
    """
    Les plats qui ne sont pas dans la base : ni le même code-barres, ni le même nom avec la
    même marque (un autre format du même plat). Une marque vide relue dans l'Excel vaut None.
    """
    nomEtMarque = lambda plat: ((plat["nom"] or "").lower(), (plat["marque"] or "").lower())
    codes = {plat["code"] for plat in base}
    nomsEtMarques = {nomEtMarque(plat) for plat in base}
    return [plat for plat in plats if plat["code"] not in codes and nomEtMarque(plat) not in nomsEtMarques]


def construireBaseEtendue(graine=GRAINE, depuisCache=False, afficher=True):
    """
    La base étendue : les 125 plats de la base, plus PAR_CLASSE_AJOUT plats par classe tirés
    hors de la base, avec les mêmes filtres et la même graine, soit 75 plats par classe.

    On reprend l'ordre des pages tiré pour la base (ordreDesPages), là où la base s'est
    arrêtée : tant qu'une classe manque de plats hors base, on ajoute une page de la même
    lettre de l'index. La base elle-même ne change pas.

    Renvoie (etendue, entonnoir, infos). Chaque plat porte son lot : LOT_BASE ou LOT_AJOUT ;
    infos["vivier"] donne tous les plats retenus, tirés ou non.
    """
    base, _, infosBase = construireBase(graine, depuisCache, afficher=False)
    jour = dateExtraction(depuisCache, "extraction_etendue.json")

    # Les pages déjà tirées pour la base sont les premières de l'ordre ; la suite reste à tirer
    ordre = ordreDesPages(graine, depuisCache)
    dejaTirees = {classe: ordre[classe][:len(infosBase["pagesTirees"][classe.upper()])] for classe in CLASSES}
    pagesRestantes = {classe: ordre[classe][len(dejaTirees[classe]):] for classe in CLASSES}
    pagesAjoutees = {classe: [] for classe in CLASSES}
    codes = []
    for classe in CLASSES:
        for page in dejaTirees[classe]:
            for code in codesDeLaPage(classe, page, depuisCache):
                if code not in codes:
                    codes.append(code)
    vivier, entonnoir = construireVivier(codes, depuisCache, afficher)

    # Une page de plus dans la même lettre, tant qu'une classe manque de plats hors base
    for _ in range(TOURS_ETENDUE):
        horsBase = vivierParClasse(horsDeLaBase(vivier, base))
        manquantes = [classe for classe in CLASSES if horsBase[classe.upper()] < PAR_CLASSE_AJOUT]
        if not manquantes:
            break
        if afficher:
            print(f"Classes à compléter hors base : {', '.join(c.upper() for c in manquantes)}")
        for classe in manquantes:
            ajouterPage(classe, pagesRestantes, pagesAjoutees, codes, depuisCache)
        vivier, entonnoir = construireVivier(codes, depuisCache, afficher)

    ajout = tirerEchantillon(horsDeLaBase(vivier, base), PAR_CLASSE_AJOUT, graine)
    etendue = [dict(plat, lot=LOT_BASE) for plat in base] + [dict(plat, lot=LOT_AJOUT) for plat in ajout]
    infos = {
        "graine": graine,
        "dateExtraction": jour,
        "parClasse": PAR_CLASSE + PAR_CLASSE_AJOUT,
        "ajoutParClasse": PAR_CLASSE_AJOUT,
        "pagesTirees": {classe.upper(): sorted(dejaTirees[classe] + pagesAjoutees[classe]) for classe in CLASSES},
        "pagesAjoutees": {classe.upper(): sorted(pages) for classe, pages in pagesAjoutees.items()},
        "vivierParClasse": vivierParClasse(vivier),
        "vivierHorsBase": vivierParClasse(horsDeLaBase(vivier, base)),
        "vivier": vivier,                       # tous les plats retenus, pour vérifier notre Nutri-Score (non rangé dans le JSON)
    }
    return etendue, entonnoir, infos


# --- Questions 3.2 et 3.5 : un produit d'OFF à la demande, pour l'interface ---

def reseauPermis():
    """Le réseau est permis, sauf si la variable d'environnement PROJET_HORS_LIGNE vaut 1 (pour les tests)."""
    return os.environ.get("PROJET_HORS_LIGNE") != "1"


def codeDepuisSaisie(texte):
    """
    Lit un code-barres dans ce que l'utilisateur a saisi : un code de 8 à 14 chiffres (les
    espaces sont permis), ou un lien vers une fiche d'Open Food Facts, dans n'importe quelle
    langue (…/produit/<code>/…, …/product/<code>). Renvoie le code, ou None.
    """
    texte = (texte or "").strip()
    if "openfoodfacts" in texte.lower():
        trouve = re.search(r"/(\d{8,14})(?:[/?#]|$)", texte)
        return trouve.group(1) if trouve else None
    chiffres = texte.replace(" ", "")
    if chiffres.isdigit() and 8 <= len(chiffres) <= 14:
        return chiffres
    return None


def sansAccents(texte):
    """Le texte en minuscules et sans accents : « Poêlée » devient « poelee »."""
    decompose = unicodedata.normalize("NFKD", texte or "")
    return "".join(caractere for caractere in decompose if not unicodedata.combining(caractere)).lower()


def motsDeLaRecherche(texte):
    """
    Les mots d'une recherche, en minuscules et sans accents ni ponctuation. Le « s » ou le
    « x » final d'un mot de plus de trois lettres tombe : « lasagnes » trouve aussi « Lasagne ».
    """
    mots = []
    for mot in re.findall(r"\w+", sansAccents(texte)):
        if len(mot) > 3 and mot[-1] in "sx":
            mot = mot[:-1]
        mots.append(mot)
    return mots


def correspond(mots, texte):
    """Vrai si chaque mot de la recherche se trouve dans le texte (un nom et une marque), accents mis à part."""
    texte = sansAccents(texte)
    return all(mot in texte for mot in mots)


def fichesDuCache():
    """Le nom et la marque de chaque fiche gardée dans le cache : une liste de (code, nom, marque)."""
    fiches = []
    for chemin in sorted((DOSSIER_BRUT / "produits").glob("*.json")):
        fiche = json.loads(chemin.read_text(encoding="utf-8")).get("product") or {}
        nom = (fiche.get("product_name_fr") or fiche.get("product_name") or "").strip()
        if nom:
            fiches.append((chemin.stem, nom, (fiche.get("brands") or "").split(",")[0].strip()))
    return fiches


def lireEnDirect(url, parametres):
    """
    Une seule requête à OFF, pour l'interface : délai DELAI_DIRECT, sans relance et sans
    écrire dans le cache. Renvoie (données, None), ou (None, message) si OFF ne répond pas
    (le message dit quoi faire) ; une réponse 404 donne (None, None).
    """
    adresse = url + "?" + urllib.parse.urlencode(parametres)
    try:
        requete = urllib.request.Request(adresse, headers={"User-Agent": AGENT})
        with urllib.request.urlopen(requete, timeout=DELAI_DIRECT) as reponse:
            return json.loads(reponse.read().decode("utf-8")), None
    except urllib.error.HTTPError as erreur:
        if erreur.code == 404:
            return None, None
        return None, "Open Food Facts est surchargé : réessayez dans une minute, ou saisissez les valeurs à la main."
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None, "Open Food Facts est injoignable : vérifiez la connexion, ou saisissez les valeurs à la main."


def rechercherParNom(texte, reseau=None):
    """
    Cherche des produits par leur nom : d'abord dans les fiches du cache, sans réseau, puis,
    si le réseau est permis (reseau=None suit reseauPermis), dans l'index de recherche d'OFF,
    parmi les produits vendus en France. Dans le cache, tous les mots saisis doivent se
    trouver dans le nom ou la marque ; les accents et les majuscules ne comptent pas.
    Renvoie (résultats, erreur) : au plus RESULTATS_PAR_NOM dictionnaires (code, nom, marque,
    source « cache » ou « OFF »), ceux du cache d'abord ; erreur dit si OFF n'a pas répondu.
    """
    mots = motsDeLaRecherche(texte)
    if not mots:
        return [], None
    resultats = [{"code": code, "nom": nom, "marque": marque, "source": "cache"}
                 for code, nom, marque in fichesDuCache() if correspond(mots, f"{nom} {marque}")]
    resultats = resultats[:RESULTATS_PAR_NOM]
    if reseau is None:
        reseau = reseauPermis()
    if not reseau or len(resultats) >= RESULTATS_PAR_NOM:
        return resultats, None

    # L'index d'OFF classe les produits qui ont au moins un des mots : on lui en demande plus, et l'on
    # garde ceux qui ont tous les mots ; s'il n'y en a aucun, on garde ses premiers résultats.
    # Les signes qui ont un sens dans la syntaxe de l'index (« : », guillemets…) sont retirés.
    requete = " ".join(re.findall(r"\w+", texte)) + f' countries_tags:"{PAYS}"'
    reponse, erreur = lireEnDirect(URL_RECHERCHE, {"q": requete, "page_size": 5 * RESULTATS_PAR_NOM,
                                                   "fields": "code,product_name,product_name_fr,brands"})
    trouves = []
    for trouve in (reponse or {}).get("hits", []):
        code = str(trouve.get("code") or "")
        nom = (trouve.get("product_name_fr") or trouve.get("product_name") or "").strip()
        marques = trouve.get("brands") or ""
        marque = (marques[0] if isinstance(marques, list) and marques else str(marques).split(",")[0]).strip()
        if code and nom:
            trouves.append({"code": code, "nom": nom, "marque": marque, "source": "OFF"})
    complets = [trouve for trouve in trouves if correspond(mots, f"{trouve['nom']} {trouve['marque']}")]
    dejaVus = {resultat["code"] for resultat in resultats}
    for trouve in complets or trouves:
        if trouve["code"] not in dejaVus:
            resultats.append(trouve)
            dejaVus.add(trouve["code"])
    return resultats[:RESULTATS_PAR_NOM], erreur


def ficheEnDirect(code, reseau=None):
    """
    La fiche d'un produit pour l'interface : d'abord dans le cache (donnees/brut/produits/),
    sinon par une seule requête à l'API produit d'OFF (lireEnDirect), si le réseau est permis
    (reseau=None suit reseauPermis). Renvoie (réponse, None), ou (None, message).
    """
    fichier = DOSSIER_BRUT / "produits" / f"{code}.json"
    if fichier.exists():
        reponse = json.loads(fichier.read_text(encoding="utf-8"))
    else:
        if reseau is None:
            reseau = reseauPermis()
        if not reseau:
            return None, f"Le code {code} n'est pas dans les fiches gardées, et l'interface est hors ligne."
        reponse, erreur = lireEnDirect(URL_PRODUIT.format(code=code), {"fields": CHAMPS_PRODUIT})
        if erreur:
            return None, erreur
    if not reponse or reponse.get("status") != 1 or not reponse.get("product"):
        return None, f"Open Food Facts ne connaît pas le code {code}."
    return reponse, None


def produitDepuisFiche(reponse):
    """
    Lit une fiche d'OFF pour l'interface, sans les filtres de la base : n'importe quel produit.
    Renvoie un dictionnaire :
    - les sept composantes (en, sa, su, so, pr, fi, fr), lues comme pour la base
      (valeursDuCalculOff). Des fibres absentes du tableau nutritionnel, mais qu'OFF a estimées
      et comptées, sont reprises et signalées dans la liste « estimees ». Ce que le calcul d'OFF
      ne montre pas (l'énergie et les AGS des matières grasses, ou tout, s'il ne calcule pas le
      Nutri-Score du produit) vient du tableau nutritionnel ; sans tableau, les AGS d'une matière
      grasse se déduisent de l'énergie des AGS (÷ 37). Une valeur encore manquante vaut 0, comme
      dans le calcul d'OFF, et la liste « manquantes » la signale ;
    - lipides (pour les matières grasses ; sans tableau, déduits du ratio AGS / lipides
      d'OFF) et edulcorants (pour les boissons) ;
    - categorie : le type proposé par OFF (categorieDepuisOff), et raisonCategorie, qui le dit ;
    - nutriscoreOff : le score et le label de 2023 d'OFF, ou None s'il ne les calcule pas ;
    - platPrepare : vrai pour un plat préparé (en:meals), le domaine de nos modèles MR-Sort ;
    - les champs de la fiche (champsDeLaFiche) : code, nom, marque, quantité, lien, NOVA…
    """
    from projet_nutriscore import CATEGORIES, KJ_PAR_GRAMME_AGS, categorieDepuisOff

    fiche = reponse.get("product") or {}
    calcul = (fiche.get("nutriscore") or {}).get("2023") or {}
    donnees = calcul.get("data") or {}
    nutriments = fiche.get("nutriments") or {}
    composantes = {}                                     # les valeurs que le calcul d'OFF a notées
    for cote in ("negative", "positive"):
        for composante in (donnees.get("components") or {}).get(cote, []):
            composantes[composante.get("id")] = valeurNombre(composante.get("value"))

    valeurs = valeursDuCalculOff(fiche)
    estimees = []
    if valeurs["fi"] is None and composantes.get("fiber") is not None:
        valeurs["fi"] = composantes["fiber"]
        estimees.append("fi")
    # Ce que le calcul d'OFF ne montre pas (l'énergie et les AGS des matières grasses), ou tout, quand OFF
    # ne calcule pas le Nutri-Score du produit : on le lit dans le tableau nutritionnel
    for cle, champs in list(CHAMPS_NUTRIMENTS.values()) + [("en", ["energy_100g"])]:
        for champ in champs:
            if valeurs[cle] is None:
                valeurs[cle] = valeurNombre(nutriments.get(champ))
    if valeurs["sa"] is None and composantes.get("energy_from_saturated_fat") is not None:
        valeurs["sa"] = composantes["energy_from_saturated_fat"] / KJ_PAR_GRAMME_AGS
    lipides = valeurNombre(nutriments.get("fat_100g"))
    if lipides is None and valeurs["sa"] and composantes.get("saturated_fat_ratio"):
        lipides = 100 * valeurs["sa"] / composantes["saturated_fat_ratio"]
    manquantes = [cle for cle, champs in CHAMPS_NUTRIMENTS.values() if valeurs[cle] is None]
    for cle in manquantes:
        valeurs[cle] = 0.0

    edulcorants = (composantes.get("non_nutritive_sweeteners") or 0) > 0
    categorie = categorieDepuisOff(donnees)
    if categorie == "general":
        raison = "Open Food Facts le range dans le cas général."
    else:
        raison = f"Open Food Facts le marque « {CATEGORIES[categorie].lower()} »."
    nutriscoreOff = None
    if calcul.get("nutriscore_computed") == 1 and calcul.get("grade") in CLASSES:
        score = valeurNombre(calcul.get("score"))
        nutriscoreOff = {"score": int(score) if score is not None else None, "label": calcul["grade"].upper()}

    code = str(fiche.get("code") or reponse.get("code"))
    produit = champsDeLaFiche(fiche, code)
    produit["nom"] = produit["nom"] or f"Produit {code}"
    produit.update(valeurs)
    produit.update({
        "manquantes": manquantes,
        "estimees": estimees,
        "lipides": lipides,
        "edulcorants": edulcorants,
        "categorie": categorie,
        "raisonCategorie": raison,
        "nutriscoreOff": nutriscoreOff,
        "platPrepare": CATEGORIE in (fiche.get("categories_tags") or []),
    })
    return produit


# --- Question 3.1 : écriture et lecture de la base Excel ---

def lignesDeLaNotice(entonnoir, infos):
    """Renvoie les lignes de la feuille « lisez-moi » : sources, méthode, colonnes, unités."""
    pages = "; ".join(f"{classe} : {', '.join(map(str, liste))}" for classe, liste in infos["pagesTirees"].items())
    return [
        "Base de plats préparés pour le projet MR-Sort",
        f"Source : Open Food Facts (fr.openfoodfacts.org), données sous licence ODbL, extraites le {infos['dateExtraction']}.",
        f"Contenu : {PAR_CLASSE * len(CLASSES)} plats préparés vendus en France, "
        f"{PAR_CLASSE} par classe du Nutri-Score (A à E).",
        "# Méthode",
        "1. Repérage de candidats dans l'index de recherche d'OFF, par pages tirées au hasard "
        f"(graine {infos['graine']}). Pages tirées par classe de l'index : {pages}.",
        "2. Lecture de chaque fiche par l'API produit d'OFF : le score et le label sont ceux du Nutri-Score de 2023.",
        "3. Filtres, dans l'ordre : " + " ; ".join(ETAPES) + " ; sans doublon (même nom et même marque).",
        f"4. Tirage au hasard de {PAR_CLASSE} plats par classe parmi les plats retenus (graine {infos['graine']}).",
    ] + lignesDesColonnes()


def lignesDeLaNoticeEtendue(entonnoir, infos):
    """Renvoie les lignes de la feuille « lisez-moi » de la base étendue : sources, méthode, usage, colonnes."""
    pages = "; ".join(f"{classe} : {', '.join(map(str, liste))}" for classe, liste in infos["pagesAjoutees"].items() if liste)
    return [
        "Base étendue de plats préparés pour le projet MR-Sort",
        f"Source : Open Food Facts (fr.openfoodfacts.org), données sous licence ODbL ; ajout extrait le {infos['dateExtraction']}.",
        f"Contenu : {infos['parClasse'] * len(CLASSES)} plats préparés vendus en France, {infos['parClasse']} par classe "
        f"du Nutri-Score (A à E) : les {PAR_CLASSE * len(CLASSES)} plats de la base (lot « {LOT_BASE} »), plus "
        f"{infos['ajoutParClasse']} plats par classe tirés hors de la base (lot « {LOT_AJOUT} »).",
        "# Méthode",
        "1. Les pages de l'index déjà tirées pour la base, puis les pages suivantes, dans le même ordre tiré au hasard "
        f"(graine {infos['graine']}), tant qu'une classe manque de plats hors de la base. Pages ajoutées : {pages}.",
        "2. Les mêmes lectures et les mêmes filtres que la base : " + " ; ".join(ETAPES) + " ; sans doublon.",
        "3. Les plats de la base sont écartés (même code-barres, ou même nom et même marque), puis "
        f"{infos['ajoutParClasse']} plats par classe sont tirés au hasard (graine {infos['graine']}).",
        "# Usage",
        "Les plats ajoutés mesurent les modèles appris sur la base sur des plats qu'ils n'ont pas vus ; "
        "le modèle final est appris sur les 375 plats.",
    ] + lignesDesColonnes() + [f"Lot : « {LOT_BASE} » pour les plats de la base, « {LOT_AJOUT} » pour les autres."]


def lignesDesColonnes():
    """Les lignes de la notice qui décrivent les colonnes, communes à la base et à la base étendue."""
    return [
        "# Colonnes",
        "Les sept composantes du Nutri-Score sont celles qu'OFF a utilisées pour son calcul de 2023, pour 100 g.",
        "Énergie en kJ, acides gras saturés, sucres, sel, protéines et fibres en grammes, fruits, légumes et "
        "légumineuses en pourcentage (estimé par OFF à partir de la liste des ingrédients).",
        "Le sel sert au calcul, car les barèmes de 2023 sont en sel. Le sodium est donné à part : sodium = sel / 2,5.",
        "Groupe NOVA : degré de transformation, de 1 (brut) à 4 (ultra-transformé). Additifs : codes E relevés par OFF.",
        "Green-Score : score environnemental d'OFF (ex-Eco-Score), sur 100, vide quand OFF ne le calcule pas.",
    ]


def ecrireBase(base, entonnoir, infos, chemin=FICHIER_BASE, etendue=False):
    """
    Écrit la base dans un classeur Excel de trois feuilles : « base » (une ligne par plat),
    « lisez-moi » (sources, méthode, colonnes) et « contrôles » (entonnoir des filtres,
    vivier par classe, conditions du sujet). Avec etendue=True, c'est la base étendue : une
    colonne « Lot » de plus, sa notice, et le vivier hors de la base.
    """
    from openpyxl import Workbook
    from projet_design import mettreEnFormeFeuille, mettreEnFormeNotice

    colonnes = COLONNES_ETENDUE if etendue else COLONNES
    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "base"
    feuille.append([entete for cle, entete in colonnes])
    for produit in base:
        feuille.append([produit[cle] for cle, entete in colonnes])
    largeurs = [15, 42, 20, 11, 40, 11, 11, 12, 11, 10, 11, 11, 10, 13, 10, 10, 9, 10, 24, 11, 10, 7, 12] + ([16] if etendue else [])
    formats = {6: "0", 7: "0", 8: "0.0", 9: "0.0", 10: "0.00", 11: "0", 12: "0.0", 13: "0.0", 14: "0.0", 20: "0"}
    mettreEnFormeFeuille(feuille, largeurs, colonnesClasses=(16,), formats=formats)

    notice = classeur.create_sheet("lisez-moi")
    for ligne in (lignesDeLaNoticeEtendue if etendue else lignesDeLaNotice)(entonnoir, infos):
        notice.append([ligne])
    mettreEnFormeNotice(notice)

    controles = classeur.create_sheet("contrôles")
    controles.append(["Étape ou contrôle", "Nombre", "Détail"])
    for etape, nombre in entonnoir.items():
        controles.append([f"Entonnoir : {etape}", nombre, ""])
    if etendue:
        for classe, nombre in infos["vivierHorsBase"].items():
            controles.append([f"Vivier hors de la base, classe {classe}", nombre, f"{infos['ajoutParClasse']} tirés"])
    else:
        for classe, nombre in infos["vivierParClasse"].items():
            controles.append([f"Vivier de la classe {classe}", nombre, f"{PAR_CLASSE} tirés"])
    for libelle, respectee, detail in verifierBase(base):
        controles.append([f"Condition du sujet : {libelle}", "oui" if respectee else "non", detail])
    mettreEnFormeFeuille(controles, [62, 10, 30])

    chemin.parent.mkdir(parents=True, exist_ok=True)
    classeur.save(chemin)


def lireBase(chemin=FICHIER_BASE):
    """
    Lit la feuille « base » d'un classeur Excel et renvoie une liste de plats, chacun sous
    forme de dictionnaire dont les clés sont celles de COLONNES (en, sa, su, so, pr, fi, fr…).
    """
    from openpyxl import load_workbook

    classeur = load_workbook(chemin, read_only=True, data_only=True)
    lignes = list(classeur["base"].iter_rows(values_only=True))
    classeur.close()
    clesParEntete = {entete: cle for cle, entete in COLONNES_ETENDUE}
    entetes = [clesParEntete.get(entete, entete) for entete in lignes[0]]
    manquantes = [cle for cle in CLES_OBLIGATOIRES if cle not in entetes]
    if manquantes:
        raise ValueError(f"Colonnes absentes de {chemin} : {', '.join(manquantes)}")
    produits = []
    for ligne in lignes[1:]:
        if any(valeur is not None for valeur in ligne):
            produit = dict(zip(entetes, ligne))
            produit["code"] = str(produit.get("code"))
            produits.append(produit)
    return produits


# --- Question 3.1 : contrôles du sujet ---

def verifierBase(base):
    """
    Vérifie sur la base les conditions du sujet (§3.1). La base est une liste de plats ou
    le chemin d'un classeur Excel. Renvoie une liste de triplets (libellé, respectée, détail).
    """
    produits = base if isinstance(base, list) else lireBase(base)
    conditions = []
    conditions.append(("au moins 100 aliments", len(produits) >= 100, f"{len(produits)} aliments"))
    for classe in CLASSES:
        nombre = sum(1 for p in produits if p.get("label") == classe.upper())
        conditions.append((f"au moins 20 aliments de label {classe.upper()}", nombre >= 20, f"{nombre} aliments"))
    incompletes = sum(1 for p in produits if any(p.get(cle) is None for cle in CLES_OBLIGATOIRES))
    conditions.append(("le label, le score et les 7 composantes renseignés", incompletes == 0,
                       f"{incompletes} ligne(s) incomplète(s)"))
    codes = [p.get("code") for p in produits]
    doublons = len(codes) - len(set(codes))
    conditions.append(("pas de code-barres en double", doublons == 0, f"{doublons} doublon(s)"))
    return conditions


def intersectionAvecAutreBase(baseA, baseB):
    """
    Mesure le recoupement entre deux bases (listes de plats ou chemins Excel), par code-barres.
    Renvoie (nombre de plats communs, pourcentage). Le pourcentage est rapporté à la plus
    petite des deux bases, la lecture la plus sévère de la règle des 25 % du sujet.
    """
    produitsA = baseA if isinstance(baseA, list) else lireBase(baseA)
    produitsB = baseB if isinstance(baseB, list) else lireBase(baseB)
    codesA = {str(p["code"]) for p in produitsA}
    codesB = {str(p["code"]) for p in produitsB}
    communs = len(codesA & codesB)
    return communs, 100 * communs / min(len(codesA), len(codesB))


def enregistrerResultats(cle, valeurs, fichier=FICHIER_RESULTATS):
    """
    Range les chiffres d'une étape dans resultats/resultats_projet.json, sous la clé donnée.
    Le README, les slides et le rapport citent ces chiffres, et seulement eux.
    """
    tout = json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else {}
    tout[cle] = valeurs
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text(json.dumps(tout, ensure_ascii=False, indent=2), encoding="utf-8")


def mainEtendue(arguments):
    """Construit la base étendue (375 plats), l'écrit en Excel, puis affiche son entonnoir et ses contrôles."""
    sortie = arguments.sortie or FICHIER_BASE_ETENDUE
    etendue, entonnoir, infos = construireBaseEtendue(arguments.graine, arguments.depuis_cache)
    ecrireBase(etendue, entonnoir, infos, sortie, etendue=True)
    print("\nEntonnoir des filtres (pages de la base et pages ajoutées)")
    for etape, nombre in entonnoir.items():
        print(f"  {etape:.<40} {nombre:>5}")
    print("Vivier hors de la base : " + ", ".join(f"{c} {n}" for c, n in infos["vivierHorsBase"].items()))
    print(f"Base étendue : {len(etendue)} plats, {infos['parClasse']} par classe, écrite dans {sortie}")
    for libelle, respectee, detail in verifierBase(etendue):
        print(f"  [{'oui' if respectee else 'non'}] {libelle} ({detail})")
    if sortie.resolve() == FICHIER_BASE_ETENDUE:
        enregistrerResultats("baseEtendue", {
            "nombrePlats": len(etendue),
            "parClasse": infos["parClasse"],
            "ajoutParClasse": infos["ajoutParClasse"],
            "graine": infos["graine"],
            "dateExtraction": infos["dateExtraction"],
            "pagesAjoutees": infos["pagesAjoutees"],
            "entonnoir": entonnoir,
            "vivierParClasse": infos["vivierParClasse"],
            "vivierHorsBase": infos["vivierHorsBase"],
        })


def main():
    """Construit la base (ou la base étendue), l'écrit en Excel, puis affiche l'entonnoir et les contrôles du sujet."""
    parseur = argparse.ArgumentParser(description="Constitution de la base de plats préparés (question 3.1).")
    parseur.add_argument("--depuis-cache", action="store_true", help="lire seulement le cache, sans réseau")
    parseur.add_argument("--graine", type=int, default=GRAINE, help="graine du hasard")
    parseur.add_argument("--etendue", action="store_true", help="construire la base étendue (375 plats)")
    parseur.add_argument("--sortie", type=Path, default=None, help="classeur Excel à écrire")
    arguments = parseur.parse_args()
    if arguments.etendue:
        mainEtendue(arguments)
        return
    arguments.sortie = arguments.sortie or FICHIER_BASE

    base, entonnoir, infos = construireBase(arguments.graine, arguments.depuis_cache)
    ecrireBase(base, entonnoir, infos, arguments.sortie)

    print("\nEntonnoir des filtres")
    for etape, nombre in entonnoir.items():
        print(f"  {etape:.<40} {nombre:>5}")
    print("Vivier par classe : " + ", ".join(f"{c} {n}" for c, n in infos["vivierParClasse"].items()))
    print(f"Base : {len(base)} plats, graine {infos['graine']}, écrite dans {arguments.sortie}")
    print("Conditions du sujet")
    for libelle, respectee, detail in verifierBase(base):
        print(f"  [{'oui' if respectee else 'non'}] {libelle} ({detail})")

    # Les chiffres de référence ne sont enregistrés que pour la base livrée
    if arguments.sortie.resolve() == FICHIER_BASE:
        enregistrerResultats("base", {
            "nombrePlats": len(base),
            "parClasse": PAR_CLASSE,
            "graine": infos["graine"],
            "dateExtraction": infos["dateExtraction"],
            "pagesTirees": infos["pagesTirees"],
            "entonnoir": entonnoir,
            "vivierParClasse": infos["vivierParClasse"],
        })


if __name__ == "__main__":
    main()
