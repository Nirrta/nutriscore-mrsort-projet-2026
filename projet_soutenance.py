"""
projet_soutenance.py : les textes de la soutenance, du Markdown au PDF.

Le dossier soutenance/ contient deux textes écrits en Markdown :
- texte_soutenance_1.md : le texte de l'oral, slide par slide, avec la durée et l'orateur
  de chaque slide, la démonstration pas à pas et les questions probables du jury ;
- dossier_soutenance_1.md : la démarche jusqu'à la soutenance intermédiaire.

Ce script les compile en PDF au style « Verso » du rapport (rapport/verso.sty) : pandoc
convertit le Markdown en LaTeX, une enveloppe ajoute la page de titre, puis XeLaTeX
compose le PDF. Il lit aussi le texte de l'oral slide par slide, pour les notes des slides
(slides_projet.py) et pour les tests.

    python3 projet_soutenance.py   # soutenance/texte_soutenance_1.pdf et soutenance/dossier_soutenance_1.pdf
"""

import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
DOSSIER_SOUTENANCE = DOSSIER / "soutenance"
TEXTE_ORAL = DOSSIER_SOUTENANCE / "texte_soutenance_1.md"
# Le texte de l'oral de chaque soutenance : la soutenance intermédiaire (30/10), puis la soutenance finale (27/11)
TEXTES_ORAUX = {1: TEXTE_ORAL, 2: DOSSIER_SOUTENANCE / "texte_soutenance_2.md"}
DOSSIER_DEMARCHE = DOSSIER_SOUTENANCE / "dossier_soutenance_1.md"

# L'en-tête d'une slide dans le texte de l'oral : « ## Slide 3 : la base (Daniel, 1 min 15) »
ENTETE_SLIDE = re.compile(r"^## Slide (\d+) : (.+) \((\w+), (\d+) min(?: (\d+))?\)$")


# --- Lecture du texte de l'oral ---

def lireEntete(markdown):
    """Sépare l'en-tête YAML (title, subtitle) du corps du texte. Renvoie (titre, sous-titre, corps)."""
    titre, sousTitre, corps = "", "", markdown
    if markdown.startswith("---\n"):
        entete, corps = markdown[4:].split("\n---\n", 1)
        for ligne in entete.splitlines():
            cle, _, valeur = ligne.partition(":")
            if cle.strip() == "title":
                titre = valeur.strip()
            elif cle.strip() == "subtitle":
                sousTitre = valeur.strip()
    return titre, sousTitre, corps


def slidesDuTexte(chemin=TEXTE_ORAL):
    """
    Lit le texte de l'oral et renvoie, pour chaque slide, un dictionnaire : numero, titre,
    orateur, duree (en secondes), texte (ce qu'on dit, en paragraphes) et transition.
    """
    lignes = chemin.read_text(encoding="utf-8").splitlines()
    slides, courante, partie = [], None, None
    for ligne in lignes:
        entete = ENTETE_SLIDE.match(ligne)
        if entete:
            numero, titre, orateur, minutes, secondes = entete.groups()
            courante = {"numero": int(numero), "titre": titre, "orateur": orateur,
                        "duree": 60 * int(minutes) + int(secondes or 0), "texte": [], "transition": ""}
            slides.append(courante)
            partie = None
        elif ligne.startswith("#"):
            courante, partie = None, None
        elif courante is not None:
            if ligne.startswith("**On dit :**"):
                partie = "texte"
            elif ligne.startswith("**Transition :**"):
                courante["transition"] = ligne.replace("**Transition :**", "").strip()
                partie = None
            elif ligne.startswith("**On montre :**"):
                partie = None
            elif partie == "texte" and ligne.strip():
                courante["texte"].append(ligne.strip())
    return slides


# --- Compilation en PDF ---

def empreinte(texte):
    """Les 16 premiers caractères de l'empreinte SHA-256 d'un texte : elle change dès qu'un caractère change."""
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()[:16]


