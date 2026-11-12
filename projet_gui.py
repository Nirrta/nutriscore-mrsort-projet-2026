"""
projet_gui.py : l'interface du projet (questions 3.2 et 3.5), en Streamlit.

Le consommateur saisit les sept composantes d'un produit, part d'un exemple, ou cherche un
produit d'Open Food Facts par son code-barres, le lien de sa fiche ou son nom. Il voit
s'afficher le score et le label du Nutri-Score, avec le détail des points (question 3.2),
puis la classe des modèles MR-Sort, dont les paramètres sont modifiables à la main (question
3.5). Le SuperNutri-score s'y ajoutera.

Le type de produit (cas général, fromage, viande rouge, matières grasses, boisson, eau)
choisit les règles du Nutri-Score. Pour un produit cherché, il est proposé par OFF, avec sa
raison, et reste modifiable : OFF range parfois des plats composés parmi les viandes rouges,
que la FAQ du Nutri-Score laisse au cas général. Les modèles MR-Sort sont appris sur des plats
préparés du cas général : hors de ce domaine (un autre type, un produit cherché qui n'est pas
un plat préparé, les céréales des exemples du sujet), leur classe est donnée à titre indicatif.
Au premier affichage, le calculateur montre la Poêlée Fermière, le plat suivi par la soutenance.

L'interface lit les fiches gardées dans donnees/brut/ avant de demander à OFF, et n'écrit
rien sur le disque : les fiches lues sont gardées une heure en mémoire.

Les calculs viennent des modules projet_nutriscore, projet_mrsort et projet_supernutri ;
l'interface ne fait que les mettre en forme, au style « Verso de l'emballage » : noir et
blanc, filets de tableau nutritionnel, police Archivo. La couleur vient du Nutri-Score : ses
classes, et ses points (rouge pour les négatifs, vert pour les positifs, comme les fig. 6 et 7).
Les couleurs et les filets viennent de projet_design.py ; le thème de Streamlit est dans
.streamlit/config.toml, à côté de ce fichier.

Onglets : Calculateur, Pas à pas (MR-Sort pour le plat et le modèle du calculateur : les
profils sur leur diagramme, les concordances partielles, la concordance, l'affectation),
Modèles (les modèles appris, comparés sur la base et sur des plats jamais vus ; la question du
modèle exact ; la courbe d'apprentissage), Base. Viendra : SuperNutri-score (phase 3).

Commande :
    streamlit run projet_gui.py
"""

import base64
import json
from html import escape

import pandas as pd
import streamlit as st

from projet_base import (FICHIER_BASE, FICHIER_BASE_ETENDUE, FICHIER_RESULTATS, LOT_AJOUT, codeDepuisSaisie,
                         ficheEnDirect, lireBase, motsDeLaRecherche, produitDepuisFiche, rechercherParNom)
from projet_design import (COULEUR_NEGATIFS, COULEUR_POSITIFS, COULEURS_CLASSES, ENCRE, ENCRE_SECONDAIRE,
                           FILET_GROUPE, FILET_LIGNE, FILET_PANNEAU, LETTRE_SUR_CLASSE, couleurClasse, lettreDeClasse)
from projet_mrsort import (CRITERES, CRITERES_SEPT, CRITERES_TROIS, PROFILS, SEUILS_MAJORITAIRES, affecter,
                           approximerNutriscore, concordancePartielle, etapesDeLAffectation, nomDeClasse, sensDuCritere)
from projet_nutriscore import (CATEGORIES, EXEMPLES_SUJET, LIBELLES, NEGATIFS, POSITIFS, UNITES,
                               composantesDeLaCategorie, scoreNutriscore)


COMPOSANTES = NEGATIFS + POSITIFS
PLAT_DE_DEPART = "3257982125116"       # la Poêlée Fermière (Cora), le plat suivi par la soutenance du 30/10

# Les champs de saisie : (pas, maximum, nombre de décimales affichées). Le sel va jusqu'à 100 g :
# un produit cherché sur OFF peut être un bouillon ou du sel.
CHAMPS = {
    "en": (10.0, 4000.0, 0), "sa": (0.1, 100.0, 1), "su": (0.1, 100.0, 1), "so": (0.01, 100.0, 2),
    "pr": (0.1, 100.0, 1), "fi": (0.1, 100.0, 1), "fr": (1.0, 100.0, 0), "lipides": (0.1, 100.0, 1),
}
# L'aide de deux champs dont la valeur ne se lit pas toujours dans le tableau nutritionnel
AIDES = {
    "fr": "Ce pourcentage se lit dans la liste des ingrédients (par exemple « carottes 12 % »), pas dans le tableau "
          "nutritionnel. Sans indication, laissez 0.",
    "fi": "Les fibres sont facultatives sur l'étiquette : non déclarées, elles comptent 0, comme chez Open Food Facts.",
}
# Les décimales affichées dans le tableau des points, y compris pour les composantes des matières grasses
DECIMALES = {cle: decimales for cle, (pas, maximum, decimales) in CHAMPS.items()} | {"enAgs": 0, "ratioAgs": 1}

# Les types qui sortent du domaine de nos modèles MR-Sort, appris sur des plats préparés du cas général,
# et ceux que la FAQ du Nutri-Score n'applique pas aux plats composés (FAQ, p. 17 et 19-20)
TYPES_DE_LA_FAQ_HORS_PLATS_COMPOSES = ("fromage", "viandeRouge", "matieresGrasses")
# Les types auxquels le Nutri-Score applique une règle à part, dits en toutes lettres (raisonHorsDomaine)
REGLES_A_PART = {"fromage": "aux fromages", "viandeRouge": "aux viandes rouges",
                 "matieresGrasses": "aux matières grasses, fruits à coque et graines"}

# Les modèles MR-Sort que l'on peut choisir, par base (« 375 », ou « 125 », la base du 30/10) et par
# apprentissage : (clé du JSON, fichier de la base). « poids » : profils par les médianes, poids appris ;
# « profils » : poids des points maximaux du Nutri-Score, profils appris ; « complet » : poids et profils
# appris tour à tour. Seuls les poids s'apprennent assez vite pour l'interface : les autres viennent du JSON.
MODELES_APPRIS = {("375", "poids"): ("mrsortEtendu", FICHIER_BASE_ETENDUE),
                  ("375", "profils"): ("mrsortEtenduProfils", FICHIER_BASE_ETENDUE),
                  ("375", "complet"): ("modeleCompletEtendu", FICHIER_BASE_ETENDUE),
                  ("125", "poids"): ("mrsort", FICHIER_BASE),
                  ("125", "profils"): ("mrsortProfils", FICHIER_BASE),
                  ("125", "complet"): ("modeleComplet", FICHIER_BASE)}
# Les libellés des deux choix du calculateur : la base (repris par l'onglet Base), puis l'apprentissage
# (repris par l'onglet Modèles)
LIBELLES_DES_BASES = {"375": "375 plats", "125": "125 plats (30/10)"}
LIBELLES_APPRENTISSAGES = {"poids": "Poids appris", "profils": "Profils appris", "complet": "Tout appris"}

PASTILLES = "".join(
    f".pastille-{lettre} {{ background: {couleur}; color: {LETTRE_SUR_CLASSE[lettre]}; }}\n"
    for lettre, couleur in COULEURS_CLASSES.items()
)

