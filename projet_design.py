"""
projet_design.py : les jetons de design de la direction « Verso de l'emballage ».

Toutes les productions du projet (interface, slides, figures, rapport, fichiers Excel)
prennent ici leurs couleurs, leurs filets et leurs polices, pour rester cohérentes.

Le principe : chaque production se lit comme le verso d'un emballage, c'est-à-dire comme
un tableau nutritionnel bien composé. Le noir et blanc porte la structure, et la couleur
vient du Nutri-Score : ses classes, et ses points (rouge pour les points négatifs, vert
pour les positifs, comme dans les captures d'Open Food Facts des fig. 6 et 7 du sujet).

Les classes officielles (A à E) sont des pastilles pleines aux couleurs du Nutri-Score.
Les classes de nos modèles (A′ à E′) sont des cadres noirs avec une barre de couleur :
on ne peut pas confondre les deux.
"""

from pathlib import Path


# --- Couleurs ---

PAPIER = "#FFFFFF"            # le fond de toutes les productions
ENCRE = "#000000"             # un vrai noir, comme sur un tableau nutritionnel
TRAME = "#E9E9E6"             # gris clair des lignes alternées et des zones secondaires
ENCRE_SECONDAIRE = "#5C5C58"  # texte secondaire : légendes, unités, notes

# Les couleurs officielles des cinq classes du Nutri-Score
COULEURS_CLASSES = {"A": "#038141", "B": "#85BB2F", "C": "#FECB02", "D": "#EE8100", "E": "#E63E11"}

# La couleur de la lettre posée sur chaque classe : blanc sur les fonds foncés, noir sinon
LETTRE_SUR_CLASSE = {"A": "#FFFFFF", "B": "#000000", "C": "#000000", "D": "#000000", "E": "#FFFFFF"}

# Les points du Nutri-Score, comme dans les fig. 6 et 7 : les négatifs prennent le rouge de E,
# les positifs le vert de A. Ces couleurs remplissent des cases et des repères, jamais du texte :
# le rouge de E est trop clair pour un petit texte sur fond blanc.
COULEUR_NEGATIFS = COULEURS_CLASSES["E"]
COULEUR_POSITIFS = COULEURS_CLASSES["A"]


# --- Filets (épaisseurs en pixels) : ils codent la hiérarchie ---

FILET_PANNEAU = 8   # en tête d'un panneau : un bloc de résultat, une section
FILET_GROUPE = 4    # entre deux groupes d'un même panneau (points négatifs, points positifs)
FILET_LIGNE = 1     # entre deux lignes d'un tableau


# --- Polices : la seule famille Archivo (licence OFL), en instances statiques ---

DOSSIER_POLICES = Path(__file__).resolve().parent / "design" / "polices"

POLICE_TEXTE = "Archivo"                       # texte, tableaux, boutons
POLICE_TEXTE_DEMI_GRAS = "Archivo SemiBold"    # intertitres, en-têtes de tableau
POLICE_TITRE = "Archivo Condensed"             # en gras (graisse 800) : titres, lettres de classe, chiffres clés

# Les fichiers de chaque instance, rangés dans design/polices/
FICHIERS_POLICES = {
    "Archivo": "Archivo-Regular.ttf",
    "Archivo Italic": "Archivo-Italic.ttf",
    "Archivo SemiBold": "Archivo-SemiBold.ttf",
    "Archivo Bold": "Archivo-Bold.ttf",
    "Archivo Condensed": "ArchivoCondensed-ExtraBold.ttf",
}


def lettreDeClasse(classe):
    """Renvoie la lettre d'une classe sans son prime : « A′ » donne « A », « b » donne « B »."""
    return str(classe).strip().rstrip("′'").upper()


def couleurClasse(classe):
    """Renvoie la couleur officielle d'une classe (A à E, avec ou sans prime)."""
    return COULEURS_CLASSES[lettreDeClasse(classe)]


def couleurLettre(classe):
    """Renvoie la couleur de la lettre à poser sur la pastille d'une classe."""
    return LETTRE_SUR_CLASSE[lettreDeClasse(classe)]


# --- Fichiers Excel ---

def mettreEnFormeFeuille(feuille, largeurs, colonnesClasses=(), formats=None):
    """
    Met une feuille Excel au style « Verso » : en-tête noir à texte blanc, filet fin sous
    chaque ligne, volets figés sous l'en-tête, cellules de classe aux couleurs officielles.

    feuille : une feuille openpyxl dont la ligne 1 contient les en-têtes.
    largeurs : la largeur de chaque colonne, dans l'ordre (en caractères).
    colonnesClasses : les numéros (à partir de 1) des colonnes qui contiennent une classe.
    formats : un dictionnaire {numéro de colonne: format numérique Excel}, par exemple "0.0".
    """
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    formats = formats or {}
    filetFin = Side(style="thin", color=ENCRE[1:])
    filetEpais = Side(style="medium", color=ENCRE[1:])

    # Les largeurs des colonnes
    for numero, largeur in enumerate(largeurs, start=1):
        feuille.column_dimensions[get_column_letter(numero)].width = largeur

    # L'en-tête : noir, texte blanc, filet épais dessous
    for cellule in feuille[1]:
        cellule.font = Font(name=POLICE_TEXTE, bold=True, color=PAPIER[1:])
        cellule.fill = PatternFill("solid", fgColor=ENCRE[1:])
        cellule.alignment = Alignment(vertical="center", wrap_text=True)
        cellule.border = Border(bottom=filetEpais)
    feuille.row_dimensions[1].height = 32

    # Le corps : police du projet, filet fin sous chaque ligne, formats numériques
    for ligne in feuille.iter_rows(min_row=2):
        for cellule in ligne:
            cellule.font = Font(name=POLICE_TEXTE, color=ENCRE[1:])
            cellule.border = Border(bottom=filetFin)
            if cellule.column in formats:
                cellule.number_format = formats[cellule.column]
            if cellule.column in colonnesClasses and cellule.value:
                lettre = lettreDeClasse(cellule.value)
                if lettre in COULEURS_CLASSES:
                    cellule.fill = PatternFill("solid", fgColor=couleurClasse(lettre)[1:])
                    cellule.font = Font(name=POLICE_TEXTE, bold=True, color=couleurLettre(lettre)[1:])
                    cellule.alignment = Alignment(horizontal="center")

    # Les volets figés : l'en-tête et les deux premières colonnes restent visibles
    feuille.freeze_panes = "C2"


def mettreEnFormeNotice(feuille, largeur=110):
    """
    Met en forme une feuille de texte (la notice « lisez-moi ») : première ligne en titre,
    lignes commençant par « # » en intertitres, les autres en texte courant.
    """
    from openpyxl.styles import Alignment, Font

    feuille.column_dimensions["A"].width = largeur
    for numero, ligne in enumerate(feuille.iter_rows(), start=1):
        cellule = ligne[0]
        texte = str(cellule.value or "")
        if numero == 1:
            cellule.font = Font(name=POLICE_TITRE, bold=True, size=18, color=ENCRE[1:])
        elif texte.startswith("# "):
            cellule.value = texte[2:]
            cellule.font = Font(name=POLICE_TEXTE, bold=True, size=12, color=ENCRE[1:])
        else:
            cellule.font = Font(name=POLICE_TEXTE, size=11, color=ENCRE[1:])
        cellule.alignment = Alignment(wrap_text=True, vertical="top")
