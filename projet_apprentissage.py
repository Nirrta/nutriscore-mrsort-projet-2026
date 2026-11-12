"""
projet_apprentissage.py : l'apprentissage des paramètres de MR-Sort (question 3.3).

Le sujet demande deux apprentissages (§3.3 et annexes B et C) :
1. fixer les profils, en le justifiant, et apprendre les poids ;
2. fixer les poids, en le justifiant, et apprendre les profils.
On y ajoute l'apprentissage de tous les paramètres à la fois, qui répond à la question de
l'existence d'un modèle MR-Sort reproduisant exactement le Nutri-Score.

Chaque apprentissage est un programme linéaire en nombres entiers, résolu par HiGHS
(scipy.optimize.milp). Il cherche les paramètres qui rangent bien le plus de plats
possible. Les inégalités strictes utilisent une marge EPSILON = 0,001, comme le propose
l'annexe B (« w2 + w3 ≤ 0,6 − ε »).

Les paramètres fixés :
- profils fixés : sur chaque critère, le profil b_h est le milieu des médianes des deux
  classes qu'il sépare, puis l'ordre des profils est imposé (profilsParMedianes) ;
- poids fixés : chaque poids est proportionnel aux points maximaux de la composante dans
  le Nutri-Score, soit (10, 10, 15, 20, 7, 5, 5) / 72 pour les sept critères et
  (10, 20, 5) / 35 pour les trois critères (poidsDesPointsMax).

Plusieurs jeux de poids rangent souvent aussi bien les plats : intervallesDesPoids donne,
pour chaque critère, le plus petit et le plus grand poids possibles, et apprendrePoids peut
départager ces solutions par la plus grande marge (departage="marge", margeDuModele).

État : tout est écrit. profilsParMedianes et apprendrePoids (profils fixés, poids appris),
intervallesDesPoids et margeDuModele (les poids possibles, le départage), poidsDesPointsMax
et apprendreProfils (poids fixés, profils appris), apprendreParAlternance et
apprendreModeleComplet (tout est appris : par recherche locale, ou par un seul programme).
"""

import time
from statistics import median

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from projet_mrsort import EPSILON, affecter, concordancePartielle, sensDuCritere


# --- Question 3.3 : paramètres fixés, et leur justification ---

def profilsParMedianes(produits, classes, criteres, sens=None):
    """
    Profils fixés, à partir des données : le profil qui sépare deux classes voisines est,
    sur chaque critère, le milieu des médianes de ces deux classes. C'est le « plat
    fictif » typique de la frontière entre les deux classes.

    Les profils doivent ensuite être ordonnés : un profil plus haut doit être au moins aussi
    bon que le précédent sur chaque critère. Si les médianes ne le sont pas, on reprend la
    valeur du profil précédent.

    produits : les plats ; classes : le numéro de classe de chaque plat (0 pour C1, E′) ;
    criteres : les critères du modèle ; sens : facultatif, comme dans un modèle.
    Renvoie la liste des profils, du moins bon (b2) au meilleur (b5).
    """
    modele = {"sens": sens or {}}
    nombreDeClasses = max(classes) + 1
    profils = []
    for classeDuHaut in range(1, nombreDeClasses):
        profil = {}
        for critere in criteres:
            valeursDuBas = [p[critere] for p, k in zip(produits, classes) if k == classeDuHaut - 1]
            valeursDuHaut = [p[critere] for p, k in zip(produits, classes) if k == classeDuHaut]
            profil[critere] = (median(valeursDuBas) + median(valeursDuHaut)) / 2
            if profils:
                precedent = profils[-1][critere]
                if sensDuCritere(critere, modele) == "max":
                    profil[critere] = max(profil[critere], precedent)
                else:
                    profil[critere] = min(profil[critere], precedent)
        profils.append(profil)
    return profils


