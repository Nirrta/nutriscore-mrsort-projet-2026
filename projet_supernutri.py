"""
projet_supernutri.py : le SuperNutri-score, notre propre modèle MR-Sort (question 3.4).

Le SuperNutri-score ne cherche plus à reproduire le Nutri-Score. Il range les plats préparés
selon onze critères, groupés en trois piliers (choix du groupe, 20/11/2026) :
- à limiter (0,40) : énergie, acides gras saturés, sucres, sel ;
- à favoriser (0,30) : protéines, fibres, fruits, légumes et légumineuses ;
- transformation et production (0,30) : groupe NOVA, nombre d'additifs, additifs à risque, bio.

Les poids. Dans les deux piliers nutritionnels, chaque critère pèse au prorata de ses points
maximaux dans le Nutri-Score : le sel (20 points) pèse deux fois l'énergie (10 points). Dans le
troisième pilier : NOVA 0,10 ; nombre d'additifs et additifs à risque 0,075 chacun (les 0,15 des
additifs sont partagés entre « combien » et « lesquels », pour ne pas les compter deux fois) ;
bio 0,05, le plus faible, car son effet sur la santé (moins de pesticides) est le moins établi.

Les profils viennent des textes officiels : pour A′, les seuils des allégations du règlement
CE 1924/2006 (« faible teneur » en graisses saturées, en sucres et en sel, « riche en fibres ») ;
pour les autres classes, les seuils de points du Nutri-Score de 2023. Le seuil majoritaire vaut
λ = 0,7 : un plat peut rater au plus 0,3 du poids face à un profil, par exemple tout le pilier de
la transformation et de la production, mais rien d'autre.

Les classes ont le sens de celles du Nutri-Score : elles vont des plats les plus favorables à la
santé (A′) aux moins favorables (E′), par leur composition, leur transformation et leur mode de
production. Il ne s'agit pas de « bons » ou de « mauvais » plats : les classes servent à comparer
des plats préparés entre eux.

Une valeur absente ne vote jamais pour le plat : elle prend la pire valeur possible.

Commande :
    python3 projet_supernutri.py   # range les deux bases, écrit resultats/supernutri_*.xlsx et la clé « supernutri » du JSON
"""

import csv
import math
import random
import re
from datetime import date
from pathlib import Path

from projet_base import (DOSSIER, DOSSIER_BRUT, FICHIER_BASE, FICHIER_BASE_ETENDUE, champsDeLaFiche,
                         enregistrerResultats, ficheEnDirect, ficheProduit, intersectionAvecAutreBase, lireBase)
from projet_mrsort import (CLASSES, PROFILS, TOLERANCE, affecter, classeDuLabel, comparerAuNutriscore,
                           concordancePartielle, nomDeClasse)
from projet_nutriscore import (POINTS_MAX, PROTEINES_MAX_VIANDE_ROUGE, SEUIL_PROTEINES, SEUILS_PROTEINES,
                               categorieDepuisOff, scoreNutriscore)


# --- Question 3.4 : le modèle ---

# Les onze critères : (libellé, unité, sens). « min » : moins c'est mieux ; « max » : plus c'est mieux.
CRITERES_LIBELLES = {
    "en": ("Énergie", "kJ/100 g", "min"),
    "sa": ("Acides gras saturés", "g/100 g", "min"),
    "su": ("Sucres", "g/100 g", "min"),
    "so": ("Sel", "g/100 g", "min"),
    "pr": ("Protéines", "g/100 g", "max"),
    "fi": ("Fibres", "g/100 g", "max"),
    "fr": ("Fruits, légumes et légumineuses", "%", "max"),
    "nova": ("Groupe NOVA", "de 1 à 4", "min"),
    "additifs": ("Nombre d'additifs", "", "min"),
    "aRisque": ("Additifs à risque", "", "min"),
    "bio": ("Bio", "1 si bio, 0 sinon", "max"),
    "sodium": ("Sodium", "mg/100 g", "min"),          # un critère du modèle de l'autre groupe, pas du nôtre
}

# Les trois piliers : (poids du pilier, critères)
PILIERS = {
    "à limiter": (0.40, ["en", "sa", "su", "so"]),
    "à favoriser": (0.30, ["pr", "fi", "fr"]),
    "transformation et production": (0.30, ["nova", "additifs", "aRisque", "bio"]),
}

# Les poids propres du pilier de la transformation et de la production (leur somme fait 0,30)
POIDS_TRANSFORMATION = {"nova": 0.10, "additifs": 0.075, "aRisque": 0.075, "bio": 0.05}

# Les critères dans l'ordre des piliers
CRITERES_SUPER = []
for poidsDuPilier, criteresDuPilier in PILIERS.values():
    CRITERES_SUPER += criteresDuPilier

# Les profils, de b2 (seuil de D′) à b5 (seuil de A′)
PROFILS_SUPER = {
    "en": [1340, 1005, 670, 335],      # au plus 3, 2, 1 et 0 point d'énergie au Nutri-Score de 2023
    "sa": [7, 5, 3, 1.5],              # A′ : « faible teneur en graisses saturées » ; puis points du Nutri-Score
    "su": [14, 10, 6.8, 5],            # A′ : « faible teneur en sucres » ; puis points du Nutri-Score
    "so": [1.4, 1.0, 0.6, 0.3],        # A′ : « faible teneur en sel » ; puis points du Nutri-Score
    "pr": [2.4, 4.8, 7.2, 12],         # points de protéines du Nutri-Score de 2023
    "fi": [1, 2, 3, 6],                # A′ : « riche en fibres », B′ : « source de fibres » ; puis 2 et 1 g
    "fr": [0, 20, 40, 60],             # points du Nutri-Score de 2023 (40 et 60 %) ; puis 20 et 0 %
    "nova": [4, 4, 3, 3],              # A′ et B′ : au plus un aliment transformé (NOVA 3)
    "additifs": [5, 3, 1, 0],          # A′ : aucun additif ; B′ : un au plus
    "aRisque": [2, 1, 0, 0],           # A′ et B′ : aucun additif à risque
    "bio": [0, 0, 1, 1],               # A′ et B′ : le label bio
}

# La source de chaque seuil, pour le README, les slides et l'interface
SOURCES_DES_SEUILS = {
    "en": "seuils de points d'énergie du Nutri-Score de 2023",
    "sa": "A′ : allégation « faible teneur en graisses saturées » (règlement CE 1924/2006) ; puis points du Nutri-Score",
    "su": "A′ : allégation « faible teneur en sucres » (règlement CE 1924/2006) ; puis points du Nutri-Score",
    "so": "A′ : allégation « faible teneur en sel » (règlement CE 1924/2006) ; puis points du Nutri-Score",
    "pr": "seuils de points de protéines du Nutri-Score de 2023",
    "fi": "A′ : « riche en fibres », B′ : « source de fibres » (règlement CE 1924/2006) ; puis 2 et 1 g",
    "fr": "seuils de points du Nutri-Score de 2023 (40 et 60 %) ; puis 20 et 0 %",
    "nova": "classification NOVA : A′ et B′ au plus transformés (NOVA 3), pas ultra-transformés",
    "additifs": "aucun additif pour A′, un au plus pour B′, puis 3 et 5",
    "aRisque": "aucun additif à risque pour A′ et B′, puis 1 et 2",
    "bio": "label bio (règlement UE 2018/848) exigé pour A′ et B′",
}

LAM_SUPER = 0.7

# Le sens des classes, comme celles du Nutri-Score : du plus favorable à la santé au moins favorable
SENS_DES_CLASSES = {
    "A′": "les plus favorables à la santé",
    "B′": "favorables à la santé",
    "C′": "moyens",
    "D′": "peu favorables à la santé",
    "E′": "les moins favorables à la santé",
}

# Les additifs signalés par une autorité sanitaire, par famille : (numéros E, source)
ADDITIFS_A_RISQUE = {
    "nitrites et nitrates": ({249, 250, 251, 252}, "ANSES, avis de 2022 sur les nitrites et les nitrates"),
    "phosphates": ({338, 339, 340, 341, 343, 450, 451, 452}, "EFSA, réévaluation des phosphates de 2019"),
    "carraghénanes": ({407}, "EFSA, réévaluation des carraghénanes de 2018"),
}

# Pourquoi chaque famille est « à risque », en une ligne (sources vérifiées le 26/11)
RAISONS_DES_ADDITIFS_A_RISQUE = {
    "nitrites et nitrates": "associés au cancer colorectal",
    "phosphates": "une dose admise que l'apport total des enfants dépasse",
    "carraghénanes": "une dose admise provisoire, faute de données",
}

# Les quatre groupes NOVA (Université de São Paulo, 2009) : ils rangent les aliments selon leur
# transformation, pas selon leurs nutriments. Open Food Facts les calcule à partir des ingrédients.
GROUPES_NOVA = {
    1: "brut ou peu transformé",
    2: "ingrédient culinaire : huile, beurre, sucre, sel",
    3: "transformé : conserve, fromage, pain",
    4: "ultra-transformé : formulation industrielle, souvent avec des additifs",
}

# Les deux plats qui illustrent la transformation : la Poêlée Fermière (NOVA 4, trois additifs, aucun
# à risque) et la pizza Regina de Buitoni (le nitrite du jambon et un polyphosphate)
EXEMPLES_TRANSFORMATION = ("3257982125116", "7613033139642")