STYLE = f"""
<style>
.titre-page {{ font-family: "Archivo Condensed", Archivo, sans-serif; font-weight: 800; font-size: 3.2rem;
  line-height: 1; letter-spacing: -.01em; border-top: {FILET_PANNEAU}px solid {ENCRE}; padding-top: .7rem; margin: 0 0 .5rem; }}
.chapo {{ font-size: 1.05rem; color: {ENCRE_SECONDAIRE}; max-width: 62ch; margin: 0 0 1.4rem; }}
.panneau {{ border-top: {FILET_PANNEAU}px solid {ENCRE}; padding-top: .55rem; margin: 0 0 .9rem; }}
.panneau .titre {{ font-family: "Archivo Condensed", Archivo, sans-serif; font-weight: 800; font-size: 1.7rem; line-height: 1.1; }}
.panneau .sous-titre {{ font-size: .95rem; color: {ENCRE_SECONDAIRE}; margin-top: .15rem; }}
.resultat {{ display: flex; align-items: flex-end; gap: 1.6rem; margin: .4rem 0 1rem; flex-wrap: wrap; }}
.bande {{ display: flex; align-items: center; }}
.bande span {{ width: 2.5rem; height: 2.5rem; display: flex; align-items: center; justify-content: center;
  font-family: "Archivo Condensed", Archivo, sans-serif; font-weight: 800; font-size: 1.35rem; }}
.bande span.choisie {{ width: 4.4rem; height: 4.4rem; font-size: 2.7rem; outline: 3px solid {ENCRE}; position: relative; z-index: 1; }}
{PASTILLES}
.score .valeur {{ font-family: "Archivo Condensed", Archivo, sans-serif; font-weight: 800; font-size: 4.4rem; line-height: .85; }}
.score .legende {{ font-size: .9rem; color: {ENCRE_SECONDAIRE}; }}
table.verso {{ width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; margin: .2rem 0 .6rem; }}
table.verso th {{ text-align: left; font-weight: 600; border-bottom: {FILET_GROUPE}px solid {ENCRE}; padding: .3rem .35rem; }}
table.verso td {{ border-bottom: {FILET_LIGNE}px solid {ENCRE}; padding: .3rem .35rem; }}
table.verso .nombre {{ text-align: right; white-space: nowrap; }}
table.verso tr.groupe td {{ border-top: {FILET_GROUPE}px solid {ENCRE}; }}
table.verso tr.total td {{ font-weight: 700; }}
table.verso tr.ecarte td {{ color: {ENCRE_SECONDAIRE}; text-decoration: line-through; }}
.note {{ font-size: .92rem; color: {ENCRE_SECONDAIRE}; max-width: 62ch; }}
.comptes {{ display: flex; gap: 1.2rem; flex-wrap: wrap; margin: .3rem 0 1rem; }}
.comptes div {{ display: flex; align-items: center; gap: .5rem; font-variant-numeric: tabular-nums; font-size: 1.1rem; }}
.comptes span {{ width: 2rem; height: 2rem; display: flex; align-items: center; justify-content: center;
  font-family: "Archivo Condensed", Archivo, sans-serif; font-weight: 800; font-size: 1.15rem; }}
.classe-modele {{ width: 4.4rem; height: 4.4rem; border: 3px solid {ENCRE}; display: flex; flex-direction: column; flex: none; }}
.classe-modele .lettre {{ flex: 1; display: flex; align-items: center; justify-content: center;
  font-family: "Archivo Condensed", Archivo, sans-serif; font-weight: 800; font-size: 2.3rem; }}
.classe-modele .barre {{ height: 7px; }}
/* un produit hors du domaine de nos modèles : un encadré en tête de la colonne MR-Sort, et des classes en pointillés */
.hors-domaine {{ border: 2px solid {ENCRE}; padding: .5rem .7rem .55rem; margin: .4rem 0 .9rem; font-size: .95rem; }}
.hors-domaine .titre {{ font-weight: 600; margin-bottom: .2rem; }}
.hors-domaine p {{ margin: 0; }}
.classe-modele.indicatif, .classe-petite.indicatif {{ border-style: dashed; }}
.classe-modele.indicatif .lettre, .classe-petite.indicatif .lettre {{ color: {ENCRE_SECONDAIRE}; }}
.verdict-modele {{ display: flex; align-items: center; gap: 1rem; margin: .5rem 0 .4rem; }}
.verdict-modele .texte {{ font-size: .98rem; line-height: 1.35; }}
.erreur {{ font-size: .92rem; border-top: {FILET_GROUPE}px solid {ENCRE}; padding: .35rem 0 0; margin: .5rem 0; }}
.sous-titre-editeur {{ display: flex; align-items: center; flex-wrap: wrap; gap: .45rem; margin: .2rem 0 .3rem; font-size: 1rem; }}
/* la classe d'un modèle en petit, dans la ligne de titre d'un éditeur : le même cadre noir et la même barre de couleur */
.classe-petite {{ display: inline-flex; flex-direction: column; width: 2.1rem; height: 2.1rem; border: 2px solid {ENCRE}; flex: none; }}
.classe-petite .lettre {{ flex: 1; display: flex; align-items: center; justify-content: center;
  font-family: "Archivo Condensed", Archivo, sans-serif; font-weight: 800; font-size: 1.1rem; }}
.classe-petite .barre {{ height: 4px; }}
/* les étapes numérotées du pas à pas : un filet de groupe, puis le titre de l'étape */
.etape {{ border-top: {FILET_GROUPE}px solid {ENCRE}; padding-top: .35rem; margin: 1.4rem 0 .4rem;
  font-family: "Archivo Condensed", Archivo, sans-serif; font-weight: 800; font-size: 1.35rem; }}
.jauge {{ display: inline-flex; gap: 1px; vertical-align: middle; margin-right: .45rem; }}
.jauge i {{ width: 6px; height: 6px; border: 1px solid {ENCRE}; display: block; }}
.jauge i.point {{ background: {ENCRE}; }}
.jauge.negatif i.point {{ background: {COULEUR_NEGATIFS}; border-color: {COULEUR_NEGATIFS}; }}
.jauge.positif i.point {{ background: {COULEUR_POSITIFS}; border-color: {COULEUR_POSITIFS}; }}
/* le repère d'un groupe de points, comme les ⊖ et ⊕ des fig. 6 et 7, mais carré comme nos pastilles */
.signe {{ display: inline-flex; align-items: center; justify-content: center; width: 1.05rem; height: 1.05rem;
  margin-right: .45rem; vertical-align: -.15rem; color: #FFFFFF; font-weight: 700; line-height: 1; }}
.signe.negatif {{ background: {COULEUR_NEGATIFS}; }}
.signe.positif {{ background: {COULEUR_POSITIFS}; }}
/* des protéines qui ne comptent pas : leurs points restent visibles, mais en gris, comme leur ligne barrée */
table.verso tr.ecarte .jauge i.point {{ background: {ENCRE_SECONDAIRE}; border-color: {ENCRE_SECONDAIRE}; }}
.concordances {{ margin: .6rem 0 .3rem; }}
.ligne-concordance {{ display: grid; grid-template-columns: 3.8rem minmax(0, 1fr) 8.6rem; gap: .5rem; align-items: center; margin: .32rem 0; }}
.ligne-concordance .profil {{ font-weight: 600; }}
.ligne-concordance .barre {{ display: flex; height: 1.55rem; border: 2px solid {ENCRE}; }}
.ligne-concordance .case {{ display: flex; align-items: center; justify-content: center; overflow: hidden;
  font-size: .74rem; font-weight: 600; border-right: 1px solid {ENCRE}; }}
.ligne-concordance .case:last-child {{ border-right: 0; }}
.ligne-concordance .case.pleine {{ background: {ENCRE}; color: #FFFFFF; border-right-color: #FFFFFF; }}
.ligne-concordance .case.vide {{ background: #FFFFFF; color: {ENCRE_SECONDAIRE}; }}
.ligne-concordance .verdict {{ font-variant-numeric: tabular-nums; font-size: .9rem; white-space: nowrap; }}
.ligne-concordance .verdict.franchi {{ font-weight: 700; }}
.fiche-plat {{ border: 2px solid {ENCRE}; padding: .6rem .75rem .5rem; margin: .2rem 0 .9rem; }}
.fiche-plat .nom {{ font-family: "Archivo Condensed", Archivo, sans-serif; font-weight: 800; font-size: 1.45rem; line-height: 1.05;
  border-bottom: {FILET_GROUPE}px solid {ENCRE}; padding-bottom: .3rem; margin-bottom: .35rem; }}
.fiche-plat .details {{ font-size: .92rem; color: {ENCRE_SECONDAIRE}; }}
.fiche-plat .code {{ display: flex; align-items: flex-end; justify-content: space-between; gap: .8rem; margin-top: .4rem; flex-wrap: wrap; }}
.fiche-plat .modifie {{ font-size: .9rem; font-weight: 600; }}
.fiche-plat a {{ color: {ENCRE}; font-size: .9rem; text-underline-offset: .18em; }}
/* le bouton « Chercher » est là : l'aide « Press Enter to submit form » recouvrirait un long lien */
.st-key-recherche [data-testid="InputInstructions"] {{ display: none; }}
.fiche-plat .note-fiche {{ font-size: .9rem; margin: .4rem 0 0; padding-top: .35rem; border-top: {FILET_LIGNE}px solid {ENCRE}; }}
/* Les trois colonnes du calculateur font au moins 24rem : sur un écran plus étroit (un vidéoprojecteur en 1280
   ou 1024 px), la colonne MR-Sort passe sous les deux autres, sur toute la largeur, au lieu de se tasser. */
@media (min-width: 640px) {{
  .st-key-calculateur [data-testid="stColumn"] {{ min-width: 24rem; }}
}}
/* Un groupe de boutons trop large pour sa colonne passe à la ligne, et ses boutons se partagent la largeur, au lieu
   de fuir à droite ; un groupe qui tient sur une ligne ne change pas. Deux boutons voisins se chevauchent d'un
   pixel, le dernier de chaque ligne aussi. */
.stButtonGroup div:has(> button) {{ flex-wrap: wrap; padding-right: 1px; }}
.stButtonGroup div:has(> button) > button,
.stButtonGroup div:has(> button) > button:last-child {{ flex-grow: 1; margin-right: -1px; }}
/* sur un téléphone, Streamlit empile les colonnes ; un tableau trop large y défile dans son cadre, sans être coupé */
.tableau {{ overflow-x: auto; }}
@media (max-width: 639px) {{
  /* une jauge de plus de dix cases (sucres, sel) passe à la ligne toutes les dix cases de 6 px, séparées de 1 px :
     le tableau des points tient alors dans l'écran */
  .jauge:has(> i:nth-child(11)) {{ flex-wrap: wrap; width: calc(10 * 6px + 9 * 1px); }}
  /* les trois choix d'« Apprentissage » ne tiennent pas sur une ligne : un par ligne, sur toute la largeur */
  .st-key-apprentissage div:has(> button) > button {{ flex-basis: 100%; }}
}}
/* un nom à ne pas couper en fin de ligne, comme « b2 (D′) » */
.insecable {{ white-space: nowrap; }}
/* La barre des onglets reste collée en haut de l'écran, sous l'en-tête de Streamlit (3,75rem, soit 60 px) : on change
   d'onglet sans remonter la page. La règle va sur la liste des onglets, car son parent contient aussi les panneaux. */
.stTabs [role="tablist"] {{ position: sticky; top: 3.75rem; z-index: 2; background: #FFFFFF; }}
::selection {{ background: {ENCRE}; color: #FFFFFF; }}
/* pas de mot seul en dernière ligne d'un paragraphe, et des titres coupés en lignes égales */
p {{ text-wrap: pretty; }}
.titre-page, .panneau .titre {{ text-wrap: balance; }}
</style>
"""

# Le codage EAN-13 des codes-barres : chaque chiffre devient 7 modules (1 = barre noire, 0 = espace).
# Les six chiffres de gauche sont écrits en code L ou G, selon le premier chiffre ; ceux de droite en code R.
CODE_L = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
CODE_G = ["0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111"]
CODE_R = ["1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100"]
PARITES = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]


# --- Mise en forme ---

def html(contenu):
    """Affiche un bloc HTML (titres, panneaux, tableaux au style Verso)."""
    st.html(contenu)


def texteHtml(texte):
    """Texte placé dans une balise : on échappe < > & (les apostrophes restent lisibles)."""
    return escape(str(texte), quote=False)


def nombre(valeur, decimales=0):
    """Écrit un nombre à la française : virgule décimale, espace fine entre les milliers."""
    texte = f"{valeur:,.{decimales}f}"
    return texte.replace(",", " ").replace(".", ",")


def tableHtml(colonnes, lignes):
    """
    Tableau au style Verso. colonnes = [(titre, clé, genre)], avec genre « texte » ou
    « nombre » ; les valeurs sont des textes déjà mis en forme. La clé « _classe » d'une
    ligne lui donne une classe CSS : « groupe » (filet épais au-dessus), « total », « ecarte ».
    """
    entete = "".join(f"<th class='{genre}'>{texteHtml(titre)}</th>" for titre, _, genre in colonnes)
    corps = ""
    for ligne in lignes:
        cases = "".join(f"<td class='{genre}'>{ligne.get(cle, '')}</td>" for _, cle, genre in colonnes)
        corps += f"<tr class='{ligne.get('_classe', '')}'>{cases}</tr>"
    return f"<div class='tableau'><table class='verso'><thead><tr>{entete}</tr></thead><tbody>{corps}</tbody></table></div>"


def bandeNutriscore(label):
    """La bande des cinq lettres du Nutri-Score, la lettre obtenue en grand."""
    lettres = "".join(f"<span class='pastille-{lettre}{' choisie' if lettre == label else ''}'>{lettre}</span>"
                      for lettre in COULEURS_CLASSES)
    return f"<div class='bande' aria-label='Nutri-Score {label}'>{lettres}</div>"


def panneau(titre, sousTitre=""):
    """L'en-tête d'un panneau : filet épais, titre en Archivo Condensed, sous-titre facultatif."""
    sous = f"<div class='sous-titre'>{texteHtml(sousTitre)}</div>" if sousTitre else ""
    return f"<div class='panneau'><div class='titre'>{texteHtml(titre)}</div>{sous}</div>"


def jaugeHtml(points, maximum, groupe=""):
    """
    La jauge des points d'une composante : une case par point possible, pleine pour chaque
    point obtenu. groupe : « negatif » (cases rouges) ou « positif » (cases vertes) ; sans
    groupe, les cases pleines sont noires.
    """
    cases = "".join("<i class='point'></i>" if numero < points else "<i></i>" for numero in range(maximum))
    classes = f"jauge {groupe}" if groupe else "jauge"
    return f"<span class='{classes}' aria-hidden='true'>{cases}</span>"