def poidsDesPointsMax(criteres):
    """
    Poids fixés, pour apprendre les profils : chaque poids est proportionnel aux points
    maximaux de sa composante dans le Nutri-Score, soit (10, 10, 15, 20, 7, 5, 5) / 72 pour les
    sept critères. Ce sont les poids implicites du Nutri-Score : les quatre critères négatifs
    pèsent 55/72, plus que λ, et les trois positifs (17/72) ne peuvent pas compenser.
    """
    from projet_nutriscore import POINTS_MAX

    total = sum(POINTS_MAX[critere] for critere in criteres)
    return {critere: POINTS_MAX[critere] / total for critere in criteres}


# --- Question 3.3 : apprentissage des poids, profils fixés (annexe B) ---

def contraintesDesPlats(produits, classes, modele, epsilon=EPSILON, avecMarge=False):
    """
    Les contraintes « bien rangé » des programmes linéaires sur les poids, profils fixés.

    Colonnes : un poids w_j par critère, puis une variable z_a par plat (1 si le plat doit
    être bien rangé), puis, avec avecMarge, la marge δ. La première ligne dit que les poids
    font 1. Pour un plat de la classe C_k, bien rangé veut dire :
      - il franchit le profil du bas de sa classe :  Σ_j w_j c_j(a, b_k)   ≥ λ + δ ;
      - il ne franchit pas le profil du haut :       Σ_j w_j c_j(a, b_k+1) ≤ λ − ε − δ.
    Comme les profils sont fixés, les concordances partielles c_j valent 0 ou 1 et sont
    connues : ces contraintes sont linéaires en w. Quand z_a = 0, on retire M au membre de
    droite de la première et on en ajoute M à la seconde, qui sont alors toujours vraies (le
    « grand M » vaut 1 sans marge, 2 avec, car la marge ajoute au plus 1).
    Renvoie (lignes, minimums, maximums).
    """
    criteres, profils, lam = modele["criteres"], modele["profils"], modele["lam"]
    nombreDePoids, nombreDePlats = len(criteres), len(produits)
    grandM = 2 if avecMarge else 1
    marge = [0] if avecMarge else []

    lignes = [[1] * nombreDePoids + [0] * nombreDePlats + marge]          # les poids font 1
    minimums, maximums = [1], [1]
    for numero in range(nombreDePlats):
        plat, classe = produits[numero], classes[numero]
        if classe >= 1:                                                     # franchir le profil du bas
            profil = profils[classe - 1]
            ligne = [concordancePartielle(plat[c], profil[c], sensDuCritere(c, modele)) for c in criteres]
            ligne += [0] * nombreDePlats + ([-1] if avecMarge else [])
            ligne[nombreDePoids + numero] = -grandM
            lignes.append(ligne)
            minimums.append(lam - grandM)
            maximums.append(np.inf)
        if classe <= len(profils) - 1:                                      # ne pas franchir le profil du haut
            profil = profils[classe]
            ligne = [concordancePartielle(plat[c], profil[c], sensDuCritere(c, modele)) for c in criteres]
            ligne += [0] * nombreDePlats + ([1] if avecMarge else [])
            ligne[nombreDePoids + numero] = grandM
            lignes.append(ligne)
            minimums.append(-np.inf)
            maximums.append(lam - epsilon + grandM)
    return lignes, minimums, maximums


def resoudre(objectif, lignes, minimums, maximums, entiers):
    """Résout un programme linéaire en nombres entiers avec HiGHS ; toutes les variables restent entre 0 et 1."""
    solution = milp(c=objectif, constraints=LinearConstraint(np.array(lignes, dtype=float), minimums, maximums),
                    integrality=entiers, bounds=Bounds(0, 1))
    if solution.x is None:
        raise RuntimeError(f"Le solveur n'a pas trouvé de solution : {solution.message}")
    return solution