def libelleEnMinuscule(critere):
    """Le libellé d'un critère dans une phrase : sa première lettre en minuscule, ses sigles gardés (« groupe NOVA »)."""
    libelle = CRITERES_LIBELLES[critere][0]
    return libelle[:1].lower() + libelle[1:]


def poidsDesPiliers():
    """
    Les poids du SuperNutri-score. Dans les piliers à limiter et à favoriser, chaque critère pèse
    au prorata de ses points maximaux dans le Nutri-Score (POINTS_MAX) ; le pilier de la
    transformation et de la production a ses propres poids (POIDS_TRANSFORMATION).
    """
    poids = {}
    for nom, (poidsDuPilier, criteres) in PILIERS.items():
        if nom == "transformation et production":
            for critere in criteres:
                poids[critere] = POIDS_TRANSFORMATION[critere]
        else:
            total = sum(POINTS_MAX[critere] for critere in criteres)
            for critere in criteres:
                poids[critere] = poidsDuPilier * POINTS_MAX[critere] / total
    return poids


def modeleSuper():
    """Le modèle MR-Sort du SuperNutri-score : critères, poids, profils de b2 à b5, λ, et sens de chaque critère."""
    profils = []
    for numero in range(4):
        profils.append({critere: PROFILS_SUPER[critere][numero] for critere in CRITERES_SUPER})
    return {"criteres": list(CRITERES_SUPER), "poids": poidsDesPiliers(), "profils": profils, "lam": LAM_SUPER,
            "sens": {critere: CRITERES_LIBELLES[critere][2] for critere in CRITERES_SUPER}}


MODELE_SUPER = modeleSuper()


def numerosDesAdditifs(listeAdditifs):
    """Les numéros des additifs d'une liste écrite « E330, E407a » : {330, 407}. Une liste vide donne un ensemble vide."""
    numeros = set()
    for code in (listeAdditifs or "").split(","):
        trouve = re.match(r"\s*E(\d+)", code, re.IGNORECASE)
        if trouve:
            numeros.add(int(trouve.group(1)))
    return numeros


def additifsARisque(listeAdditifs):
    """Le nombre d'additifs de la liste qui appartiennent à une famille d'ADDITIFS_A_RISQUE."""
    numeros = numerosDesAdditifs(listeAdditifs)
    total = 0
    for numerosDeLaFamille, source in ADDITIFS_A_RISQUE.values():
        total += len(numeros & numerosDeLaFamille)
    return total


# Les sept composantes du Nutri-Score : il faut toutes les connaître pour savoir s'il compte les protéines
COMPOSANTES_NUTRISCORE = ["en", "sa", "su", "so", "pr", "fi", "fr"]

# Une viande rouge garde au plus 2 points de protéines au Nutri-Score : ses protéines votent comme 4,8 g au plus
PROTEINES_RETENUES_VIANDE_ROUGE = SEUILS_PROTEINES[PROTEINES_MAX_VIANDE_ROUGE - 1]


def proteinesRetenues(plat, categorie):
    """
    Les protéines que le Nutri-Score de 2023 retient pour ce type de produit (FAQ de 2023), c'est
    la performance du critère des protéines : None s'il ne les compte pas (cas général à partir de
    11 points négatifs, matière grasse à partir de 7) ; 4,8 g au plus pour une viande rouge, qui
    garde au plus 2 points ; sinon les protéines du plat. Un fromage et une boisson les gardent
    toujours. Si une des sept composantes manque, le Nutri-Score ne peut pas trancher : on garde
    les protéines du plat.
    """
    if any(plat.get(composante) is None for composante in COMPOSANTES_NUTRISCORE):
        return plat.get("pr")
    if not scoreNutriscore(plat, categorie=categorie)["proteinesComptees"]:
        return None
    if categorie == "viandeRouge":
        return min(plat["pr"], PROTEINES_RETENUES_VIANDE_ROUGE)
    return plat["pr"]


def valeursDuPlat(plat, categorie=None):
    """
    Les onze valeurs d'un plat pour le SuperNutri-score. Les protéines sont celles que le
    Nutri-Score de 2023 retient pour le type du produit (proteinesRetenues) : categorie, sinon le
    type que porte le produit, sinon le cas général. Le bio vaut 1 (label bio) ou 0 ; les additifs
    à risque se comptent dans la liste des additifs. Une valeur absente prend la pire valeur
    possible (+∞ pour un critère à minimiser, −∞ pour un critère à maximiser) : elle ne vote
    jamais pour le plat.
    """
    valeurs = {}
    for critere in ["en", "sa", "su", "so", "fi", "fr", "nova", "additifs"]:
        valeurs[critere] = plat.get(critere)
    valeurs["pr"] = proteinesRetenues(plat, categorie or plat.get("categorie") or "general")
    if "aRisque" in plat:                               # saisi directement, dans l'interface
        valeurs["aRisque"] = plat["aRisque"]
    elif plat.get("additifs") is None:                  # la liste n'est connue que si le nombre l'est
        valeurs["aRisque"] = None
    else:                                               # une liste vide veut alors dire « aucun »
        valeurs["aRisque"] = additifsARisque(plat.get("listeAdditifs"))
    bio = plat.get("bio")
    if bio in ("oui", True):
        valeurs["bio"] = 1
    elif bio in ("non", False):
        valeurs["bio"] = 0
    else:
        valeurs["bio"] = None
    for critere in CRITERES_SUPER:
        if valeurs[critere] is None:
            valeurs[critere] = math.inf if CRITERES_LIBELLES[critere][2] == "min" else -math.inf
    return valeurs


def explicationDuPlat(valeurs, modele):
    """
    Profil par profil, de A′ jusqu'à la classe du plat, les critères qui votent contre lui :
    « A′ : rate sel, fibres ; B′ : rate fibres ; C′ : franchi ».
    """
    detail = affecter(valeurs, modele)
    satisfaits = criteresSatisfaits(valeurs, modele)
    morceaux = []
    for numero in range(len(modele["profils"]) - 1, -1, -1):
        classe = nomDeClasse(numero + 1)
        if detail["franchis"][numero]:
            morceaux.append(f"{classe} : franchi")
            break
        rates = [libelleEnMinuscule(critere) for critere in modele["criteres"] if critere not in satisfaits[numero]]
        morceaux.append(f"{classe} : rate {', '.join(rates)}")
    return " ; ".join(morceaux)


def classerPlat(plat, modele=None, categorie=None):
    """
    Range un plat avec le SuperNutri-score (MODELE_SUPER par défaut) ; categorie : son type au
    Nutri-Score, sinon le sien, sinon le cas général. Renvoie le détail d'affecter (classe,
    concordances, profils franchis), plus la lettre de la classe.
    """
    detail = affecter(valeursDuPlat(plat, categorie), modele or MODELE_SUPER)
    detail["lettre"] = nomDeClasse(detail["classe"])
    return detail


def sensDesEcarts(matrice):
    """
    Le sens des écarts d'un modèle à sa référence, lu dans leur matrice de confusion (lignes : la
    référence, de A à E ; colonnes : le modèle, de A′ à E′). Plus sévère : le modèle range le
    produit plus bas (à droite de la diagonale) ; plus permissif : plus haut. L'écart moyen se
    compte en classes, positif quand le modèle est plus sévère.
    """
    total = sum(sum(ligne) for ligne in matrice)
    plusSevere = plusPermissif = ecarts = 0
    for ligne, comptes in enumerate(matrice):
        for colonne, nombre in enumerate(comptes):
            if colonne > ligne:
                plusSevere += nombre
            elif colonne < ligne:
                plusPermissif += nombre
            ecarts += (colonne - ligne) * nombre
    return {"plusSevere": plusSevere / total, "pareil": (total - plusSevere - plusPermissif) / total,
            "plusPermissif": plusPermissif / total, "ecartMoyen": ecarts / total}


def transformationDesPlats(plats, exemples=EXEMPLES_TRANSFORMATION):
    """
    Le pilier de la transformation, compté sur une base : les plats de chaque groupe NOVA, les plats
    bio, les plats sans additif, ceux qui ont au moins un additif à risque, et le nombre de plats de
    chaque famille d'additifs à risque. Pour chaque code d'exemples présent dans la base : son nom,
    sa marque, son groupe NOVA et ses additifs.
    """
    nova = {str(groupe): 0 for groupe in GROUPES_NOVA}
    familles = {famille: 0 for famille in ADDITIFS_A_RISQUE}
    bio = sansAdditif = avecARisque = 0
    for plat in plats:
        if plat.get("nova") in GROUPES_NOVA:
            nova[str(plat["nova"])] += 1
        bio += plat.get("bio") == "oui"
        sansAdditif += plat.get("additifs") == 0
        numeros = numerosDesAdditifs(plat.get("listeAdditifs"))
        avecARisque += additifsARisque(plat.get("listeAdditifs")) > 0
        for famille, (numerosDeLaFamille, _) in ADDITIFS_A_RISQUE.items():
            familles[famille] += bool(numeros & numerosDeLaFamille)
    lignesExemples = [{"code": plat["code"], "nom": plat.get("nom"), "marque": plat.get("marque"), "label": plat.get("label"),
                       "nova": plat.get("nova"), "additifs": plat.get("additifs"), "listeAdditifs": plat.get("listeAdditifs"),
                       "aRisque": additifsARisque(plat.get("listeAdditifs"))}
                      for code in exemples for plat in plats if plat["code"] == code]
    return {"total": len(plats), "nova": nova, "bio": bio, "sansAdditif": sansAdditif, "avecARisque": avecARisque,
            "familles": familles, "exemples": lignesExemples}