def motifEan13(code):
    """
    Le motif d'un code-barres EAN-13 : 95 modules, 1 pour une barre, 0 pour un espace.
    Renvoie None si le code n'a pas 13 chiffres ou si sa clé de contrôle est fausse.
    """
    if len(code) != 13 or not code.isdigit():
        return None
    chiffres = [int(caractere) for caractere in code]
    somme = sum(chiffre * (3 if rang % 2 else 1) for rang, chiffre in enumerate(chiffres[:12]))
    if (10 - somme % 10) % 10 != chiffres[12]:
        return None
    motif = "101"                                            # garde de gauche
    for rang, chiffre in enumerate(chiffres[1:7]):
        motif += CODE_L[chiffre] if PARITES[chiffres[0]][rang] == "L" else CODE_G[chiffre]
    motif += "01010"                                         # garde du milieu
    for chiffre in chiffres[7:]:
        motif += CODE_R[chiffre]
    return motif + "101"                                     # garde de droite


def codeBarresSvg(code, module=2, hauteur=46):
    """
    Le code-barres EAN-13 d'un plat, en SVG, avec ses chiffres dessous. Les barres de garde
    descendent plus bas, comme sur un emballage. Un code qui n'est pas un EAN-13 valide est
    simplement écrit en chiffres.
    """
    motif = motifEan13(code)
    if motif is None:
        return f"<span class='details'>Code {texteHtml(code)}</span>"
    marge = 9 * module                                       # la zone blanche à gauche, où s'écrit le premier chiffre
    gardes = set(range(0, 3)) | set(range(45, 50)) | set(range(92, 95))
    barres = ""
    for position, module_noir in enumerate(motif):
        if module_noir == "1":
            longueur = hauteur + 6 if position in gardes else hauteur
            barres += f"<rect x='{marge + position * module}' y='0' width='{module}' height='{longueur}'/>"
    chiffres = (f"<text x='{marge - 3}' y='{hauteur + 12}' text-anchor='end'>{code[0]}</text>"
                f"<text x='{marge + 24 * module}' y='{hauteur + 12}' text-anchor='middle'>{code[1:7]}</text>"
                f"<text x='{marge + 71 * module}' y='{hauteur + 12}' text-anchor='middle'>{code[7:]}</text>")
    largeur = marge + 95 * module + 2 * module
    return (f"<svg width='{largeur}' height='{hauteur + 16}' viewBox='0 0 {largeur} {hauteur + 16}' role='img' "
            f"aria-label='Code-barres {code}'><g fill='{ENCRE}'>{barres}</g>"
            f"<g font-family='Archivo, sans-serif' font-size='11' fill='{ENCRE}'>{chiffres}</g></svg>")


def codeBarresImage(code):
    """
    Le code-barres en image : Streamlit retire les balises SVG de st.html, mais garde une
    image dont la source est le SVG lui-même, encodé en base 64.
    """
    svg = codeBarresSvg(code)
    if not svg.startswith("<svg"):
        return svg
    svg = svg.replace("<svg ", "<svg xmlns='http://www.w3.org/2000/svg' ", 1)
    donnees = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"<img alt='Code-barres {texteHtml(code)}' src='data:image/svg+xml;base64,{donnees}'>"


def fichePlatHtml(plat, modifie, notes=()):
    """
    La fiche du produit dont on part, comme le haut d'un emballage : nom, marque, quantité,
    NOVA, additifs, code-barres et lien vers Open Food Facts. Si la saisie s'écarte du
    produit, la fiche le dit. notes : des phrases ajoutées sous la fiche (le type proposé par
    OFF, son résultat, les valeurs manquantes ou estimées).
    """
    details = ", ".join(morceau for morceau in [plat.get("marque"), plat.get("quantite"),
                                                f"NOVA {plat['nova']}" if plat.get("nova") else "",
                                                f"{plat['additifs']} additif{'s' if plat.get('additifs', 0) > 1 else ''}"
                                                if plat.get("additifs") is not None else ""] if morceau)
    note = ("<span class='modifie'>Valeurs modifiées : ce n'est plus exactement ce produit.</span>" if modifie
            else f"<a href='{texteHtml(plat['url'])}' target='_blank'>Voir la fiche sur Open Food Facts</a>")
    lignes = "".join(f"<p class='note-fiche'>{texteHtml(phrase)}</p>" for phrase in notes)
    return (f"<div class='fiche-plat'><div class='nom'>{texteHtml(plat['nom'])}</div>"
            f"<div class='details'>{texteHtml(details)}</div>"
            f"<div class='code'>{codeBarresImage(str(plat['code']))}{note}</div>{lignes}</div>")


def barresDeConcordanceHtml(detail, modele, plat):
    """
    Les barres de concordance d'un plat : pour chaque profil, de b5 (A′) à b2 (D′), une case
    par critère, de largeur égale à son poids. La case est noire quand le plat vaut au moins le
    profil sur ce critère, et la somme des cases noires est la concordance, comparée à λ.
    Chaque ligne porte aussi sa description en toutes lettres, pour les lecteurs d'écran.
    """
    lam = modele["lam"]
    lignes = ""
    for numero in range(len(modele["profils"]) - 1, -1, -1):
        profil = modele["profils"][numero]
        cases, passent = "", []
        for critere in modele["criteres"]:
            passe = concordancePartielle(plat[critere], profil[critere], sensDuCritere(critere, modele)) == 1
            if passe:
                passent.append(CRITERES[critere][0].lower())
            largeur = 100 * modele["poids"][critere]
            sigle = critere if largeur >= 6 else ""
            cases += (f"<span class='case {'pleine' if passe else 'vide'}' style='width:{largeur:.2f}%' "
                      f"title='{texteHtml(CRITERES[critere][0])}, poids {nombre(modele['poids'][critere], 3)}'>{sigle}</span>")
        franchi = detail["franchis"][numero]
        valeur = nombre(detail["concordances"][numero], 3)
        verdict = f"{valeur} ≥ {nombre(lam, 1)}, franchi" if franchi else f"{valeur} < {nombre(lam, 1)}"
        description = (f"{PROFILS[numero]}, le seuil de {nomDeClasse(numero + 1)} : le plat vaut au moins le profil sur "
                       f"{', '.join(passent) or 'aucun critère'}, concordance {valeur}, {'franchi' if franchi else 'non franchi'}")
        lignes += (f"<div class='ligne-concordance' role='img' aria-label='{texteHtml(description)}'>"
                   f"<span class='profil'>{nomDuProfil(numero)}</span><div class='barre'>{cases}</div>"
                   f"<span class='verdict{' franchi' if franchi else ''}'>{texteHtml(verdict)}</span></div>")
    return f"<div class='concordances'>{lignes}</div>"


# --- Données ---

@st.cache_data(show_spinner=False)
def baseDesPlats():
    """Lit la base de plats préparés, ou renvoie une liste vide si elle n'est pas construite."""
    if not FICHIER_BASE.exists():
        return []
    return lireBase(FICHIER_BASE)


@st.cache_data(show_spinner=False)
def baseEtendue():
    """Lit la base étendue (375 plats), ou renvoie une liste vide si elle n'est pas construite."""
    if not FICHIER_BASE_ETENDUE.exists():
        return []
    return lireBase(FICHIER_BASE_ETENDUE)


@st.cache_data(show_spinner=False)
def resultatsDuProjet():
    """Lit resultats/resultats_projet.json, ou renvoie un dictionnaire vide."""
    if not FICHIER_RESULTATS.exists():
        return {}
    return json.loads(FICHIER_RESULTATS.read_text(encoding="utf-8"))


@st.cache_data(ttl=3600, max_entries=200, show_spinner="Lecture de la fiche sur Open Food Facts…")
def ficheMemorisee(code):
    """
    La fiche d'un produit (ficheEnDirect : le cache, sinon OFF), gardée une heure en mémoire.
    Une erreur lève LookupError, que Streamlit ne garde pas : la recherche suivante réessaie.
    """
    reponse, erreur = ficheEnDirect(code)
    if erreur:
        raise LookupError(erreur)
    return reponse


def exemplesDisponibles():
    """
    Les plats dont on peut partir : les deux exemples du sujet, les plats de la base, classe
    par classe, puis ceux que la base étendue ajoute.
    """
    exemples = {}
    for numero, exemple in EXEMPLES_SUJET.items():
        exemples[f"Exemple du sujet ({numero}) : {exemple['nom']}"] = exemple["produit"]
    for plat in sorted(baseDesPlats(), key=lambda p: (p["label"], p["nom"].lower())):
        exemples[f"Base, classe {plat['label']} : {nomEtMarque(plat)}"] = plat
    ajout = [plat for plat in baseEtendue() if plat.get("lot") == LOT_AJOUT]
    for plat in sorted(ajout, key=lambda p: (p["label"], p["nom"].lower())):
        exemples[f"Base étendue, classe {plat['label']} : {nomEtMarque(plat)}"] = plat
    return exemples


def nomEtMarque(plat):
    """« Nom (marque) », ou le nom seul quand la marque manque (une case vide de l'Excel vaut None)."""
    return f"{plat['nom']} ({plat['marque']})" if plat.get("marque") else plat["nom"]


def platDeDepart(exemples):
    """
    Le libellé du plat du premier affichage, parmi les exemples : la Poêlée Fermière, le plat
    suivi par la soutenance du 30/10 (un plat préparé, avec sa fiche) ; sans la base, l'exemple
    de la fig. 6 du sujet.
    """
    for libelle, plat in exemples.items():
        if plat.get("code") == PLAT_DE_DEPART:
            return libelle
    for libelle in exemples:
        if libelle.startswith("Exemple du sujet (figure 6)"):
            return libelle


# --- Calculateur ---

def recopierExemple():
    """
    Recopie les sept composantes de l'exemple choisi dans les champs de saisie : on revient
    au cas général, et le produit cherché sur OFF s'efface, avec la recherche qui l'a trouvé.
    Quand on vide le choix (la croix de la liste), il n'y a rien à recopier : les valeurs
    saisies restent.
    """
    if st.session_state["exemple"] is None:
        return
    valeurs = exemplesDisponibles()[st.session_state["exemple"]]
    for composante in COMPOSANTES:
        st.session_state[f"saisie_{composante}"] = float(valeurs[composante])
    st.session_state["categorie"] = "general"
    st.session_state["produitCherche"] = None
    st.session_state["messageRecherche"] = None
    st.session_state["recherche"] = ""                       # la recherche précédente ne parle plus de ce plat
    st.session_state["resultatsRecherche"] = {}
    st.session_state.pop("choixRecherche", None)


def valeursDuProduit(produit):
    """
    Les valeurs d'un produit cherché, telles que les champs les reçoivent : une valeur absente
    vaut 0, une valeur au-delà du maximum d'un champ est ramenée à ce maximum, et les
    édulcorants sont un oui ou un non.
    """
    valeurs = {cle: min(float(produit[cle] or 0.0), CHAMPS[cle][1]) for cle in COMPOSANTES + ["lipides"]}
    valeurs["edulcorants"] = bool(produit["edulcorants"])
    return valeurs


def ouvrirProduit(code):
    """
    Ouvre un produit d'OFF : ses valeurs vont dans les champs, son type (proposé par OFF) dans
    la liste des types, et « Partir d'un plat » se vide. Un produit introuvable laisse un message.
    """
    try:
        produit = produitDepuisFiche(ficheMemorisee(code))
    except LookupError as erreur:
        st.session_state["messageRecherche"] = str(erreur)
        return
    st.session_state["produitCherche"] = produit
    st.session_state["messageRecherche"] = None
    for cle, valeur in valeursDuProduit(produit).items():
        st.session_state[f"saisie_{cle}"] = valeur
    st.session_state["categorie"] = produit["categorie"]
    st.session_state["exemple"] = None


