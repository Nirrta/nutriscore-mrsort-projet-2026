"""
projet_figures.py : les figures du rapport et des slides (matplotlib), au style « Verso ».

Chaque figure s'écrit en PNG (slides) ou en PDF vectoriel (rapport), selon l'extension du
chemin donné. Les couleurs, les filets et les polices viennent de projet_design.py.

Les figures :
- figureEntonnoir : le nombre de candidats restant après chaque filtre de la base ;
- figureMatriceConfusion : le Nutri-Score en lignes, un modèle MR-Sort en colonnes ;
- figureProfils : le diagramme des profils, l'élément signature du projet. Sept axes
  verticaux, un par critère, avec le mieux toujours en haut ; les profils b2 à b5 en
  traits de couleur ; le plat en trait noir ; le poids de chaque critère sous son axe ;
- figureCourbe : la courbe d'apprentissage, à 7 et à 3 critères : l'exactitude sur les
  plats appris (tirets gris) et sur des plats jamais vus (trait noir, avec son écart-type).

Archivo n'a pas de lettres grecques : λ passe par la police de repli (DejaVu Sans).
"""

import dataclasses

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib import font_manager

from projet_design import (COULEURS_CLASSES, DOSSIER_POLICES, ENCRE, ENCRE_SECONDAIRE, FICHIERS_POLICES, PAPIER,
                           TRAME)
from projet_mrsort import CLASSES, CRITERES, LETTRES_NUTRISCORE, PROFILS, sensDuCritere


# Le profil b_k sépare C(k-1) et C(k) : on le trace de la couleur de la classe qu'il ouvre
COULEURS_PROFILS = {"b2": COULEURS_CLASSES["D"], "b3": "#D9A800", "b4": COULEURS_CLASSES["B"], "b5": COULEURS_CLASSES["A"]}
LIBELLES_COURTS = {"en": "Énergie", "sa": "Acides gras saturés", "su": "Sucres", "so": "Sel", "pr": "Protéines",
                   "fi": "Fibres", "fr": "Fruits, légumes"}


def preparerPolices():
    """Déclare les polices Archivo du dossier design/polices à matplotlib, avec DejaVu Sans en repli."""
    for fichier in FICHIERS_POLICES.values():
        font_manager.fontManager.addfont(str(DOSSIER_POLICES / fichier))
    # Les titres sont en Archivo Condensed (graisse 800), avec DejaVu Sans en repli pour λ. DejaVu Sans n'a pas
    # de graisse 800 : matplotlib prend son gras (700), mais l'écrit dans le journal à chaque titre.
    # On déclare donc ce remplacement une fois pour toutes, comme matplotlib le fait pour les autres noms d'une police.
    polices = font_manager.fontManager.ttflist
    if not any(police.name == "DejaVu Sans" and police.weight == 800 for police in polices):
        gras = next(police for police in polices
                    if police.name == "DejaVu Sans" and police.weight == 700 and police.style == "normal")
        polices.append(dataclasses.replace(gras, weight=800))
    plt.rcParams.update({
        "font.family": ["Archivo", "DejaVu Sans"],
        "font.size": 11,
        "text.color": ENCRE,
        "axes.edgecolor": ENCRE,
        "axes.labelcolor": ENCRE,
        "xtick.color": ENCRE,
        "ytick.color": ENCRE,
        "figure.facecolor": PAPIER,
        "axes.facecolor": PAPIER,
        "savefig.facecolor": PAPIER,
        "axes.formatter.use_locale": False,
    })


def nombre(valeur, decimales=0):
    """Écrit un nombre à la française : virgule décimale, espace fine entre les milliers."""
    return f"{valeur:,.{decimales}f}".replace(",", " ").replace(".", ",")


def enregistrer(figure, chemin):
    """Enregistre la figure (PNG à 200 points par pouce, ou PDF vectoriel) et la ferme."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(chemin, dpi=200, bbox_inches="tight")
    plt.close(figure)


def titreDeFigure(axe, titre):
    """Le titre d'une figure : Archivo Condensed en gras (graisse 800), aligné à gauche."""
    if titre:
        axe.set_title(titre, loc="left", fontfamily=["Archivo Condensed", "DejaVu Sans"], fontweight=800,
                      fontsize=17, pad=14)


# --- Base : l'entonnoir des filtres ---