def produitsSecsEnAPrime(plats, modele=None):
    """
    Les plats en A′ qui dépassent le seuil d'énergie de D′ (1 340 kJ pour 100 g) : des produits
    secs, à cuire ou à réhydrater. Une limite de notre modèle : ses seuils lisent 100 g du produit
    tel qu'il est vendu, et λ = 0,7 laisse rater l'énergie.
    """
    modele = modele or MODELE_SUPER
    seuil = modele["profils"][0]["en"]
    return [plat["nom"] for plat in plats if plat["en"] > seuil and classerPlat(plat, modele)["lettre"] == "A′"]


def superNutriScore(fichier=FICHIER_BASE, modele=None, sortie=None, afficher=True):
    """
    Range tous les plats d'une base avec le SuperNutri-score. Écrit l'Excel `sortie` s'il est
    donné, et affiche la répartition des classes si afficher. Renvoie un dictionnaire : le
    modèle, une ligne par plat (code, nom, Nutri-Score, classe et concordances), la répartition
    des classes de A′ à E′ et la comparaison au Nutri-Score.
    """
    modele = modele or MODELE_SUPER
    plats = lireBase(fichier)
    lignes = []
    for plat in plats:
        detail = classerPlat(plat, modele)
        lignes.append({"code": plat["code"], "nom": plat["nom"], "label": plat["label"], "classe": detail["classe"],
                       "lettre": detail["lettre"], "concordances": [round(c, 4) for c in detail["concordances"]]})
    repartition = {lettre: 0 for lettre in reversed(CLASSES)}
    for ligne in lignes:
        repartition[ligne["lettre"]] += 1
    comparaison = comparerAuNutriscore([classeDuLabel(ligne["label"]) for ligne in lignes],
                                       [ligne["classe"] for ligne in lignes])
    comparaison["sens"] = sensDesEcarts(comparaison["matrice"])
    resultat = {"modele": modele, "plats": lignes, "repartition": repartition, "comparaison": comparaison,
                "ecarts": ecartsAuNutriscore(plats, modele), "secsEnAPrime": produitsSecsEnAPrime(plats, modele)}
    if sortie:
        ecrireSuperNutri(plats, resultat, sortie)
    if afficher:
        afficherSuperNutri(resultat)
    return resultat


def ecrireSuperNutri(plats, resultat, chemin):
    """
    Écrit un Excel au style Verso. La première feuille a une ligne par plat : ses onze valeurs, son
    Nutri-Score, sa classe au SuperNutri-score, l'écart entre les deux (en classes, positif si le
    plat monte) et les critères qui l'expliquent (ecartsAuNutriscore). Une valeur absente reste une
    case vide. La feuille « comparaison » croise les deux classements, puis compte les critères
    ratés par les plats qui descendent.
    """
    from openpyxl import Workbook
    from projet_design import mettreEnFormeFeuille

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "supernutri-score"
    feuille.append(["Code-barres", "Nom"] + [CRITERES_LIBELLES[critere][0] for critere in CRITERES_SUPER]
                   + ["Nutri-Score", "SuperNutri-score", "Écart au Nutri-Score", "Critères ratés",
                      "Protéines retenues par le Nutri-Score", "Explication"])
    for plat, ligne, ecart in zip(plats, resultat["plats"], resultat["ecarts"]["plats"]):
        valeurs = valeursDuPlat(plat)
        cellules = [None if math.isinf(valeurs[critere]) else valeurs[critere] for critere in CRITERES_SUPER]
        rates = ", ".join(CRITERES_LIBELLES[critere][0] for critere in ecart["rates"])
        retenues = proteinesRetenues(plat, plat.get("categorie") or "general")
        feuille.append([plat["code"], plat["nom"]] + cellules + [plat["label"], ligne["lettre"], ecart["ecart"], rates,
                                                                  "non comptées" if retenues is None else retenues,
                                                                  explicationDuPlat(valeurs, resultat["modele"])])
    colonneNutriscore = 3 + len(CRITERES_SUPER)
    mettreEnFormeFeuille(feuille, [16, 40] + [12] * len(CRITERES_SUPER) + [12, 16, 12, 60, 14, 90],
                         colonnesClasses=(colonneNutriscore, colonneNutriscore + 1))

    feuille = classeur.create_sheet("comparaison")
    feuille.append(["Nutri-Score \\ SuperNutri-score"] + list(reversed(CLASSES)))
    for rang, ligne in enumerate(resultat["comparaison"]["matrice"]):
        feuille.append(["ABCDE"[rang]] + ligne)
    feuille.append([])
    feuille.append(["Critère raté face au profil de la classe du Nutri-Score", "Plats qui descendent"])
    for critere, nombre in resultat["ecarts"]["raisonsDesDescentes"].items():
        feuille.append([CRITERES_LIBELLES[critere][0], nombre])
    mettreEnFormeFeuille(feuille, [44, 10, 10, 10, 10, 10], colonnesClasses=(1,))

    chemin.parent.mkdir(parents=True, exist_ok=True)
    classeur.save(chemin)


def afficherSuperNutri(resultat):
    """Affiche la répartition des classes du SuperNutri-score et sa comparaison au Nutri-Score."""
    total = len(resultat["plats"])
    comparaison = resultat["comparaison"]
    print(f"SuperNutri-score, {total} plats, λ = {resultat['modele']['lam']}")
    print("  répartition : " + ", ".join(f"{lettre} {nombre}" for lettre, nombre in resultat["repartition"].items()))
    print(f"  même classe que le Nutri-Score : {comparaison['bienRanges']}/{total} ; "
          f"à une classe près : {100 * comparaison['aUneClassePres']:.1f} %")
    sens = comparaison["sens"]
    print(f"  plus sévère que le Nutri-Score pour {100 * sens['plusSevere']:.1f} % des plats, plus permissif pour "
          f"{100 * sens['plusPermissif']:.1f} % ; écart moyen {sens['ecartMoyen']:+.2f} classe")
    ecarts = resultat["ecarts"]
    raisons = sorted(ecarts["raisonsDesDescentes"].items(), key=lambda paire: -paire[1])[:4]
    print(f"  {ecarts['montent']} plats montent, {ecarts['descendent']} descendent ; les plats qui descendent ratent surtout : "
          + ", ".join(f"{CRITERES_LIBELLES[critere][0]} ({nombre})" for critere, nombre in raisons))


# --- Question 3.4 : analyses de sensibilité ---

def criteresSatisfaits(valeurs, modele):
    """
    Pour chaque profil, de b2 à b5, la liste des critères sur lesquels le plat est au moins aussi
    bon que le profil. Elle ne dépend pas des poids : l'analyse des poids la calcule une seule fois
    par plat, puis ne refait que des sommes.
    """
    satisfaits = []
    for profil in modele["profils"]:
        liste = []
        for critere in modele["criteres"]:
            if concordancePartielle(valeurs[critere], profil[critere], modele["sens"][critere]) == 1:
                liste.append(critere)
        satisfaits.append(liste)
    return satisfaits


def classeDepuisSatisfaits(satisfaits, poids, lam):
    """
    La classe d'un plat dont on connaît les critères satisfaits face à chaque profil : celle du
    meilleur profil dont la concordance (la somme des poids satisfaits) atteint λ, comme affecter.
    """
    for numero in range(len(satisfaits) - 1, -1, -1):
        if sum(poids[critere] for critere in satisfaits[numero]) >= lam - TOLERANCE:
            return numero + 1
    return 0


def poidsModifies(poids, critere, delta):
    """
    Les poids après avoir ajouté delta au poids d'un critère, sans descendre sous 0 ; les autres
    poids sont multipliés par un même facteur, pour que la somme fasse toujours 1.
    """
    nouveau = max(0.0, poids[critere] + delta)
    facteur = (1 - nouveau) / (1 - poids[critere])
    resultat = {}
    for autre, valeur in poids.items():
        resultat[autre] = nouveau if autre == critere else valeur * facteur
    return resultat


def poidsTires(poids, amplitude, hasard):
    """
    Des poids tirés au hasard : chacun bouge d'au plus ± amplitude, sans descendre sous 0, puis
    tous sont divisés par leur somme, qui revient à 1. hasard : un random.Random.
    """
    tires = {}
    for critere, valeur in poids.items():
        tires[critere] = max(0.0, valeur + hasard.uniform(-amplitude, amplitude))
    total = sum(tires.values())
    return {critere: valeur / total for critere, valeur in tires.items()}


