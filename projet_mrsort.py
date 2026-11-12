"""
projet_mrsort.py : le modèle MR-Sort et l'approximation du Nutri-Score (question 3.3).

MR-Sort range chaque plat dans l'une des cinq classes ordonnées C1 ≺ C2 ≺ C3 ≺ C4 ≺ C5,
notées E′, D′, C′, B′ et A′. Quatre profils limites b2, b3, b4 et b5 séparent ces classes.
Un plat « franchit » un profil quand il est au moins aussi bon que lui sur une coalition
de critères dont le poids total atteint le seuil majoritaire λ. Il est rangé dans la
classe du meilleur profil qu'il franchit (sujet, §2).

Entrée : la base Excel (donnees/base_plats_prepares.xlsx), lue par projet_base.lireBase.
Sorties : un classeur Excel par modèle (affectations, paramètres, synthèse avec la matrice
de confusion), resultats/comparaison_modeles.xlsx, et la clé « mrsort » de
resultats/resultats_projet.json.

Sens des classes : A′ veut dire que le plat franchit b5, c'est-à-dire qu'il est au moins
aussi bon que le « plat-frontière » des A sur une majorité pondérée de critères (≥ λ).

Commandes :
    python3 projet_mrsort.py            # les modèles à 7 et 3 critères, λ = 0,6 et 0,7, les paires inversées ;
                                        # avec la base étendue : les modèles sur 375 plats, et le test sur les plats ajoutés
    python3 projet_mrsort.py --courbe   # en plus, la courbe d'apprentissage (quelques minutes)
    python3 projet_mrsort.py --profils  # en plus, les modèles aux profils appris (jusqu'à cinq minutes chacun)
    python3 projet_mrsort.py --complet  # en plus, le modèle complet et la recherche d'un modèle exact (jusqu'à une heure)

La généralisation se mesure sur des plats que le modèle n'a pas vus : appliquerModele range
une autre base sans rien apprendre, et courbeDApprentissage mesure l'exactitude en fonction
du nombre de plats appris (une graine par tirage : chaque point se refait à l'identique).

État : le modèle, l'apprentissage des poids, la comparaison et la généralisation sont écrits ;
l'apprentissage des profils et le modèle complet viendront en phase 2.
"""

import argparse
import json
import random
import time
from statistics import mean, stdev


# --- Question 3.3 : les critères et les classes ---

# Pour chaque critère : (libellé, unité, sens). « min » : moins c'est mieux ; « max » : plus c'est mieux.
CRITERES = {
    "en": ("Énergie", "kJ/100 g", "min"),
    "sa": ("Acides gras saturés", "g/100 g", "min"),
    "su": ("Sucres", "g/100 g", "min"),
    "so": ("Sel", "g/100 g", "min"),
    "pr": ("Protéines", "g/100 g", "max"),
    "fi": ("Fibres", "g/100 g", "max"),
    "fr": ("Fruits, légumes et légumineuses", "%", "max"),
}
CRITERES_SEPT = ["en", "sa", "su", "so", "pr", "fi", "fr"]
CRITERES_TROIS = ["en", "so", "fr"]                       # énergie, sodium (ici le sel), fruits

CLASSES = ["E′", "D′", "C′", "B′", "A′"]                  # C1 à C5
LETTRES_NUTRISCORE = ["E", "D", "C", "B", "A"]            # la classe du Nutri-Score qui correspond à chaque Ck
PROFILS = ["b2", "b3", "b4", "b5"]                        # bk sépare C(k-1) et Ck
SEUILS_MAJORITAIRES = [0.6, 0.7]
EPSILON = 0.001                                          # marge des inégalités strictes (annexe B)
TOLERANCE = 1e-9                                         # absorbe les erreurs d'arrondi des sommes de poids


# --- Question 3.3 : le modèle MR-Sort ---

# Un modèle est un dictionnaire :
#   "criteres" : la liste des critères, par exemple CRITERES_SEPT ;
#   "poids"    : {critère: poids}, des poids positifs de somme 1 ;
#   "profils"  : la liste des profils, du moins bon (b2) au meilleur (b5), chacun {critère: valeur} ;
#   "lam"      : le seuil majoritaire λ, entre 0,5 et 1 ;
#   "sens"     : facultatif, {critère: "min" ou "max"} pour des critères absents de CRITERES.

def sensDuCritere(critere, modele):
    """Renvoie le sens d'un critère : « min » (moins c'est mieux) ou « max » (plus c'est mieux)."""
    sens = modele.get("sens", {})
    if critere in sens:
        return sens[critere]
    return CRITERES[critere][2]


def concordancePartielle(valeur, valeurProfil, sens):
    """
    Concordance partielle c_j(a, b) (sujet, §2.2) : vaut 1 si le plat est au moins aussi bon
    que le profil sur ce critère, 0 sinon. Une égalité compte comme « au moins aussi bon ».
    """
    if sens == "max":
        return 1 if valeur >= valeurProfil else 0
    return 1 if valeur <= valeurProfil else 0


def concordance(plat, profil, modele):
    """
    Concordance globale C(a, b) : la somme des poids des critères sur lesquels le plat est
    au moins aussi bon que le profil.
    """
    total = 0
    for critere in modele["criteres"]:
        total += modele["poids"][critere] * concordancePartielle(plat[critere], profil[critere],
                                                                  sensDuCritere(critere, modele))
    return total


def franchit(plat, profil, modele):
    """
    Le plat franchit le profil (a S b) si sa concordance atteint le seuil majoritaire λ.
    La comparaison se fait à TOLERANCE près : 0,1 + 0,7 vaut 0,7999999999999999 en machine,
    et doit bien atteindre λ = 0,8.
    """
    return concordance(plat, profil, modele) >= modele["lam"] - TOLERANCE


def affecter(plat, modele):
    """
    Range un plat dans la classe du meilleur profil qu'il franchit (sujet, §2.3) : on essaie
    b5, puis b4, b3 et b2 ; un plat qui n'en franchit aucun va dans C1.

    Renvoie un dictionnaire :
      "classe"        : le numéro de la classe, de 0 (C1, E′) au nombre de profils (C5, A′) ;
      "concordances"  : la concordance avec chaque profil, du moins bon au meilleur ;
      "franchis"      : pour chaque profil, True si le plat le franchit.
    """
    concordances = [concordance(plat, profil, modele) for profil in modele["profils"]]
    franchis = [valeur >= modele["lam"] - TOLERANCE for valeur in concordances]
    classe = 0
    for numero in range(len(modele["profils"]) - 1, -1, -1):
        if franchis[numero]:
            classe = numero + 1
            break
    return {"classe": classe, "concordances": concordances, "franchis": franchis}