def apprendrePoids(produits, classes, modele, epsilon=EPSILON, departage=None):
    """
    Profils et seuil majoritaire fixés : cherche les poids qui rangent bien le plus de plats
    (annexe B). Les contraintes sont celles de contraintesDesPlats ; on maximise le nombre de
    plats bien rangés, Σ_a z_a.

    Plusieurs jeux de poids atteignent souvent ce maximum. Sans départage, on garde celui
    que rend le solveur. Avec departage="marge", un second programme cherche, parmi les poids
    qui gardent le maximum, ceux dont la plus petite marge δ est la plus grande (Leroy,
    Mousseau et Pirlot, 2011) : les plats bien rangés y sont le moins sensibles aux petites
    variations des poids.

    produits : les plats ; classes : le numéro de classe attendu de chaque plat (0 pour C1) ;
    modele : un modèle MR-Sort (projet_mrsort) dont on garde les critères, les profils et λ.
    Renvoie un dictionnaire : "modele" (le modèle avec ses poids appris, arrondis),
    "bienRanges" (le nombre de plats bien rangés par ce modèle), "optimum" (le maximum
    trouvé par le solveur, avant l'arrondi des poids) et "marge" (la plus petite marge des
    plats bien rangés, margeDuModele).
    """
    criteres = modele["criteres"]
    nombreDePoids, nombreDePlats = len(criteres), len(produits)
    entiers = [0] * nombreDePoids + [1] * nombreDePlats

    lignes, minimums, maximums = contraintesDesPlats(produits, classes, modele, epsilon)
    objectif = [0] * nombreDePoids + [-1] * nombreDePlats                  # milp minimise : on prend l'opposé
    solution = resoudre(objectif, lignes, minimums, maximums, entiers)
    optimum = int(round(-solution.fun))

    if departage == "marge":
        lignes, minimums, maximums = contraintesDesPlats(produits, classes, modele, epsilon, avecMarge=True)
        lignes.append([0] * nombreDePoids + [1] * nombreDePlats + [0])      # garder le maximum de plats
        minimums.append(optimum)
        maximums.append(np.inf)
        solution = resoudre([0] * (nombreDePoids + nombreDePlats) + [-1], lignes, minimums, maximums, entiers + [0])

    poids = dict(zip(criteres, solution.x[:nombreDePoids]))
    appris = arrondirPoids(dict(modele, poids=poids), produits, classes)
    return {"modele": appris, "bienRanges": nombreBienRanges(produits, classes, appris), "optimum": optimum,
            "marge": margeDuModele(produits, classes, appris)}


def intervallesDesPoids(produits, classes, modele, optimum, epsilon=EPSILON, criteres=None):
    """
    Les poids possibles : pour chaque critère, le plus petit et le plus grand poids parmi les
    modèles qui rangent bien `optimum` plats, profils et λ fixés. Deux programmes linéaires
    par critère, avec les contraintes de contraintesDesPlats. Un intervalle large dit que ce
    poids n'est pas imposé par les données : seul un départage le fixe.
    criteres : les critères à étudier (par défaut, tous ceux du modèle).
    Renvoie un dictionnaire : critère → (minimum, maximum).
    """
    criteresVoulus = criteres
    nombreDePoids, nombreDePlats = len(modele["criteres"]), len(produits)
    lignes, minimums, maximums = contraintesDesPlats(produits, classes, modele, epsilon)
    lignes.append([0] * nombreDePoids + [1] * nombreDePlats)               # garder le maximum de plats
    minimums.append(optimum)
    maximums.append(np.inf)
    intervalles = {}
    for numero, critere in enumerate(modele["criteres"]):
        if criteresVoulus is not None and critere not in criteresVoulus:
            continue
        bornes = []
        for signe in (1, -1):                                               # minimiser, puis maximiser ce poids
            objectif = [0] * (nombreDePoids + nombreDePlats)
            objectif[numero] = signe
            solution = resoudre(objectif, lignes, minimums, maximums, [0] * nombreDePoids + [1] * nombreDePlats)
            bornes.append(signe * solution.fun)
        intervalles[critere] = (bornes[0], bornes[1])
    return intervalles