def sensibilitePoids(produits, modele=None, amplitude=0.05, tirages=1000, graine=2026):
    """
    L'analyse de sensibilité aux poids (§3.4) : les poids bougent un peu, en restant positifs et de
    somme 1, et l'on compte les plats qui changent de classe.
    - Un par un : chaque poids gagne ou perd amplitude (0,05), les autres sont rajustés.
    - Au hasard : tirages fois, tous les poids bougent ensemble d'au plus ± amplitude (graine fixée).
    Renvoie les changements de chaque variation une par une, la part moyenne et la plus grande
    part de plats qui changent lors des tirages, et les plats qui changent le plus souvent.
    """
    modele = modele or MODELE_SUPER
    satisfaits = [criteresSatisfaits(valeursDuPlat(plat), modele) for plat in produits]
    reference = [classeDepuisSatisfaits(s, modele["poids"], modele["lam"]) for s in satisfaits]

    def platsQuiChangent(poids):
        """Les numéros des plats dont la classe n'est plus la même avec ces poids."""
        return [numero for numero, s in enumerate(satisfaits)
                if classeDepuisSatisfaits(s, poids, modele["lam"]) != reference[numero]]

    unParUn = []
    for critere in modele["criteres"]:
        for delta in (amplitude, -amplitude):
            poids = poidsModifies(modele["poids"], critere, delta)
            changes = platsQuiChangent(poids)
            unParUn.append({"critere": critere, "delta": delta, "poids": round(poids[critere], 4),
                            "plats": len(changes), "part": len(changes) / len(produits)})

    hasard = random.Random(graine)
    parts = []
    frequences = [0] * len(produits)
    for tirage in range(tirages):
        changes = platsQuiChangent(poidsTires(modele["poids"], amplitude, hasard))
        parts.append(len(changes) / len(produits))
        for numero in changes:
            frequences[numero] += 1
    sensibles = []
    for numero in sorted(range(len(produits)), key=lambda n: -frequences[n]):
        if frequences[numero] > 0 and len(sensibles) < 10:
            plat = produits[numero]
            sensibles.append({"code": plat.get("code"), "nom": plat.get("nom"), "lettre": nomDeClasse(reference[numero]),
                              "frequence": frequences[numero] / tirages})
    return {"amplitude": amplitude, "unParUn": unParUn, "tirages": tirages,
            "partMoyenne": sum(parts) / len(parts) if parts else 0, "partMax": max(parts) if parts else 0,
            "platsSensibles": sensibles}


def profilsOrdonnes(profils, sens):
    """Vrai si, de b2 à b5, chaque profil est au moins aussi exigeant que le précédent, sur chaque critère."""
    for critere, sensDuCritere in sens.items():
        for numero in range(1, len(profils)):
            avant, apres = profils[numero - 1][critere], profils[numero][critere]
            if (sensDuCritere == "min" and apres > avant) or (sensDuCritere == "max" and apres < avant):
                return False
    return True


def sensibiliteProfils(produits, modele=None, decalage=0.05, pasEntier=1):
    """
    L'analyse de sensibilité aux profils (§3.4) : une valeur de profil bouge à la fois, en gardant
    l'ordre des profils, et l'on liste les plats dont la classe change.
    - Les sept composantes bougent de ± decalage (5 %).
    - NOVA et les deux nombres d'additifs, des entiers, bougent de ± pasEntier (1) ; NOVA reste
      entre 1 et 4, et un nombre d'additifs ne descend pas sous 0.
    - Le bio, qui vaut 0 ou 1, ne bouge pas.
    Un décalage qui casserait l'ordre des profils est écarté. Renvoie chaque décalage avec le
    nombre de plats qui changent, puis ces plats, avec les décalages qui les changent. Les plats
    touchés par les composantes et par les entiers se comptent aussi à part, car leurs pas ne se
    comparent pas.
    """
    modele = modele or MODELE_SUPER
    valeurs = [valeursDuPlat(plat) for plat in produits]
    reference = [affecter(v, modele)["classe"] for v in valeurs]
    scenarios = []
    touches = {}                                       # numéro du plat → les décalages qui changent sa classe
    parFamille = {"composantes": set(), "entiers": set()}
    for numero, nomDuProfil in enumerate(PROFILS):
        for critere in modele["criteres"]:
            if critere == "bio":
                continue
            ancienne = modele["profils"][numero][critere]
            if critere in ("nova", "additifs", "aRisque"):
                nouvelles = [ancienne + pasEntier, ancienne - pasEntier]
            else:
                nouvelles = [round(ancienne * (1 + decalage), 4), round(ancienne * (1 - decalage), 4)]
            for nouvelle in nouvelles:
                if nouvelle == ancienne or nouvelle < 0 or (critere == "nova" and not 1 <= nouvelle <= 4):
                    continue
                profils = [dict(profil) for profil in modele["profils"]]
                profils[numero][critere] = nouvelle
                if not profilsOrdonnes(profils, modele["sens"]):
                    continue
                decale = dict(modele, profils=profils)
                changes = []
                for numeroDuPlat, v in enumerate(valeurs):
                    classe = affecter(v, decale)["classe"]
                    if classe != reference[numeroDuPlat]:
                        changes.append(numeroDuPlat)
                        parFamille["entiers" if critere in ("nova", "additifs", "aRisque") else "composantes"].add(numeroDuPlat)
                        texte = (f"{nomDuProfil} {libelleEnMinuscule(critere)} {ancienne} → {nouvelle} : "
                                 f"{nomDeClasse(reference[numeroDuPlat])} → {nomDeClasse(classe)}")
                        touches.setdefault(numeroDuPlat, []).append(texte)
                scenarios.append({"profil": nomDuProfil, "critere": critere, "ancienne": ancienne, "nouvelle": nouvelle,
                                  "plats": len(changes), "codes": [produits[n].get("code") for n in changes]})
    plats = []
    for numero in sorted(touches):
        plat = produits[numero]
        plats.append({"code": plat.get("code"), "nom": plat.get("nom"), "lettre": nomDeClasse(reference[numero]),
                      "decalages": touches[numero]})
    return {"decalage": decalage, "pasEntier": pasEntier, "scenarios": scenarios, "plats": plats,
            "part": len(plats) / len(produits), "platsComposantes": len(parFamille["composantes"]),
            "platsEntiers": len(parFamille["entiers"])}


# Les amplitudes des tirages au hasard : la part de plats qui changent, selon que les poids bougent peu ou plus
AMPLITUDES = [0.01, 0.02, 0.05]
AMPLITUDE_PRINCIPALE = 0.05
NOMS_DES_BASES = {"base": "125 plats", "etendue": "375 plats"}


def platsAuBord(produits, modele=None):
    """
    Les plats au bord de leur classe : la concordance face au profil qui décide de leur classe
    vaut λ pile. Le moindre changement de poids les fait basculer. Renvoie, pour chacun, son code,
    son nom, sa classe et les critères qu'il rate face à ce profil.
    """
    modele = modele or MODELE_SUPER
    bord = []
    for plat in produits:
        valeurs = valeursDuPlat(plat)
        detail = affecter(valeurs, modele)
        numero = detail["classe"] - 1                   # le profil franchi qui décide de la classe
        if numero >= 0 and abs(detail["concordances"][numero] - modele["lam"]) < TOLERANCE:
            satisfaits = criteresSatisfaits(valeurs, modele)[numero]
            bord.append({"code": plat.get("code"), "nom": plat.get("nom"), "lettre": nomDeClasse(detail["classe"]),
                         "rates": [critere for critere in modele["criteres"] if critere not in satisfaits]})
    return bord


def sensibilites(produits, modele=None, tirages=1000):
    """
    Les deux analyses de sensibilité d'une base : les poids à ± 0,05 (un par un et au hasard), la
    part de plats qui changent pour chaque amplitude d'AMPLITUDES, les profils, et les plats au bord
    de leur classe, qui expliquent qu'une petite variation des poids en change déjà quelques-uns.
    """
    courbe = []
    poids = None
    for amplitude in AMPLITUDES:
        resultat = sensibilitePoids(produits, modele, amplitude=amplitude, tirages=tirages)
        courbe.append({"amplitude": amplitude, "partMoyenne": resultat["partMoyenne"], "partMax": resultat["partMax"]})
        if amplitude == AMPLITUDE_PRINCIPALE:
            poids = resultat
    return {"poids": poids, "courbe": courbe, "profils": sensibiliteProfils(produits, modele),
            "auBord": platsAuBord(produits, modele)}


def nomDuProfilEtDeSaClasse(profil):
    """« b5 » devient « b5 (A′) » : le profil bk est le seuil de la classe Ck."""
    return f"{profil} ({nomDeClasse(PROFILS.index(profil) + 1)})"