def figureEntonnoir(entonnoir, chemin, titre=None):
    """Barres horizontales : le nombre de candidats restant après chaque étape, de haut en bas."""
    preparerPolices()
    etapes = list(entonnoir)
    valeurs = [entonnoir[etape] for etape in etapes]
    figure, axe = plt.subplots(figsize=(8, 0.42 * len(etapes) + 0.8))
    positions = list(range(len(etapes)))[::-1]
    axe.barh(positions, valeurs, color=ENCRE, height=0.62)
    for position, valeur in zip(positions, valeurs):
        axe.text(valeur + max(valeurs) * 0.01, position, nombre(valeur), va="center", fontsize=10.5)
    axe.set_yticks(positions, [etape[0].upper() + etape[1:] for etape in etapes])
    axe.set_xticks([])
    for cote in ("top", "right", "bottom"):
        axe.spines[cote].set_visible(False)
    axe.spines["left"].set_linewidth(1)
    axe.tick_params(axis="y", length=0)
    titreDeFigure(axe, titre)
    enregistrer(figure, chemin)


# --- MR-Sort : la courbe d'apprentissage ---

def figureCourbe(courbe, chemin, titre=None):
    """
    La courbe d'apprentissage (courbeDApprentissage), un panneau pour 7 critères et un pour 3 :
    en abscisse, le nombre de plats appris ; en ordonnée, l'exactitude à classes égales, sur
    les plats appris (tirets gris) et sur des plats jamais vus (trait noir, avec une bande d'un
    écart-type de part et d'autre, en trame).
    """
    preparerPolices()
    figure, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for axe, (nom, sousTitre) in zip(axes, (("sept", "7 critères"), ("trois", "3 critères"))):
        points = courbe[nom]
        tailles = [point["taille"] for point in points]
        tenus = [100 * point["tenusAPart"] for point in points]
        ecarts = [100 * point["ecartType"] for point in points]
        axe.fill_between(tailles, [t - e for t, e in zip(tenus, ecarts)], [t + e for t, e in zip(tenus, ecarts)],
                         color=TRAME, linewidth=0)
        axe.plot(tailles, [100 * point["appris"] for point in points], color=ENCRE_SECONDAIRE, linestyle="--",
                 linewidth=1.5, label="plats appris")
        axe.plot(tailles, tenus, color=ENCRE, linewidth=2.2, marker="o", markersize=4, label="plats jamais vus")
        axe.text(tailles[-1], tenus[-1] + 2, f"{nombre(tenus[-1], 1)} %", ha="right", fontsize=10.5, fontweight="bold")
        axe.set_title(sousTitre, loc="left", fontsize=12, fontweight="bold", pad=8)
        axe.set_xlabel("Plats appris")
        axe.set_xticks(tailles, [str(taille) for taille in tailles], fontsize=9)
        for cote in ("top", "right"):
            axe.spines[cote].set_visible(False)
        axe.tick_params(length=3)
    axes[0].set_ylabel("Bien rangés, à classes égales (%)")
    axes[0].yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda valeur, _: nombre(valeur)))
    axes[0].legend(frameon=False, loc="lower right", fontsize=10)
    if titre:
        # au-dessus des titres des deux panneaux, et non sur eux (l'image est rognée au plus juste à l'enregistrement)
        figure.suptitle(titre, x=0.06, y=1.06, ha="left", fontfamily=["Archivo Condensed", "DejaVu Sans"],
                        fontweight=800, fontsize=17)
    enregistrer(figure, chemin)


# --- MR-Sort : la matrice de confusion ---

