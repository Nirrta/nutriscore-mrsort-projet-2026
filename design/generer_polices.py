"""
generer_polices.py : tire les instances statiques d'Archivo de sa police variable.

Archivo (Omnibus-Type, licence OFL) est distribuée par Google Fonts en police variable,
avec un axe de largeur (62 à 125) et un axe de graisse (100 à 900). PowerPoint, Excel et
LaTeX gèrent mal les polices variables : on en tire donc des instances statiques, avec
des noms de famille simples que tous ces logiciels comprennent.

Usage :
    python3 design/generer_polices.py <dossier des polices variables> design/polices
"""

import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer


# Chaque instance : (fichier, famille, style, largeur, graisse, italique).
# La famille et le style suivent la règle des logiciels de bureau : une famille regroupe au
# plus Regular, Italic, Bold et Bold Italic ; les autres graisses forment leur propre famille.
# La graisse ExtraBold (800) des titres est le « Bold » de la famille « Archivo Condensed » :
# PowerPoint ne retrouve pas une famille nommée « Archivo Condensed ExtraBold » (il la remplace
# par Calibri), alors qu'il retrouve « Archivo Condensed » en gras.
INSTANCES = [
    ("Archivo-Regular.ttf", "Archivo", "Regular", 100, 400, False),
    ("Archivo-Italic.ttf", "Archivo", "Italic", 100, 400, True),
    ("Archivo-Bold.ttf", "Archivo", "Bold", 100, 700, False),
    ("Archivo-SemiBold.ttf", "Archivo SemiBold", "Regular", 100, 600, False),
    ("ArchivoCondensed-ExtraBold.ttf", "Archivo Condensed", "Bold", 75, 800, False),
]


def renommer(police, famille, style, graisse, largeur, italique):
    """Réécrit les noms et les indicateurs de style d'une instance."""
    nomComplet = famille if style == "Regular" else f"{famille} {style}"
    nomPostScript = nomComplet.replace(" ", "-") if style != "Regular" else f"{famille.replace(' ', '')}-Regular"
    noms = police["name"]
    for identifiant in (16, 17, 21, 22, 25):      # noms typographiques et variables : inutiles ici
        noms.removeNames(nameID=identifiant)
    for identifiant, valeur in ((1, famille), (2, style), (3, f"{nomPostScript};Archivo"), (4, nomComplet), (6, nomPostScript)):
        noms.setName(valeur, identifiant, 3, 1, 0x409)     # Windows, Unicode, anglais
        noms.setName(valeur, identifiant, 1, 0, 0)          # Macintosh, Roman, anglais

    gras = style in ("Bold", "Bold Italic")
    os2 = police["OS/2"]
    os2.usWeightClass = graisse
    os2.usWidthClass = 3 if largeur == 75 else 5         # 3 : condensé ; 5 : normal
    os2.fsSelection &= ~0b1100001                        # retire italique, gras et normal
    if italique:
        os2.fsSelection |= 0b1
    if gras:
        os2.fsSelection |= 0b100000
    if not italique and not gras:
        os2.fsSelection |= 0b1000000
    police["head"].macStyle = (1 if gras else 0) | (2 if italique else 0)


def main():
    """Écrit chaque instance de INSTANCES dans le dossier de destination."""
    source, destination = Path(sys.argv[1]), Path(sys.argv[2])
    destination.mkdir(parents=True, exist_ok=True)
    for fichier, famille, style, largeur, graisse, italique in INSTANCES:
        variable = TTFont(source / ("Archivo-Italic[wdth,wght].ttf" if italique else "Archivo[wdth,wght].ttf"))
        police = instancer.instantiateVariableFont(variable, {"wdth": largeur, "wght": graisse})
        if "DSIG" in police:
            del police["DSIG"]                           # la signature ne vaut plus après l'instanciation
        renommer(police, famille, style, graisse, largeur, italique)
        police.save(destination / fichier)
        print(f"{fichier} : {famille}, {style}, largeur {largeur}, graisse {graisse}")


if __name__ == "__main__":
    main()