def revenirAuProduit():
    """
    Le bouton « Revenir aux valeurs du produit » : le produit cherché se rouvre (ses valeurs et
    le type proposé par OFF), ou l'exemple choisi se recopie (ses valeurs, au cas général).
    Rechoisir le même plat dans la liste ne suffirait pas : Streamlit ne réagit qu'à un changement.
    """
    produit = st.session_state.get("produitCherche")
    if produit:
        ouvrirProduit(produit["code"])
    else:
        recopierExemple()


def chercherProduit():
    """
    Le bouton « Chercher » : un code-barres ou un lien ouvre le produit ; un nom donne la liste
    des produits trouvés (rechercherParNom : le cache, puis OFF), où l'on choisit.
    """
    texte = st.session_state.get("recherche") or ""
    st.session_state["messageRecherche"] = None
    st.session_state["resultatsRecherche"] = {}
    code = codeDepuisSaisie(texte)
    if code:
        ouvrirProduit(code)
        return
    chiffres = texte.replace(" ", "").strip()
    if chiffres.isdigit():                         # que des chiffres, mais pas de 8 à 14 : un code-barres mal recopié
        st.session_state["messageRecherche"] = (f"Un code-barres a de 8 à 14 chiffres : « {texte.strip()} » en a "
                                                f"{len(chiffres)}. Vérifiez-le sous les barres de l'emballage.")
        return
    if not motsDeLaRecherche(texte):
        st.session_state["messageRecherche"] = "Saisissez un code-barres, le lien d'une fiche Open Food Facts ou un nom de produit."
        return
    resultats, erreur = rechercherParNom(texte)
    if not resultats:
        st.session_state["messageRecherche"] = erreur or f"Aucun produit trouvé pour « {texte.strip()} »."
        return
    if erreur:
        st.session_state["messageRecherche"] = "Open Food Facts n'a pas répondu : seules les fiches gardées sont proposées."
    st.session_state["resultatsRecherche"] = {
        f"{r['nom']} ({r['marque']}), {r['code']}" if r["marque"] else f"{r['nom']}, {r['code']}": r["code"]
        for r in resultats}


def choisirResultat():
    """Choisir un produit dans les résultats d'une recherche par nom l'ouvre."""
    choix = st.session_state.get("choixRecherche")
    if choix is not None:
        ouvrirProduit(st.session_state["resultatsRecherche"][choix])


def sectionRecherche():
    """La recherche d'un produit : le champ, le bouton « Chercher », le message, et les résultats d'un nom."""
    with st.form("formulaireRecherche", border=False):
        with st.container(horizontal=True, vertical_alignment="bottom"):
            st.text_input("Code-barres, lien Open Food Facts ou nom", key="recherche",
                          placeholder="3257982125116, un lien de fiche, ou « poêlée fermière »")
            st.form_submit_button("Chercher", key="chercher", on_click=chercherProduit)
    if st.session_state.get("messageRecherche"):
        html(f"<p class='erreur'>{texteHtml(st.session_state['messageRecherche'])}</p>")
    resultats = st.session_state.get("resultatsRecherche") or {}
    if resultats:
        st.selectbox("Produits trouvés", list(resultats), key="choixRecherche", index=None, on_change=choisirResultat,
                     placeholder=f"{len(resultats)} produit{'s' if len(resultats) > 1 else ''} : choisir")


def notesDuProduit(produit, categorie, calcul, modifie):
    """
    Les phrases de la fiche d'un produit cherché sur OFF : le type proposé (et la réserve de la
    FAQ pour un plat composé), le résultat d'OFF comparé au nôtre, et les valeurs manquantes ou
    estimées. Range aussi l'accord avec OFF dans st.session_state["accordOff"] (lu par les tests).
    """
    notes = []
    if categorie == produit["categorie"]:
        raison = produit["raisonCategorie"]
        if produit["platPrepare"] and categorie in TYPES_DE_LA_FAQ_HORS_PLATS_COMPOSES:
            raison += " La FAQ du Nutri-Score laisse les plats composés au cas général : changez le type si besoin."
        notes.append(raison)
    else:
        notes.append(f"Type changé à la main : Open Food Facts proposait « {CATEGORIES[produit['categorie']].lower()} ».")

    off = produit["nutriscoreOff"]
    st.session_state["accordOff"] = None
    if off is None:
        notes.append("Open Food Facts ne calcule pas le Nutri-Score de ce produit.")
    elif not modifie and categorie == produit["categorie"]:
        accord = calcul["label"] == off["label"] and (calcul["score"] is None or calcul["score"] == off["score"])
        st.session_state["accordOff"] = accord
        score = f", score {off['score']}" if off["score"] is not None else ""
        notes.append(f"Open Food Facts : {off['label']}{score}, "
                     + ("le même résultat que notre calcul." if accord else f"et notre calcul donne {calcul['label']}."))

    libelles = ", ".join(LIBELLES[cle].lower() for cle in produit["manquantes"])
    if libelles:
        notes.append(f"Non déclaré : {libelles}. Compté 0, comme le fait Open Food Facts.")
    libelles = ", ".join(LIBELLES[cle].lower() for cle in produit["estimees"])
    if libelles:
        notes.append(f"Estimé par Open Food Facts, absent du tableau nutritionnel : {libelles}.")
    return notes


def saisieModifiee(plat, origine, categorie):
    """
    Vrai si la saisie s'écarte des valeurs d'origine (un produit cherché ou un exemple) : les
    sept composantes, plus les lipides d'une matière grasse et les édulcorants d'une boisson,
    qui comptent aussi dans le calcul de ces types.
    """
    cles = COMPOSANTES + (["lipides"] if categorie == "matieresGrasses" else [])
    modifie = any(abs(plat[cle] - float(origine.get(cle) or 0.0)) > 1e-6 for cle in cles)
    if categorie == "boisson":
        modifie = modifie or plat["edulcorants"] != bool(origine.get("edulcorants"))
    return modifie


def sectionSaisie():
    """
    La composition du produit : la recherche, le choix d'un exemple, le type de produit, puis
    les champs des sept composantes (plus les lipides des matières grasses et les édulcorants
    des boissons). La fiche du produit cherché, ou du plat de la base, s'affiche au-dessus des
    champs. Renvoie (produit saisi, type de produit).
    """
    categorie = st.session_state.get("categorie", "general")
    quantite = "100 mL" if categorie == "boisson" else "100 g"
    html(panneau(f"Composition pour {quantite}",
                 "Cherchez un produit, partez d'un plat, ou saisissez les valeurs du tableau nutritionnel."))
    sectionRecherche()
    st.selectbox("Partir d'un plat", list(exemplesDisponibles()), key="exemple", on_change=recopierExemple,
                 index=None, placeholder="Choisir un exemple du sujet ou un plat de la base")
    st.selectbox("Type de produit", list(CATEGORIES), format_func=CATEGORIES.get, key="categorie")
    zoneFiche = st.container()                     # la fiche dépend des valeurs saisies : on la remplit après les champs
    plat = {}
    for composante in COMPOSANTES:
        pas, maximum, decimales = CHAMPS[composante]
        plat[composante] = st.number_input(f"{LIBELLES[composante]} ({UNITES[composante]})", min_value=0.0,
                                           max_value=maximum, step=pas, format=f"%.{decimales}f",
                                           help=AIDES.get(composante), key=f"saisie_{composante}")
    if categorie == "matieresGrasses":
        pas, maximum, decimales = CHAMPS["lipides"]
        plat["lipides"] = st.number_input("Lipides (g)", min_value=0.0, max_value=maximum, step=pas,
                                          format=f"%.{decimales}f", key="saisie_lipides")
    if categorie == "boisson":
        plat["edulcorants"] = st.checkbox("Contient des édulcorants non nutritifs", key="saisie_edulcorants")
    st.session_state["avertissementSaisie"] = None                    # lu par les tests
    if categorie == "matieresGrasses" and plat["lipides"] < plat["sa"]:
        message = (f"Les acides gras saturés ({nombre(plat['sa'], 1)} g) ne peuvent pas dépasser les lipides "
                   f"({nombre(plat['lipides'], 1)} g) : corrigez l'une des deux valeurs.")
        st.session_state["avertissementSaisie"] = message
        html(f"<p class='erreur'>{texteHtml(message)}</p>")
    st.caption("Le sel compte pour le Nutri-Score de 2023 ; le sodium vaut sel\u00a0/\u00a02,5.")   # « sel / 2,5 » ne se coupe pas

    # Le produit dont on part : un produit cherché sur OFF (son type d'origine est celui proposé par OFF),
    # ou un exemple choisi dans la liste (au cas général). Sa fiche dit si la saisie s'en écarte.
    produit = st.session_state.get("produitCherche")
    choisi = exemplesDisponibles().get(st.session_state.get("exemple") or "")
    st.session_state["platChoisi"] = choisi if choisi and "code" in choisi else None    # lu par les tests
    st.session_state["accordOff"] = None
    origine, typeDOrigine = (valeursDuProduit(produit), produit["categorie"]) if produit else (choisi, "general")
    modifie = bool(origine) and saisieModifiee(plat, origine, categorie)
    st.session_state["valeursModifiees"] = modifie                                     # lu par les tests
    # Le nom du plat, repris par le pas à pas : le libellé d'un exemple s'écrit « Base, classe B : nom (marque) »
    if produit:
        nomDuPlat = nomEtMarque(produit)
    elif choisi:
        nomDuPlat = st.session_state["exemple"].split(" : ", 1)[1]
    else:
        nomDuPlat = "Un produit saisi à la main"
    st.session_state["nomDuPlat"] = nomDuPlat + (", valeurs modifiées" if modifie else "")
    if produit:
        notes = notesDuProduit(produit, categorie, scoreNutriscore(plat, categorie=categorie), modifie)
        with zoneFiche:
            html(fichePlatHtml(produit, modifie, notes))
    elif st.session_state["platChoisi"]:
        with zoneFiche:
            html(fichePlatHtml(choisi, modifie))
    # Rechoisir le même plat dans la liste ne rend pas ses valeurs (Streamlit ne réagit qu'à un changement) :
    # ce bouton le fait, type compris
    if origine and (modifie or categorie != typeDOrigine):
        with zoneFiche:
            st.button("Revenir aux valeurs du produit", key="revenirAuProduit", on_click=revenirAuProduit)
    return plat, categorie


def lignesDesPoints(plat, resultat):
    """
    Les lignes du tableau des points, comme dans les fig. 6 et 7 : l'en-tête des points
    négatifs (repère − rouge, total N), leurs composantes, puis l'en-tête des points positifs
    (repère + vert, total P) et leurs composantes. Les lignes et leurs maximums suivent le
    type de produit (composantesDeLaCategorie) ; les jauges prennent la couleur de leur groupe.
    """
    composantes = composantesDeLaCategorie(resultat["categorie"])
    groupes = [("negatif", "−", "Points négatifs N", resultat["N"]), ("positif", "+", "Points positifs P", resultat["P"])]
    lignes = []
    for groupe, signe, titre, total in groupes:
        membres = [ligne for ligne in composantes if ligne["groupe"] == groupe]
        lignes.append({"composante": f"<span class='signe {groupe}' aria-hidden='true'>{signe}</span>{titre}",
                       "points": f"{total} / {sum(ligne['maximum'] for ligne in membres)}",
                       "_classe": "groupe total" if groupe == "positif" else "total"})
        for ligne in membres:
            cle, maximum = ligne["cle"], ligne["maximum"]
            compte = cle != "pr" or resultat["proteinesComptees"]
            valeur = resultat["valeurs"][cle]
            texte = ("oui" if valeur else "non") if cle == "edulcorants" else f"{nombre(valeur, DECIMALES[cle])} {ligne['unite']}"
            lignes.append({
                "composante": texteHtml(ligne["libelle"]),
                "valeur": texte,
                "points": f"{jaugeHtml(resultat['points'][cle], maximum, groupe)}{resultat['points'][cle]} / {maximum}",
                "_classe": "" if compte else "ecarte",
            })
    return lignes