def figureMatriceConfusion(matrice, chemin, titre=None):
    """
    La matrice de confusion : le Nutri-Score en lignes (A en haut), le modèle en colonnes
    (A′ à gauche). Plus une case compte de plats, plus elle est foncée ; la diagonale, qui
    compte les plats bien rangés, est encadrée de noir.
    """
    preparerPolices()
    taille = len(matrice)
    maximum = max(max(ligne) for ligne in matrice) or 1
    figure, axe = plt.subplots(figsize=(5.2, 5.0))
    for i in range(taille):
        for j in range(taille):
            valeur = matrice[i][j]
            gris = 1 - 0.85 * valeur / maximum
            axe.add_patch(plt.Rectangle((j, taille - 1 - i), 1, 1, facecolor=(gris, gris, gris),
                                        edgecolor=ENCRE if i == j else TRAME, linewidth=2.2 if i == j else 0.8))
            axe.text(j + 0.5, taille - 0.5 - i, str(valeur), ha="center", va="center", fontsize=13,
                     color=PAPIER if gris < 0.5 else ENCRE, fontweight="bold" if i == j else "normal")
    lettres = LETTRES_NUTRISCORE[::-1]
    axe.set_xlim(0, taille)
    axe.set_ylim(0, taille)
    axe.set_xticks([j + 0.5 for j in range(taille)], [f"{lettre}′" for lettre in lettres])
    axe.set_yticks([taille - 0.5 - i for i in range(taille)], lettres)
    axe.xaxis.tick_top()
    axe.set_xlabel("Classe MR-Sort", labelpad=8)
    axe.xaxis.set_label_position("top")
    axe.set_ylabel("Nutri-Score")
    axe.tick_params(length=0)
    for cote in axe.spines.values():
        cote.set_visible(False)
    axe.set_aspect("equal")
    titreDeFigure(axe, titre)
    enregistrer(figure, chemin)


# --- MR-Sort : le diagramme des profils ---

def positionSurLAxe(valeur, critere, etendues, modele):
    """
    La hauteur d'une valeur sur l'axe de son critère, entre 0 (en bas) et 1 (en haut).
    Le mieux est toujours en haut : l'axe d'un critère à minimiser est retourné.
    """
    bas, haut = etendues[critere]
    position = (valeur - bas) / (haut - bas) if haut > bas else 0.5
    position = min(1, max(0, position))
    return position if sensDuCritere(critere, modele) == "max" else 1 - position


def etenduesDuModele(modele, plats):
    """Les bornes de chaque axe : de la plus petite à la plus grande valeur des profils et des plats."""
    etendues = {}
    for critere in modele["criteres"]:
        valeurs = [profil[critere] for profil in modele["profils"]] + [plat[critere] for plat in plats]
        etendues[critere] = (min(valeurs), max(valeurs))
    return etendues


def etenduesDeLaBase(plats, criteres):
    """
    Les bornes de chaque axe tirées de la base : du 5e au 95e centile des valeurs. Les
    quelques plats extrêmes (un sel de 4 g) ne tassent pas l'axe ; ils restent au bord.
    """
    etendues = {}
    for critere in criteres:
        valeurs = sorted(plat[critere] for plat in plats)
        bas = valeurs[int(0.05 * (len(valeurs) - 1))]
        haut = valeurs[int(0.95 * (len(valeurs) - 1))]
        etendues[critere] = (bas, haut)
    return etendues