def ecrireSensibilite(sensibilitesParBase, chemin):
    """
    Écrit resultats/supernutri_sensibilite.xlsx au style Verso, en quatre feuilles : les poids
    un par un, les tirages au hasard par amplitude, les décalages des profils, et les plats dont
    la classe change, avec les décalages qui la changent. Une colonne par base pour les comptes.
    """
    from openpyxl import Workbook
    from projet_design import mettreEnFormeFeuille

    bases = list(sensibilitesParBase)
    noms = [NOMS_DES_BASES[base] for base in bases]
    classeur = Workbook()

    feuille = classeur.active
    feuille.title = "poids un par un"
    entetes = ["Critère", "Variation du poids", "Nouveau poids"]
    for nom in noms:
        entetes += [f"Plats qui changent ({nom})", f"Part ({nom})"]
    feuille.append(entetes)
    premiere = sensibilitesParBase[bases[0]]["poids"]["unParUn"]
    for numero, ligne in enumerate(premiere):
        cellules = [CRITERES_LIBELLES[ligne["critere"]][0], ligne["delta"], ligne["poids"]]
        for base in bases:
            autre = sensibilitesParBase[base]["poids"]["unParUn"][numero]
            cellules += [autre["plats"], autre["part"]]
        feuille.append(cellules)
    formats = {4 + 2 * rang: "0.0%" for rang in range(len(bases))}
    mettreEnFormeFeuille(feuille, [30, 12, 12] + [16, 10] * len(bases), formats=formats)

    feuille = classeur.create_sheet("tirages")
    entetes = ["Amplitude"]
    for nom in noms:
        entetes += [f"Part moyenne ({nom})", f"Part la plus grande ({nom})"]
    feuille.append(entetes)
    for numero, amplitude in enumerate(AMPLITUDES):
        cellules = [amplitude]
        for base in bases:
            point = sensibilitesParBase[base]["courbe"][numero]
            cellules += [point["partMoyenne"], point["partMax"]]
        feuille.append(cellules)
    mettreEnFormeFeuille(feuille, [12] + [18, 18] * len(bases), formats={c: "0.0%" for c in range(2, 2 + 2 * len(bases))})

    feuille = classeur.create_sheet("profils")
    feuille.append(["Profil", "Critère", "Valeur", "Nouvelle valeur"] + [f"Plats qui changent ({nom})" for nom in noms])
    premiers = sensibilitesParBase[bases[0]]["profils"]["scenarios"]
    for numero, scenario in enumerate(premiers):
        cellules = [nomDuProfilEtDeSaClasse(scenario["profil"]), CRITERES_LIBELLES[scenario["critere"]][0],
                    scenario["ancienne"], scenario["nouvelle"]]
        for base in bases:
            cellules.append(sensibilitesParBase[base]["profils"]["scenarios"][numero]["plats"])
        feuille.append(cellules)
    mettreEnFormeFeuille(feuille, [12, 30, 10, 14] + [18] * len(bases))

    feuille = classeur.create_sheet("plats qui changent")
    feuille.append(["Base", "Code-barres", "Nom", "Classe", "Décalages qui changent sa classe"])
    for base, nom in zip(bases, noms):
        for plat in sensibilitesParBase[base]["profils"]["plats"]:
            feuille.append([nom, plat["code"], plat["nom"], plat["lettre"], " ; ".join(plat["decalages"])])
    mettreEnFormeFeuille(feuille, [12, 16, 40, 10, 90], colonnesClasses=(4,))

    chemin.parent.mkdir(parents=True, exist_ok=True)
    classeur.save(chemin)


def afficherSensibilite(base, sensibilite):
    """Affiche les chiffres clés des deux analyses de sensibilité d'une base."""
    poids, profils = sensibilite["poids"], sensibilite["profils"]
    plusSensible = max(poids["unParUn"], key=lambda ligne: ligne["plats"])
    print(f"Sensibilité, {NOMS_DES_BASES[base]} :")
    print(f"  poids un par un (± {AMPLITUDE_PRINCIPALE}) : jusqu'à {plusSensible['plats']} plats "
          f"({100 * plusSensible['part']:.1f} %), en changeant le poids de « {CRITERES_LIBELLES[plusSensible['critere']][0]} »")
    for point in sensibilite["courbe"]:
        print(f"  poids au hasard (± {point['amplitude']}) : {100 * point['partMoyenne']:.1f} % des plats changent "
              f"en moyenne, {100 * point['partMax']:.1f} % au plus")
    print(f"  profils : {len(profils['plats'])} plats changent au moins une fois ({100 * profils['part']:.1f} %), "
          f"dont {profils['platsComposantes']} par les composantes (± 5 %) et {profils['platsEntiers']} par les entiers (± 1)")
    print(f"  au bord de leur classe (concordance = λ pile) : {len(sensibilite['auBord'])} plats")


# --- Question 3.4 : comparaisons ---

def ecartsAuNutriscore(produits, modele=None):
    """
    Compare, plat par plat, le SuperNutri-score au Nutri-Score : les plats qui montent, ceux qui
    descendent, et pourquoi.
    - Un plat qui descend : les critères qu'il rate face au profil de la classe que lui donne le
      Nutri-Score (pour un plat B, le profil de B′).
    - Un plat qui monte : les critères qu'il rate face au profil de sa classe SuperNutri, qu'il
      franchit pourtant.
    Renvoie les comptes, le nombre de plats qui descendent en ratant chaque critère, ces
    descentes classe par classe du Nutri-Score, une ligne par plat (écart en classes, positif s'il
    monte) et les plus grands écarts. Pour les plats qui montent : les critères qu'ils ratent, et
    combien sont chargés, avec au moins 11 points négatifs au Nutri-Score (qui les additionne,
    quand MR-Sort, sans veto, ne retire que le poids des critères ratés).
    """
    modele = modele or MODELE_SUPER
    lignes = []
    raisonsDesDescentes = {critere: 0 for critere in modele["criteres"]}
    descentesParLabel = {}
    montees = {"raisons": {critere: 0 for critere in modele["criteres"]}, "chargees": 0}
    for plat in produits:
        valeurs = valeursDuPlat(plat)
        classe = affecter(valeurs, modele)["classe"]
        classeNutri = classeDuLabel(plat["label"])
        ecart = classe - classeNutri
        satisfaits = criteresSatisfaits(valeurs, modele)
        rates = []
        if ecart != 0:
            # La classe k est celle du profil k − 1 : pour une descente, celui du Nutri-Score ; pour une montée, le sien
            numero = classeNutri - 1 if ecart < 0 else classe - 1
            rates = [critere for critere in modele["criteres"] if critere not in satisfaits[numero]]
        if ecart < 0:
            parLabel = descentesParLabel.setdefault(plat["label"], {"plats": 0, "raisons": {}})
            parLabel["plats"] += 1
            for critere in rates:
                raisonsDesDescentes[critere] += 1
                parLabel["raisons"][critere] = parLabel["raisons"].get(critere, 0) + 1
        if ecart > 0:
            for critere in rates:
                montees["raisons"][critere] += 1
            complet = all(plat.get(composante) is not None for composante in COMPOSANTES_NUTRISCORE)
            if complet and scoreNutriscore(plat, categorie=plat.get("categorie") or "general")["N"] >= SEUIL_PROTEINES:
                montees["chargees"] += 1
        lignes.append({"code": plat.get("code"), "nom": plat.get("nom"), "label": plat["label"],
                       "lettre": nomDeClasse(classe), "ecart": ecart, "rates": rates})
    plusGrands = sorted(lignes, key=lambda ligne: (-abs(ligne["ecart"]), ligne["ecart"], str(ligne["nom"])))[:10]
    return {"montent": sum(1 for ligne in lignes if ligne["ecart"] > 0),
            "descendent": sum(1 for ligne in lignes if ligne["ecart"] < 0),
            "egaux": sum(1 for ligne in lignes if ligne["ecart"] == 0),
            "raisonsDesDescentes": raisonsDesDescentes, "descentesParLabel": descentesParLabel, "montees": montees,
            "plats": lignes,
            "plusGrandsEcarts": [ligne for ligne in plusGrands if ligne["ecart"] != 0]}


# --- Question 3.4 : la base d'un autre groupe ---

# Nos clés, dans l'ordre : la correspondance donne, pour chacune, le nom de la colonne de leur base
CLES_AUTRE_GROUPE = ["code", "nom", "en", "sa", "su", "so", "sodium", "pr", "fi", "fr", "label", "nova", "additifs",
                     "listeAdditifs", "bio", "leurClasse"]

# La base de l'autre groupe (Branchu, Becavin, Bundhoo, Castan : 300 céréales du petit-déjeuner, reçue le 20/11),
# et la correspondance de ses colonnes avec nos clés. Leur « so » est le sodium en mg ; notre « so » est le sel en g.
FICHIER_AUTRE_GROUPE = DOSSIER / "donnees" / "autre_groupe" / "Base_cereales_Branchu_Becavin_Bundhoo_Castan.xlsx"
CORRESPONDANCE_AUTRE_GROUPE = {"code": "code", "nom": "nom", "en": "en_kJ", "sa": "sa_g", "su": "su_g", "so": "sel_g",
                               "sodium": "so_mg", "pr": "pr_g", "fi": "fi_g", "fr": "fr_pct", "label": "nutriscore_label",
                               "nova": "nova", "leurClasse": "supernutriscore"}


def lignesDuFichier(fichier, feuille=None):
    """
    Les lignes d'un Excel (la feuille nommée, sinon la première) ou d'un CSV (séparé par des
    virgules ou des points-virgules), chacune en dictionnaire {en-tête : valeur}. Les lignes
    vides sont sautées.
    """
    fichier = Path(fichier)
    if fichier.suffix.lower() == ".csv":
        lignes = fichier.read_text(encoding="utf-8-sig").splitlines()
        separateur = ";" if lignes[0].count(";") > lignes[0].count(",") else ","
        return [dict(ligne) for ligne in csv.DictReader(lignes, delimiter=separateur)]
    from openpyxl import load_workbook

    classeur = load_workbook(fichier, read_only=True, data_only=True)
    lignes = list((classeur[feuille] if feuille else classeur.worksheets[0]).iter_rows(values_only=True))
    entetes = ["" if entete is None else str(entete).strip() for entete in lignes[0]]
    return [dict(zip(entetes, ligne)) for ligne in lignes[1:] if any(valeur is not None for valeur in ligne)]


def nombreDeLaCellule(valeur):
    """Un nombre lu dans une cellule : 1.5, « 1,5 » ou « 1,5 g » donnent 1.5 ; une cellule vide ou sans nombre donne None."""
    if valeur is None:
        return None
    if isinstance(valeur, (int, float)):
        return valeur
    trouve = re.search(r"-?\d+(?:[.,]\d+)?", str(valeur))
    return float(trouve.group(0).replace(",", ".")) if trouve else None


