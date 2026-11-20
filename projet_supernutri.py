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
import random
import re

from projet_base import DOSSIER, FICHIER_BASE, FICHIER_BASE_ETENDUE, enregistrerResultats, lireBase
from projet_mrsort import (CLASSES, PROFILS, TOLERANCE, affecter, classeDuLabel, comparerAuNutriscore,
                           concordancePartielle, nomDeClasse)
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
    resultat = {"modele": modele, "plats": lignes, "repartition": repartition, "comparaison": comparaison,
                "ecarts": ecartsAuNutriscore(plats, modele)}
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
                   + ["Nutri-Score", "SuperNutri-score", "Écart au Nutri-Score", "Critères ratés"])
    for plat, ligne, ecart in zip(plats, resultat["plats"], resultat["ecarts"]["plats"]):
        valeurs = valeursDuPlat(plat)
        cellules = [None if math.isinf(valeurs[critere]) else valeurs[critere] for critere in CRITERES_SUPER]
        rates = ", ".join(CRITERES_LIBELLES[critere][0] for critere in ecart["rates"])
        feuille.append([plat["code"], plat["nom"]] + cellules + [plat["label"], ligne["lettre"], ecart["ecart"], rates])
    colonneNutriscore = 3 + len(CRITERES_SUPER)
    mettreEnFormeFeuille(feuille, [16, 40] + [12] * len(CRITERES_SUPER) + [12, 16, 12, 60],
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
                        texte = (f"{nomDuProfil} {CRITERES_LIBELLES[critere][0].lower()} {ancienne} → {nouvelle} : "
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
    Renvoie les comptes, le nombre de plats qui descendent en ratant chaque critère, une ligne
    par plat (écart en classes, positif s'il monte) et les plus grands écarts.
    """
    modele = modele or MODELE_SUPER
    lignes = []
    raisonsDesDescentes = {critere: 0 for critere in modele["criteres"]}
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
            for critere in rates:
                raisonsDesDescentes[critere] += 1
        lignes.append({"code": plat.get("code"), "nom": plat.get("nom"), "label": plat["label"],
                       "lettre": nomDeClasse(classe), "ecart": ecart, "rates": rates})
    plusGrands = sorted(lignes, key=lambda ligne: (-abs(ligne["ecart"]), ligne["ecart"], str(ligne["nom"])))[:10]
    return {"montent": sum(1 for ligne in lignes if ligne["ecart"] > 0),
            "descendent": sum(1 for ligne in lignes if ligne["ecart"] < 0),
            "egaux": sum(1 for ligne in lignes if ligne["ecart"] == 0),
            "raisonsDesDescentes": raisonsDesDescentes, "plats": lignes,
            "plusGrandsEcarts": [ligne for ligne in plusGrands if ligne["ecart"] != 0]}


def importerBaseAutreGroupe(fichier, correspondance):
    """
    Lit la base d'un autre groupe, en renommant ses colonnes selon la correspondance donnée.
    Le groupe NOVA et les additifs sont récupérés sur OFF par code-barres s'ils manquent.
    """
    raise NotImplementedError("phase 3")


def main():
    """
    Range la base de 125 plats, puis la base étendue si elle existe, et fait leurs deux analyses de
    sensibilité ; écrit les Excel de resultats/ et la clé « supernutri » du JSON.
    """
    resume = {"modele": MODELE_SUPER, "sources": SOURCES_DES_SEUILS, "sensDesClasses": SENS_DES_CLASSES,
              "amplitudes": AMPLITUDES, "sensibilite": {}}
    for nom, fichier in (("base", FICHIER_BASE), ("etendue", FICHIER_BASE_ETENDUE)):
        if fichier.exists():
            resultat = superNutriScore(fichier, sortie=DOSSIER / "resultats" / f"supernutri_{nom}.xlsx")
            ecarts = resultat["ecarts"]
            for ligne, ecart in zip(resultat["plats"], ecarts["plats"]):
                ligne.update(ecart=ecart["ecart"], rates=ecart["rates"])
            resume[nom] = {"repartition": resultat["repartition"], "comparaison": resultat["comparaison"],
                           "plats": resultat["plats"],
                           "ecarts": {cle: ecarts[cle] for cle in ("montent", "descendent", "egaux",
                                                                   "raisonsDesDescentes", "plusGrandsEcarts")}}
            resume["sensibilite"][nom] = sensibilites(lireBase(fichier))
            afficherSensibilite(nom, resume["sensibilite"][nom])
    ecrireSensibilite(resume["sensibilite"], DOSSIER / "resultats" / "supernutri_sensibilite.xlsx")
    enregistrerResultats("supernutri", resume)


if __name__ == "__main__":
    main()