def figureProfils(modele, plat, chemin, titre=None, etendues=None, nomDuPlat=None, taille=None, zoom=1.0):
    """
    Le diagramme des profils d'un modèle MR-Sort, avec un plat. Chaque critère a son axe
    vertical, le mieux en haut ; les valeurs extrêmes de l'axe sont écrites en haut et en bas,
    et le poids du critère sous son nom. Les profils b2 à b5 sont des traits de couleur, le
    plat un trait noir épais : sur chaque axe, on voit d'un coup d'œil s'il est au-dessus
    (au moins aussi bon) ou au-dessous d'un profil.
    taille (largeur, hauteur en pouces) et zoom (facteur des polices) servent aux slides :
    la figure y est tracée à sa taille d'affichage, pour que ses textes restent lisibles.
    """
    preparerPolices()
    criteres = modele["criteres"]
    etendues = etendues or etenduesDuModele(modele, [plat])
    figure, axe = plt.subplots(figsize=taille or (1.35 * len(criteres) + 1.8, 4.8))
    abscisses = list(range(len(criteres)))

    # les textes des axes sont placés à des écarts fixes, en points, des bouts de l'axe : ils ne se
    # chevauchent pas, quelle que soit la hauteur de la figure
    ecartNom = 5 + 1.25 * 9 * zoom + 4
    ecartPoids = ecartNom + 1.25 * 11 * zoom + 1
    for x, critere in zip(abscisses, criteres):
        axe.plot([x, x], [0, 1], color=ENCRE, linewidth=1, zorder=1)
        bas, haut = etendues[critere]
        meilleur, pire = (haut, bas) if sensDuCritere(critere, modele) == "max" else (bas, haut)
        unite = CRITERES[critere][1].split("/")[0] if critere in CRITERES else ""
        ecrireAuBout(axe, x, 1, 5, f"{nombre(meilleur, 0 if critere == 'en' else 1)} {unite}", fontsize=9 * zoom,
                     color=ENCRE_SECONDAIRE)
        ecrireAuBout(axe, x, 0, -5, f"{nombre(pire, 0 if critere == 'en' else 1)} {unite}", fontsize=9 * zoom,
                     color=ENCRE_SECONDAIRE)
        ecrireAuBout(axe, x, 0, -ecartNom, LIBELLES_COURTS.get(critere, critere), fontsize=11 * zoom,
                     fontfamily="Archivo SemiBold", fontweight=600)
        ecrireAuBout(axe, x, 0, -ecartPoids, f"poids {nombre(modele['poids'][critere], 4)}", fontsize=9.5 * zoom)

    for profil, valeurs in zip(PROFILS, modele["profils"]):
        hauteurs = [positionSurLAxe(valeurs[c], c, etendues, modele) for c in criteres]
        axe.plot(abscisses, hauteurs, color=COULEURS_PROFILS[profil], linewidth=2.2, zorder=2)
        axe.text(abscisses[-1] + 0.18, hauteurs[-1], profil, va="center", fontsize=10.5 * zoom,
                 color=COULEURS_PROFILS[profil], fontfamily="Archivo Condensed", fontweight=800)

    hauteurs = [positionSurLAxe(plat[c], c, etendues, modele) for c in criteres]
    axe.plot(abscisses, hauteurs, color=ENCRE, linewidth=3.4, marker="s", markersize=8, zorder=3)
    if nomDuPlat:
        axe.text(abscisses[0] - 0.25, hauteurs[0], nomDuPlat, ha="right", va="center", fontsize=10.5 * zoom,
                 fontfamily="Archivo SemiBold", fontweight=600)

    axe.set_xlim(-0.6 if not nomDuPlat else -2.4, abscisses[-1] + 0.6)
    axe.set_ylim(-0.03, 1.03)
    axe.axis("off")
    titreDeFigure(axe, titre)
    enregistrer(figure, chemin)


def ecrireAuBout(axe, x, y, ecart, texte, **style):
    """
    Écrit un texte centré sur l'axe x, à `ecart` points au-dessus (ecart > 0) ou au-dessous
    (ecart < 0) du point (x, y), le bout d'un axe du diagramme des profils.
    """
    axe.annotate(texte, (x, y), xytext=(0, ecart), textcoords="offset points", ha="center",
                 va="bottom" if ecart > 0 else "top", annotation_clip=False, **style)


# --- Nutri-Score : le détail des points, avec leurs jauges ---

LIBELLES_POINTS = {"en": "Énergie", "sa": "Acides gras saturés", "su": "Sucres", "so": "Sel", "pr": "Protéines",
                   "fi": "Fibres", "fr": "Fruits, légumes"}
UNITES_POINTS = {"en": "kJ", "sa": "g", "su": "g", "so": "g", "pr": "g", "fi": "g", "fr": "%"}
DECIMALES_POINTS = {"en": 0, "sa": 1, "su": 1, "so": 2, "pr": 1, "fi": 1, "fr": 0}


