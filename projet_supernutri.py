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

import math
import re

from projet_base import DOSSIER, FICHIER_BASE, FICHIER_BASE_ETENDUE, enregistrerResultats, lireBase
from projet_mrsort import CLASSES, affecter, classeDuLabel, comparerAuNutriscore, nomDeClasse
from projet_nutriscore import POINTS_MAX


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
    "additifs": ("Nombre d'additifs", "additifs", "min"),
    "aRisque": ("Additifs à risque", "additifs", "min"),
    "bio": ("Bio", "1 si bio, 0 sinon", "max"),
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


def valeursDuPlat(plat):
    """
    Les onze valeurs d'un plat pour le SuperNutri-score. Le bio vaut 1 (label bio) ou 0 ; les
    additifs à risque se comptent dans la liste des additifs. Une valeur absente prend la pire
    valeur possible (+∞ pour un critère à minimiser, −∞ pour un critère à maximiser) : elle ne
    vote jamais pour le plat.
    """
    valeurs = {}
    for critere in ["en", "sa", "su", "so", "pr", "fi", "fr", "nova", "additifs"]:
        valeurs[critere] = plat.get(critere)
    # La liste des additifs n'est connue que si leur nombre l'est : une liste vide veut alors dire « aucun »
    valeurs["aRisque"] = None if plat.get("additifs") is None else additifsARisque(plat.get("listeAdditifs"))
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


def classerPlat(plat, modele=None):
    """
    Range un plat avec le SuperNutri-score (MODELE_SUPER par défaut). Renvoie le détail
    d'affecter (classe, concordances, profils franchis), plus la lettre de la classe.
    """
    detail = affecter(valeursDuPlat(plat), modele or MODELE_SUPER)
    detail["lettre"] = nomDeClasse(detail["classe"])
    return detail


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
    resultat = {"modele": modele, "plats": lignes, "repartition": repartition, "comparaison": comparaison}
    if sortie:
        ecrireSuperNutri(plats, resultat, sortie)
    if afficher:
        afficherSuperNutri(resultat)
    return resultat


def ecrireSuperNutri(plats, resultat, chemin):
    """
    Écrit un Excel au style Verso : une ligne par plat, avec ses onze valeurs, son Nutri-Score
    et sa classe au SuperNutri-score. Une valeur absente reste une case vide.
    """
    from openpyxl import Workbook
    from projet_design import mettreEnFormeFeuille

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "supernutri-score"
    feuille.append(["Code-barres", "Nom"] + [CRITERES_LIBELLES[critere][0] for critere in CRITERES_SUPER]
                   + ["Nutri-Score", "SuperNutri-score"])
    for plat, ligne in zip(plats, resultat["plats"]):
        valeurs = valeursDuPlat(plat)
        cellules = [None if math.isinf(valeurs[critere]) else valeurs[critere] for critere in CRITERES_SUPER]
        feuille.append([plat["code"], plat["nom"]] + cellules + [plat["label"], ligne["lettre"]])
    colonneNutriscore = 3 + len(CRITERES_SUPER)
    mettreEnFormeFeuille(feuille, [16, 40] + [12] * len(CRITERES_SUPER) + [12, 16],
                         colonnesClasses=(colonneNutriscore, colonneNutriscore + 1))
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


# --- Question 3.4 : analyses de sensibilité ---

def sensibilitePoids(produits, modele, amplitude=0.05, tirages=1000, graine=2026):
    """Fait varier légèrement les poids (somme toujours égale à 1) et mesure la part des plats qui changent de classe."""
    raise NotImplementedError("phase 3")


def sensibiliteProfils(produits, modele, decalage=0.05):
    """Déplace les valeurs des profils (en gardant leur ordre) et liste les plats dont l'affectation change."""
    raise NotImplementedError("phase 3")


# --- Question 3.4 : comparaisons ---

def ecartsAuNutriscore(produits, modele):
    """Compare le SuperNutri-score au Nutri-Score : plats qui montent ou descendent, et pourquoi."""
    raise NotImplementedError("phase 3")


def importerBaseAutreGroupe(fichier, correspondance):
    """
    Lit la base d'un autre groupe, en renommant ses colonnes selon la correspondance donnée.
    Le groupe NOVA et les additifs sont récupérés sur OFF par code-barres s'ils manquent.
    """
    raise NotImplementedError("phase 3")


def main():
    """Range la base de 125 plats, puis la base étendue si elle existe ; écrit les Excel et la clé « supernutri » du JSON."""
    resume = {"modele": MODELE_SUPER, "sources": SOURCES_DES_SEUILS, "sensDesClasses": SENS_DES_CLASSES}
    for nom, fichier in (("base", FICHIER_BASE), ("etendue", FICHIER_BASE_ETENDUE)):
        if fichier.exists():
            resultat = superNutriScore(fichier, sortie=DOSSIER / "resultats" / f"supernutri_{nom}.xlsx")
            resume[nom] = {"repartition": resultat["repartition"], "comparaison": resultat["comparaison"],
                           "plats": resultat["plats"]}
    enregistrerResultats("supernutri", resume)


if __name__ == "__main__":
    main()