def margeDuModele(produits, classes, modele):
    """
    La plus petite marge des plats bien rangés : de combien leur concordance dépasse λ face
    au profil du bas de leur classe, ou reste sous λ face au profil du haut. Une marge
    nulle veut dire qu'un plat est tout juste à la frontière. 0 si aucun plat n'est bien rangé.
    """
    marges = []
    for plat, classe in zip(produits, classes):
        detail = affecter(plat, modele)
        if detail["classe"] != classe:
            continue
        if classe >= 1:
            marges.append(detail["concordances"][classe - 1] - modele["lam"])
        if classe <= len(modele["profils"]) - 1:
            marges.append(modele["lam"] - detail["concordances"][classe])
    return min(marges) if marges else 0.0


def nombreBienRanges(produits, classes, modele):
    """Compte les plats que le modèle range dans leur classe attendue."""
    return sum(1 for plat, classe in zip(produits, classes) if affecter(plat, modele)["classe"] == classe)


def arrondirPoids(modele, produits, classes):
    """
    Arrondit les poids trouvés par le solveur au millième, pour qu'ils restent lisibles, en
    gardant une somme exactement égale à 1 (l'écart d'arrondi va au plus grand poids).
    Si l'arrondi fait perdre un plat bien rangé, on garde une décimale de plus, jusqu'à six.
    """
    attendu = nombreBienRanges(produits, classes, modele)
    for decimales in range(3, 7):
        # « + 0.0 » change −0,0 (un poids que le solveur rend à −0,000000001) en 0,0
        poids = {critere: round(valeur, decimales) + 0.0 for critere, valeur in modele["poids"].items()}
        plusGrand = max(poids, key=poids.get)
        poids[plusGrand] = round(poids[plusGrand] + 1 - sum(poids.values()), decimales)
        arrondi = dict(modele, poids=poids)
        if nombreBienRanges(produits, classes, arrondi) >= attendu:
            return arrondi
    return modele


# --- Question 3.3 : apprentissages de la phase 2 ---

def seuilsCandidats(valeurs):
    """
    Les valeurs possibles d'un profil sur un critère : un peu sous la plus petite valeur des
    plats (une unité), le milieu de deux valeurs voisines, un peu au-dessus de la plus grande.
    Entre deux plats voisins, un profil range les plats de la même façon où qu'il soit : le
    milieu suffit, et il reste lisible (l'annexe C prend de même une valeur entre deux plats).
    """
    distinctes = sorted(set(valeurs))
    milieux = [(bas + haut) / 2 for bas, haut in zip(distinctes, distinctes[1:])]
    return [distinctes[0] - 1] + milieux + [distinctes[-1] + 1]


def seuilsFranchis(valeur, seuils, sens):
    """Les numéros des seuils que le plat vaut au moins : sous sa valeur s'il faut maximiser, au-dessus s'il faut minimiser."""
    if sens == "max":
        return [numero for numero, seuil in enumerate(seuils) if seuil <= valeur]
    return [numero for numero, seuil in enumerate(seuils) if seuil >= valeur]