# --- Question 3.3 : classes et comparaison au Nutri-Score ---

def etapesDeLAffectation(plat, modele):
    """
    Le détail de l'affectation d'un plat, pour l'expliquer pas à pas. Pour chaque profil, de b2
    à b5 : les concordances partielles c_j (1 si le plat vaut au moins le profil sur le
    critère j), les critères qui votent pour le plat, la concordance (la somme de leurs poids)
    et le verdict (franchi si elle atteint λ). Renvoie (étapes, classe) : la liste des étapes,
    du profil le plus bas au plus haut, et la classe du plat (affecter).
    """
    etapes = []
    for numero, profil in enumerate(modele["profils"]):
        partielles = {critere: concordancePartielle(plat[critere], profil[critere], sensDuCritere(critere, modele))
                      for critere in modele["criteres"]}
        etapes.append({"profil": PROFILS[numero], "partielles": partielles,
                       "pour": [critere for critere in modele["criteres"] if partielles[critere] == 1],
                       "concordance": concordance(plat, profil, modele), "franchi": franchit(plat, profil, modele)})
    return etapes, affecter(plat, modele)["classe"]


def classeDuLabel(label):
    """Le numéro de classe qui correspond à un label du Nutri-Score : 0 pour E, 4 pour A."""
    return LETTRES_NUTRISCORE.index(str(label).strip().rstrip("′'").upper())


def nomDeClasse(numero):
    """Le nom d'une classe de MR-Sort : 0 donne E′, 4 donne A′."""
    return CLASSES[numero]


def matriceDeConfusion(attendues, obtenues):
    """
    Compte les plats par couple (classe du Nutri-Score, classe de MR-Sort). La ligne 0 est
    la classe A du Nutri-Score, la colonne 0 la classe A′ : la diagonale compte les plats
    que le modèle range comme le Nutri-Score.
    """
    matrice = [[0] * len(CLASSES) for _ in CLASSES]
    dernier = len(CLASSES) - 1
    for attendue, obtenue in zip(attendues, obtenues):
        matrice[dernier - attendue][dernier - obtenue] += 1
    return matrice


def comparerAuNutriscore(attendues, obtenues):
    """
    Compare les classes d'un modèle aux classes du Nutri-Score. Renvoie le nombre de plats
    bien rangés, l'exactitude (part des plats bien rangés), la part des plats rangés à une
    classe près, et la matrice de confusion.
    """
    total = len(attendues)
    bienRanges = sum(1 for a, o in zip(attendues, obtenues) if a == o)
    aUneClassePres = sum(1 for a, o in zip(attendues, obtenues) if abs(a - o) <= 1)
    return {"total": total, "bienRanges": bienRanges, "exactitude": bienRanges / total,
            "exactitudeEquilibree": exactitudeEquilibree(attendues, obtenues),
            "aUneClassePres": aUneClassePres / total, "matrice": matriceDeConfusion(attendues, obtenues)}


def exactitudeEquilibree(attendues, obtenues):
    """
    L'exactitude où chaque classe compte autant : la moyenne, sur les classes présentes, de la
    part de leurs plats bien rangés. Elle ne dépend pas du mélange des classes d'une base.
    """
    parClasse = {}
    for attendue, obtenue in zip(attendues, obtenues):
        parClasse.setdefault(attendue, []).append(attendue == obtenue)
    return mean(sum(rangs) / len(rangs) for rangs in parClasse.values())


# --- Question 3.3 : la généralisation, sur des plats que le modèle n'a pas vus ---

def appliquerModele(produits, modele):
    """
    Range des plats avec un modèle déjà appris, sans rien apprendre : des plats que le modèle
    n'a pas vus, ou la base d'un autre groupe (§3.4). Renvoie un dictionnaire : les classes
    attendues (le Nutri-Score) et obtenues, et la comparaison (comparerAuNutriscore).
    """
    attendues = [classeDuLabel(plat["label"]) for plat in produits]
    obtenues = [affecter(plat, modele)["classe"] for plat in produits]
    return {"attendues": attendues, "obtenues": obtenues, "comparaison": comparerAuNutriscore(attendues, obtenues)}