def panneauNutriscore(plat, categorie="general"):
    """
    Le panneau du Nutri-Score : la bande des lettres, le score, le détail des points et la règle
    des protéines, avec les règles du type de produit. Une eau est classée A, sans calcul.
    """
    resultat = scoreNutriscore(plat, categorie=categorie)
    st.session_state["nutriscore"] = resultat          # lu par les tests de l'interface
    html(panneau("Nutri-Score", f"Algorithme de 2023 : {CATEGORIES[categorie].lower()}. "
                                "Plus le score est bas, meilleur est le produit."))
    if resultat["score"] is None:
        valeur, legende = "—", "les eaux sont classées A, sans calcul"
    else:
        valeur, legende = nombre(resultat["score"]), f"score = N − P = {resultat['N']} − {resultat['P']}"
    html(f"<div class='resultat'>{bandeNutriscore(resultat['label'])}"
         f"<div class='score'><div class='valeur'>{valeur}</div><div class='legende'>{legende}</div></div></div>")
    if resultat["points"]:
        quantite = "Pour 100 mL" if categorie == "boisson" else "Pour 100 g"
        colonnes = [("Composante", "composante", "texte"), (quantite, "valeur", "nombre"), ("Points", "points", "nombre")]
        html(tableHtml(colonnes, lignesDesPoints(plat, resultat)))
        html(f"<p class='note'>{texteHtml(resultat['raison'][0].upper() + resultat['raison'][1:])}.</p>")


# --- Modèles MR-Sort (question 3.5) ---

def modelesDisponibles():
    """
    Les modèles MR-Sort que l'on peut choisir, en couples (base, apprentissage), dans l'ordre de
    MODELES_APPRIS : ceux qui sont dans le JSON, et les poids appris d'une base construite, qui
    s'apprennent vite (modeleAppris).
    """
    return [(base, apprentissage) for (base, apprentissage), (cle, fichier) in MODELES_APPRIS.items()
            if cle in resultatsDuProjet() or (apprentissage == "poids" and fichier.exists())]


def libelleDuModele(base, apprentissage):
    """Le nom d'un modèle appris, avec les mots des deux choix du calculateur : « 375 plats, tout appris »."""
    return f"{base} plats, {LIBELLES_APPRENTISSAGES[apprentissage].lower()}"


def apprentissageParDefaut():
    """
    L'apprentissage proposé d'abord, sur les 375 plats : celui qui range le mieux des plats
    jamais vus en validation croisée (7 critères, λ = 0,6), parmi ceux qui sont calculés ;
    sans validation croisée, les poids appris.
    """
    lignes = [ligne for ligne in resultatsDuProjet().get("validationCroisee", {}).get("modeles", [])
              if ligne["nom"] == "sept" and ligne["lam"] == 0.6 and ("375", ligne["mode"]) in modelesDisponibles()]
    if not lignes:
        return "poids"
    return max(lignes, key=lambda ligne: ligne["exactitudeMoyenne"])["mode"]


@st.cache_data(show_spinner="Apprentissage des poids…")
def modeleAppris(nom, lam, base="125", apprentissage="poids"):
    """
    Le modèle MR-Sort appris sur une base (les 375 plats de la base étendue, ou les 125 du
    30/10) par un apprentissage (MODELES_APPRIS) : celui de resultats_projet.json s'il y est,
    avec les intervalles de ses poids ; sinon, pour les poids appris seulement, on l'apprend
    (départagé par la plus grande marge pour la base étendue). Renvoie (modèle, intervalles),
    ou (None, None) s'il n'est pas calculé.
    """
    cle, fichier = MODELES_APPRIS[(base, apprentissage)]
    for modele in resultatsDuProjet().get(cle, {}).get("modeles", []):
        if modele["nom"] == nom and modele["lam"] == lam:
            regle = {"criteres": modele["criteres"], "poids": modele["poids"], "profils": modele["profils"], "lam": lam}
            return regle, modele.get("intervalles")
    if not fichier.exists() or apprentissage != "poids":
        return None, None
    criteres = CRITERES_SEPT if nom == "sept" else CRITERES_TROIS
    resultat = approximerNutriscore(lireBase(fichier), criteres, lam, "poids", departage="marge" if base == "375" else None)
    return resultat["modele"], None


def nomDuProfil(numero):
    """
    Le nom d'un profil avec la classe qu'il ouvre : « b5 (A′) ». Le profil bk est le seuil de la
    classe Ck (projet_mrsort.PROFILS) : un plat qui le franchit est au moins dans cette classe.
    """
    return f"{PROFILS[numero]} ({nomDeClasse(numero + 1)})"


def tableauDesParametres(modele, intervalles=None):
    """
    Le tableau modifiable d'un modèle : une ligne par critère, avec son poids, ses poids possibles
    (de même exactitude sur la base, non modifiables) s'ils sont connus, et ses quatre profils.
    """
    lignes = []
    for critere in modele["criteres"]:
        ligne = {"Critère": f"{CRITERES[critere][0]} ({CRITERES[critere][1]})",
                 "Sens": "moins, c'est mieux" if sensDuCritere(critere, modele) == "min" else "plus, c'est mieux",
                 "Poids": modele["poids"][critere]}
        if intervalles:
            bas, haut = intervalles[critere]
            ligne["Poids possibles"] = f"{nombre(bas, 3)} à {nombre(haut, 3)}"
        for numero, valeurs in enumerate(modele["profils"]):
            ligne[nomDuProfil(numero)] = valeurs[critere]
        lignes.append(ligne)
    return pd.DataFrame(lignes)


def modeleDuTableau(tableau, modele):
    """
    Relit le tableau modifié par l'utilisateur. Renvoie (modèle, messages, valide) : les poids
    sont ramenés à une somme de 1 si besoin, et les profils doivent rester ordonnés.
    """
    messages = []
    poids = {c: max(0.0, float(tableau["Poids"][i])) for i, c in enumerate(modele["criteres"])}
    somme = sum(poids.values())
    if somme == 0:
        return modele, ["Donnez un poids positif à au moins un critère."], False
    if abs(somme - 1) > 0.001:
        messages.append(f"Les poids font {nombre(somme, 3)} au total : ils sont ramenés à 1 pour le calcul.")
        poids = {c: valeur / somme for c, valeur in poids.items()}
    profils = [{c: float(tableau[nomDuProfil(numero)][i]) for i, c in enumerate(modele["criteres"])}
               for numero in range(len(PROFILS))]
    valide = True
    for critere in modele["criteres"]:
        for numero in range(len(PROFILS) - 1):                 # chaque profil doit valoir au moins le précédent
            ecart = profils[numero + 1][critere] - profils[numero][critere]
            if (sensDuCritere(critere, modele) == "max" and ecart < 0) or (sensDuCritere(critere, modele) == "min" and ecart > 0):
                messages.append(f"{CRITERES[critere][0]} : {nomDuProfil(numero + 1)} doit être au moins aussi bon que "
                                f"{nomDuProfil(numero)}. Corrigez l'une des deux valeurs pour voir la classe.")
                valide = False
    return dict(modele, poids=poids, profils=profils), messages, valide


def classeModeleHtml(numero, indicatif=False):
    """
    La classe d'un modèle MR-Sort : un cadre noir, la lettre et son prime, une barre de la couleur
    de la classe. Indicative (un produit hors du domaine des modèles), son cadre est en pointillés.
    """
    classe = nomDeClasse(numero)
    return (f"<div class='classe-modele{' indicatif' if indicatif else ''}' "
            f"aria-label='Classe {classe}{', indicative' if indicatif else ''}'><span class='lettre'>{classe}</span>"
            f"<span class='barre' style='background:{couleurClasse(classe)}'></span></div>")


def classeModelePetiteHtml(numero, indicatif=False):
    """La classe d'un modèle MR-Sort en petit, dans une ligne de texte : le cadre noir (en pointillés si indicative), la lettre et sa barre."""
    classe = nomDeClasse(numero)
    return (f"<span class='classe-petite{' indicatif' if indicatif else ''}' "
            f"aria-label='Classe {classe}{', indicative' if indicatif else ''}'><span class='lettre'>{classe}</span>"
            f"<span class='barre' style='background:{couleurClasse(classe)}'></span></span>")


def ligneDeLEditeur(titre, lam, libelle, classe, indicatif=False, sansClasse=None):
    """
    La ligne de titre de l'éditeur d'un modèle : le modèle, λ, son apprentissage (libelle, par
    libelleDuModele), et la classe du plat avec ces paramètres. On la voit changer en modifiant
    un poids, sans remonter jusqu'au panneau MR-Sort. classe : le numéro de la classe, ou None
    (profils non ordonnés, ou une eau : sansClasse dit alors pourquoi) ; indicatif : un produit
    hors du domaine.
    """
    debut = f"<span><strong>{texteHtml(titre)}</strong>, λ = {nombre(lam, 1)}, {texteHtml(libelle)} :</span>"
    if classe is None:
        raison = sansClasse or "pas de classe tant que les profils ne sont pas ordonnés."
        return f"<div class='sous-titre-editeur'>{debut}<span>{texteHtml(raison)}</span></div>"
    return f"<div class='sous-titre-editeur'>{debut}<span>classe</span>{classeModelePetiteHtml(classe, indicatif)}</div>"


def accordAvecLeNutriscore(classe, labelNutriscore, categorie="general", horsDomaine=False):
    """
    Ce que la classe d'un modèle dit face au Nutri-Score : « comme le Nutri-Score », ou « le
    Nutri-Score dit B ». Hors du domaine des modèles, la classe est « à titre indicatif », et la
    comparaison ne reste que pour un produit du cas général, qui suit le même calcul.
    """
    comparaison = "comme le Nutri-Score" if lettreDeClasse(classe) == labelNutriscore else f"le Nutri-Score dit {labelNutriscore}"
    if not horsDomaine:
        return comparaison
    return "à titre indicatif" + (f" ; {comparaison}" if categorie == "general" else "")


def phraseDeFranchissement(detail, lam):
    """
    Explique la classe par les seuils : le profil franchi le plus haut, nommé par la classe qu'il
    ouvre (bk est le seuil de Ck), puis le suivant, qui ne l'est pas.
    """
    classe = detail["classe"]
    morceaux = []
    if classe >= 1:
        morceaux.append(f"franchit le seuil de {nomDeClasse(classe)} ({PROFILS[classe - 1]}, concordance "
                        f"{nombre(detail['concordances'][classe - 1], 3)} ≥ λ = {nombre(lam, 1)})")
    if classe < len(PROFILS):
        suivant = f"({PROFILS[classe]}, {nombre(detail['concordances'][classe], 3)} < {nombre(lam, 1)})"
        if classe >= 1:
            morceaux.append(f"pas celui de {nomDeClasse(classe + 1)} {suivant}")
        else:
            morceaux.append(f"ne franchit pas le seuil de {nomDeClasse(classe + 1)} {suivant}")
    texte = ", ".join(morceaux)
    return texte[0].upper() + texte[1:] + "."