def resoudreCreux(objectif, lignes, minimums, maximums, entiers, bornes, limiteSecondes):
    """
    Résout un programme linéaire en nombres entiers avec HiGHS, en s'arrêtant au bout de
    limiteSecondes. Chaque ligne est un dictionnaire {numéro de variable : coefficient} : la
    matrice des contraintes, creuse, reste légère. bornes : (minimums, maximums) des variables.

    La mise en veille de l'ordinateur : l'horloge de HiGHS compte aussi le temps où le Mac
    dort. Un calcul surpris par la veille s'arrête donc au réveil, sans avoir eu son temps.
    time.perf_counter, lui, ne compte pas la veille : si le solveur s'arrête sur sa limite
    après moins de 90 % de ce temps de calcul, la veille l'a coupé, et on recommence.
    Renvoie la solution de scipy ; solution.x vaut None si le solveur n'a rien trouvé.
    """
    rangs, colonnes, valeurs = [], [], []
    for rang, ligne in enumerate(lignes):
        for colonne, valeur in ligne.items():
            rangs.append(rang)
            colonnes.append(colonne)
            valeurs.append(valeur)
    matrice = coo_matrix((valeurs, (rangs, colonnes)), shape=(len(lignes), len(objectif))).tocsr()
    coupeParLaVeille = True
    while coupeParLaVeille:
        debut = time.perf_counter()
        solution = milp(c=objectif, constraints=LinearConstraint(matrice, minimums, maximums), integrality=entiers,
                        bounds=Bounds(*bornes), options={"time_limit": limiteSecondes})
        # Statut 1 : arrêt sur la limite de temps (la seule limite que l'on donne au solveur)
        coupeParLaVeille = solution.status == 1 and time.perf_counter() - debut < 0.9 * limiteSecondes
    return solution


def apprendreProfils(produits, classes, modele, limiteSecondes=300, epsilon=EPSILON):
    """
    Poids et seuil majoritaire fixés : cherche les profils qui rangent bien le plus de plats
    (annexe C).

    Sur chaque critère, chaque profil prend l'une des valeurs de seuilsCandidats : une
    variable binaire y par (critère, profil, seuil), et une seule vaut 1. Un plat vaut au moins
    le profil sur un critère quand le seuil choisi est l'un de ses seuilsFranchis : c'est une
    somme de y, et la concordance (les poids étant fixés) est linéaire. Comme pour les poids,
    une variable z_a par plat dit s'il doit être bien rangé : franchir le profil du bas de sa
    classe (concordance ≥ λ), pas celui du haut (≤ λ − ε), avec un « grand M » de 1.
    Les profils restent ordonnés : sur chaque critère, chaque profil vaut au moins le précédent.
    On maximise le nombre de plats bien rangés, en au plus limiteSecondes.

    produits, classes : les plats et le numéro de classe attendu de chacun (0 pour C1) ; il y
    a autant de profils que le plus grand numéro de classe. modele : les critères, les poids,
    λ, et facultativement le sens des critères.
    Renvoie un dictionnaire : "modele" (avec ses profils appris), "bienRanges", "optimum" (le
    meilleur trouvé par le solveur), "borne" (le maximum prouvé) et "optimal" (vrai si le
    solveur a prouvé l'optimum avant la limite de temps).
    """
    criteres, poids, lam = modele["criteres"], modele["poids"], modele["lam"]
    nombreDeProfils = max(classes)
    seuils = {critere: seuilsCandidats([plat[critere] for plat in produits]) for critere in criteres}

    # Les variables : y (critère, profil, seuil), puis z (plat)
    numeros = {}
    for critere in criteres:
        for profil in range(nombreDeProfils):
            for seuil in range(len(seuils[critere])):
                numeros[("y", critere, profil, seuil)] = len(numeros)
    for plat in range(len(produits)):
        numeros[("z", plat)] = len(numeros)

    lignes, minimums, maximums = [], [], []
    for critere in criteres:                                     # un seul seuil par profil et par critère
        for profil in range(nombreDeProfils):
            lignes.append({numeros[("y", critere, profil, seuil)]: 1 for seuil in range(len(seuils[critere]))})
            minimums.append(1)
            maximums.append(1)
    for critere in criteres:                                     # chaque profil vaut au moins le précédent
        for profil in range(nombreDeProfils - 1):
            ligne = {}
            for seuil, valeur in enumerate(seuils[critere]):
                ligne[numeros[("y", critere, profil + 1, seuil)]] = valeur
                ligne[numeros[("y", critere, profil, seuil)]] = -valeur
            lignes.append(ligne)
            if sensDuCritere(critere, modele) == "max":
                minimums.append(0)
                maximums.append(np.inf)
            else:
                minimums.append(-np.inf)
                maximums.append(0)
    for numero, (plat, classe) in enumerate(zip(produits, classes)):
        for profil, franchir in ((classe - 1, True), (classe, False)):
            if not 0 <= profil < nombreDeProfils:
                continue
            ligne = {}                                           # la concordance du plat face à ce profil
            for critere in criteres:
                for seuil in seuilsFranchis(plat[critere], seuils[critere], sensDuCritere(critere, modele)):
                    ligne[numeros[("y", critere, profil, seuil)]] = poids[critere]
            if franchir:                                         # concordance − z ≥ λ − 1
                ligne[numeros[("z", numero)]] = -1
                minimums.append(lam - 1)
                maximums.append(np.inf)
            else:                                                # concordance + z ≤ λ − ε + 1
                ligne[numeros[("z", numero)]] = 1
                minimums.append(-np.inf)
                maximums.append(lam - epsilon + 1)
            lignes.append(ligne)

    objectif = [0] * len(numeros)
    for numero in range(len(produits)):
        objectif[numeros[("z", numero)]] = -1                     # milp minimise : on prend l'opposé
    solution = resoudreCreux(objectif, lignes, minimums, maximums, [1] * len(numeros),
                             ([0] * len(numeros), [1] * len(numeros)), limiteSecondes)
    if solution.x is None:
        raise RuntimeError(f"Le solveur n'a pas trouvé de solution : {solution.message}")

    profils = []
    for profil in range(nombreDeProfils):
        profils.append({critere: seuils[critere][seuil] for critere in criteres for seuil in range(len(seuils[critere]))
                        if solution.x[numeros[("y", critere, profil, seuil)]] > 0.5})
    appris = dict(modele, profils=profils)
    return {"modele": appris, "bienRanges": nombreBienRanges(produits, classes, appris),
            "optimum": int(round(-solution.fun)), "borne": int(np.floor(-solution.mip_dual_bound + 1e-6)),
            "optimal": solution.status == 0}