def codeDeLaCellule(valeur):
    """Un code-barres en texte : un nombre perd sa partie décimale, un texte garde ses zéros de tête."""
    if valeur is None:
        return ""
    if isinstance(valeur, float):
        valeur = int(valeur)
    return str(valeur).replace(" ", "").strip()


def lettreDeLaCellule(valeur):
    """La lettre d'une classe : « B », « b », « C′ » ou « A' » donnent B, C ou A ; sinon None."""
    texte = str(valeur or "").strip().upper()
    return texte[0] if texte and texte[0] in "ABCDE" else None


def bioDeLaCellule(valeur):
    """« oui » ou « non » pour un bio écrit oui/non, yes/no, vrai/faux ou 1/0 ; None si la cellule est vide."""
    texte = str(valeur).strip().lower() if valeur is not None else ""
    if texte in ("oui", "o", "yes", "y", "true", "vrai", "1", "bio"):
        return "oui"
    if texte in ("non", "n", "no", "false", "faux", "0"):
        return "non"
    return None


def ficheGardee(code):
    """
    Le code sous lequel le cache garde la fiche d'un produit, ou None. Le cache garde parfois une
    fiche sous une autre écriture du même code (« 0635646 » pour « 00635646 ») : on essaie le code
    tel quel, puis le code sans ses zéros de tête, complété de zéros jusqu'à 13 chiffres.
    """
    sansZeros = code.lstrip("0")
    for variante in [code] + [sansZeros.zfill(longueur) for longueur in range(len(sansZeros), 14)]:
        if variante and (DOSSIER_BRUT / "produits" / f"{variante}.json").exists():
            return variante
    return None


def ficheDuCode(code, reseau=None):
    """
    La fiche d'OFF d'un code-barres : celle du cache, sous l'une des écritures du code
    (ficheGardee), sinon une seule requête à OFF avec le code tel quel (ficheEnDirect). Renvoie
    (réponse, None) ou (None, message).
    """
    return ficheEnDirect(ficheGardee(code) or code, reseau)


def dateDeLaFiche(code):
    """La date où la fiche d'OFF d'un produit a été rangée dans le cache, ou aujourd'hui si elle n'y est pas."""
    gardee = ficheGardee(code)
    if gardee is None:
        return date.today().isoformat()
    return date.fromtimestamp((DOSSIER_BRUT / "produits" / f"{gardee}.json").stat().st_mtime).isoformat()


def telechargerFichesAutreGroupe(fichier=FICHIER_AUTRE_GROUPE, correspondance=None):
    """
    Range dans le cache d'Open Food Facts (donnees/brut/produits/) la fiche de chaque produit de
    la base de l'autre groupe : ensuite, leur base se complète hors ligne. Une fiche déjà gardée
    n'est pas redemandée, et ficheProduit respecte la cadence d'OFF. Renvoie (fiches lues, codes
    qu'OFF ne connaît pas).
    """
    correspondance = correspondance or CORRESPONDANCE_AUTRE_GROUPE
    lues, introuvables = 0, []
    for ligne in lignesDuFichier(fichier):
        code = codeDeLaCellule(ligne.get(correspondance["code"]))
        if not code or ficheGardee(code):
            continue
        reponse = ficheProduit(code, False)
        lues += 1
        if reponse.get("status") != 1:
            introuvables.append(code)
    return lues, introuvables


def importerBaseAutreGroupe(fichier, correspondance, completer=True, reseau=None):
    """
    Lit la base d'un autre groupe (Excel ou CSV) et la met à notre format.
    correspondance : {notre clé : le nom de leur colonne}, par exemple {"code": "EAN"}. Nos clés
    sont celles de CLES_AUTRE_GROUPE : les sept composantes, leur Nutri-Score (label), NOVA, les
    additifs, le bio, et leurClasse, la classe que leur SuperNutri-score donne à l'aliment. Une
    clé sans colonne reste vide.
    Si completer, NOVA, les additifs et le bio qui manquent viennent de la fiche d'OFF du
    code-barres : d'abord le cache, sinon une seule requête (ficheEnDirect ; reseau=None suit
    PROJET_HORS_LIGNE). Renvoie (plats, manques) : manques donne, pour chaque code dont la fiche
    n'a pu être lue, la raison.
    """
    plats, manques = [], {}
    for ligne in lignesDuFichier(fichier):
        plat = {}
        for cle in CLES_AUTRE_GROUPE:
            colonne = correspondance.get(cle)
            valeur = ligne.get(colonne) if colonne else None
            if cle == "code":
                plat[cle] = codeDeLaCellule(valeur)
            elif cle == "nom":
                plat[cle] = "" if valeur is None else str(valeur).strip()
            elif cle in ("label", "leurClasse"):
                plat[cle] = lettreDeLaCellule(valeur)
            elif cle == "bio":
                plat[cle] = bioDeLaCellule(valeur)
            elif cle == "listeAdditifs":
                plat[cle] = str(valeur).strip() if valeur else None
            elif cle == "nova":
                nombre = nombreDeLaCellule(valeur)
                plat[cle] = int(nombre) if nombre in (1, 2, 3, 4) else None
            elif cle == "additifs":
                nombre = nombreDeLaCellule(valeur)
                plat[cle] = None if nombre is None else int(nombre)
            else:
                plat[cle] = nombreDeLaCellule(valeur)
        plat["categorie"], plat["ficheLue"] = None, None
        manque = plat["nova"] is None or plat["additifs"] is None or plat["bio"] is None
        if completer and plat["code"] and manque:
            reponse, message = ficheDuCode(plat["code"], reseau)
            if reponse is None:
                manques[plat["code"]] = message
            else:
                fiche = reponse["product"]
                calcul = ((fiche.get("nutriscore") or {}).get("2023") or {}).get("data") or {}
                plat["categorie"] = categorieDepuisOff(calcul)
                plat["ficheLue"] = dateDeLaFiche(plat["code"])
                champs = champsDeLaFiche(fiche, plat["code"])
                if plat["nova"] is None:
                    plat["nova"] = champs["nova"]
                if plat["additifs"] is None:                    # la liste va avec le nombre qu'on reprend
                    plat["additifs"] = champs["additifs"]
                    plat["listeAdditifs"] = champs["listeAdditifs"] or None
                if plat["bio"] is None:
                    plat["bio"] = champs["bio"]
        plats.append(plat)
    return plats, manques


# Les deux produits suivis dans la comparaison, un par base : un muesli bio sans additif de leur base
# (C au Nutri-Score, B′ chez eux), et notre Poêlée Fermière (B au Nutri-Score, C′ chez nous)
EXEMPLES_AUTRE_GROUPE = ("3421557922435", "3257982125116")

# La base de l'autre groupe, complétée par OFF de ce que notre SuperNutri-score demande en plus
FICHIER_BASE_COMPLETEE = DOSSIER / "donnees" / "autre_groupe" / "base_cereales_completee.xlsx"
AJOUTS_DE_LA_BASE_COMPLETEE = ["NOVA (OFF s'il manquait)", "Additifs (OFF)", "Liste des additifs (OFF)", "Additifs à risque (OFF)",
                               "Bio (OFF)", "Type au Nutri-Score (OFF)", "Fiche lue le"]


def ecrireBaseCompletee(plats, fichierSource, chemin):
    """
    Écrit la base de l'autre groupe complétée par Open Food Facts : leurs colonnes, telles
    quelles, puis ce que notre SuperNutri-score demande en plus (AJOUTS_DE_LA_BASE_COMPLETEE).
    Une feuille « lisez-moi » dit d'où vient chaque chose. plats : les produits de
    importerBaseAutreGroupe, dans l'ordre des lignes de fichierSource.
    """
    from openpyxl import Workbook
    from projet_design import mettreEnFormeFeuille, mettreEnFormeNotice

    lignes = lignesDuFichier(fichierSource)
    entetes = list(lignes[0]) if lignes else []
    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "produits"
    feuille.append(entetes + AJOUTS_DE_LA_BASE_COMPLETEE)
    for ligne, plat in zip(lignes, plats):
        aRisque = None if plat.get("additifs") is None else additifsARisque(plat.get("listeAdditifs"))
        feuille.append([ligne[entete] for entete in entetes]
                       + [plat.get("nova"), plat.get("additifs"), plat.get("listeAdditifs"), aRisque, plat.get("bio"),
                          plat.get("categorie"), plat.get("ficheLue")])
    mettreEnFormeFeuille(feuille, [14] * len(entetes) + [16, 12, 30, 16, 10, 18, 14])

    notice = classeur.create_sheet("lisez-moi")
    for element, valeur in [
        ("Base d'origine", f"{Path(fichierSource).name} : leurs colonnes, telles qu'ils nous les ont envoyées."),
        ("Ajouts", "Lus sur Open Food Facts (API produit), fiche par fiche, d'après le code-barres ; les fiches sont "
                   "gardées dans donnees/brut/produits/. Leur groupe NOVA est gardé ; celui d'OFF ne sert que s'il manquait."),
        ("Additifs à risque", "Nitrites et nitrates (E249 à E252), phosphates (E338 à E341, E343, E450 à E452), "
                              "carraghénanes (E407), comptés dans la liste des additifs."),
        ("Bio", "« oui » si la fiche porte un label bio (en:organic, en:eu-organic, AB)."),
        ("Type au Nutri-Score", "Celui que donnent les marqueurs du calcul de 2023 d'OFF : « general » pour le cas général."),
        ("Produits introuvables sur OFF", str(sum(1 for plat in plats if plat.get("ficheLue") is None))),
    ]:
        notice.append([element, valeur])
    mettreEnFormeNotice(notice)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    classeur.save(chemin)