def revenirAuxParametresAppris(nom):
    """Le bouton « Revenir aux paramètres appris » : un nouvel éditeur repart du modèle appris."""
    st.session_state[f"version_{nom}"] = st.session_state.get(f"version_{nom}", 0) + 1


MODELES = [("sept", "MR-Sort à 7 critères"), ("trois", "MR-Sort à 3 critères")]


def enteteMRSort(nom, titre, base="125", apprentissage="poids"):
    """L'en-tête du panneau d'un modèle : son titre, sa base et son apprentissage, et le choix du seuil λ. Renvoie λ."""
    plats = "375 plats" if base == "375" else "les 125 plats"
    if apprentissage == "profils":
        sousTitre = f"Appris sur {plats} : poids des points maximaux du Nutri-Score, profils appris."
    elif apprentissage == "complet":
        sousTitre = f"Appris sur {plats} : poids et profils, appris tour à tour tant que le modèle progresse."
    elif base == "375":
        sousTitre = "Appris sur 375 plats : profils par les médianes, poids départagés par la plus grande marge."
    else:
        sousTitre = "Appris sur les 125 plats du 30/10 : profils par les médianes, poids par programme linéaire."
    html(panneau(titre, sousTitre))
    return st.segmented_control("Seuil majoritaire λ", SEUILS_MAJORITAIRES, default=SEUILS_MAJORITAIRES[0],
                                required=True, format_func=lambda valeur: nombre(valeur, 1), key=f"lam_{nom}")


def configurationDeLEditeur():
    """
    Les colonnes numériques de l'éditeur d'un modèle : le poids (positif, modifiable au
    dix-millième) et les quatre profils, au format du navigateur (« localized ») : une virgule
    décimale dans un navigateur en français, comme le reste de l'interface.
    """
    configuration = {"Poids": st.column_config.NumberColumn(min_value=0.0, step=0.0001, format="localized")}
    for numero in range(len(PROFILS)):
        configuration[nomDuProfil(numero)] = st.column_config.NumberColumn(format="localized")
    return configuration


def editeurMRSort(nom, lam, base="125", apprentissage="poids"):
    """
    L'éditeur des paramètres d'un modèle : poids et profils, partis du modèle appris, avec ses
    poids possibles. Sa ligne de titre est écrite après, par ligneDeLEditeur, une fois la classe
    connue. Renvoie (modèle, messages, valide), ou None si le modèle n'est pas calculé.
    """
    appris, intervalles = modeleAppris(nom, lam, base, apprentissage)
    if appris is None:
        return None
    version = st.session_state.get(f"version_{nom}", 0)
    tableau = st.data_editor(tableauDesParametres(appris, intervalles),
                             key=f"editeur_{nom}_{lam}_{base}_{apprentissage}_{version}",
                             hide_index=True, disabled=["Critère", "Sens"] + (["Poids possibles"] if intervalles else []),
                             column_config=configurationDeLEditeur())
    st.button("Revenir aux paramètres appris", key=f"revenir_{nom}", on_click=revenirAuxParametresAppris, args=(nom,))
    return modeleDuTableau(tableau, dict(appris, lam=lam))


def resultatMRSort(nom, plat, labelNutriscore, edition, lam, base="125", avecNote=True, categorie="general",
                   horsDomaine=False, apprentissage="poids"):
    """
    La classe du plat pour un modèle, sa raison, et les barres de concordance de chaque profil,
    suivies de la note qui les explique si avecNote (elle vaut pour les deux modèles : on ne
    l'écrit qu'une fois). Hors du domaine des modèles, la classe est indicative ; une eau n'en
    a pas. Renvoie le numéro de la classe, ou None sans classe (une eau, base absente, profils
    non ordonnés).
    """
    if categorie == "eau":                              # le Nutri-Score classe une eau A sans calcul (raisonHorsDomaine)
        html("<p class='note'>Pas de classe MR-Sort pour une eau.</p>")
        return None
    if edition is None:
        st.info("Les modèles MR-Sort sont appris sur la base : lancez d'abord projet_base.py.")
        return None
    modele, messages, valide = edition
    for message in messages:
        html(f"<p class='erreur'>{texteHtml(message)}</p>")
    if not valide:
        return None
    detail = affecter(plat, modele)
    st.session_state[f"mrsort_{nom}"] = {"classe": detail["classe"], "lam": lam, "base": base,       # lu par les tests
                                         "apprentissage": apprentissage}
    appris = modeleAppris(nom, lam, base, apprentissage)[0]
    st.session_state["modelesAffiches"][nom] = {                                                  # lu par le pas à pas
        "modele": modele, "base": base, "apprentissage": apprentissage, "parametresModifies": not memesParametres(modele, appris)}
    classe = nomDeClasse(detail["classe"])
    accord = accordAvecLeNutriscore(classe, labelNutriscore, categorie, horsDomaine)
    html(f"<div class='verdict-modele'>{classeModeleHtml(detail['classe'], horsDomaine)}"
         f"<div class='texte'><strong>Classe {classe}</strong>, {accord}.<br>"
         f"{texteHtml(phraseDeFranchissement(detail, lam))}</div></div>")
    html(barresDeConcordanceHtml(detail, modele, plat))
    if avecNote:
        html("<p class='note'>Une case par critère, de largeur égale à son poids ; noire si le plat vaut au moins "
             "le profil. Le profil est franchi quand les cases noires pèsent au moins λ.</p>")
    return detail["classe"]


def choixDuModele():
    """
    Les deux choix du modèle MR-Sort : la base d'apprentissage (« Appris sur »), puis
    l'apprentissage, parmi ceux qui sont calculés pour cette base. Un choix qui n'existe pas
    pour la base choisie passe au premier qui existe. Renvoie (base, apprentissage).
    """
    disponibles = modelesDisponibles()
    bases = list(dict.fromkeys(base for base, apprentissage in disponibles))      # 375 d'abord, puis 125
    if not bases:
        return "125", "poids"
    if st.session_state.get("apprisSur") not in bases:
        st.session_state["apprisSur"] = bases[0]
    if len(bases) > 1:
        st.segmented_control("Appris sur", bases, format_func=LIBELLES_DES_BASES.get, required=True, key="apprisSur")
    base = st.session_state["apprisSur"]
    methodes = [apprentissage for autre, apprentissage in disponibles if autre == base]
    if st.session_state.get("apprentissage") not in methodes:
        st.session_state["apprentissage"] = methodes[0]
    st.segmented_control("Apprentissage", methodes, format_func=LIBELLES_APPRENTISSAGES.get, required=True,
                         key="apprentissage")
    return base, st.session_state["apprentissage"]


def raisonHorsDomaine(categorie, produit=None, exempleDuSujet=False):
    """
    Pourquoi la classe MR-Sort d'un produit n'est qu'indicative, ou None pour un plat préparé du
    cas général, le seul domaine de nos modèles : ils n'ont appris que des plats préparés. Une
    eau n'a pas de classe du tout. produit : le produit cherché sur OFF, s'il y en a un.
    """
    if categorie == "eau":
        return ("Une eau n'a pas de classe MR-Sort : le Nutri-Score la classe A sans calcul, et nos modèles n'ont "
                "appris que des plats préparés.")
    if categorie == "boisson":
        return ("Une boisson suit les barèmes des boissons du Nutri-Score (les yaourts à boire et les boissons lactées "
                "en font partie depuis 2023), alors que nos modèles n'ont appris que des plats préparés.")
    if categorie in REGLES_A_PART:
        return (f"Le Nutri-Score applique une règle à part {REGLES_A_PART[categorie]}, alors que nos modèles n'ont "
                "appris que des plats préparés du cas général.")
    if produit and not produit["platPrepare"]:
        return ("Pour Open Food Facts, ce produit n'est pas un plat préparé, alors que nos modèles n'ont appris que "
                "des plats préparés.")
    if exempleDuSujet:
        return ("Les exemples du sujet sont des céréales du petit-déjeuner, alors que nos modèles n'ont appris que "
                "des plats préparés.")
    return None


def ongletCalculateur():
    """
    L'onglet du consommateur : la saisie, le Nutri-Score et les deux modèles MR-Sort en trois
    colonnes (sur un écran étroit, la troisième passe dessous : voir STYLE), puis, sur toute la
    largeur, les paramètres modifiables des deux modèles. Les
    classes affichées en haut suivent les paramètres saisis en bas : les zones du haut sont
    réservées d'abord, et remplies une fois les paramètres lus.
    """
    st.session_state["modelesAffiches"] = {}         # les modèles affichés, tels qu'édités : le pas à pas les reprend
    with st.container(key="calculateur"):
        saisie, nutriscore, colonneModeles = st.columns(3, gap="medium")
    with saisie:
        plat, categorie = sectionSaisie()
    st.session_state["platAffiche"] = plat
    with nutriscore:
        panneauNutriscore(plat, categorie)

    # Nos modèles sont appris sur des plats préparés du cas général : au-delà, leur classe est indicative
    produit = st.session_state.get("produitCherche")
    exempleDuSujet = (st.session_state.get("exemple") or "").startswith("Exemple du sujet")   # des céréales
    raison = raisonHorsDomaine(categorie, produit, exempleDuSujet)
    horsDomaine = raison is not None
    st.session_state["horsDomaine"] = horsDomaine        # lu par les tests et par le pas à pas
    st.session_state["raisonHorsDomaine"] = raison
    zones, seuils = {}, {}
    with colonneModeles:
        base, apprentissage = choixDuModele()
        if horsDomaine:
            suite = "" if categorie == "eau" else " Leur classe est donnée à titre indicatif."
            html(f"<div class='hors-domaine'><div class='titre'>Hors du domaine de nos modèles</div>"
                 f"<p>{texteHtml(raison + suite)}</p></div>")
        for nom, titre in MODELES:
            zones[nom] = st.container()
            with zones[nom]:
                seuils[nom] = enteteMRSort(nom, titre, base, apprentissage)

    # Seuls les poids appris ont des poids possibles (leurs intervalles) : la phrase n'accompagne que leur colonne
    avecIntervalles = any(modeleAppris(nom, seuils[nom], base, apprentissage)[1] for nom, _ in MODELES)
    html(panneau("Paramètres des modèles MR-Sort",
                 "Modifiez un poids ou un profil : les classes ci-dessus suivent. Les poids sont ramenés à une somme de 1."
                 + (" Les poids possibles rangent aussi bien les plats de la base." if avecIntervalles else "")))
    editions, titres = {}, {}
    for nom, titre in MODELES:
        titres[nom] = st.container()                 # la ligne de titre de l'éditeur, avec la classe : remplie à la fin
        editions[nom] = editeurMRSort(nom, seuils[nom], base, apprentissage)

    label = st.session_state["nutriscore"]["label"]
    noteEcrite = False                               # la note des barres, sous le premier modèle qui en affiche
    for nom, titre in MODELES:
        with zones[nom]:
            classe = resultatMRSort(nom, plat, label, editions[nom], seuils[nom], base, avecNote=not noteEcrite,
                                    categorie=categorie, horsDomaine=horsDomaine, apprentissage=apprentissage)
        noteEcrite = noteEcrite or classe is not None
        if editions[nom] is not None:
            with titres[nom]:
                sansClasse = "pas de classe pour une eau." if categorie == "eau" else None
                html(ligneDeLEditeur(titre, seuils[nom], libelleDuModele(base, apprentissage), classe, horsDomaine, sansClasse))


