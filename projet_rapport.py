"""
projet_rapport.py : prépare le rapport LaTeX à partir des résultats.

Le rapport (rapport/rapport.tex) ne contient aucun chiffre écrit à la main : il cite des
macros, que ce script écrit dans rapport/chiffres.tex à partir de
resultats/resultats_projet.json. Les figures viennent de projet_figures.py.

    python3 projet_rapport.py                                     # chiffres.tex et figures
    cd rapport && latexmk -xelatex rapport.tex                    # le PDF

État : à écrire en phase 4 (à partir du 28/11).
"""


def ecrireChiffres(resultats, chemin):
    r"""Écrit une macro LaTeX par chiffre cité, par exemple \newcommand{\nbPlats}{125}."""
    raise NotImplementedError("phase 4")