def figurePoints(plat, resultat, maximums, chemin):
    """
    Le détail des points du Nutri-Score d'un plat, comme dans l'interface : une ligne par
    composante, avec sa valeur, une jauge d'une case par point possible (noire pour chaque
    point obtenu) et ses points. Un filet épais sépare les composantes négatives des
    positives ; les totaux N et P, puis le score, viennent en dessous.
    """
    preparerPolices()
    negatives, positives = ["en", "sa", "su", "so"], ["pr", "fi", "fr"]
    figure, axe = plt.subplots(figsize=(6.4, 4.3))
    y, pas, cote = 0, 1.0, 0.42
    # les deux axes n'ont pas la même échelle : la hauteur d'une case en tient compte, pour qu'elle reste carrée
    largeurAxe = figure.get_figwidth() * (figure.subplotpars.right - figure.subplotpars.left)
    hauteurAxe = figure.get_figheight() * (figure.subplotpars.top - figure.subplotpars.bottom)
    hauteurCase = cote * (largeurAxe / 31.4) / (hauteurAxe / (len(negatives + positives) + 1.6))
    for composante in negatives + positives:
        if composante == "pr":
            axe.plot([0, 31], [y + 0.55, y + 0.55], color=ENCRE, linewidth=3.2)
        axe.text(0, y, LIBELLES_POINTS[composante], va="center", fontsize=12)
        valeur = f"{nombre(plat[composante], DECIMALES_POINTS[composante])} {UNITES_POINTS[composante]}"
        axe.text(12.6, y, valeur, va="center", ha="right", fontsize=12)
        points, maximum = resultat["points"][composante], maximums[composante]
        for case in range(maximum):
            axe.add_patch(plt.Rectangle((13.2 + case * 0.55, y - hauteurCase / 2), cote, hauteurCase,
                                        facecolor=ENCRE if case < points else PAPIER, edgecolor=ENCRE, linewidth=0.8))
        axe.text(31, y, f"{points} / {maximum}", va="center", ha="right", fontsize=12)
        axe.plot([0, 31], [y - 0.5, y - 0.5], color=ENCRE, linewidth=0.6)
        y -= pas
    axe.plot([0, 31], [y + 0.5, y + 0.5], color=ENCRE, linewidth=3.2)
    axe.text(0, y - 0.1, f"N = {resultat['N']}, P = {resultat['P']}", va="center", fontsize=12,
             fontfamily="Archivo SemiBold", fontweight=600)
    axe.text(31, y - 0.1, f"score = {resultat['N']} − {resultat['P']} = {resultat['score']}", va="center", ha="right",
             fontsize=15, fontfamily=["Archivo Condensed", "DejaVu Sans"], fontweight=800)
    axe.set_xlim(-0.2, 31.2)
    axe.set_ylim(y - 0.8, 0.8)
    axe.axis("off")
    enregistrer(figure, chemin)


# --- MR-Sort : les barres de concordance ---

def figureConcordance(modele, plat, chemin, profils=None):
    """
    Les barres de concordance d'un plat, comme dans l'interface : pour chaque profil, une
    case par critère, de largeur égale à son poids, noire quand le plat vaut au moins le
    profil sur ce critère. La somme des cases noires est la concordance, comparée à λ.
    profils : les profils à montrer, du meilleur au moins bon (par défaut b5 à b2).
    """
    preparerPolices()
    numeros = [PROFILS.index(nom) for nom in (profils or PROFILS[::-1])]
    figure, axe = plt.subplots(figsize=(7.6, 0.62 * len(numeros) + 0.3))
    lam = modele["lam"]
    for rang, numero in enumerate(numeros):
        y = -rang
        profil = modele["profils"][numero]
        concordance, gauche = 0, 0.0
        axe.text(-0.03, y, PROFILS[numero], va="center", ha="right", fontsize=13,
                 fontfamily="Archivo SemiBold", fontweight=600)
        for critere in modele["criteres"]:
            poids = modele["poids"][critere]
            sens = sensDuCritere(critere, modele)
            passe = plat[critere] >= profil[critere] if sens == "max" else plat[critere] <= profil[critere]
            concordance += poids if passe else 0
            # un filet blanc sépare deux cases noires voisines ; une case blanche garde un bord noir
            axe.add_patch(plt.Rectangle((gauche, y - 0.32), poids, 0.64, facecolor=ENCRE if passe else PAPIER,
                                        edgecolor=PAPIER if passe else ENCRE, linewidth=1.2))
            if poids >= 0.06:
                axe.text(gauche + poids / 2, y, critere, va="center", ha="center", fontsize=11,
                         color=PAPIER if passe else ENCRE_SECONDAIRE, fontweight=600)
            gauche += poids
        axe.add_patch(plt.Rectangle((0, y - 0.32), 1, 0.64, facecolor="none", edgecolor=ENCRE, linewidth=1.8))
        franchi = concordance >= lam - 1e-9
        verdict = f"{nombre(concordance, 3)} ≥ {nombre(lam, 1)}, franchi" if franchi else f"{nombre(concordance, 3)} < {nombre(lam, 1)}"
        axe.text(1.04, y, verdict, va="center", fontsize=13, fontweight="bold" if franchi else "normal")
    axe.set_xlim(-0.12, 1.55)
    axe.set_ylim(-len(numeros) + 0.45, 0.55)
    axe.axis("off")
    enregistrer(figure, chemin)