# --- Base ---

def ongletBase():
    """
    L'onglet de la base : la base du 30/10 (125 plats) ou la base étendue (375 plats), avec
    leur répartition par classe, l'entonnoir des filtres, la vérification et le tableau.
    """
    bases = [base for base, plats in (("375", baseEtendue()), ("125", baseDesPlats())) if plats]
    if not bases:
        st.info("La base n'est pas encore construite : lancez projet_base.py.")
        return
    if len(bases) > 1:
        st.segmented_control("Base", bases, format_func=LIBELLES_DES_BASES.get, default=bases[0], required=True,
                             key="baseAffichee")
    choix = st.session_state.get("baseAffichee") or bases[0]
    plats = baseEtendue() if choix == "375" else baseDesPlats()
    resultats = resultatsDuProjet()
    infos = resultats.get("baseEtendue" if choix == "375" else "base")
    if choix == "375":
        sousTitre = "Les 125 plats du 30/10, plus 50 par classe tirés au hasard hors de cette base : 75 par classe."
    else:
        sousTitre = "Tirés d'Open Food Facts au hasard, 25 par classe du Nutri-Score de 2023."
    html(panneau(f"{len(plats)} plats préparés vendus en France", sousTitre))
    comptes = "".join(f"<div><span class='pastille-{lettre}'>{lettre}</span>"
                      f"{sum(1 for p in plats if p['label'] == lettre)} plats</div>" for lettre in COULEURS_CLASSES)
    html(f"<div class='comptes'>{comptes}</div>")

    gauche, droite = st.columns(2, gap="large")
    with gauche:
        if infos:
            html(panneau("Entonnoir des filtres", "Nombre de candidats restant après chaque étape."))
            lignes = [{"etape": texteHtml(etape[0].upper() + etape[1:]), "nombre": nombre(valeur)}
                      for etape, valeur in infos["entonnoir"].items()]
            html(tableHtml([("Étape", "etape", "texte"), ("Plats", "nombre", "nombre")], lignes))
    with droite:
        if "nutriscore" in resultats:
            # Pour la base étendue, la vérification porte sur tout son vivier : les plats retenus, tirés ou non
            etendue = choix == "375" and "vivierEtendu" in resultats["nutriscore"]
            verification = resultats["nutriscore"]["vivierEtendu"] if etendue else resultats["nutriscore"]
            st.session_state["verificationAffichee"] = verification          # lu par les tests
            html(panneau("Vérification du Nutri-Score",
                         f"{verification['reproduits']} plats sur {verification['total']}"
                         f"{' du vivier, tirés ou non' if etendue else ''} : notre calcul retrouve le score et "
                         f"le label d'Open Food Facts."))
            for ecart in verification["ecarts"]:
                html(f"<p class='note'>Écart : {texteHtml(ecart)}</p>")

    html(panneau("La base", "Les sept composantes pour 100 g, le Nutri-Score d'OFF, NOVA, additifs et Green-Score."))
    colonnes = ["nom", "marque", "label", "score", "en", "sa", "su", "so", "pr", "fi", "fr", "nova", "additifs", "green"]
    st.dataframe(
        [{cle: plat[cle] for cle in colonnes} for plat in plats],
        hide_index=True,
        column_config={
            "nom": "Nom", "marque": "Marque", "label": "Label", "score": "Score",
            "en": st.column_config.NumberColumn("Énergie (kJ)", format="%.0f"),
            "sa": st.column_config.NumberColumn("AGS (g)", format="%.1f"),
            "su": st.column_config.NumberColumn("Sucres (g)", format="%.1f"),
            "so": st.column_config.NumberColumn("Sel (g)", format="%.2f"),
            "pr": st.column_config.NumberColumn("Protéines (g)", format="%.1f"),
            "fi": st.column_config.NumberColumn("Fibres (g)", format="%.1f"),
            "fr": st.column_config.NumberColumn("Fruits, légumes (%)", format="%.0f"),
            "nova": "NOVA", "additifs": "Additifs",
            "green": st.column_config.NumberColumn("Green-Score", format="%.0f"),
        },
    )


# --- Pas à pas ---

@st.cache_data(max_entries=50, show_spinner=False)
def diagrammeDesProfils(modeleJson, platJson):
    """
    Le diagramme des profils (projet_figures.figureProfils) d'un modèle et d'un plat, en PNG.
    Les axes vont du 5e au 95e centile de la base ; un plat plus extrême reste au bord. Le
    modèle et le plat arrivent en JSON, pour que Streamlit garde l'image d'une saisie à l'autre.
    """
    import tempfile
    from pathlib import Path

    from projet_figures import etenduesDeLaBase, figureProfils

    modele, plat = json.loads(modeleJson), json.loads(platJson)
    etendues = etenduesDeLaBase(baseDesPlats(), modele["criteres"]) if baseDesPlats() else None
    with tempfile.TemporaryDirectory() as dossier:
        chemin = Path(dossier) / "profils.png"
        figureProfils(modele, plat, chemin, etendues=etendues)
        return chemin.read_bytes()


def memesParametres(modele, appris):
    """Vrai si le modèle édité garde les poids et les profils du modèle appris (à 1e-9 près)."""
    for critere in appris["criteres"]:
        if abs(modele["poids"][critere] - appris["poids"][critere]) > 1e-9:
            return False
        for profil, profilAppris in zip(modele["profils"], appris["profils"]):
            if abs(profil[critere] - profilAppris[critere]) > 1e-9:
                return False
    return True


def sousTitreDuPasAPas(nomDuPlat, libelle, lam, parametresModifies, horsDomaine=False):
    """
    Le sous-titre du pas à pas : le plat du calculateur (avec « valeurs modifiées » s'il y a
    lieu), le modèle (libelle, par libelleDuModele) et λ, puis « paramètres modifiés à la main »
    seulement si c'est le cas, et « classe indicative » pour un produit hors du domaine des modèles.
    """
    texte = f"{nomDuPlat}. Modèle « {libelle} », λ = {nombre(lam, 1)}"
    if parametresModifies:
        texte += ", paramètres modifiés à la main"
    texte += "."
    if horsDomaine:
        texte += " Hors du domaine de nos modèles : classe indicative."
    return texte


def ongletPasAPas():
    """
    MR-Sort pas à pas, pour le plat et le modèle du calculateur (tels qu'ils y sont saisis et
    édités) : 1. les profils, sur leur diagramme ; 2. les concordances partielles, critère par
    critère ; 3. la concordance face à chaque profil, comparée à λ ; 4. l'affectation, dans la
    classe du meilleur profil franchi (sujet, §2).
    """
    plat, modeles = st.session_state.get("platAffiche"), st.session_state.get("modelesAffiches") or {}
    if st.session_state.get("categorie") == "eau":
        html("<p class='note'>Pas de classe MR-Sort pour une eau : le pas à pas n'a rien à expliquer.</p>")
        return
    if not plat or not modeles:
        st.info("Le pas à pas suit le calculateur : il faut un modèle MR-Sort valide pour le plat saisi.")
        return
    noms = [nom for nom, titre in MODELES if nom in modeles]
    nom = st.segmented_control("Modèle", noms, format_func=lambda cle: dict(MODELES)[cle], default=noms[0],
                               required=True, key="pasAPasModele")
    modele, base = modeles[nom]["modele"], modeles[nom]["base"]
    etapes, classe = etapesDeLAffectation(plat, modele)
    nomDuPlat = st.session_state.get("nomDuPlat", "Un produit saisi à la main")
    st.session_state["pasAPas"] = {"nom": nom, "classe": classe, "etapes": len(etapes), "plat": nomDuPlat}  # lu par les tests
    criteres = modele["criteres"]
    html(panneau(f"{dict(MODELES)[nom]}, pas à pas",
                 sousTitreDuPasAPas(nomDuPlat, libelleDuModele(base, modeles[nom]["apprentissage"]), modele["lam"],
                                    modeles[nom]["parametresModifies"], st.session_state.get("horsDomaine", False))))

    seuils = ", ".join(f"<span class='insecable'>{nomDuProfil(numero)}</span>" for numero in range(len(PROFILS)))  # b2 (D′)…
    html("<div class='etape'>1. Les profils</div>"
         f"<p class='note'>Quatre profils séparent les cinq classes, et chacun porte la classe qu'il ouvre : {seuils}. "
         "Sur chaque axe, le mieux est en haut : le plat (en noir) vaut au moins un profil sur un critère quand il "
         "passe au-dessus de lui.</p>")
    # à sa taille de lecture, et non sur toute la largeur de l'écran
    st.image(diagrammeDesProfils(json.dumps(modele, sort_keys=True), json.dumps({c: plat[c] for c in criteres}, sort_keys=True)),
             width=760)
    lignes = []
    for critere in criteres:
        decimales = DECIMALES.get(critere, 1)
        ligne = {"critere": texteHtml(CRITERES[critere][0]), "poids": nombre(modele["poids"][critere], 3),
                 "plat": nombre(plat[critere], decimales)}
        for profil, valeurs in zip(PROFILS, modele["profils"]):
            ligne[profil] = nombre(valeurs[critere], decimales)
        lignes.append(ligne)
    html(tableHtml([("Critère", "critere", "texte"), ("Poids", "poids", "nombre"), ("Plat", "plat", "nombre")]
                   + [(nomDuProfil(numero), profil, "nombre") for numero, profil in enumerate(PROFILS)], lignes))

    html("<div class='etape'>2. Les concordances partielles</div>"
         "<p class='note'>Pour chaque critère et chaque profil : 1 si le plat vaut au moins le profil, 0 sinon. Moins "
         "c'est mieux pour l'énergie, les acides gras saturés, les sucres et le sel ; plus c'est mieux pour les autres.</p>")
    st.latex(r"c_j(a, b_k) = \begin{cases} 1 & \text{si } g_j(a) \geq g_j(b_k) \text{ (critère à maximiser)} \\ "
             r"1 & \text{si } g_j(a) \leq g_j(b_k) \text{ (critère à minimiser)} \\ 0 & \text{sinon} \end{cases}")
    lignes = [{"critere": texteHtml(CRITERES[critere][0]), **{etape["profil"]: str(etape["partielles"][critere]) for etape in etapes}}
              for critere in criteres]
    html(tableHtml([("Critère", "critere", "texte")] + [(f"c(a, {p})", p, "nombre") for p in PROFILS], lignes))

    html("<div class='etape'>3. La concordance</div>"
         f"<p class='note'>Face à chaque profil, on additionne les poids des critères qui votent pour le plat. Le plat "
         f"franchit le profil quand cette somme atteint λ = {nombre(modele['lam'], 1)}.</p>")
    st.latex(r"C(a, b_k) = \sum_j w_j \, c_j(a, b_k) \qquad a \, S \, b_k \iff C(a, b_k) \geq \lambda")
    lignes = []
    for numero, etape in enumerate(etapes):                  # les étapes vont de b2 à b5, comme PROFILS
        termes = " + ".join(nombre(modele["poids"][critere], 3) for critere in etape["pour"]) or "0"
        signe = "≥" if etape["franchi"] else "<"
        lignes.append({"profil": nomDuProfil(numero),
                       "pour": texteHtml(", ".join(CRITERES[c][0].lower() for c in etape["pour"]) or "aucun critère"),
                       "somme": f"{termes} = {nombre(etape['concordance'], 3)}",
                       "verdict": f"{signe} {nombre(modele['lam'], 1)}, {'franchi' if etape['franchi'] else 'non franchi'}",
                       "_classe": "total" if etape["franchi"] else ""})
    html(tableHtml([("Profil", "profil", "texte"), ("Critères qui votent pour le plat", "pour", "texte"),
                    ("Concordance", "somme", "nombre"), ("Verdict", "verdict", "nombre")], lignes))

    html("<div class='etape'>4. L'affectation</div>")
    st.latex(r"C_{MR}(a) = C_{k} \quad \text{pour le meilleur profil } b_k \text{ que le plat franchit}")
    franchis = [etape["profil"] for etape in etapes if etape["franchi"]]
    raison = (f"Le meilleur profil franchi est {franchis[-1]} : le plat est rangé en {nomDeClasse(classe)}."
              if franchis else f"Le plat ne franchit aucun profil : il est rangé en {nomDeClasse(classe)}.")
    label = st.session_state.get("nutriscore", {}).get("label")
    horsDomaine = st.session_state.get("horsDomaine", False)
    if horsDomaine:
        accord = " À titre indicatif : ce produit sort du domaine de nos modèles."
    else:
        accord = "" if not label else (" C'est la classe du Nutri-Score." if lettreDeClasse(nomDeClasse(classe)) == label
                                       else f" Le Nutri-Score dit {label}.")
    html(f"<div class='verdict-modele'>{classeModeleHtml(classe, horsDomaine)}<div class='texte'>{texteHtml(raison + accord)}</div></div>")