def apprendreParAlternance(produits, classes, criteres, lam, poids=None, sens=None, toursMax=5, limiteSecondes=180):
    """
    Le modèle complet, par alternance (à la manière de Sobrie, Mousseau et Pirlot) : on
    apprend les profils à poids fixés (apprendreProfils), puis les poids sur ces profils
    (apprendrePoids), puis de nouveau les profils sur ces poids, et ainsi de suite tant que le
    nombre de plats bien rangés progresse, en au plus toursMax tours.

    Chaque étape part d'un modèle que son programme peut retrouver : elle ne peut donc pas
    faire moins bien, sauf si la limite de temps arrête le solveur avant la fin. On garde
    toujours le meilleur modèle. C'est une recherche locale : elle ne prouve pas qu'on ne
    puisse pas faire mieux (pour cela, voir apprendreModeleComplet).

    poids : les poids de départ (par défaut, ceux des points maximaux du Nutri-Score) ;
    sens : facultatif, le sens des critères, comme dans un modèle.
    Renvoie un dictionnaire : "modele" (le meilleur), "bienRanges", et "historique" (le nombre
    de plats bien rangés après chaque étape, dans l'ordre).
    """
    modele = {"criteres": criteres, "poids": poids or poidsDesPointsMax(criteres), "lam": lam, "sens": sens or {}}
    meilleur = apprendreProfils(produits, classes, modele, limiteSecondes)
    historique = [meilleur["bienRanges"]]
    for tour in range(toursMax):
        surLesProfils = apprendrePoids(produits, classes, meilleur["modele"])
        historique.append(surLesProfils["bienRanges"])
        if surLesProfils["bienRanges"] <= meilleur["bienRanges"]:
            break
        meilleur = surLesProfils
        surLesPoids = apprendreProfils(produits, classes, meilleur["modele"], limiteSecondes)
        historique.append(surLesPoids["bienRanges"])
        if surLesPoids["bienRanges"] <= meilleur["bienRanges"]:
            break
        meilleur = surLesPoids
    return {"modele": meilleur["modele"], "bienRanges": meilleur["bienRanges"], "historique": historique}