def pointDeLaCourbe(produits, criteres, lam, taille, tirage, tenusAPart, graine=None, departage="marge"):
    """
    Un tirage de la courbe d'apprentissage. Le hasard de ce tirage a sa propre graine (la
    graine de la base, la taille et le numéro du tirage) : il se refait seul, à l'identique.
    Dans chaque classe, les plats sont mélangés ; les `tenusAPart` premiers sont tenus à part,
    les taille / 5 suivants sont appris (profils par les médianes, poids appris).
    Renvoie l'exactitude équilibrée sur les plats appris et sur les plats tenus à part.
    """
    from projet_base import GRAINE

    hasard = random.Random(f"{graine if graine is not None else GRAINE}-{taille}-{tirage}")
    appris, tenus = [], []
    for lettre in LETTRES_NUTRISCORE:
        plats = sorted((plat for plat in produits if plat["label"] == lettre), key=lambda plat: plat["code"])
        hasard.shuffle(plats)
        tenus += plats[:tenusAPart]
        appris += plats[tenusAPart:tenusAPart + taille // len(LETTRES_NUTRISCORE)]
    resultat = approximerNutriscore(appris, criteres, lam, "poids", departage=departage)
    return {"appris": resultat["comparaison"]["exactitudeEquilibree"],
            "tenusAPart": appliquerModele(tenus, resultat["modele"])["comparaison"]["exactitudeEquilibree"]}


def courbeDApprentissage(produits, criteres, lam=0.6, tailles=(25, 50, 75, 100, 125, 150, 200, 250, 300),
                         tirages=10, tenusAPart=15, graine=None):
    """
    La courbe d'apprentissage : pour chaque taille, `tirages` tirages (pointDeLaCourbe), qui
    tiennent à part `tenusAPart` plats par classe et apprennent sur taille plats, autant par
    classe. Elle dit combien un modèle gagne à apprendre sur plus de plats, sur des plats
    qu'il n'a pas vus.
    Renvoie une liste, une entrée par taille : taille, appris et tenusAPart (moyennes),
    ecartType (des plats tenus à part), et le détail des tirages.
    """
    courbe = []
    for taille in tailles:
        details = [pointDeLaCourbe(produits, criteres, lam, taille, tirage, tenusAPart, graine) for tirage in range(tirages)]
        tenus = [detail["tenusAPart"] for detail in details]
        courbe.append({"taille": taille, "appris": mean(detail["appris"] for detail in details),
                       "tenusAPart": mean(tenus), "ecartType": stdev(tenus) if len(tenus) > 1 else 0.0,
                       "tirages": details})
    return courbe


def plisStratifies(produits, plis=5, graine=None):
    """
    Répartit les plats en `plis` parts, autant de chaque classe dans chacune : 15 par classe
    pour les 375 plats de la base étendue et 5 parts. Dans chaque classe, les plats sont
    mélangés avec une graine fixée (celle de la base) : les parts se refont à l'identique.
    """
    from projet_base import GRAINE

    hasard = random.Random(f"{graine if graine is not None else GRAINE}-parts-{plis}")
    parts = [[] for _ in range(plis)]
    for lettre in LETTRES_NUTRISCORE:
        plats = sorted((plat for plat in produits if plat["label"] == lettre), key=lambda plat: plat["code"])
        hasard.shuffle(plats)
        for rang, plat in enumerate(plats):
            parts[rang % plis].append(plat)
    return parts


def validationCroisee(produits, criteres, lam, apprentissage, plis=5, limiteSecondes=300, graine=None):
    """
    Compare un apprentissage sur des plats jamais vus, sans en mettre de côté : les plats sont
    répartis en `plis` parts (plisStratifies) ; pour chaque part, on apprend sur les autres,
    puis on range la part. Chaque plat est ainsi rangé une fois, par un modèle qui ne l'a pas vu.

    apprentissage : "poids" (départagés par la plus grande marge), "profils", ou "complet"
    (apprendreParAlternance, en au plus 3 tours) ; limiteSecondes : la limite de chaque
    apprentissage des profils.
    Renvoie un dictionnaire : les parts (bien rangés, total, exactitude, et la borne prouvée et
    `optimal` quand le solveur les donne), l'exactitude moyenne des parts et son écart-type, et
    la comparaison au Nutri-Score sur tous les plats.
    """
    from projet_apprentissage import apprendreParAlternance

    parts = plisStratifies(produits, plis, graine)
    attendues, obtenues, resultatsDesParts = [], [], []
    for numero, part in enumerate(parts):
        appris = [plat for autre, morceau in enumerate(parts) if autre != numero for plat in morceau]
        if apprentissage == "complet":
            classes = [classeDuLabel(plat["label"]) for plat in appris]
            modele = apprendreParAlternance(appris, classes, criteres, lam, toursMax=3, limiteSecondes=limiteSecondes)["modele"]
            borne, optimal = None, None                    # une recherche locale : rien n'est prouvé
        else:
            resultat = approximerNutriscore(appris, criteres, lam, apprentissage,
                                            departage="marge" if apprentissage == "poids" else None,
                                            limiteSecondes=limiteSecondes)
            modele, borne, optimal = resultat["modele"], resultat["borne"], resultat["optimal"]
        rangement = appliquerModele(part, modele)
        attendues += rangement["attendues"]
        obtenues += rangement["obtenues"]
        comparaison = rangement["comparaison"]
        resultatsDesParts.append({"bienRanges": comparaison["bienRanges"], "total": comparaison["total"],
                                  "exactitude": comparaison["exactitude"], "borne": borne, "optimal": optimal})
    exactitudes = [part["exactitude"] for part in resultatsDesParts]
    return {"lam": lam, "criteres": criteres, "plis": plis, "parts": resultatsDesParts,
            "exactitudeMoyenne": mean(exactitudes), "ecartType": stdev(exactitudes) if len(exactitudes) > 1 else 0.0,
            "comparaison": comparerAuNutriscore(attendues, obtenues)}


# --- Question 3.3 : les fonctions demandées par le sujet ---

def approximerNutriscore(produits, criteres, lam=0.6, apprentissage="poids", departage=None, limiteSecondes=300):
    """
    Construit un modèle MR-Sort sur les critères donnés, range les plats et compare le
    résultat au Nutri-Score.

    apprentissage :
      "poids"   : profils fixés par les médianes (profilsParMedianes), poids appris (apprendrePoids) ;
      "profils" : poids fixés par les points maximaux du Nutri-Score (poidsDesPointsMax), profils
                  appris (apprendreProfils, en au plus limiteSecondes, cinq minutes par défaut) ;
      un dictionnaire : un modèle donné à la main, avec ses poids, ses profils et son λ.
    departage : None (les poids que rend le solveur) ou "marge" (parmi les meilleurs poids,
    ceux qui laissent la plus grande marge : voir apprendrePoids).
    Renvoie un dictionnaire : le modèle, les classes attendues et obtenues, la comparaison,
    l'optimum du programme linéaire et la plus petite marge (None pour un modèle donné à la main).
    """
    from projet_apprentissage import apprendrePoids, apprendreProfils, poidsDesPointsMax, profilsParMedianes

    attendues = [classeDuLabel(plat["label"]) for plat in produits]
    optimum, marge, borne, optimal = None, None, None, None
    if isinstance(apprentissage, dict):
        modele = dict(apprentissage, criteres=criteres)
        methode = "paramètres donnés à la main"
    elif apprentissage == "poids":
        profils = profilsParMedianes(produits, attendues, criteres)
        appris = apprendrePoids(produits, attendues, {"criteres": criteres, "profils": profils, "lam": lam, "poids": {}},
                                departage=departage)
        modele, optimum, marge = appris["modele"], appris["optimum"], appris["marge"]
        borne, optimal = optimum, True                     # le programme des poids se résout toujours jusqu'au bout
        methode = "profils fixés (médianes), poids appris"
        if departage == "marge":
            methode += ", départagés par la plus grande marge"
    elif apprentissage == "profils":
        appris = apprendreProfils(produits, attendues, {"criteres": criteres, "poids": poidsDesPointsMax(criteres), "lam": lam},
                                  limiteSecondes)
        modele, optimum, borne, optimal = appris["modele"], appris["optimum"], appris["borne"], appris["optimal"]
        methode = "poids fixés (points maximaux du Nutri-Score), profils appris"
    else:
        raise ValueError(f"Apprentissage inconnu : {apprentissage}")
    obtenues = [affecter(plat, modele)["classe"] for plat in produits]
    return {"modele": modele, "methode": methode, "attendues": attendues, "obtenues": obtenues,
            "comparaison": comparerAuNutriscore(attendues, obtenues), "optimum": optimum, "marge": marge,
            "borne": borne, "optimal": optimal}


def MRSort_sept(fichier, lam=0.6, apprentissage="poids", sortie=None, afficher=True, departage=None, limiteSecondes=300):
    """
    Approxime le Nutri-Score par un MR-Sort à 7 critères (énergie, acides gras saturés,
    sucres, sel, protéines, fibres, fruits, légumes et légumineuses).

    fichier : le classeur Excel de la base (une des entrées, comme le demande le sujet) ;
    lam : le seuil majoritaire λ (0,6 ou 0,7 dans le sujet) ;
    apprentissage : "poids", "profils", ou un modèle donné à la main (voir approximerNutriscore) ;
    sortie : le classeur Excel des affectations à écrire (par défaut dans resultats/) ;
    departage : None ou "marge", pour départager les poids (voir approximerNutriscore) ;
    limiteSecondes : la limite de temps de l'apprentissage des profils.
    Renvoie le résultat d'approximerNutriscore, avec le chemin du classeur écrit.
    """
    return approximerFichier("sept", CRITERES_SEPT, fichier, lam, apprentissage, sortie, afficher, departage, limiteSecondes)


def MRSort_trois(fichier, lam=0.6, apprentissage="poids", sortie=None, afficher=True, departage=None, limiteSecondes=300):
    """
    Approxime le Nutri-Score par un MR-Sort à 3 critères : l'énergie, le sodium (le sel,
    qui range les plats dans le même ordre) et les fruits, légumes et légumineuses.
    Mêmes paramètres et même résultat que MRSort_sept.
    """
    return approximerFichier("trois", CRITERES_TROIS, fichier, lam, apprentissage, sortie, afficher, departage, limiteSecondes)


def approximerFichier(nom, criteres, fichier, lam, apprentissage, sortie, afficher, departage=None, limiteSecondes=300):
    """Lit la base, approxime le Nutri-Score, écrit l'Excel des affectations et affiche le bilan."""
    from projet_base import DOSSIER, lireBase

    produits = lireBase(fichier)
    resultat = approximerNutriscore(produits, criteres, lam, apprentissage, departage, limiteSecondes)
    if sortie is None:
        mode = apprentissage if isinstance(apprentissage, str) else "manuel"
        sortie = DOSSIER / "resultats" / f"MRSort_{nom}_{mode}_lambda_{lam}.xlsx"
    ecrireAffectations(produits, resultat, sortie)
    resultat["fichier"] = sortie
    if afficher:
        afficherBilan(f"MRSort_{nom}, λ = {lam}, {resultat['methode']}", resultat)
    return resultat


def ecrireAffectations(produits, resultat, chemin):
    """
    Écrit le classeur Excel d'un modèle, au style du projet : les affectations (une ligne par
    plat), les paramètres (poids et profils de chaque critère, λ) et la synthèse (exactitude,
    matrice de confusion).
    """
    from openpyxl import Workbook
    from projet_design import mettreEnFormeFeuille

    modele, comparaison = resultat["modele"], resultat["comparaison"]
    classeur = Workbook()

    feuille = classeur.active
    feuille.title = "affectations"
    feuille.append(["Code-barres", "Nom", "Marque", "Score Nutri-Score", "Label Nutri-Score", "Classe MR-Sort",
                    "Identique", "Écart (classes)"])
    for plat, attendue, obtenue in zip(produits, resultat["attendues"], resultat["obtenues"]):
        feuille.append([plat["code"], plat["nom"], plat.get("marque", ""), plat.get("score"), plat["label"],
                        nomDeClasse(obtenue), "oui" if attendue == obtenue else "non", obtenue - attendue])
    mettreEnFormeFeuille(feuille, [15, 42, 20, 10, 10, 10, 10, 10], colonnesClasses=(5, 6))

    parametres = classeur.create_sheet("paramètres")
    parametres.append(["Critère", "Sens", "Poids"] + [f"Profil {profil}" for profil in PROFILS[:len(modele["profils"])]])
    for critere in modele["criteres"]:
        libelle = CRITERES[critere][0] if critere in CRITERES else critere
        parametres.append([libelle, "à minimiser" if sensDuCritere(critere, modele) == "min" else "à maximiser",
                           modele["poids"][critere]] + [profil[critere] for profil in modele["profils"]])
    parametres.append(["Seuil majoritaire λ", "", modele["lam"]])
    parametres.append(["Méthode", "", resultat["methode"]])
    mettreEnFormeFeuille(parametres, [34, 13, 10] + [12] * len(modele["profils"]))

    synthese = classeur.create_sheet("synthèse")
    synthese.append(["Indicateur", "Valeur"])
    synthese.append(["Plats bien rangés", f"{comparaison['bienRanges']} sur {comparaison['total']}"])
    synthese.append(["Exactitude", round(comparaison["exactitude"], 4)])
    synthese.append(["À une classe près", round(comparaison["aUneClassePres"], 4)])
    synthese.append([])
    synthese.append(["Nutri-Score (lignes) / MR-Sort (colonnes)"] + list(reversed(CLASSES)))
    for numero, ligne in enumerate(comparaison["matrice"]):
        synthese.append([LETTRES_NUTRISCORE[len(CLASSES) - 1 - numero]] + ligne)
    mettreEnFormeFeuille(synthese, [40, 12, 8, 8, 8, 8], formats={2: "0.0%"})

    chemin.parent.mkdir(parents=True, exist_ok=True)
    classeur.save(chemin)


def afficherBilan(titre, resultat):
    """Affiche le modèle appris et sa comparaison au Nutri-Score."""
    modele, comparaison = resultat["modele"], resultat["comparaison"]
    print(titre)
    print("  poids : " + ", ".join(f"{c} {modele['poids'][c]:.4f}" for c in modele["criteres"]))
    for profil, valeurs in zip(PROFILS, modele["profils"]):
        print(f"  {profil} : " + ", ".join(f"{c} {valeurs[c]:g}" for c in modele["criteres"]))
    print(f"  bien rangés : {comparaison['bienRanges']}/{comparaison['total']} "
          f"({comparaison['exactitude']:.1%}), à une classe près : {comparaison['aUneClassePres']:.1%}")


# --- Question 3.3 : existence d'un modèle exact ---

def auMoinsAussiBon(a, b, criteres, modele=None):
    """Vrai si le plat a est au moins aussi bon que le plat b sur chacun des critères."""
    modele = modele or {}
    for critere in criteres:
        if concordancePartielle(a[critere], b[critere], sensDuCritere(critere, modele)) == 0:
            return False
    return True


def paresDeDominanceInversees(produits, criteres, modele=None):
    """
    Cherche les paires (a, b) où a est au moins aussi bon que b sur tous les critères, mais
    moins bien classé que b par le Nutri-Score.

    Une seule paire suffit à prouver qu'aucun MR-Sort ne reproduit exactement le Nutri-Score
    sur ces critères : MR-Sort est monotone. Si a vaut au moins b partout, a franchit tous
    les profils que b franchit, donc il est rangé au moins aussi haut que b.

    Renvoie la liste des paires (a, b), de l'écart de classes le plus grand au plus petit.
    """
    paires = []
    for a in produits:
        for b in produits:
            if a is not b and classeDuLabel(a["label"]) < classeDuLabel(b["label"]) \
                    and auMoinsAussiBon(a, b, criteres, modele):
                paires.append((a, b))
    paires.sort(key=lambda paire: classeDuLabel(paire[0]["label"]) - classeDuLabel(paire[1]["label"]))
    return paires


# --- Question 3.3 : comparaison des modèles ---

def resumeDeLaPaire(a, b, criteres):
    """Décrit une paire inversée : les deux plats, leurs labels et leurs valeurs sur les critères."""
    return {"meilleur": {"nom": a["nom"], "label": a["label"], **{c: a[c] for c in criteres}},
            "moinsBon": {"nom": b["nom"], "label": b["label"], **{c: b[c] for c in criteres}}}


def comparerModeles(fichier=None, modes=("poids",), afficher=True, departage=None, limiteSecondes=300):
    """
    Compare les modèles MR-Sort : les deux jeux de critères (7 et 3), chaque mode
    d'apprentissage demandé, et les deux seuils majoritaires du sujet (0,6 et 0,7). Cherche
    aussi les paires de dominance inversées, qui répondent à la question de l'existence d'un
    modèle exact. limiteSecondes : la limite de chaque apprentissage des profils.

    Écrit un Excel par modèle et resultats/comparaison_modeles.xlsx (suffixe « _etendue »
    pour la base étendue). Range aussi les chiffres dans resultats_projet.json : sous la clé
    « mrsort » pour la base livrée, « mrsortEtendu » pour la base étendue, et « …Profils »
    pour les profils appris.
    Renvoie (resultats, inversions) : la liste des résultats, un par modèle, et les paires
    inversées de chaque jeu de critères.
    """
    from projet_base import DOSSIER, FICHIER_BASE, FICHIER_BASE_ETENDUE, enregistrerResultats, lireBase

    fichier = fichier or FICHIER_BASE
    suffixe = ("" if fichier == FICHIER_BASE else "_etendue") + ("_profils" if "poids" not in modes else "")
    resultats = []
    for nom, fonction in (("sept", MRSort_sept), ("trois", MRSort_trois)):
        for mode in modes:
            for lam in SEUILS_MAJORITAIRES:
                sortie = DOSSIER / "resultats" / f"MRSort_{nom}_{mode}_lambda_{lam}{suffixe}.xlsx"
                resultat = fonction(fichier, lam, mode, sortie=sortie, afficher=afficher, departage=departage,
                                    limiteSecondes=limiteSecondes)
                resultat.update(nom=nom, mode=mode, lam=lam)
                resultats.append(resultat)

    produits = lireBase(fichier)
    ajouterIntervalles(resultats, produits)
    inversions = {"sept": paresDeDominanceInversees(produits, CRITERES_SEPT),
                  "trois": paresDeDominanceInversees(produits, CRITERES_TROIS)}
    ecrireComparaison(resultats, inversions, DOSSIER / "resultats" / f"comparaison_modeles{suffixe}.xlsx")
    if afficher:
        for nom, paires in inversions.items():
            print(f"Paires inversées à {nom} critères : {len(paires)}")

    cle = {FICHIER_BASE: "mrsort", FICHIER_BASE_ETENDUE: "mrsortEtendu"}.get(fichier)
    poids = [r for r in resultats if r["mode"] == "poids"]
    profils = [r for r in resultats if r["mode"] == "profils"]
    if cle and poids:
        enregistrerResultats(cle, {
            "modeles": [{
                "nom": r["nom"], "mode": r["mode"], "lam": r["lam"], "methode": r["methode"],
                "bienRanges": r["comparaison"]["bienRanges"], "total": r["comparaison"]["total"],
                "exactitude": r["comparaison"]["exactitude"], "aUneClassePres": r["comparaison"]["aUneClassePres"],
                "matrice": r["comparaison"]["matrice"],
                "criteres": r["modele"]["criteres"], "poids": r["modele"]["poids"], "profils": r["modele"]["profils"],
                "marge": round(r["marge"], 4), "intervalles": r["intervalles"],
            } for r in poids],
            "inversions": {nom: {"nombre": len(paires),
                                 "exemple": resumeDeLaPaire(*paires[0], CRITERES_SEPT if nom == "sept" else CRITERES_TROIS)
                                 if paires else None}
                           for nom, paires in inversions.items()},
        })
    if cle and profils:                                     # les profils appris : leur propre clé (« mrsortProfils »)
        enregistrerResultats(cle + "Profils", {
            "modeles": [{
                "nom": r["nom"], "mode": r["mode"], "lam": r["lam"], "methode": r["methode"],
                "bienRanges": r["comparaison"]["bienRanges"], "total": r["comparaison"]["total"],
                "exactitude": r["comparaison"]["exactitude"], "aUneClassePres": r["comparaison"]["aUneClassePres"],
                "matrice": r["comparaison"]["matrice"],
                "criteres": r["modele"]["criteres"], "poids": r["modele"]["poids"], "profils": r["modele"]["profils"],
                "optimum": r["optimum"], "borne": r["borne"], "optimal": r["optimal"],
            } for r in profils],
        })
    return resultats, inversions


def ajouterIntervalles(resultats, produits):
    """
    Ajoute à chaque modèle appris ses poids possibles : pour chaque critère, le plus petit et
    le plus grand poids parmi les modèles qui rangent bien autant de plats (intervallesDesPoids),
    arrondis au millième.
    """
    from projet_apprentissage import intervallesDesPoids

    for r in resultats:
        if r.get("mode") == "poids" and r.get("optimum") is not None:
            bornes = intervallesDesPoids(produits, r["attendues"], r["modele"], r["optimum"])
            r["intervalles"] = {critere: [round(bas, 3), round(haut, 3)] for critere, (bas, haut) in bornes.items()}


def ecrireComparaison(resultats, inversions, chemin):
    """
    Écrit le classeur de comparaison : une ligne par modèle (critères, apprentissage, λ,
    plats bien rangés, exactitude, poids), puis les paires inversées à 3 critères.
    """
    from openpyxl import Workbook
    from projet_design import mettreEnFormeFeuille

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "modèles"
    feuille.append(["Critères", "Apprentissage", "λ", "Bien rangés", "Exactitude", "À une classe près", "Poids",
                    "Plus petite marge", "Poids possibles (même nombre de plats bien rangés)"])
    for r in resultats:
        poids = " ; ".join(f"{c} {r['modele']['poids'][c]:.4f}" for c in r["modele"]["criteres"])
        possibles = " ; ".join(f"{c} de {bas:.3f} à {haut:.3f}" for c, (bas, haut) in r.get("intervalles", {}).items())
        feuille.append([f"{len(r['modele']['criteres'])} critères", r["methode"], r["lam"],
                        f"{r['comparaison']['bienRanges']} sur {r['comparaison']['total']}",
                        r["comparaison"]["exactitude"], r["comparaison"]["aUneClassePres"], poids,
                        r.get("marge"), possibles])
    mettreEnFormeFeuille(feuille, [12, 36, 6, 13, 11, 14, 80, 12, 110], formats={5: "0.0%", 6: "0.0%", 8: "0.000"})

    paires = classeur.create_sheet("paires inversées")
    paires.append(["Plat au moins aussi bon partout", "Label", "Plat moins bon", "Label",
                   "Énergie (kJ)", "Sel (g)", "Fruits, légumes (%)"])
    for a, b in inversions["trois"][:100]:
        paires.append([a["nom"], a["label"], b["nom"], b["label"],
                       f"{a['en']:g} contre {b['en']:g}", f"{a['so']:g} contre {b['so']:g}",
                       f"{a['fr']:g} contre {b['fr']:g}"])
    mettreEnFormeFeuille(paires, [40, 7, 40, 7, 18, 14, 18], colonnesClasses=(2, 4))

    chemin.parent.mkdir(parents=True, exist_ok=True)
    classeur.save(chemin)


def chercherUnModeleExact(produits, criteres, limiteSecondes=1800):
    """
    La question 1 du sujet : existe-t-il un modèle MR-Sort qui range exactement les plats
    dans leur classe du Nutri-Score ? Une paire inversée suffit à prouver que non : MR-Sort est
    monotone, un plat au moins aussi bon qu'un autre partout ne peut pas être rangé plus bas.
    Sans paire inversée, le programme du modèle complet (apprendreModeleComplet, exact=True)
    cherche un modèle exact, en au plus limiteSecondes.
    Renvoie un dictionnaire : "existe" (True, False, ou None si le temps manque), "preuve"
    (« paires inversées » ou « programme linéaire », None sans réponse), "modele" (s'il
    existe), "paires" (le nombre de paires inversées) et "limiteSecondes".
    """
    from projet_apprentissage import apprendreModeleComplet

    paires = paresDeDominanceInversees(produits, criteres)
    reponse = {"existe": None, "preuve": None, "modele": None, "paires": len(paires), "limiteSecondes": limiteSecondes}
    if paires:
        reponse.update(existe=False, preuve="paires inversées")
        return reponse
    classes = [classeDuLabel(plat["label"]) for plat in produits]
    resultat = apprendreModeleComplet(produits, classes, criteres, exact=True, limiteSecondes=limiteSecondes)
    if resultat["existe"] is not None:
        reponse.update(existe=resultat["existe"], preuve="programme linéaire", modele=resultat["modele"])
    return reponse


def apprendreLesModelesComplets(limiteExacte=1800, afficher=True, fichier=None, chercherExact=True, limiteSecondes=180):
    """
    Le modèle complet : poids et profils appris par alternance (apprendreParAlternance, chaque
    apprentissage des profils en au plus limiteSecondes), à 7 et 3 critères, λ = 0,6 et 0,7.
    Sur les 125 plats de la base (par défaut), puis la question 1 du sujet : un modèle exact
    existe-t-il (chercherUnModeleExact, en au plus limiteExacte secondes) ? Range le tout sous
    la clé « modeleComplet » de resultats_projet.json. Sur la base étendue (fichier), sans la
    question 1, qui porte sur la base : sous la clé « modeleCompletEtendu ». Renvoie le résultat.
    """
    from projet_apprentissage import apprendreParAlternance
    from projet_base import FICHIER_BASE, enregistrerResultats, lireBase

    fichier = fichier or FICHIER_BASE
    produits = lireBase(fichier)
    classes = [classeDuLabel(plat["label"]) for plat in produits]
    modeles = []
    for nom, criteres in (("sept", CRITERES_SEPT), ("trois", CRITERES_TROIS)):
        for lam in SEUILS_MAJORITAIRES:
            appris = apprendreParAlternance(produits, classes, criteres, lam, limiteSecondes=limiteSecondes)
            comparaison = comparerAuNutriscore(classes, [affecter(plat, appris["modele"])["classe"] for plat in produits])
            modeles.append({"nom": nom, "mode": "complet", "lam": lam, "methode": APPRENTISSAGES["complet"],
                            "bienRanges": comparaison["bienRanges"], "total": comparaison["total"],
                            "exactitude": comparaison["exactitude"], "aUneClassePres": comparaison["aUneClassePres"],
                            "matrice": comparaison["matrice"], "criteres": criteres, "poids": appris["modele"]["poids"],
                            "profils": appris["modele"]["profils"], "historique": appris["historique"]})
            if afficher:
                print(f"Modèle complet, {nom} critères, λ = {lam} : {comparaison['bienRanges']}/{comparaison['total']} "
                      f"(étapes : {' → '.join(map(str, appris['historique']))})")
    resultat = {"modeles": modeles}
    if chercherExact:
        exact = {}
        for nom, criteres in (("sept", CRITERES_SEPT), ("trois", CRITERES_TROIS)):
            exact[nom] = chercherUnModeleExact(produits, criteres, limiteExacte)
            if afficher:
                print(f"Un modèle exact à {len(criteres)} critères existe-t-il ? {exact[nom]['existe']} ({exact[nom]['preuve']})")
        resultat["exact"] = exact
    enregistrerResultats("modeleComplet" if fichier == FICHIER_BASE else "modeleCompletEtendu", resultat)
    return resultat


def evaluerGeneralisation():
    """
    Les modèles appris sur les 125 plats de la base, appliqués aux plats que la base étendue
    ajoute, qu'ils n'ont jamais vus : les 4 modèles du 30/10 (poids appris), et les 4 aux
    profils appris, s'ils sont dans le JSON. Renvoie une ligne par modèle : son exactitude sur
    la base, et sa comparaison sur les plats ajoutés (exactitude brute et équilibrée, à une
    classe près, matrice de confusion).
    """
    from projet_base import FICHIER_BASE_ETENDUE, FICHIER_RESULTATS, LOT_AJOUT, lireBase

    resultats = json.loads(FICHIER_RESULTATS.read_text(encoding="utf-8"))
    ajout = [plat for plat in lireBase(FICHIER_BASE_ETENDUE) if plat.get("lot") == LOT_AJOUT]
    lignes = []
    autres = resultats.get("mrsortProfils", {}).get("modeles", []) + resultats.get("modeleComplet", {}).get("modeles", [])
    for modele in resultats["mrsort"]["modeles"] + autres:
        regle = {"criteres": modele["criteres"], "poids": modele["poids"], "profils": modele["profils"], "lam": modele["lam"]}
        test = appliquerModele(ajout, regle)["comparaison"]
        lignes.append({"nom": modele["nom"], "mode": modele["mode"], "lam": modele["lam"],
                       "base": {"bienRanges": modele["bienRanges"], "total": modele["total"],
                                "exactitude": modele["exactitude"]},
                       "ajout": {cle: test[cle] for cle in ("bienRanges", "total", "exactitude", "exactitudeEquilibree",
                                                           "aUneClassePres", "matrice")}})
    return lignes


# Les deux apprentissages du sujet (§3.3), en toutes lettres
APPRENTISSAGES = {"poids": "profils fixés (médianes), poids appris",
                  "profils": "poids fixés (points maximaux), profils appris",
                  "complet": "poids et profils appris (alternance)"}

# La limite de temps de chaque apprentissage des profils sur la base étendue (--etendue, --croisee),
# en secondes : la même pour tous les apprentissages comparés
LIMITE_ETENDUE = 600


def comparerParValidationCroisee(limiteSecondes=LIMITE_ETENDUE, afficher=True):
    """
    La validation croisée des trois apprentissages (poids, profils, complet) sur les 375 plats
    de la base étendue, à 7 et 3 critères, λ = 0,6 et 0,7 : 5 parts de 75 plats, chaque plat
    rangé par un modèle appris sur les 300 autres (validationCroisee). Long : plusieurs heures.
    Range le tout sous la clé « validationCroisee » de resultats_projet.json, écrit
    resultats/validation_croisee.xlsx, et le renvoie.
    """
    from projet_base import DOSSIER, FICHIER_BASE_ETENDUE, GRAINE, enregistrerResultats, lireBase

    produits = lireBase(FICHIER_BASE_ETENDUE)
    lignes = []
    for nom, criteres in (("sept", CRITERES_SEPT), ("trois", CRITERES_TROIS)):
        for mode in APPRENTISSAGES:
            for lam in SEUILS_MAJORITAIRES:
                debut = time.perf_counter()
                ligne = validationCroisee(produits, criteres, lam, mode, limiteSecondes=limiteSecondes)
                ligne.update(nom=nom, mode=mode, secondes=round(time.perf_counter() - debut))
                lignes.append(ligne)
                if afficher:
                    print(f"Validation croisée, {nom} critères, {mode} appris, λ = {lam} : "
                          f"{100 * ligne['exactitudeMoyenne']:.1f} % (écart-type {100 * ligne['ecartType']:.1f}), "
                          f"{ligne['secondes']} s", flush=True)
    croisee = {"plis": 5, "graine": GRAINE, "limiteSecondes": limiteSecondes, "modeles": lignes}
    enregistrerResultats("validationCroisee", croisee)
    ecrireValidationCroisee(croisee, DOSSIER / "resultats" / "validation_croisee.xlsx")
    return croisee


def ecrireValidationCroisee(croisee, chemin):
    """
    Écrit resultats/validation_croisee.xlsx : une ligne par apprentissage, avec l'exactitude
    moyenne des parts, son écart-type, les plats bien rangés sur les 375, « à une classe près »,
    et le nombre de parts où le solveur a prouvé l'optimum.
    """
    from openpyxl import Workbook
    from projet_design import mettreEnFormeFeuille

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "validation croisée"
    feuille.append(["Critères", "Apprentissage", "λ", "Exactitude moyenne", "Écart-type entre les parts",
                    "Bien rangés", "À une classe près", "Parts à l'optimum prouvé", "Durée (s)"])
    for ligne in croisee["modeles"]:
        comparaison = ligne["comparaison"]
        prouvees = sum(1 for part in ligne["parts"] if part["optimal"])
        feuille.append([f"{len(CRITERES_SEPT) if ligne['nom'] == 'sept' else len(CRITERES_TROIS)} critères",
                        APPRENTISSAGES[ligne["mode"]], ligne["lam"], ligne["exactitudeMoyenne"], ligne["ecartType"],
                        f"{comparaison['bienRanges']} sur {comparaison['total']}", comparaison["aUneClassePres"],
                        f"{prouvees} sur {len(ligne['parts'])}", ligne["secondes"]])
    mettreEnFormeFeuille(feuille, [12, 34, 6, 16, 18, 14, 14, 18, 10], formats={4: "0.0%", 5: "0.0%", 7: "0.0%"})
    chemin.parent.mkdir(parents=True, exist_ok=True)
    classeur.save(chemin)


def ecrireGeneralisation(lignes, courbe, chemin):
    """
    Écrit resultats/generalisation.xlsx : la comparaison des modèles appris sur la base (les
    deux apprentissages, 7 et 3 critères, λ = 0,6 et 0,7), sur la base et sur les plats
    ajoutés, puis la courbe d'apprentissage (si elle est calculée).
    """
    from openpyxl import Workbook
    from projet_design import mettreEnFormeFeuille

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "les modèles"
    feuille.append(["Critères", "Apprentissage", "λ", "Exactitude sur la base (125)", "Bien rangés parmi les plats ajoutés",
                    "Exactitude sur les plats ajoutés", "Exactitude équilibrée", "À une classe près"])
    for ligne in lignes:
        ajout = ligne["ajout"]
        feuille.append([f"{len(CRITERES_SEPT) if ligne['nom'] == 'sept' else len(CRITERES_TROIS)} critères",
                        APPRENTISSAGES[ligne["mode"]], ligne["lam"],
                        ligne["base"]["exactitude"], f"{ajout['bienRanges']} sur {ajout['total']}",
                        ajout["exactitude"], ajout["exactitudeEquilibree"], ajout["aUneClassePres"]])
    mettreEnFormeFeuille(feuille, [12, 34, 6, 16, 18, 16, 14, 14], formats={4: "0.0%", 6: "0.0%", 7: "0.0%", 8: "0.0%"})
    if courbe:
        feuilleCourbe = classeur.create_sheet("courbe d'apprentissage")
        feuilleCourbe.append(["Critères", "Plats appris", "Exactitude sur les plats appris",
                              "Exactitude sur les plats tenus à part", "Écart-type (tenus à part)"])
        for nom in ("sept", "trois"):
            for point in courbe[nom]:
                feuilleCourbe.append([f"{len(CRITERES_SEPT) if nom == 'sept' else len(CRITERES_TROIS)} critères",
                                      point["taille"], point["appris"], point["tenusAPart"], point["ecartType"]])
        mettreEnFormeFeuille(feuilleCourbe, [12, 12, 18, 20, 16], formats={3: "0.0%", 4: "0.0%", 5: "0.0%"})
    chemin.parent.mkdir(parents=True, exist_ok=True)
    classeur.save(chemin)


def main():
    """
    Compare les modèles sur la base de plats préparés. Avec --profils, apprend aussi les
    modèles aux profils appris (sinon, ceux du JSON servent). Avec la base étendue : les
    modèles appris sur ses 375 plats (départagés par la plus grande marge), et les modèles de
    la base sur les plats ajoutés. Avec --courbe, la courbe d'apprentissage en plus. Avec
    --etendue, les profils appris et le modèle complet sur les 375 plats ; avec --croisee, la
    validation croisée des trois apprentissages ; --limite règle leur limite de temps.
    """
    from projet_base import DOSSIER, FICHIER_BASE_ETENDUE, FICHIER_RESULTATS, enregistrerResultats, lireBase

    parseur = argparse.ArgumentParser(description="Les modèles MR-Sort qui approchent le Nutri-Score (question 3.3).")
    parseur.add_argument("--courbe", action="store_true", help="calculer aussi la courbe d'apprentissage (quelques minutes)")
    parseur.add_argument("--profils", action="store_true",
                         help="apprendre aussi les profils, poids fixés (jusqu'à cinq minutes par modèle)")
    parseur.add_argument("--complet", action="store_true",
                         help="le modèle complet (alternance) et la recherche d'un modèle exact (jusqu'à une heure)")
    parseur.add_argument("--etendue", action="store_true",
                         help="apprendre aussi les profils et le modèle complet sur les 375 plats (une heure ou plus)")
    parseur.add_argument("--croisee", action="store_true",
                         help="la validation croisée des trois apprentissages sur les 375 plats (plusieurs heures)")
    parseur.add_argument("--limite", type=int, default=LIMITE_ETENDUE,
                         help=f"la limite de chaque apprentissage des profils pour --etendue et --croisee ({LIMITE_ETENDUE} s par défaut)")
    arguments = parseur.parse_args()

    comparerModeles()
    if arguments.profils:
        comparerModeles(modes=("profils",))
    if arguments.complet:
        apprendreLesModelesComplets()
    if not FICHIER_BASE_ETENDUE.exists():
        return
    comparerModeles(FICHIER_BASE_ETENDUE, departage="marge")
    if arguments.etendue:
        comparerModeles(FICHIER_BASE_ETENDUE, modes=("profils",), limiteSecondes=arguments.limite)
        apprendreLesModelesComplets(fichier=FICHIER_BASE_ETENDUE, chercherExact=False, limiteSecondes=arguments.limite)
    if arguments.croisee:
        comparerParValidationCroisee(arguments.limite)
    lignes = evaluerGeneralisation()
    enregistrerResultats("generalisation", {"modeles": lignes})
    for ligne in lignes:
        print(f"MRSort_{ligne['nom']}, {ligne['mode']} appris, λ = {ligne['lam']} : {100 * ligne['base']['exactitude']:.1f} % sur la base, "
              f"{100 * ligne['ajout']['exactitude']:.1f} % sur les plats ajoutés "
              f"({100 * ligne['ajout']['exactitudeEquilibree']:.1f} % à classes égales)")

    if arguments.courbe:
        plats = lireBase(FICHIER_BASE_ETENDUE)
        courbe = {"lam": 0.6, "tenusAPart": 15, "tirages": 10}
        for nom, criteres in (("sept", CRITERES_SEPT), ("trois", CRITERES_TROIS)):
            courbe[nom] = courbeDApprentissage(plats, criteres, lam=0.6, tirages=10, tenusAPart=15)
            for point in courbe[nom]:
                print(f"  {nom}, {point['taille']} plats appris : {100 * point['appris']:.1f} % appris, "
                      f"{100 * point['tenusAPart']:.1f} % tenus à part")
        enregistrerResultats("courbeApprentissage", courbe)
    courbe = json.loads(FICHIER_RESULTATS.read_text(encoding="utf-8")).get("courbeApprentissage")
    ecrireGeneralisation(lignes, courbe, DOSSIER / "resultats" / "generalisation.xlsx")


if __name__ == "__main__":
    main()