# Leurs critères dans nos clés : leur « tr » est le groupe NOVA ; leur « so » est le sodium en mg (notre « so »
# est le sel en g, d'où la clé « sodium »)
CRITERES_DE_L_AUTRE_GROUPE = {"su": "su", "fi": "fi", "tr": "nova", "sa": "sa", "so": "sodium"}


def modeleDeLAutreGroupe(fichier=FICHIER_AUTRE_GROUPE):
    """
    Le SuperNutri-score de l'autre groupe, tel que leur feuille « notre_modele » le décrit :
    critères (dans nos clés), sens, poids, profils de b2 à b5, et λ. Leurs poids sont des parts
    de 15 points arrondies au dix-millième : on les ramène à une somme de 1. Le modèle se range
    dans notre moteur MR-Sort, comme le nôtre.
    """
    criteres, poids, sens, profils, lam = [], {}, {}, [{}, {}, {}, {}], None
    for ligne in lignesDuFichier(fichier, "notre_modele"):
        if ligne["critere"] == "lambda":
            lam = nombreDeLaCellule(ligne["poids"])
            continue
        critere = CRITERES_DE_L_AUTRE_GROUPE[ligne["critere"]]
        criteres.append(critere)
        poids[critere] = nombreDeLaCellule(ligne["poids"])
        sens[critere] = ligne["sens"]
        for numero, colonne in enumerate(("b2", "b3", "b4", "b5")):
            profils[numero][critere] = nombreDeLaCellule(ligne[colonne])
    total = sum(poids.values())
    return {"criteres": criteres, "poids": {critere: valeur / total for critere, valeur in poids.items()},
            "profils": profils, "lam": lam, "sens": sens}


def valeursPourUnModele(plat, modele):
    """Les valeurs d'un produit pour un modèle quelconque : celles du produit, et une valeur absente ne vote pas (la pire possible)."""
    valeurs = {}
    for critere in modele["criteres"]:
        valeur = plat.get(critere)
        if valeur is None:
            valeur = math.inf if modele["sens"][critere] == "min" else -math.inf
        valeurs[critere] = valeur
    return valeurs


def classerAvecUnModele(plat, modele):
    """
    Range un produit avec un modèle MR-Sort quelconque (celui de l'autre groupe), avec
    valeursPourUnModele. Renvoie le détail d'affecter, plus la lettre de la classe.
    """
    detail = affecter(valeursPourUnModele(plat, modele), modele)
    detail["lettre"] = nomDeClasse(detail["classe"])
    return detail


def repartitionDesClasses(classes):
    """Le nombre de produits de chaque classe, de A′ à E′."""
    repartition = {lettre: 0 for lettre in reversed(CLASSES)}
    for classe in classes:
        repartition[nomDeClasse(classe)] += 1
    return repartition


def comparerDeuxModeles(plats, leurModele, notreModele=None):
    """
    Les deux SuperNutri-scores sur une même base (§3.4) : chacun face au Nutri-Score (même classe,
    à une classe près, matrice), puis le nôtre face au leur. Pour chaque modèle, la part des
    produits qui ratent chaque critère au seuil de B′ : ce qui le bloque sur cette base. Avec leur
    colonne de classes (leurClasse), compte aussi les produits où leur modèle redonne leur classe.
    """
    notreModele = notreModele or MODELE_SUPER
    nos, leurs, nutriscore, reproduits = [], [], [], 0
    bloquants = {"notre": {critere: 0 for critere in notreModele["criteres"]},
                 "leur": {critere: 0 for critere in leurModele["criteres"]}}
    for plat in plats:
        for nom, modele, valeurs in (("notre", notreModele, valeursDuPlat(plat)),
                                     ("leur", leurModele, valeursPourUnModele(plat, modele=leurModele))):
            classe = affecter(valeurs, modele)["classe"]
            (nos if nom == "notre" else leurs).append(classe)
            satisfaits = criteresSatisfaits(valeurs, modele)[2]            # le profil b4, le seuil de B′
            for critere in modele["criteres"]:
                if critere not in satisfaits:
                    bloquants[nom][critere] += 1
        nutriscore.append(classeDuLabel(plat["label"]))
        if plat.get("leurClasse") and nomDeClasse(leurs[-1])[0] == plat["leurClasse"]:
            reproduits += 1
    total = len(plats)
    comparaisons = {"notreFaceAuNutriscore": comparerAuNutriscore(nutriscore, nos),
                    "leurFaceAuNutriscore": comparerAuNutriscore(nutriscore, leurs),
                    "notreFaceALeur": comparerAuNutriscore(leurs, nos)}
    for comparaison in comparaisons.values():
        comparaison["sens"] = sensDesEcarts(comparaison["matrice"])
    return {"total": total, "notre": repartitionDesClasses(nos), "leur": repartitionDesClasses(leurs),
            **comparaisons, "leurReproduit": reproduits,
            "bloquants": {nom: {critere: nombre / total for critere, nombre in compte.items()}
                          for nom, compte in bloquants.items()}}


def avecLeSodium(plat):
    """
    Le plat, avec son sodium en mg, tiré du sel s'il ne le donne pas : le sel vaut 2,5 fois le
    sodium (règlement UE 1169/2011), donc 1 g de sel, c'est 400 mg de sodium. Nos plats donnent
    le sel ; le modèle de l'autre groupe lit le sodium.
    """
    if plat.get("sodium") is None and plat.get("so") is not None:
        return dict(plat, sodium=plat["so"] * 400)
    return plat


def rateAuDessus(valeurs, modele):
    """
    Les critères qu'un produit rate face au profil de la classe juste au-dessus de la sienne, et
    leur poids : ce qui l'empêche de monter (il monterait si ce poids ne dépassait pas 1 − λ).
    None pour un produit en A′.
    """
    classe = affecter(valeurs, modele)["classe"]
    if classe == len(modele["profils"]):
        return None
    satisfaits = criteresSatisfaits(valeurs, modele)[classe]
    rates = [critere for critere in modele["criteres"] if critere not in satisfaits]
    return {"rates": rates, "poids": sum(modele["poids"][critere] for critere in rates)}


def exempleDesDeuxModeles(plat, base, leurModele):
    """
    Un produit vu par les deux modèles : sa classe au Nutri-Score, dans le nôtre et dans le leur ;
    pour chacun, ce qui l'empêche de monter d'une classe (rateAuDessus), et profil par profil, les
    critères qui votent contre lui (explicationDuPlat).
    """
    nosValeurs, leursValeurs = valeursDuPlat(plat), valeursPourUnModele(plat, leurModele)
    return {"code": plat["code"], "nom": plat["nom"], "base": base, "label": plat.get("label"),
            "notre": nomDeClasse(affecter(nosValeurs, MODELE_SUPER)["classe"]),
            "leur": nomDeClasse(affecter(leursValeurs, leurModele)["classe"]),
            "notreAuDessus": rateAuDessus(nosValeurs, MODELE_SUPER), "leurAuDessus": rateAuDessus(leursValeurs, leurModele),
            "proteinesComptees": proteinesRetenues(plat, plat.get("categorie") or "general") is not None,
            "notreExplication": explicationDuPlat(nosValeurs, MODELE_SUPER),
            "leurExplication": explicationDuPlat(leursValeurs, leurModele)}


def analyseAutreGroupe(leurs, manques, leurModele, nos, exemples=()):
    """
    La comparaison avec l'autre groupe (§3.4), sur les deux bases : leurs produits et nos plats,
    rangés chacun par les deux modèles et comparés au Nutri-Score (comparerDeuxModeles). Donne
    aussi : combien de leurs classes leur modèle recodé redonne, les fiches d'OFF manquantes, le
    recoupement des deux bases par code-barres (§3.1 : moins de 25 %), le type au Nutri-Score de
    leurs produits, et, pour chaque code d'exemples, le produit vu par les deux modèles.
    """
    leurs = [avecLeSodium(plat) for plat in leurs]
    nos = [avecLeSodium(plat) for plat in nos]
    types = {}
    for plat in leurs:
        typeDuProduit = plat.get("categorie") or "inconnu"
        types[typeDuProduit] = types.get(typeDuProduit, 0) + 1
    comparaisonLeurs = comparerDeuxModeles(leurs, leurModele)
    communs, part = intersectionAvecAutreBase(nos, leurs)
    lignesExemples = []
    for code in exemples:
        for base, plats in (("leurs", leurs), ("nos", nos)):
            lignesExemples += [exempleDesDeuxModeles(plat, base, leurModele) for plat in plats if plat["code"] == code]
    return {"total": len(leurs), "reproduits": comparaisonLeurs["leurReproduit"], "manques": sorted(manques),
            "recoupement": [communs, part], "types": types,
            "leurs": comparaisonLeurs, "nos": comparerDeuxModeles(nos, leurModele), "exemples": lignesExemples}