def apprendreModeleComplet(produits, classes, criteres, lam=None, limiteSecondes=600, exact=False, sens=None,
                           epsilon=EPSILON):
    """
    Cherche à la fois les poids, les profils et, si lam vaut None, le seuil majoritaire, dans
    ]0,5 ; 1] comme le veut le sujet (Leroy, Mousseau et Pirlot, 2011). C'est ce qui répond à la question du
    sujet : existe-t-il un modèle MR-Sort qui reproduise exactement les classes ?

    Les profils sont choisis comme dans apprendreProfils (une variable y par critère, profil
    et seuil candidat). Les poids w_j deviennent des variables : la concordance contient
    alors des produits w_j × δ, que l'on remplace par une variable c entre 0 et 1, avec
    c ≤ w_j, c ≤ δ et c ≥ w_j + δ − 1 (c vaut w_j si le plat vaut au moins le profil, 0
    sinon). Il n'en faut que pour les deux profils qui bornent la classe de chaque plat.

    Avec exact=True, tous les plats doivent être bien rangés : le programme cherche seulement
    s'il existe un tel modèle. « existe » vaut alors True (le modèle est rendu), False (le
    solveur prouve qu'il n'en existe pas) ou None (la limite de temps est atteinte sans réponse).
    Sans exact, on maximise le nombre de plats bien rangés, en au plus limiteSecondes.

    sens : facultatif, le sens des critères, comme dans un modèle.
    Renvoie un dictionnaire : "modele" (None si aucun n'est trouvé), "bienRanges", "optimum",
    "borne" (le maximum prouvé), "optimal" (vrai si le solveur a fini) et "existe".
    """
    regle = {"criteres": criteres, "sens": sens or {}}
    nombreDeProfils = max(classes)
    seuils = {critere: seuilsCandidats([plat[critere] for plat in produits]) for critere in criteres}

    # Les variables : poids, λ (s'il est appris), y (critère, profil, seuil), z (plat), puis c (plat, critère, profil)
    numeros = {}
    for critere in criteres:
        numeros[("w", critere)] = len(numeros)
    if lam is None:
        numeros[("lam",)] = len(numeros)
    for critere in criteres:
        for profil in range(nombreDeProfils):
            for seuil in range(len(seuils[critere])):
                numeros[("y", critere, profil, seuil)] = len(numeros)
    for plat in range(len(produits)):
        numeros[("z", plat)] = len(numeros)
    for numero, classe in enumerate(classes):
        for profil in (classe - 1, classe):
            if 0 <= profil < nombreDeProfils:
                for critere in criteres:
                    numeros[("c", numero, critere, profil)] = len(numeros)

    lignes, minimums, maximums = [], [], []
    lignes.append({numeros[("w", critere)]: 1 for critere in criteres})          # les poids font 1
    minimums.append(1)
    maximums.append(1)
    for critere in criteres:                                     # un seul seuil par profil et par critère
        for profil in range(nombreDeProfils):
            lignes.append({numeros[("y", critere, profil, seuil)]: 1 for seuil in range(len(seuils[critere]))})
            minimums.append(1)
            maximums.append(1)
    for critere in criteres:                                     # chaque profil vaut au moins le précédent
        for profil in range(nombreDeProfils - 1):
            ligne = {}
            for seuil, valeur in enumerate(seuils[critere]):
                ligne[numeros[("y", critere, profil + 1, seuil)]] = valeur
                ligne[numeros[("y", critere, profil, seuil)]] = -valeur
            lignes.append(ligne)
            if sensDuCritere(critere, regle) == "max":
                minimums.append(0)
                maximums.append(np.inf)
            else:
                minimums.append(-np.inf)
                maximums.append(0)
    for numero, (plat, classe) in enumerate(zip(produits, classes)):
        for profil, franchir in ((classe - 1, True), (classe, False)):
            if not 0 <= profil < nombreDeProfils:
                continue
            concordance = {}
            for critere in criteres:
                c, w = numeros[("c", numero, critere, profil)], numeros[("w", critere)]
                delta = [numeros[("y", critere, profil, seuil)]
                         for seuil in seuilsFranchis(plat[critere], seuils[critere], sensDuCritere(critere, regle))]
                lignes.append({c: 1, w: -1})                                 # c ≤ w
                minimums.append(-np.inf)
                maximums.append(0)
                ligne = {c: 1}                                               # c ≤ δ
                for y in delta:
                    ligne[y] = -1
                lignes.append(ligne)
                minimums.append(-np.inf)
                maximums.append(0)
                ligne = {c: 1, w: -1}                                        # c ≥ w + δ − 1
                for y in delta:
                    ligne[y] = -1
                lignes.append(ligne)
                minimums.append(-1)
                maximums.append(np.inf)
                concordance[c] = 1
            ligne = dict(concordance)
            seuilFixe = lam if lam is not None else 0
            if lam is None:
                ligne[numeros[("lam",)]] = -1
            if franchir:                                                     # concordance − λ − z ≥ −1
                ligne[numeros[("z", numero)]] = -1
                minimums.append(seuilFixe - 1)
                maximums.append(np.inf)
            else:                                                            # concordance − λ + z ≤ 1 − ε
                ligne[numeros[("z", numero)]] = 1
                minimums.append(-np.inf)
                maximums.append(seuilFixe - epsilon + 1)
            lignes.append(ligne)

    objectif, entiers = [0] * len(numeros), [0] * len(numeros)
    basses, hautes = [0] * len(numeros), [1] * len(numeros)
    for cle, numero in numeros.items():
        if cle[0] in ("y", "z"):
            entiers[numero] = 1
        if cle[0] == "z":
            objectif[numero] = 0 if exact else -1                            # milp minimise : on prend l'opposé
            basses[numero] = 1 if exact else 0                               # exact : tous les plats bien rangés
        if cle[0] == "lam":
            basses[numero] = 0.5 + epsilon                                   # λ ∈ ]0,5 ; 1] (sujet, §2.2)
    solution = resoudreCreux(objectif, lignes, minimums, maximums, entiers, (basses, hautes), limiteSecondes)

    if solution.x is None:
        existe = False if solution.status == 2 else None                     # 2 : infaisable, prouvé
        return {"modele": None, "bienRanges": 0, "optimum": 0, "borne": None, "optimal": solution.status == 2,
                "existe": existe if exact else None}
    poids = {critere: float(solution.x[numeros[("w", critere)]]) for critere in criteres}
    profils = [{critere: seuils[critere][seuil] for critere in criteres for seuil in range(len(seuils[critere]))
                if solution.x[numeros[("y", critere, profil, seuil)]] > 0.5} for profil in range(nombreDeProfils)]
    seuilAppris = float(solution.x[numeros[("lam",)]]) if lam is None else lam
    appris = arrondirPoids(dict(regle, poids=poids, profils=profils, lam=seuilAppris), produits, classes)
    bienRanges = nombreBienRanges(produits, classes, appris)
    return {"modele": appris, "bienRanges": bienRanges,
            "optimum": len(produits) if exact else int(round(-solution.fun)),
            "borne": len(produits) if exact else int(np.floor(-solution.mip_dual_bound + 1e-6)),
            "optimal": solution.status == 0, "existe": (bienRanges == len(produits)) if exact else None}