def empreinteDuPdf(chemin):
    """
    L'empreinte rangée dans les mots-clés d'un PDF (« empreinte 0123… »), ou None. Chaque PDF de la
    soutenance porte celle de sa source : un test voit ainsi s'il n'a pas été refait.
    """
    from pypdf import PdfReader

    motsCles = (PdfReader(chemin).metadata or {}).get("/Keywords") or ""
    trouve = re.search(r"empreinte (\w+)", str(motsCles))
    return trouve.group(1) if trouve else None


def corpsLatex(markdown):
    """Convertit le corps Markdown en LaTeX avec pandoc."""
    resultat = subprocess.run(["pandoc", "--from", "markdown", "--to", "latex"], input=markdown,
                              capture_output=True, text=True, check=True)
    return resultat.stdout


def enveloppe(titre, sousTitre, corps, empreinteDuTexte=""):
    """
    Le document LaTeX complet : le style Verso, un bloc de titre, puis le corps. Les mots-clés du
    PDF portent l'empreinte du texte Markdown (empreinteDuPdf la relit).
    """
    return rf"""\documentclass[11pt]{{article}}
\usepackage{{verso}}
\hypersetup{{pdfkeywords={{empreinte {empreinteDuTexte}}}}}
\setcounter{{secnumdepth}}{{0}}
\begin{{document}}
\thispagestyle{{fancy}}
\rule{{\linewidth}}{{8pt}}\par\vspace{{8pt}}
{{\policeTitre\fontsize{{30}}{{34}}\selectfont {titre}\par}}
\vspace{{6pt}}
{{\policeDemiGras\fontsize{{14}}{{18}}\selectfont {sousTitre}\par}}
\vspace{{4pt}}
\rule{{\linewidth}}{{1pt}}\par
\vspace{{1.2em}}
{corps}
\end{{document}}
"""


def compiler(source, destination):
    """
    Compile un texte Markdown en PDF. La compilation se fait depuis soutenance/, pour que
    verso.sty trouve les polices dans ../design/polices/ ; les fichiers intermédiaires vont
    dans soutenance/construction/.
    """
    texte = source.read_text(encoding="utf-8")
    titre, sousTitre, corps = lireEntete(texte)
    construction = DOSSIER_SOUTENANCE / "construction"
    construction.mkdir(exist_ok=True)
    fichierTex = construction / (source.stem + ".tex")
    fichierTex.write_text(enveloppe(titre, sousTitre, corpsLatex(corps), empreinte(texte)), encoding="utf-8")
    environnement = dict(os.environ, TEXINPUTS=f"{DOSSIER / 'rapport'}//:")
    subprocess.run(["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "-quiet",
                    f"-outdir={construction.name}", f"{construction.name}/{fichierTex.name}"],
                   cwd=DOSSIER_SOUTENANCE, env=environnement, check=True, capture_output=True)
    shutil.copy(construction / (source.stem + ".pdf"), destination)


def main():
    """
    Compile le texte de l'oral de la soutenance demandée (et, pour la soutenance intermédiaire,
    le dossier de la démarche), puis affiche la durée de l'oral.
    """
    import argparse

    parseur = argparse.ArgumentParser(description="Les textes des soutenances, en PDF.")
    parseur.add_argument("--soutenance", type=int, choices=[1, 2], default=1)
    numero = parseur.parse_args().soutenance
    sources = (TEXTE_ORAL, DOSSIER_DEMARCHE) if numero == 1 else (TEXTES_ORAUX[2],)
    for source in sources:
        destination = source.with_suffix(".pdf")
        compiler(source, destination)
        print(f"{destination.relative_to(DOSSIER)} écrit")
    slides = slidesDuTexte(TEXTES_ORAUX[numero])
    duree = sum(slide["duree"] for slide in slides)
    print(f"Oral : {len(slides)} slides, {duree // 60} min {duree % 60:02d} s")


if __name__ == "__main__":
    main()