def ecrireAutreGroupe(leurs, nos, analyse, leurModele, chemin):
    """
    Écrit resultats/supernutri_autre_groupe.xlsx au style Verso, en trois feuilles :
    - leurs produits, rangés par les deux modèles, avec ce que notre modèle leur reproche ;
    - nos plats, rangés par leur modèle ;
    - la comparaison : chaque modèle face au Nutri-Score sur chaque base, et l'accord des deux.
    """
    from openpyxl import Workbook
    from projet_design import mettreEnFormeFeuille

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "leurs produits"
    feuille.append(["Code-barres", "Nom"] + [CRITERES_LIBELLES[critere][0] for critere in CRITERES_SUPER + ["sodium"]]
                   + ["Type au Nutri-Score", "Nutri-Score", "Leur SuperNutri-score", "Notre SuperNutri-score",
                      "Écart (classes)", "Notre explication"])
    for plat in (avecLeSodium(plat) for plat in leurs):
        valeurs = valeursDuPlat(plat)
        cellules = [None if math.isinf(valeurs[critere]) else valeurs[critere] for critere in CRITERES_SUPER]
        notre = affecter(valeurs, MODELE_SUPER)["classe"]
        leur = affecter(valeursPourUnModele(plat, leurModele), leurModele)["classe"]
        feuille.append([plat["code"], plat["nom"]] + cellules + [plat.get("sodium"), plat.get("categorie"), plat.get("label"),
                                                                  nomDeClasse(leur), nomDeClasse(notre), notre - leur,
                                                                  explicationDuPlat(valeurs, MODELE_SUPER)])
    colonne = 4 + len(CRITERES_SUPER)                       # la colonne du Nutri-Score
    mettreEnFormeFeuille(feuille, [16, 40] + [12] * (len(CRITERES_SUPER) + 1) + [14, 12, 16, 16, 12, 90],
                         colonnesClasses=(colonne + 1, colonne + 2, colonne + 3))

    feuille = classeur.create_sheet("nos plats")
    feuille.append(["Code-barres", "Nom", "Nutri-Score", "Notre SuperNutri-score", "Leur SuperNutri-score",
                    "Écart (classes)", "Leur explication"])
    for plat in (avecLeSodium(plat) for plat in nos):
        leursValeurs = valeursPourUnModele(plat, leurModele)
        notre = affecter(valeursDuPlat(plat), MODELE_SUPER)["classe"]
        leur = affecter(leursValeurs, leurModele)["classe"]
        feuille.append([plat["code"], plat["nom"], plat.get("label"), nomDeClasse(notre), nomDeClasse(leur), notre - leur,
                        explicationDuPlat(leursValeurs, leurModele)])
    mettreEnFormeFeuille(feuille, [16, 40, 12, 16, 16, 12, 70], colonnesClasses=(3, 4, 5))

    feuille = classeur.create_sheet("comparaison")
    feuille.append(["Base", "Modèle", "Même classe que le Nutri-Score", "À une classe près", "A′", "B′", "C′", "D′", "E′"])
    for base, nom in (("leurs", "leurs produits"), ("nos", "nos plats")):
        for modele, libelle in (("notre", "le nôtre"), ("leur", "le leur")):
            face = analyse[base][f"{modele}FaceAuNutriscore"]
            feuille.append([nom, libelle, face["exactitude"], face["aUneClassePres"]]
                           + list(analyse[base][modele].values()))
    feuille.append([])
    feuille.append(["Base", "Les deux modèles donnent la même classe", "À une classe près"])
    for base, nom in (("leurs", "leurs produits"), ("nos", "nos plats")):
        accord = analyse[base]["notreFaceALeur"]
        feuille.append([nom, accord["exactitude"], accord["aUneClassePres"]])
    mettreEnFormeFeuille(feuille, [18, 12, 18, 14, 8, 8, 8, 8, 8], formats={2: "0.0%", 3: "0.0%", 4: "0.0%"})
    chemin.parent.mkdir(parents=True, exist_ok=True)
    classeur.save(chemin)


def afficherAutreGroupe(analyse):
    """Affiche la comparaison avec l'autre groupe : la reproduction de leurs classes, puis les deux modèles sur les deux bases."""
    print(f"\nBase de l'autre groupe : {analyse['total']} produits, {len(analyse['manques'])} fiches d'OFF introuvables, "
          f"types au Nutri-Score {analyse['types']} ; leur modèle recodé redonne {analyse['reproduits']} de leurs classes ; "
          f"recoupement avec nos plats : {analyse['recoupement'][0]} ({analyse['recoupement'][1]:.1f} %)")
    for base, nom in (("leurs", "leurs produits"), ("nos", "nos plats")):
        comparaison = analyse[base]
        for modele in ("notre", "leur"):
            face = comparaison[f"{modele}FaceAuNutriscore"]
            print(f"  {nom}, {modele} modèle : {', '.join(f'{l} {n}' for l, n in comparaison[modele].items())} ; "
                  f"même classe que le Nutri-Score {100 * face['exactitude']:.1f} %, à une classe près "
                  f"{100 * face['aUneClassePres']:.1f} % ; plus sévère {100 * face['sens']['plusSevere']:.1f} %, "
                  f"plus permissif {100 * face['sens']['plusPermissif']:.1f} %, écart moyen {face['sens']['ecartMoyen']:+.2f}")
        accord = comparaison["notreFaceALeur"]
        print(f"  {nom}, les deux modèles d'accord : {100 * accord['exactitude']:.1f} %, à une classe près "
              f"{100 * accord['aUneClassePres']:.1f} % ; le nôtre plus sévère que le leur {100 * accord['sens']['plusSevere']:.1f} %, "
              f"plus permissif {100 * accord['sens']['plusPermissif']:.1f} %, écart moyen {accord['sens']['ecartMoyen']:+.2f}")


def main():
    """
    Range la base de 125 plats, puis la base étendue si elle existe, et fait leurs deux analyses de
    sensibilité ; écrit les Excel de resultats/ et la clé « supernutri » du JSON. Avec
    --telecharger-autre-groupe, range seulement dans le cache les fiches d'OFF de la base de
    l'autre groupe (une seule fois, quelques minutes).
    """
    import argparse

    parseur = argparse.ArgumentParser(description="Le SuperNutri-score : nos bases, ses sensibilités, l'autre groupe.")
    parseur.add_argument("--telecharger-autre-groupe", action="store_true",
                         help="ranger dans le cache les fiches d'OFF des produits de l'autre groupe, puis s'arrêter")
    if parseur.parse_args().telecharger_autre_groupe:
        lues, introuvables = telechargerFichesAutreGroupe()
        print(f"{lues} fiches lues sur Open Food Facts ; {len(introuvables)} produits inconnus d'OFF : {introuvables}")
        return
    resume = {"modele": MODELE_SUPER, "sources": SOURCES_DES_SEUILS, "sensDesClasses": SENS_DES_CLASSES,
              "amplitudes": AMPLITUDES, "sensibilite": {}}
    for nom, fichier in (("base", FICHIER_BASE), ("etendue", FICHIER_BASE_ETENDUE)):
        if fichier.exists():
            resultat = superNutriScore(fichier, sortie=DOSSIER / "resultats" / f"supernutri_{nom}.xlsx")
            ecarts = resultat["ecarts"]
            for ligne, ecart in zip(resultat["plats"], ecarts["plats"]):
                ligne.update(ecart=ecart["ecart"], rates=ecart["rates"])
            resume[nom] = {"repartition": resultat["repartition"], "comparaison": resultat["comparaison"],
                           "plats": resultat["plats"], "secsEnAPrime": resultat["secsEnAPrime"],
                           "ecarts": {cle: ecarts[cle] for cle in ("montent", "descendent", "egaux", "raisonsDesDescentes",
                                                                   "descentesParLabel", "montees", "plusGrandsEcarts")}}
            resume[nom]["transformation"] = transformationDesPlats(lireBase(fichier))
            resume["sensibilite"][nom] = sensibilites(lireBase(fichier))
            afficherSensibilite(nom, resume["sensibilite"][nom])
    ecrireSensibilite(resume["sensibilite"], DOSSIER / "resultats" / "supernutri_sensibilite.xlsx")
    # La base de l'autre groupe : leurs produits complétés par OFF (depuis le cache), puis les deux modèles sur les deux bases
    if FICHIER_AUTRE_GROUPE.exists():
        leurs, manques = importerBaseAutreGroupe(FICHIER_AUTRE_GROUPE, CORRESPONDANCE_AUTRE_GROUPE)
        ecrireBaseCompletee(leurs, FICHIER_AUTRE_GROUPE, FICHIER_BASE_COMPLETEE)
        leurModele = modeleDeLAutreGroupe()
        nos = lireBase(FICHIER_BASE_ETENDUE if FICHIER_BASE_ETENDUE.exists() else FICHIER_BASE)
        analyse = analyseAutreGroupe(leurs, manques, leurModele, nos, exemples=EXEMPLES_AUTRE_GROUPE)
        ecrireAutreGroupe(leurs, nos, analyse, leurModele, DOSSIER / "resultats" / "supernutri_autre_groupe.xlsx")
        resume["autreGroupe"] = dict(analyse, modele=leurModele)
        afficherAutreGroupe(analyse)
    else:
        print(f"Base de l'autre groupe : pas encore là ({FICHIER_AUTRE_GROUPE.relative_to(DOSSIER)}).")
    enregistrerResultats("supernutri", resume)


if __name__ == "__main__":
    main()