# --- Modèles ---

def enGras(texte, meilleur):
    """Le texte d'une case de tableau, en gras s'il est le meilleur de sa colonne."""
    return f"<strong>{texte}</strong>" if meilleur else texte


def lignesDuTableauDesModeles(lignes):
    """
    Les lignes du tableau de l'onglet Modèles, une par modèle appris sur la base : les plats bien
    rangés sur la base, puis sur les plats ajoutés (jamais vus), l'exactitude et « à une classe
    près » sur ces plats ajoutés. Le meilleur résultat de chaque colonne est en gras, ex aequo compris.
    """
    meilleurBase = max(ligne["base"]["bienRanges"] for ligne in lignes)
    meilleurAjout = max(ligne["ajout"]["bienRanges"] for ligne in lignes)
    meilleurAUneClasse = max(ligne["ajout"]["aUneClassePres"] for ligne in lignes)
    tableau = []
    for ligne in lignes:
        base, ajout = ligne["base"], ligne["ajout"]
        tableau.append({
            "criteres": f"{len(CRITERES_SEPT) if ligne['nom'] == 'sept' else len(CRITERES_TROIS)} critères",
            "apprentissage": texteHtml(LIBELLES_APPRENTISSAGES[ligne["mode"]]),
            "lam": nombre(ligne["lam"], 1),
            "base": enGras(f"{base['bienRanges']}/{base['total']}", base["bienRanges"] == meilleurBase),
            "ajout": enGras(f"{ajout['bienRanges']}/{ajout['total']}", ajout["bienRanges"] == meilleurAjout),
            "pourcentage": enGras(f"{nombre(100 * ajout['exactitude'], 1)} %", ajout["bienRanges"] == meilleurAjout),
            "classe": enGras(f"{nombre(100 * ajout['aUneClassePres'], 1)} %", ajout["aUneClassePres"] == meilleurAUneClasse),
        })
    return tableau


def lignesDeLaValidationCroisee(lignes):
    """
    Les lignes du tableau de la validation croisée, une par apprentissage : l'exactitude moyenne
    des parts, leur écart-type (en points), et « à une classe près » sur tous les plats. La
    meilleure exactitude et le meilleur « à une classe près » sont en gras, ex aequo compris.
    """
    meilleureMoyenne = max(ligne["exactitudeMoyenne"] for ligne in lignes)
    meilleurAUneClasse = max(ligne["comparaison"]["aUneClassePres"] for ligne in lignes)
    tableau = []
    for ligne in lignes:
        aUneClasse = ligne["comparaison"]["aUneClassePres"]
        tableau.append({
            "criteres": f"{len(CRITERES_SEPT) if ligne['nom'] == 'sept' else len(CRITERES_TROIS)} critères",
            "apprentissage": texteHtml(LIBELLES_APPRENTISSAGES[ligne["mode"]]),
            "lam": nombre(ligne["lam"], 1),
            "moyenne": enGras(f"{nombre(100 * ligne['exactitudeMoyenne'], 1)} %", ligne["exactitudeMoyenne"] == meilleureMoyenne),
            "ecart": f"{nombre(100 * ligne['ecartType'], 1)} points",
            "classe": enGras(f"{nombre(100 * aUneClasse, 1)} %", aUneClasse == meilleurAUneClasse),
        })
    return tableau


def phraseDuModeleExact(nombre, reponse, meilleur):
    """La réponse à la question 1 du sujet pour un jeu de critères : un modèle exact existe-t-il ?"""
    if reponse["existe"] is False and reponse["preuve"] == "paires inversées":
        return f"{nombre} critères : non. {reponse['paires']} paires de plats sont inversées, et MR-Sort est monotone."
    if reponse["existe"] is False:
        return f"{nombre} critères : non, le solveur le prouve."
    if reponse["existe"]:
        return f"{nombre} critères : oui, le solveur en trouve un."
    return (f"{nombre} critères : pas de réponse en {reponse['limiteSecondes'] // 60} minutes. Aucune paire n'est "
            f"inversée, et le meilleur modèle trouvé range {meilleur} plats sur 125.")


def ongletModeles():
    """
    L'onglet des modèles : les modèles appris sur les 125 plats de la base, comparés sur ces
    plats et sur les 250 plats que la base étendue ajoute (jamais vus) ; la réponse à la
    question 1 du sujet (un modèle exact existe-t-il ?) ; la courbe d'apprentissage.
    """
    resultats = resultatsDuProjet()
    if "generalisation" not in resultats:
        st.info("Les modèles se comparent sur la base étendue : lancez projet_base.py --etendue, puis projet_mrsort.py.")
        return
    lignes = resultats["generalisation"]["modeles"]
    st.session_state["lignesModeles"] = len(lignes)                  # lu par les tests
    html(panneau("Les modèles appris sur la base",
                 "Poids appris (profils fixés par les médianes), profils appris (poids fixés) et tout appris (les deux, "
                 "tour à tour), à 7 et 3 critères, λ = 0,6 et 0,7 : sur les 125 plats appris, puis sur les 250 plats "
                 "ajoutés, jamais vus."))
    html(tableHtml([("Critères", "criteres", "texte"), ("Apprentissage", "apprentissage", "texte"), ("λ", "lam", "nombre"),
                    ("Base : bien rangés", "base", "nombre"), ("Plats ajoutés : bien rangés", "ajout", "nombre"),
                    ("Exactitude, plats ajoutés", "pourcentage", "nombre"),
                    ("À une classe près, plats ajoutés", "classe", "nombre")], lignesDuTableauDesModeles(lignes)))
    html("<p class='note'>Les modèles appris sur les 375 plats ont appris les plats ajoutés : on ne peut pas les "
         "mesurer sur eux. La validation croisée les compare sans cela.</p>")

    croisee = resultats.get("validationCroisee")
    if croisee:
        html(panneau("Validation croisée sur les 375 plats",
                     f"{croisee['plis']} parts de 75 plats, 15 par classe : chaque plat est rangé par un modèle appris "
                     f"sur les 300 autres. Les profils s'apprennent en au plus {croisee['limiteSecondes'] // 60} minutes."))
        html(tableHtml([("Critères", "criteres", "texte"), ("Apprentissage", "apprentissage", "texte"), ("λ", "lam", "nombre"),
                        ("Exactitude moyenne", "moyenne", "nombre"), ("Écart entre les parts", "ecart", "nombre"),
                        ("À une classe près", "classe", "nombre")], lignesDeLaValidationCroisee(croisee["modeles"])))

    complet = resultats.get("modeleComplet")
    if complet:
        html(panneau("Un modèle exact existe-t-il ?", "La question 1 du sujet, sur les 125 plats de la base."))
        for nom, nombreDeCriteres in (("sept", len(CRITERES_SEPT)), ("trois", len(CRITERES_TROIS))):
            meilleur = max(ligne["base"]["bienRanges"] for ligne in lignes if ligne["nom"] == nom)
            html(f"<p class='note'>{texteHtml(phraseDuModeleExact(nombreDeCriteres, complet['exact'][nom], meilleur))}</p>")

    figure = FICHIER_RESULTATS.parent / "figures" / "courbe_apprentissage.png"
    if figure.exists():
        html(panneau("La courbe d'apprentissage", "Plus de plats appris aide un peu, puis plus guère : le plafond vient du modèle."))
        st.image(str(figure))


# --- Page ---

def main():
    """Affiche l'interface : le titre, puis les onglets."""
    st.set_page_config(page_title="Nutri-Score et MR-Sort", layout="wide")
    html(STYLE)
    if "saisie_en" not in st.session_state:           # premier affichage : un plat choisi dans la liste
        exemples = exemplesDisponibles()
        depart = platDeDepart(exemples)
        for composante in COMPOSANTES:
            st.session_state[f"saisie_{composante}"] = float(exemples[depart][composante])
        st.session_state["exemple"] = depart
    # Les valeurs de départ de la recherche et du type de produit ; les lipides et les édulcorants
    # n'ont un champ que pour leur type, et Streamlit oublie un champ qui n'est pas affiché
    for cle, valeur in {"categorie": "general", "produitCherche": None, "resultatsRecherche": {},
                        "messageRecherche": None, "saisie_lipides": 0.0, "saisie_edulcorants": False}.items():
        st.session_state.setdefault(cle, valeur)
    if modelesDisponibles():                           # par défaut : 375 plats, et le meilleur apprentissage
        st.session_state.setdefault("apprisSur", modelesDisponibles()[0][0])
        st.session_state.setdefault("apprentissage", apprentissageParDefaut())
    html("<div class='titre-page'>Nutri-Score et MR-Sort</div>"
         "<p class='chapo'>Calculez le Nutri-Score d'un produit, cherché sur Open Food Facts ou saisi à la main, "
         "et voyez comment un modèle de tri multicritère transparent, MR-Sort, range un plat préparé.</p>")
    calculateur, pasAPas, modeles, base = st.tabs(["Calculateur", "Pas à pas", "Modèles", "Base"])
    with calculateur:
        ongletCalculateur()
    with pasAPas:
        ongletPasAPas()
    with modeles:
        ongletModeles()
    with base:
        ongletBase()


if __name__ == "__main__":
    main()
