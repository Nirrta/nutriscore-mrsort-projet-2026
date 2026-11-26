"""
slides_projet.py : les slides des soutenances (python-pptx), au style « Verso de l'emballage ».

    python3 slides_projet.py --soutenance 1   # ven. 30/10/2026 : base, Nutri-Score, modèles MR-Sort
    python3 slides_projet.py --soutenance 2   # ven. 27/11/2026 : le SuperNutri-score (phase 3)

Le sujet demande, pour la soutenance intermédiaire (15 minutes au plus) : la base de données
construite, l'interface du Nutri-Score, un modèle d'approximation à 7 ou 3 critères appliqué
à la base, et la comparaison avec le Nutri-Score. Pour la soutenance finale (15 minutes au
plus) : le SuperNutri-score, les réponses aux questions de la section 3.4 et l'interface.

Tout le contenu chiffré vient du code : resultats/resultats_projet.json, la base et les
figures de projet_figures.py. Aucun résultat n'est écrit en dur ici. Chaque slide a un titre
qui énonce le constat, et ses notes donnent la trame de l'oral.

Comme au TP2, la génération s'arrête si un titre ne tient pas sur une ligne ou si un texte
déborde, et les numéros de page sont écrits à la fin.

Polices : Archivo Condensed en gras (graisse 800) pour les titres, Archivo pour le texte (design/polices).
Elles doivent être installées sur l'ordinateur de soutenance ; sinon PowerPoint les remplace.
"""

import argparse
import json
from statistics import median

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

import projet_figures as figures
from projet_base import DOSSIER, FICHIER_BASE, FICHIER_RESULTATS, lireBase
from projet_design import (COULEUR_NEGATIFS, COULEUR_POSITIFS, COULEURS_CLASSES, DOSSIER_POLICES, ENCRE,
                           ENCRE_SECONDAIRE, FICHIERS_POLICES, LETTRE_SUR_CLASSE, PAPIER, TRAME, couleurClasse,
                           lettreDeClasse)
from projet_mrsort import CRITERES, CRITERES_SEPT, PROFILS, affecter, concordancePartielle, nomDeClasse, sensDuCritere
from projet_nutriscore import EXEMPLES_SUJET, NEGATIFS, POINTS_MAX, POSITIFS, SEUIL_PROTEINES, scoreNutriscore
from projet_supernutri import PILIERS, SENS_DES_CLASSES, ecartsAuNutriscore, valeursDuPlat


# --- Format, polices et textes fixes ---

LARGEUR, HAUTEUR = 13.333, 7.5            # pouces (16:9)
MARGE = 0.7
TITRE, TEXTE, DEMI_GRAS = "Archivo Condensed", "Archivo", "Archivo SemiBold"   # TITRE toujours en gras
POLICE_DE_REPLI = "Arial"                 # Archivo n'a pas de lettres grecques : λ s'écrit dans cette police
GROUPE = "Daniel Avila Haroche, Anis Islam Rezig, YIN Biyao"     # repris du TP2 : à confirmer avant la séance
COURS = "Transparence des algorithmes pour la décision, M2 MIAGE ID-SITN, Brice Mayag"
SORTIES = {1: DOSSIER / "resultats" / "slides_soutenance_intermediaire.pptx",
           2: DOSSIER / "resultats" / "slides_soutenance_finale.pptx"}
DOSSIER_FIGURES = DOSSIER / "resultats" / "figures"


# --- Petits outils ---

def couleur(hexa):
    """Couleur PowerPoint à partir d'un code « #RRGGBB »."""
    return RGBColor.from_string(hexa.lstrip("#"))


def nombre(valeur, decimales=0):
    """Écrit un nombre à la française : virgule décimale, espace insécable entre les milliers."""
    return f"{valeur:,.{decimales}f}".replace(",", " ").replace(".", ",")


def dateFrancaise(dateIso):
    """Écrit une date AAAA-MM-JJ à la française : 28 octobre 2026."""
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
            "novembre", "décembre"]
    annee, numeroMois, jour = (int(morceau) for morceau in dateIso.split("-"))
    return f"{jour}\u00a0{mois[numeroMois - 1]} {annee}"


def pourcentage(part, decimales=0):
    """Écrit une part (entre 0 et 1) en pourcentage à la française."""
    return f"{nombre(100 * part, decimales)} %"


def m(texte, police=TEXTE, taille=18, teinte=ENCRE, gras=False):
    """Un morceau de texte et son style."""
    return texte, {"police": police, "taille": taille, "teinte": teinte, "gras": gras}


def typographie(texte):
    """
    Le texte tel qu'il s'affiche : l'apostrophe typographique, et une espace insécable avant « ; »,
    « : », « ? », « ! », « % » et « » », et après « « » : aucun de ces signes ne commence une ligne.
    """
    texte = texte.replace("'", "’")
    for signe in (";", ":", "?", "!", "%", "»"):
        texte = texte.replace(f" {signe}", f"\u00a0{signe}")
    return texte.replace("« ", "«\u00a0")


def ajouterMorceau(paragraphe, texte, style):
    """Ajoute un morceau de texte stylé à un paragraphe, avec la typographie de l'affichage."""
    morceau = paragraphe.add_run()
    morceau.text = typographie(texte)
    morceau.font.name = style["police"]
    morceau.font.size = Pt(style["taille"])
    morceau.font.bold = style["gras"] or style["police"] == TITRE     # la graisse 800 est le gras d'Archivo Condensed
    morceau.font.color.rgb = couleur(style["teinte"])


def ecrire(cadre, paragraphes, alignement=PP_ALIGN.LEFT, apres=0):
    """
    Écrit des paragraphes (listes de morceaux m(...)) dans un cadre de texte. Chaque λ est
    écrit dans la police de repli, car Archivo n'a pas de lettres grecques.
    """
    for numero, morceaux in enumerate(paragraphes):
        paragraphe = cadre.paragraphs[0] if numero == 0 else cadre.add_paragraph()
        paragraphe.alignment = alignement
        paragraphe.space_after = Pt(apres)
        for texte, style in morceaux:
            for rang, partie in enumerate(texte.split("λ")):
                if rang > 0:
                    ajouterMorceau(paragraphe, "λ", dict(style, police=POLICE_DE_REPLI))
                if partie:
                    ajouterMorceau(paragraphe, partie, style)


def boite(diapo, x, y, largeur, hauteur, paragraphes, nom, ancrage=MSO_ANCHOR.TOP, **options):
    """Zone de texte sans marge intérieure : le texte s'aligne sur les filets."""
    forme = diapo.shapes.add_textbox(Inches(x), Inches(y), Inches(largeur), Inches(hauteur))
    forme.name = nom
    cadre = forme.text_frame
    cadre.word_wrap = True
    cadre.auto_size = MSO_AUTO_SIZE.NONE
    cadre.margin_left = cadre.margin_right = cadre.margin_top = cadre.margin_bottom = 0
    cadre.vertical_anchor = ancrage
    ecrire(cadre, paragraphes, **options)
    return forme


def rectangle(diapo, x, y, largeur, hauteur, nom, fond=None, trait=None, epaisseur=1.0):
    """Rectangle plat, sans style de thème ni ombre."""
    forme = diapo.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(largeur), Inches(hauteur))
    forme.name = nom
    style = forme._element.find(qn("p:style"))
    if style is not None:
        forme._element.remove(style)
    if fond:
        forme.fill.solid()
        forme.fill.fore_color.rgb = couleur(fond)
    else:
        forme.fill.background()
    if trait:
        forme.line.color.rgb = couleur(trait)
        forme.line.width = Pt(epaisseur)
    else:
        forme.line.fill.background()
    forme.shadow.inherit = False
    return forme


def filet(diapo, x, y, largeur, epaisseur, nom):
    """Un filet noir horizontal de l'épaisseur donnée (en points) : la structure du style Verso."""
    return rectangle(diapo, x, y, largeur, epaisseur / 72, nom, fond=ENCRE)


def pastille(diapo, x, y, cote, lettre, nom, modele=False):
    """
    Une classe : pastille pleine aux couleurs officielles pour le Nutri-Score, ou cadre noir
    avec la lettre, son prime et une barre de couleur pour un modèle MR-Sort.
    """
    if modele:
        rectangle(diapo, x, y, cote, cote, nom, trait=ENCRE, epaisseur=2.5)
        rectangle(diapo, x, y + cote * 0.84, cote, cote * 0.16, nom + " (barre)", fond=couleurClasse(lettre))
        boite(diapo, x, y, cote, cote * 0.84, [[m(f"{lettre}′", TITRE, cote * 34, ENCRE)]], nom + " (lettre)",
              ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.CENTER)
    else:
        rectangle(diapo, x, y, cote, cote, nom, fond=couleurClasse(lettre))
        boite(diapo, x, y, cote, cote, [[m(lettre, TITRE, cote * 40, LETTRE_SUR_CLASSE[lettre])]], nom + " (lettre)",
              ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.CENTER)


def image(diapo, chemin, x, y, largeur=None, hauteur=None, nom="Figure"):
    """Place une image ; on donne sa largeur ou sa hauteur, l'autre suit les proportions."""
    forme = diapo.shapes.add_picture(str(chemin), Inches(x), Inches(y),
                                     Inches(largeur) if largeur else None, Inches(hauteur) if hauteur else None)
    forme.name = nom
    return forme


def proportions(chemin):
    """Le rapport largeur / hauteur d'une image."""
    from PIL import Image

    with Image.open(chemin) as fichier:
        return fichier.width / fichier.height


def notes(diapo, texte):
    """Les notes de l'orateur : la trame de l'oral pour cette slide."""
    diapo.notes_slide.notes_text_frame.text = texte


# --- Mesure du texte, pour qu'aucun texte ne déborde ---

FICHIERS_MESURE = {TITRE: FICHIERS_POLICES["Archivo Condensed"], TEXTE: FICHIERS_POLICES["Archivo"],
                   DEMI_GRAS: FICHIERS_POLICES["Archivo SemiBold"], (TEXTE, True): FICHIERS_POLICES["Archivo Bold"]}
policesOuvertes = {}


def largeurTexte(texte, police=TEXTE, taille=18, gras=False):
    """Largeur du texte en pouces, mesurée avec le fichier de la police."""
    from PIL import ImageFont

    cle = (police, True) if gras and (police, True) in FICHIERS_MESURE else police
    if cle not in policesOuvertes:
        policesOuvertes[cle] = ImageFont.truetype(str(DOSSIER_POLICES / FICHIERS_MESURE[cle]), 100)
    return policesOuvertes[cle].getlength(texte) / 100 * taille / 72


def nombreDeLignes(texte, largeur, taille, police=TEXTE, gras=False):
    """Nombre de lignes d'un texte coupé aux espaces (pas aux espaces insécables), avec 3 % de marge."""
    courant, lignes = "", 1
    for mot in [mot for mot in typographie(texte).split(" ") if mot]:      # coupé comme à l'affichage
        essai = mot if not courant else courant + " " + mot
        if courant and largeurTexte(essai, police, taille, gras) > largeur * 0.97:
            lignes += 1
            courant = mot
        else:
            courant = essai
    return lignes


def hauteurParagraphes(paragraphes, largeur, apres=0):
    """Hauteur (pouces) d'une suite de paragraphes m(...) : environ 1,2 fois la taille par ligne."""
    hauteur = 0
    for morceaux in paragraphes:
        texte = "".join(morceau for morceau, _ in morceaux)
        taille = max(style["taille"] for _, style in morceaux)
        style = morceaux[-1][1]
        hauteur += nombreDeLignes(texte, largeur, taille, style["police"], style["gras"]) * 1.22 * taille / 72
        hauteur += apres / 72
    return hauteur


def verifierUneLigne(nom, texte, police, taille, largeur):
    """Arrête la génération si un titre ne tient pas sur une ligne."""
    if nombreDeLignes(texte, largeur, taille, police) > 1:
        raise ValueError(f"{nom} ne tient pas sur une ligne à {taille} points : raccourcir le texte")


def verifierBas(nom, bas, limite=HAUTEUR - 0.6):
    """Arrête la génération plutôt que de produire un texte qui déborde de la slide."""
    if bas > limite:
        raise ValueError(f"{nom} déborde : bas à {bas:.2f} pouces pour une limite de {limite:.2f}")


def paragraphesMesures(diapo, x, y, largeur, paragraphes, nom, apres=8):
    """Écrit des paragraphes et renvoie leur bas, en vérifiant qu'ils tiennent dans la slide."""
    hauteur = hauteurParagraphes(paragraphes, largeur, apres)
    verifierBas(nom, y + hauteur)
    boite(diapo, x, y, largeur, hauteur + 0.1, paragraphes, nom, apres=apres)
    return y + hauteur


# --- Gabarit des slides ---

def nouvelleDiapo(presentation, titre, sousTitre=""):
    """Une slide de contenu : filet de 8 points, titre-constat sur une ligne, sous-titre facultatif."""
    diapo = presentation.slides.add_slide(presentation.slide_layouts[6])
    largeur = LARGEUR - 2 * MARGE
    filet(diapo, MARGE, 0.55, largeur, 8, "Filet de tête")
    verifierUneLigne("Le titre", titre, TITRE, 32, largeur)
    boite(diapo, MARGE, 0.78, largeur, 0.62, [[m(titre, TITRE, 32)]], "Titre")
    if sousTitre:
        verifierUneLigne("Le sous-titre", sousTitre, TEXTE, 16, largeur)
        boite(diapo, MARGE, 1.42, largeur, 0.4, [[m(sousTitre, TEXTE, 16, ENCRE_SECONDAIRE)]], "Sous-titre")
    return diapo


def numeroterPages(presentation, soutenance="soutenance intermédiaire"):
    """Écrit le nom de la soutenance et « page / total » en bas de chaque slide, sauf la première."""
    total = len(presentation.slides)
    for page, diapo in enumerate(presentation.slides, start=1):
        if page > 1:
            boite(diapo, MARGE, HAUTEUR - 0.42, 8, 0.25, [[m(f"Projet MR-Sort, {soutenance}", TEXTE, 10,
                                                             ENCRE_SECONDAIRE)]], "Pied")
            boite(diapo, LARGEUR - MARGE - 1.2, HAUTEUR - 0.42, 1.2, 0.25, [[m(f"{page} / {total}", TEXTE, 10,
                                                                               ENCRE_SECONDAIRE)]],
                  "Page", alignement=PP_ALIGN.RIGHT)


def tableauVerso(diapo, x, y, colonnes, lignes, nom, taille=15, hauteurLigne=0.42):
    """
    Un tableau au style Verso, fait de zones de texte et de filets : filet de 4 points sous
    l'en-tête, de 1 point entre les lignes. colonnes = [(titre, largeur, alignement)] ;
    lignes = listes de textes. Renvoie le bas du tableau.
    """
    largeurTotale = sum(largeur for _, largeur, _ in colonnes)
    gauche = x
    for titre, largeur, alignement in colonnes:
        boite(diapo, gauche, y, largeur - 0.1, hauteurLigne, [[m(titre, DEMI_GRAS, taille - 2)]], f"{nom} en-tête",
              ancrage=MSO_ANCHOR.MIDDLE, alignement=alignement)
        gauche += largeur
    y += hauteurLigne
    filet(diapo, x, y, largeurTotale, 4, f"{nom} filet d'en-tête")
    for ligne in lignes:
        gauche = x
        for (titre, largeur, alignement), texte in zip(colonnes, ligne):
            boite(diapo, gauche, y + 0.03, largeur - 0.1, hauteurLigne, [[m(texte, TEXTE, taille)]], f"{nom} case",
                  ancrage=MSO_ANCHOR.MIDDLE, alignement=alignement)
            gauche += largeur
        y += hauteurLigne + 0.03
        filet(diapo, x, y, largeurTotale, 1, f"{nom} filet")
    verifierBas(nom, y)
    return y


# --- Les données de la soutenance ---

PLAT_EXEMPLE = "3257982125116"     # la Poêlée Fermière (Cora) : B pour le Nutri-Score, C′ pour MR-Sort à 7 critères
SA_DEMONSTRATION = 1.4            # les acides gras saturés saisis pendant la démonstration (g pour 100 g)
# chaque critère en toutes lettres, et son article : avec « les », le verbe se met au pluriel
NOMS_COURTS = {"en": "énergie", "sa": "acides gras saturés", "su": "sucres", "so": "sel", "pr": "protéines",
               "fi": "fibres", "fr": "fruits et légumes", "nova": "groupe NOVA", "additifs": "nombre d'additifs",
               "aRisque": "additifs à risque", "bio": "label bio", "sodium": "sodium"}
ARTICLES = {"en": "l'", "sa": "les ", "su": "les ", "so": "le ", "pr": "les ", "fi": "les ", "fr": "les ",
            "nova": "le ", "additifs": "le ", "aRisque": "les ", "bio": "le ", "sodium": "le "}
# les sigles des critères du SuperNutri-score dans les barres de concordance : deux lettres, comme en, sa, su…
SIGLES = {"nova": "nv", "additifs": "ad", "aRisque": "ar", "bio": "bi"}


def quantite(plat):
    """La quantité du plat, sans le « e » des quantités estimées (℮) qu'Open Food Facts recopie parfois."""
    texte = plat["quantite"].strip()
    return texte[:-2] if texte.endswith((" e", " ℮")) else texte


def lireResultats():
    """Lit resultats/resultats_projet.json ; la base, le Nutri-Score et MR-Sort doivent y être."""
    resultats = json.loads(FICHIER_RESULTATS.read_text(encoding="utf-8"))
    for cle in ("base", "nutriscore", "mrsort"):
        if cle not in resultats:
            raise ValueError(f"La clé « {cle} » manque dans {FICHIER_RESULTATS.name} : lancer d'abord le module qui l'écrit.")
    return resultats


def modeleDuJson(resultats, nom, lam, mode="poids"):
    """Le résumé d'un modèle MR-Sort dans le JSON (critères, poids, profils, exactitude, matrice)."""
    for modele in resultats["mrsort"]["modeles"]:
        if modele["nom"] == nom and modele["lam"] == lam and modele["mode"] == mode:
            return modele
    raise KeyError(f"Modèle {nom}, λ = {lam}, absent du JSON")


def regleDuModele(modele):
    """Le modèle MR-Sort à appliquer (critères, poids, profils, λ), tiré de son résumé dans le JSON."""
    return {"criteres": modele["criteres"], "poids": modele["poids"], "profils": modele["profils"], "lam": modele["lam"]}


def platDExemple(plats):
    """Le plat suivi dans tout l'exposé : la Poêlée Fermière, ou à défaut le premier plat B par ordre alphabétique."""
    for plat in plats:
        if plat["code"] == PLAT_EXEMPLE:
            return plat
    return sorted((p for p in plats if p["label"] == "B"), key=lambda p: p["nom"].lower())[0]


def platDuResume(plats, resume):
    """Retrouve dans la base le plat que le JSON résume (même nom, même énergie, même sel)."""
    for plat in plats:
        if plat["nom"] == resume["nom"] and plat["en"] == resume["en"] and plat["so"] == resume["so"]:
            return plat
    raise KeyError(resume["nom"])


def votesPour(plat, regle, numero):
    """Les critères qui votent pour le plat face au profil numéro `numero` (0 pour b2) : il y vaut au moins le profil."""
    profil = regle["profils"][numero]
    return [critere for critere in regle["criteres"]
            if concordancePartielle(plat[critere], profil[critere], sensDuCritere(critere, regle)) == 1]


def enToutesLettres(criteres):
    """« les acides gras saturés et les protéines » : une liste de critères, écrite dans une phrase."""
    noms = [ARTICLES[critere] + NOMS_COURTS[critere] for critere in criteres]
    return noms[0] if len(noms) == 1 else ", ".join(noms[:-1]) + " et " + noms[-1]


def ecartSigne(valeur):
    """Un écart moyen en classes, avec son signe : « +0,43 » (plus sévère), « −0,72 » (plus permissif)."""
    return f"{'+' if valeur >= 0 else '−'}{nombre(abs(valeur), 2)}"


def majuscule(texte):
    """Le texte avec une majuscule initiale."""
    return texte[0].upper() + texte[1:]


def comparaison(detail, regle, numero):
    """La concordance face à un profil, comparée à λ : « 0,919 ≥ 0,6 » ou « 0,479 < 0,6 »."""
    valeur, lam = nombre(detail["concordances"][numero], 3), nombre(regle["lam"], 1)
    return f"{valeur} ≥ {lam}" if detail["franchis"][numero] else f"{valeur} < {lam}"


def verdict(detail, regle, numero):
    """Le verdict d'un profil, comme dans l'interface : « 0,919 ≥ 0,6, franchi » ou « 0,479 < 0,6 »."""
    return comparaison(detail, regle, numero) + (", franchi" if detail["franchis"][numero] else "")


def raisonDuVerdict(plat, regle, detail, numero):
    """
    Pourquoi un profil est franchi ou non, en une proposition. Franchi : les critères qui
    votent contre le plat. Non franchi : ceux qui votaient pour lui face au profil précédent,
    et ne votent plus.
    """
    if detail["franchis"][numero]:
        contre = [critere for critere in regle["criteres"] if critere not in votesPour(plat, regle, numero)]
        return "tous les critères votent pour le plat" + (f", sauf {enToutesLettres(contre)}" if contre else "")
    tombent = []
    if numero > 0:
        tombent = [c for c in votesPour(plat, regle, numero - 1) if c not in votesPour(plat, regle, numero)]
    if not tombent:
        return "trop peu de critères votent pour le plat"
    verbe = "votent" if len(tombent) > 1 or ARTICLES[tombent[0]] == "les " else "vote"
    return f"{enToutesLettres(tombent)} ne {verbe} plus"


def preparerFigures(resultats, plats):
    """
    Écrit les figures de la soutenance dans resultats/figures/ et renvoie leurs chemins. Le
    diagramme des profils occupe toute la largeur de la slide 6 : il est tracé à cette taille,
    et ses textes y gardent donc leur taille réelle.
    """
    chemins = {"entonnoir": DOSSIER_FIGURES / "entonnoir.png"}
    figures.figureEntonnoir(resultats["base"]["entonnoir"], chemins["entonnoir"])
    for nom in ("sept", "trois"):
        chemins[f"matrice_{nom}"] = DOSSIER_FIGURES / f"matrice_{nom}_0.6.png"
        figures.figureMatriceConfusion(modeleDuJson(resultats, nom, 0.6)["matrice"], chemins[f"matrice_{nom}"])
    chemins["profils"] = DOSSIER_FIGURES / "profils_sept_0.6.png"
    figures.figureProfils(regleDuModele(modeleDuJson(resultats, "sept", 0.6)), platDExemple(plats), chemins["profils"],
                          etendues=figures.etenduesDeLaBase(plats, CRITERES_SEPT), taille=(14.6, 2.35), zoom=1.35)
    return chemins


def notesDuTexte(soutenance=1):
    """Les notes de chaque slide, tirées du texte de l'oral (soutenance/texte_soutenance_N.md) : numéro → texte."""
    from projet_soutenance import TEXTES_ORAUX, slidesDuTexte

    notesParSlide = {}
    for slide in slidesDuTexte(TEXTES_ORAUX[soutenance]):
        texte = f"{slide['orateur']}, {slide['duree'] // 60} min {slide['duree'] % 60:02d}.\n\n" + "\n\n".join(slide["texte"])
        if slide["transition"]:
            texte += f"\n\nTransition : {slide['transition']}"
        notesParSlide[slide["numero"]] = texte
    return notesParSlide


# --- Soutenance 1 : les éléments récurrents ---

def colonne(diapo, x, y, largeur, titre, nom, reserve=0):
    """
    L'en-tête d'une colonne : un filet de 4 points, puis son titre en Archivo Condensed, sur
    une ligne. reserve : la place gardée à droite du titre, pour une pastille.
    """
    verifierUneLigne(f"Le titre de la colonne « {nom} »", titre, TITRE, 22, largeur - reserve)
    filet(diapo, x, y, largeur, 4, f"Filet {nom}")
    boite(diapo, x, y + 0.14, largeur - reserve, 0.5, [[m(titre, TITRE, 22)]], f"Titre {nom}")


def repere(diapo, x, y, numero, nom):
    """Un repère numéroté (carré noir, chiffre blanc), pour les étapes de la démonstration."""
    rectangle(diapo, x, y, 0.42, 0.42, nom, fond=ENCRE)
    boite(diapo, x, y, 0.42, 0.42, [[m(str(numero), TITRE, 18, PAPIER)]], f"{nom} (chiffre)",
          ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.CENTER)


def signe(diapo, x, y, cote, positif, nom):
    """
    Le repère d'un groupe de points du Nutri-Score, comme les ⊖ et ⊕ des fig. 6 et 7 : un
    carré rouge avec « − » pour les points négatifs, vert avec « + » pour les positifs.
    """
    rectangle(diapo, x, y, cote, cote, nom, fond=COULEUR_POSITIFS if positif else COULEUR_NEGATIFS)
    boite(diapo, x, y, cote, cote, [[m("+" if positif else "−", TITRE, cote * 56, PAPIER)]], f"{nom} (signe)",
          ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.CENTER)


def tableauDesPoints(diapo, x, y, largeur, plat, resultat, nom):
    """
    Le détail des points du Nutri-Score d'un plat, comme dans l'interface et dans les fig. 6
    et 7 du sujet. Chaque groupe s'ouvre sur son en-tête : son repère (− rouge, + vert),
    « Points négatifs N » ou « Points positifs P », et son total. Viennent ensuite ses
    composantes, une par ligne, avec leur valeur, leur jauge (une case par point possible,
    pleine et à la couleur du groupe pour chaque point obtenu) et leurs points. Un filet de
    4 points ferme chaque groupe, et le score vient en dessous. Renvoie le bas du tableau.
    """
    taille, hauteurLigne = 14, 0.36
    groupes = [("Points négatifs N", NEGATIFS, resultat["N"], False), ("Points positifs P", POSITIFS, resultat["P"], True)]
    composantes = NEGATIFS + POSITIFS
    valeurs = {c: f"{nombre(plat[c], figures.DECIMALES_POINTS[c])} {figures.UNITES_POINTS[c]}" for c in composantes}
    points = {c: f"{resultat['points'][c]} / {POINTS_MAX[c]}" for c in composantes}
    totaux = [f"{total} / {sum(POINTS_MAX[c] for c in membres)}" for _, membres, total, _ in groupes]
    # chaque colonne suit son texte le plus long ; la jauge prend la place qui reste
    largeurLibelle = max(largeurTexte(figures.LIBELLES_POINTS[c], TEXTE, taille) for c in composantes) + 0.2
    largeurValeur = max(largeurTexte(valeurs[c], TEXTE, taille) for c in composantes) + 0.1
    largeurPoints = max([largeurTexte(points[c], TEXTE, taille) for c in composantes] +
                        [largeurTexte(total, DEMI_GRAS, taille) for total in totaux]) + 0.1
    debutJauge = x + largeurLibelle + largeurValeur + 0.2
    pas = (x + largeur - largeurPoints - 0.2 - debutJauge) / max(POINTS_MAX[c] for c in composantes)
    cote, coteSigne = 0.75 * pas, 0.24
    for (titre, membres, _, positif), total in zip(groupes, totaux):
        teinte = COULEUR_POSITIFS if positif else COULEUR_NEGATIFS
        signe(diapo, x, y + (hauteurLigne - coteSigne) / 2, coteSigne, positif, f"{nom} repère {titre}")
        boite(diapo, x + coteSigne + 0.12, y, largeur - largeurPoints - coteSigne - 0.12, hauteurLigne,
              [[m(titre, DEMI_GRAS, taille)]], f"{nom} {titre}", ancrage=MSO_ANCHOR.MIDDLE)
        boite(diapo, x + largeur - largeurPoints, y, largeurPoints, hauteurLigne, [[m(total, DEMI_GRAS, taille)]],
              f"{nom} total {titre}", ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.RIGHT)
        y += hauteurLigne
        filet(diapo, x, y, largeur, 1, f"{nom} filet {titre}")
        for composante in membres:
            boite(diapo, x, y, largeurLibelle, hauteurLigne, [[m(figures.LIBELLES_POINTS[composante], TEXTE, taille)]],
                  f"{nom} {composante}", ancrage=MSO_ANCHOR.MIDDLE)
            boite(diapo, x + largeurLibelle, y, largeurValeur, hauteurLigne, [[m(valeurs[composante], TEXTE, taille)]],
                  f"{nom} valeur {composante}", ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.RIGHT)
            for case in range(POINTS_MAX[composante]):
                obtenu = case < resultat["points"][composante]
                rectangle(diapo, debutJauge + case * pas, y + (hauteurLigne - cote) / 2, cote, cote,
                          f"{nom} jauge {composante} {case + 1}", fond=teinte if obtenu else None,
                          trait=teinte if obtenu else ENCRE, epaisseur=0.75)
            boite(diapo, x + largeur - largeurPoints, y, largeurPoints, hauteurLigne,
                  [[m(points[composante], TEXTE, taille)]], f"{nom} points {composante}", ancrage=MSO_ANCHOR.MIDDLE,
                  alignement=PP_ALIGN.RIGHT)
            y += hauteurLigne
            # un filet de 4 points ferme le groupe, de 1 point entre ses lignes
            filet(diapo, x, y, largeur, 4 if composante == membres[-1] else 1, f"{nom} filet {composante}")
    y += 0.12
    boite(diapo, x, y, largeur, 0.5,
          [[m(f"score = N − P = {resultat['N']} − {resultat['P']} = {resultat['score']}", TITRE, 24)]], f"{nom} score",
          ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.RIGHT)
    verifierBas(nom, y + 0.5)
    return y + 0.5


def entonnoirDeLaBase(diapo, x, y, largeur, entonnoir, parClasse, nom):
    """
    L'entonnoir de la base : une barre noire par filtre, de longueur proportionnelle au nombre
    de candidats qui restent, avec ce nombre au bout. La dernière ligne est le tirage, en cinq
    parts égales aux couleurs des classes. Renvoie le bas de l'entonnoir.
    """
    taille, hauteurLigne = 14, 0.4
    etapes = [(etape[0].upper() + etape[1:], valeur) for etape, valeur in entonnoir.items()]
    etapes.append(("Tirés au hasard", parClasse * len(COULEURS_CLASSES)))
    largeurLibelle = max(largeurTexte(libelle, TEXTE, taille) for libelle, _ in etapes) + 0.15
    largeurNombre = max(largeurTexte(nombre(valeur), DEMI_GRAS, taille) for _, valeur in etapes) + 0.15
    longueurMax = largeur - largeurLibelle - largeurNombre
    plusGrand = max(valeur for _, valeur in etapes)
    for rang, (libelle, valeur) in enumerate(etapes):
        tirage = rang == len(etapes) - 1
        if tirage:
            y += 0.12        # le tirage n'est pas un filtre : un peu d'air le sépare des autres lignes
        boite(diapo, x, y, largeurLibelle - 0.15, hauteurLigne, [[m(libelle, DEMI_GRAS if tirage else TEXTE, taille)]],
              f"{nom} {libelle}", ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.RIGHT)
        longueur = longueurMax * valeur / plusGrand
        if tirage:
            for numero, lettre in enumerate(COULEURS_CLASSES):
                rectangle(diapo, x + largeurLibelle + numero * longueur / 5, y + 0.08, longueur / 5, hauteurLigne - 0.16,
                          f"{nom} tirage {lettre}", fond=couleurClasse(lettre))
        else:
            rectangle(diapo, x + largeurLibelle, y + 0.08, longueur, hauteurLigne - 0.16, f"{nom} barre {rang + 1}",
                      fond=ENCRE)
        boite(diapo, x + largeurLibelle + longueur + 0.08, y, largeurNombre, hauteurLigne,
              [[m(nombre(valeur), DEMI_GRAS, taille)]], f"{nom} nombre {rang + 1}", ancrage=MSO_ANCHOR.MIDDLE)
        y += hauteurLigne
    verifierBas(nom, y)
    return y


def barreDeConcordance(diapo, x, y, largeur, hauteur, regle, plat, numero, nom):
    """
    La barre de concordance d'un plat face au profil numéro `numero` (0 pour b2), comme dans
    l'interface : une case par critère, de largeur égale à son poids, noire si le critère vote
    pour le plat, avec son sigle quand elle est assez large. Un filet blanc sépare deux cases
    noires voisines, et un cadre noir de 2 points entoure la barre.
    """
    pour = votesPour(plat, regle, numero)
    gauche = x
    for critere in regle["criteres"]:
        largeurCase = regle["poids"][critere] * largeur
        passe = critere in pour
        rectangle(diapo, gauche, y, largeurCase, hauteur, f"{nom} {critere}", fond=ENCRE if passe else None,
                  trait=PAPIER if passe else ENCRE, epaisseur=1)
        if largeurCase >= 0.22:
            boite(diapo, gauche, y, largeurCase, hauteur,
                  [[m(SIGLES.get(critere, critere), DEMI_GRAS, 12, PAPIER if passe else ENCRE_SECONDAIRE)]],
                  f"{nom} sigle {critere}",
                  ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.CENTER)
        gauche += largeurCase
    rectangle(diapo, x, y, largeur, hauteur, f"{nom} cadre", trait=ENCRE, epaisseur=2)


def lignesDeConcordance(diapo, x, y, largeur, regle, plat, detail, nom):
    """
    Les barres de concordance d'un plat, de b5 à b2 : à gauche le profil, au milieu sa barre,
    à droite son verdict, en demi-gras quand le profil est franchi. Renvoie le bas des barres.
    """
    hauteur, taille = 0.42, 15
    numeros = list(range(len(PROFILS) - 1, -1, -1))
    largeurVerdict = max(largeurTexte(verdict(detail, regle, numero), DEMI_GRAS, taille) for numero in numeros) + 0.1
    largeurBarre = largeur - 0.55 - 0.2 - largeurVerdict
    for numero in numeros:
        police = DEMI_GRAS if detail["franchis"][numero] else TEXTE
        boite(diapo, x, y, 0.5, hauteur, [[m(PROFILS[numero], DEMI_GRAS, 16)]], f"{nom} {PROFILS[numero]}",
              ancrage=MSO_ANCHOR.MIDDLE)
        barreDeConcordance(diapo, x + 0.55, y, largeurBarre, hauteur, regle, plat, numero, f"{nom} {PROFILS[numero]}")
        boite(diapo, x + largeur - largeurVerdict, y, largeurVerdict, hauteur,
              [[m(verdict(detail, regle, numero), police, taille)]], f"{nom} verdict {PROFILS[numero]}",
              ancrage=MSO_ANCHOR.MIDDLE)
        y += hauteur + 0.2
    return y - 0.2


def versoPlat(diapo, x, y, largeur, plat, criteresDuModele, autresCriteres, lignesDuNom, nom):
    """
    Le verso d'emballage d'un plat : son nom (sur lignesDuNom lignes), sa marque et sa pastille
    de Nutri-Score, puis une ligne par critère. Les critères du modèle sont en demi-gras ; les
    autres sont posés sur la trame grise : ce sont ceux que le modèle ne voit pas. Renvoie le
    bas du verso.
    """
    hauteurLigne = 0.44
    yMarque = y + 0.14 + 0.32 * lignesDuNom
    yLignes = yMarque + 0.42
    hauteur = yLignes - y + hauteurLigne * (len(criteresDuModele) + len(autresCriteres)) + 0.14
    rectangle(diapo, x, y, largeur, hauteur, f"Cadre {nom}", trait=ENCRE, epaisseur=2)
    boite(diapo, x + 0.18, y + 0.12, largeur - 1.0, 0.32 * lignesDuNom, [[m(plat["nom"], TITRE, 18)]], f"Nom {nom}")
    boite(diapo, x + 0.18, yMarque, largeur - 1.0, 0.3, [[m(f"{plat['marque']}, {quantite(plat)}", TEXTE, 13,
                                                            ENCRE_SECONDAIRE)]], f"Marque {nom}")
    pastille(diapo, x + largeur - 0.7, y + 0.16, 0.52, plat["label"], f"Nutri-Score {nom}")
    filet(diapo, x + 0.18, yLignes - 0.08, largeur - 0.36, 4, f"Filet {nom}")
    yLigne = yLignes
    for critere in criteresDuModele + autresCriteres:
        dansLeModele = critere in criteresDuModele
        if not dansLeModele:
            rectangle(diapo, x + 0.18, yLigne, largeur - 0.36, hauteurLigne, f"Trame {nom} {critere}", fond=TRAME)
        decimales = figures.DECIMALES_POINTS[critere]
        police = DEMI_GRAS if dansLeModele else TEXTE
        boite(diapo, x + 0.28, yLigne, largeur - 2.2, hauteurLigne, [[m(CRITERES[critere][0], police, 15)]],
              f"Critère {nom} {critere}", ancrage=MSO_ANCHOR.MIDDLE)
        boite(diapo, x + largeur - 1.9, yLigne, 1.62, hauteurLigne,
              [[m(f"{nombre(plat[critere], decimales)} {figures.UNITES_POINTS[critere]}", police, 15)]],
              f"Valeur {nom} {critere}", ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.RIGHT)
        yLigne += hauteurLigne
        filet(diapo, x + 0.18, yLigne - 0.007, largeur - 0.36, 1, f"Filet {nom} {critere}")
    verifierBas(nom, y + hauteur)
    return y + hauteur


# --- Soutenance 1 : les slides ---

def slideTitre(presentation):
    """La page de titre : la question du projet, et les deux familles de classes."""
    diapo = presentation.slides.add_slide(presentation.slide_layouts[6])
    largeur = LARGEUR - 2 * MARGE
    boite(diapo, MARGE, 0.7, largeur, 0.4, [[m(COURS, TEXTE, 14, ENCRE_SECONDAIRE)]], "Cours")
    filet(diapo, MARGE, 2.05, largeur, 12, "Filet de titre")
    boite(diapo, MARGE, 2.35, largeur, 1.9, [[m("Approcher le Nutri-Score", TITRE, 60)], [m("par MR-Sort", TITRE, 60)]],
          "Titre")
    boite(diapo, MARGE, 4.6, largeur, 0.5, [[m("Un modèle transparent d'évaluation des plats préparés",
                                                DEMI_GRAS, 22)]], "Sous-titre")
    for numero, lettre in enumerate(COULEURS_CLASSES):
        pastille(diapo, MARGE + numero * 0.62, 5.45, 0.55, lettre, f"Nutri-Score {lettre}")
        pastille(diapo, MARGE + 3.6 + numero * 0.62, 5.45, 0.55, lettre, f"Modèle {lettre}", modele=True)
    boite(diapo, MARGE, 6.35, largeur, 0.4, [[m(f"Soutenance intermédiaire, 30 octobre 2026. {GROUPE}.", TEXTE, 14)]],
          "Groupe")


def slideQuestion(presentation, resultats, plats):
    """Deux façons de ranger le même plat : le Nutri-Score additionne des points, MR-Sort fait voter les critères."""
    plat = platDExemple(plats)
    regle = regleDuModele(modeleDuJson(resultats, "sept", 0.6))
    detail = affecter(plat, regle)
    classe = nomDeClasse(detail["classe"])
    accord = "lui donnent la même classe" if lettreDeClasse(classe) == plat["label"] else "ne lui donnent pas la même classe"
    diapo = nouvelleDiapo(presentation, f"Deux façons de ranger la {plat['nom']}",
                          f"{plat['marque']}, {quantite(plat)}. Les deux méthodes {accord}.")
    largeur = (LARGEUR - 2 * MARGE - 0.6) / 2
    droite = MARGE + largeur + 0.6
    colonne(diapo, MARGE, 2.0, largeur, "Le Nutri-Score additionne", "Nutri-Score", reserve=0.6)
    pastille(diapo, MARGE + largeur - 0.46, 2.14, 0.46, plat["label"], "Classe du Nutri-Score")
    tableauDesPoints(diapo, MARGE, 2.8, largeur, plat, scoreNutriscore(plat), "Points")
    colonne(diapo, droite, 2.0, largeur, "MR-Sort fait voter les critères", "MR-Sort", reserve=0.6)
    pastille(diapo, droite + largeur - 0.46, 2.14, 0.46, lettreDeClasse(classe), "Classe MR-Sort", modele=True)
    bas = lignesDeConcordance(diapo, droite, 2.8, largeur, regle, plat, detail, "Concordance")
    sigles = ", ".join(f"{critere} {NOMS_COURTS[critere]}" for critere in regle["criteres"])
    lignes = [[m(f"Une case par critère, large comme son poids, noire quand il vote pour le plat : {sigles}.",
                 TEXTE, 13, ENCRE_SECONDAIRE)]]
    numero = detail["classe"]       # le premier profil que le plat ne franchit pas
    if numero < len(PROFILS):
        lignes.append([m(f"Face à {PROFILS[numero]}, {raisonDuVerdict(plat, regle, detail, numero)} : il reste "
                         f"en\u00a0{classe}.", DEMI_GRAS, 15)])      # la classe ne reste pas seule en fin de ligne
    paragraphesMesures(diapo, droite, bas + 0.25, largeur, lignes, "Lecture des barres")


def slideBase(presentation, resultats, chemins):
    """La base : l'entonnoir des filtres, puis le vivier de chaque classe et le tirage."""
    base = resultats["base"]
    entonnoir = base["entonnoir"]
    diapo = nouvelleDiapo(presentation,
                          f"{base['nombrePlats']} plats préparés tirés au hasard parmi {nombre(entonnoir['sans doublon'])} retenus",
                          f"Open Food Facts, plats vendus en France, extraits le {dateFrancaise(base['dateExtraction'])}. "
                          f"{base['parClasse']} plats par classe, graine {base['graine']}.")
    entonnoirDeLaBase(diapo, MARGE, 2.05, 7.4, entonnoir, base["parClasse"], "Entonnoir")
    x = 8.6
    colonne(diapo, x, 2.0, LARGEUR - MARGE - x, "Vivier, puis tirage", "vivier")
    y = 2.8
    for lettre in COULEURS_CLASSES:
        pastille(diapo, x, y, 0.42, lettre, f"Classe {lettre}")
        boite(diapo, x + 0.6, y, 3.4, 0.42, [[m(f"{nombre(base['vivierParClasse'][lettre])} retenus, "
                                                f"{base['parClasse']} tirés", TEXTE, 16)]],
              f"Vivier {lettre}", ancrage=MSO_ANCHOR.MIDDLE)
        y += 0.52
    paragraphesMesures(diapo, x, y + 0.1, LARGEUR - MARGE - x,
                       [[m("Toutes les réponses d'Open Food Facts sont gardées : la base se reconstruit à "
                           "l'identique, sans réseau.", TEXTE, 14, ENCRE_SECONDAIRE)]], "Note du tirage")


def slideCriteres(presentation, plats):
    """Les sept critères varient tous dans la base : c'est ce qui a fait choisir les plats préparés."""
    diapo = nouvelleDiapo(presentation, "Dans les plats préparés, les sept critères varient tous",
                          "Valeurs pour 100 g dans notre base : minimum, médiane, maximum.")
    lignes = []
    for critere in CRITERES_SEPT:
        valeurs = [plat[critere] for plat in plats]
        decimales = 0 if critere in ("en", "fr") else (2 if critere == "so" else 1)
        unite = CRITERES[critere][1].split("/")[0]
        lignes.append([CRITERES[critere][0], "à limiter" if CRITERES[critere][2] == "min" else "à favoriser",
                       f"{nombre(min(valeurs), decimales)} {unite}", f"{nombre(median(valeurs), decimales)} {unite}",
                       f"{nombre(max(valeurs), decimales)} {unite}"])
    colonnes = [("Critère", 4.4, PP_ALIGN.LEFT), ("Sens", 2.0, PP_ALIGN.LEFT), ("Minimum", 1.9, PP_ALIGN.RIGHT),
                ("Médiane", 1.9, PP_ALIGN.RIGHT), ("Maximum", 1.9, PP_ALIGN.RIGHT)]
    bas = tableauVerso(diapo, MARGE, 2.05, colonnes, lignes, "Critères")
    paragraphesMesures(diapo, MARGE, bas + 0.25, LARGEUR - 2 * MARGE,
                       [[m("Dans les céréales du petit-déjeuner, la teneur en fruits et légumes est presque toujours "
                           "nulle : le modèle à 3 critères du sujet (énergie, sodium, fruits) n'en aurait plus que deux.",
                           TEXTE, 15, ENCRE_SECONDAIRE)]], "Note des critères")


def slideNutriscore(presentation, resultats):
    """
    Notre Nutri-Score face à ses deux contrôles : les exemples du sujet, puis toute la base.
    La colonne du calcul se lit « points négatifs − points positifs = score ».
    """
    verification = resultats["nutriscore"]
    titre = f"Notre Nutri-Score retrouve celui d'OFF pour {verification['reproduits']} plats sur {verification['total']}"
    diapo = nouvelleDiapo(presentation, titre, "La «\u00a0version de mars 2025\u00a0» du sujet : l'algorithme actualisé "
                                              "en 2023, en vigueur en France depuis le 16 mars 2025.")
    largeur = LARGEUR - 2 * MARGE
    # le tableau des contrôles : ce qu'on vérifie, notre calcul, la classe obtenue
    hauteurLigne, y = 0.75, 2.05
    boite(diapo, MARGE, y, 7, 0.4, [[m("Contrôle", DEMI_GRAS, 14)]], "Contrôles en-tête", ancrage=MSO_ANCHOR.MIDDLE)
    boite(diapo, MARGE + largeur - 4.4, y, 3.3, 0.4, [[m("N − P = score", DEMI_GRAS, 14)]], "Calcul en-tête",
          ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.RIGHT)
    boite(diapo, MARGE + largeur - 1.0, y, 1.0, 0.4, [[m("Classe", DEMI_GRAS, 14)]], "Classe en-tête",
          ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.RIGHT)
    y += 0.4
    filet(diapo, MARGE, y, largeur, 4, "Contrôles filet d'en-tête")
    lignes = []
    for figure, exemple in EXEMPLES_SUJET.items():
        calcul = scoreNutriscore(exemple["produit"])
        lignes.append((f"Fig. {figure.split()[-1]} du sujet : {exemple['nom']}",
                       f"{calcul['N']} − {calcul['P']} = {calcul['score']}", calcul["label"]))
    lignes.append(("Notre base : le score et le label d'OFF", f"{verification['reproduits']} / {verification['total']}",
                   None))
    for rang, (controle, calcul, lettre) in enumerate(lignes):
        boite(diapo, MARGE, y, 7.4, hauteurLigne, [[m(controle, TEXTE, 20)]], f"Contrôle {rang + 1}",
              ancrage=MSO_ANCHOR.MIDDLE)
        boite(diapo, MARGE + largeur - 4.4, y, 3.3, hauteurLigne, [[m(calcul, TITRE, 28)]], f"Calcul {rang + 1}",
              ancrage=MSO_ANCHOR.MIDDLE, alignement=PP_ALIGN.RIGHT)
        if lettre:
            pastille(diapo, MARGE + largeur - 0.46, y + (hauteurLigne - 0.46) / 2, 0.46, lettre, f"Classe {rang + 1}")
        y += hauteurLigne
        filet(diapo, MARGE, y, largeur, 1, f"Contrôle {rang + 1} filet")
    if verification["ecarts"]:
        paragraphesMesures(diapo, MARGE, y + 0.1, largeur, [[m(
            f"Écarts avec OFF : {len(verification['ecarts'])}, détaillés dans resultats/nutriscore_base.xlsx.",
            TEXTE, 15)]], "Écarts")


def slideProfils(presentation, resultats, plats, chemins):
    """
    MR-Sort en une image : le diagramme des profils du plat d'exemple sur toute la largeur,
    puis sa lecture et ses deux profils décisifs (le dernier franchi, le premier qui ne l'est pas).
    """
    plat = platDExemple(plats)
    regle = regleDuModele(modeleDuJson(resultats, "sept", 0.6))
    detail = affecter(plat, regle)
    diapo = nouvelleDiapo(presentation, "MR-Sort en une image : le plat face aux quatre profils",
                          f"{plat['nom']} ({plat['marque']}), modèle à 7 critères, λ = {nombre(regle['lam'], 1)}. "
                          "Sur chaque axe, le mieux est en haut.")
    largeur = LARGEUR - 2 * MARGE
    diagramme = image(diapo, chemins["profils"], MARGE, 1.95, largeur=largeur, nom="Diagramme des profils")
    y = 1.95 + diagramme.height.inches + 0.12
    pas = (largeur - 2 * 0.45) / 3
    colonne(diapo, MARGE, y, pas, "Lire le diagramme", "lecture")
    paragraphesMesures(diapo, MARGE, y + 0.72, pas, [[m(
        "Le trait noir est le plat, chaque trait de couleur un profil. Au-dessus d'un profil sur un axe, le critère "
        "vote pour le plat.", TEXTE, 14)]], "Texte de la lecture")
    classe = detail["classe"]
    decisifs = [numero for numero in (classe - 1, classe) if 0 <= numero < len(PROFILS)]
    for rang, numero in enumerate(decisifs):
        x = MARGE + (rang + 1) * (pas + 0.45)
        franchi = detail["franchis"][numero]
        colonne(diapo, x, y, pas, f"{PROFILS[numero]}, {'franchi' if franchi else 'non franchi'}", PROFILS[numero])
        barreDeConcordance(diapo, x, y + 0.72, pas, 0.34, regle, plat, numero, f"Barre {PROFILS[numero]}")
        phrase = f"{majuscule(raisonDuVerdict(plat, regle, detail, numero))} : {comparaison(detail, regle, numero)}."
        if not franchi:
            phrase += f" Le plat reste en\u00a0{nomDeClasse(classe)}."
        paragraphesMesures(diapo, x, y + 1.16, pas, [[m(phrase, TEXTE, 14)]], f"Texte {PROFILS[numero]}")


def slideModeles(presentation, resultats, chemins):
    """La comparaison des quatre modèles appris, et la matrice de confusion du meilleur."""
    sept = modeleDuJson(resultats, "sept", 0.6)
    diapo = nouvelleDiapo(presentation,
                          f"À 7 critères, MR-Sort range {sept['bienRanges']} plats sur {sept['total']} comme le Nutri-Score",
                          "Profils fixés par les médianes des classes voisines, poids appris par programme linéaire.")
    lignes = []
    for nom in ("sept", "trois"):
        for lam in (0.6, 0.7):
            modele = modeleDuJson(resultats, nom, lam)
            lignes.append([f"{len(modele['criteres'])} critères", nombre(lam, 1),
                           f"{modele['bienRanges']} / {modele['total']}", pourcentage(modele["exactitude"], 1),
                           pourcentage(modele["aUneClassePres"], 1)])
    colonnes = [("Modèle", 1.5, PP_ALIGN.LEFT), ("λ", 0.6, PP_ALIGN.RIGHT), ("Bien rangés", 1.5, PP_ALIGN.RIGHT),
                ("Exactitude", 1.4, PP_ALIGN.RIGHT), ("À une classe près", 2.1, PP_ALIGN.RIGHT)]
    bas = tableauVerso(diapo, MARGE, 2.1, colonnes, lignes, "Modèles", taille=17, hauteurLigne=0.5)
    loin = sum(sept["matrice"][i][j] for i in range(5) for j in range(5) if abs(i - j) > 1)
    paragraphesMesures(diapo, MARGE, bas + 0.35, 7.1, [
        [m(f"Seuls {loin} plats sont à plus d'une classe du Nutri-Score : MR-Sort se trompe aux frontières, "
           "pas sur le fond.", DEMI_GRAS, 16)]], "Lecture de la matrice")
    hauteur = 4.5
    largeurMatrice = hauteur * proportions(chemins["matrice_sept"])
    image(diapo, chemins["matrice_sept"], LARGEUR - MARGE - largeurMatrice, 1.95, hauteur=hauteur,
          nom="Matrice de confusion")


def slideTroisCriteres(presentation, resultats, plats):
    """À 3 critères, une paire de plats prouve qu'aucun MR-Sort exact n'existe : les deux versos côte à côte."""
    inversions = resultats["mrsort"]["inversions"]["trois"]
    diapo = nouvelleDiapo(presentation, "À 3 critères, aucun modèle MR-Sort ne peut être exact",
                          f"{nombre(inversions['nombre'])} paires de plats où le meilleur sur les 3 critères "
                          f"est le moins bien classé. En voici une.")
    exemple = inversions["exemple"]
    paire = [platDuResume(plats, exemple["meilleur"]), platDuResume(plats, exemple["moinsBon"])]
    largeur = (LARGEUR - 2 * MARGE - 0.6) / 2
    lignesDuNom = max(nombreDeLignes(plat["nom"], largeur - 1.0, 18, TITRE) for plat in paire)
    criteresDuModele = [c for c in CRITERES_SEPT if c in modeleDuJson(resultats, "trois", 0.6)["criteres"]]
    for rang, (plat, nom) in enumerate(zip(paire, ("meilleur", "moins bon"))):
        bas = versoPlat(diapo, MARGE + rang * (largeur + 0.6), 2.0, largeur, plat, criteresDuModele, ["sa", "pr"],
                        lignesDuNom, nom)
    paragraphesMesures(diapo, MARGE, bas + 0.3, LARGEUR - 2 * MARGE, [
        [m("En demi-gras, les 3 critères du modèle : le premier plat vaut au moins le second sur chacun. MR-Sort, "
           "monotone, le rangerait au moins aussi haut. Sur la trame grise, ce que le modèle ne voit pas, et qui "
           "fait le Nutri-Score.", TEXTE, 16)],
    ], "Explication")


def slideDemonstration(presentation, resultats, plats):
    """La démonstration de l'interface : trois captures numérotées, dans l'ordre où on les montre, puis le geste final."""
    plat = platDExemple(plats)
    regle = regleDuModele(modeleDuJson(resultats, "sept", 0.6))
    avant = affecter(plat, regle)["classe"]
    apres = affecter(dict(plat, sa=SA_DEMONSTRATION), regle)["classe"]
    diapo = nouvelleDiapo(presentation, "L'interface : un plat, son Nutri-Score et ses classes MR-Sort",
                          "Démonstration en direct : streamlit run projet_gui.py")
    etapes = [("interface_fiche.png", "On part d'un plat de la base"),
              ("interface_nutriscore.png", "Son Nutri-Score, point par point"),
              ("interface_mrsort.png", "Sa classe MR-Sort, et pourquoi")]
    largeur = (LARGEUR - 2 * MARGE - 2 * 0.35) / 3
    for rang, (fichier, legende) in enumerate(etapes):
        x = MARGE + rang * (largeur + 0.35)
        repere(diapo, x, 1.98, rang + 1, f"Repère {rang + 1}")
        boite(diapo, x + 0.55, 1.98, largeur - 0.55, 0.42, [[m(legende, DEMI_GRAS, 15)]], f"Étape {rang + 1}",
              ancrage=MSO_ANCHOR.MIDDLE)
        capture = DOSSIER_FIGURES / fichier
        if capture.exists():
            forme = image(diapo, capture, x, 2.6, largeur=largeur, nom=f"Capture {rang + 1}")
            rectangle(diapo, x, 2.6, largeur, forme.height.inches, f"Cadre de la capture {rang + 1}", trait=ENCRE,
                      epaisseur=1)
            verifierBas(f"Capture {rang + 1}", 2.6 + forme.height.inches, 6.1)
    if apres != avant:
        geste = (f"Avec {nombre(SA_DEMONSTRATION, 1)} g d'acides gras saturés au lieu de {nombre(plat['sa'], 1)}, la "
                 f"{plat['nom']} franchit {PROFILS[avant]} et passe en\u00a0{nomDeClasse(apres)}.")
        repere(diapo, MARGE, 6.2, 4, "Repère 4")
        boite(diapo, MARGE + 0.55, 6.2, LARGEUR - 2 * MARGE - 0.55, 0.42, [[m(geste, DEMI_GRAS, 15)]], "Étape 4",
              ancrage=MSO_ANCHOR.MIDDLE)


def slideSuite(presentation):
    """La suite du projet : une frise des trois dates, et ce que chacune apporte."""
    diapo = nouvelleDiapo(presentation, "La suite : le SuperNutri-score",
                          "Trois dates : aujourd'hui, la soutenance finale et le rendu.")
    largeur = LARGEUR - 2 * MARGE
    filet(diapo, MARGE, 2.95, largeur, 4, "Frise")
    jalons = [
        ("30 octobre", "Aujourd'hui", "La base, le Nutri-Score vérifié, MR-Sort à 7 et 3 critères."),
        ("27 novembre", "Soutenance finale", "Les profils appris et le modèle complet. Puis le SuperNutri-score : "
                                             "les 7 composantes, NOVA et les additifs, sa variante avec le "
                                             "Green-Score, et les analyses de sensibilité."),
        ("10 janvier", "Rendu", "Le rapport, les Excel et le code commenté."),
    ]
    pas = largeur / len(jalons)
    for rang, (date, nom, texte) in enumerate(jalons):
        x = MARGE + rang * pas
        boite(diapo, x, 2.1, pas - 0.3, 0.7, [[m(date, TITRE, 30)]], f"Date {rang + 1}")
        rectangle(diapo, x, 2.85, 0.26, 0.26, f"Jalon {rang + 1}", fond=ENCRE)
        paragraphesMesures(diapo, x, 3.35, pas - 0.35, [[m(nom, DEMI_GRAS, 17)], [m(texte, TEXTE, 16)]],
                           f"Jalon {nom}", apres=6)
    boite(diapo, MARGE, 6.05, largeur, 0.6, [[m("Merci.", TITRE, 28)]], "Merci")


def slidesSoutenance1(chemin=SORTIES[1]):
    """
    Écrit les slides de la soutenance intermédiaire et renvoie leur nombre. L'ordre suit les
    trois parties de l'oral : la base et le Nutri-Score (1 à 5), MR-Sort (6 à 8), la
    démonstration et la suite (9 et 10). Les notes de chaque slide reprennent le texte de l'oral.
    """
    resultats = lireResultats()
    plats = lireBase(FICHIER_BASE)
    chemins = preparerFigures(resultats, plats)
    presentation = Presentation()
    presentation.slide_width = Inches(LARGEUR)
    presentation.slide_height = Inches(HAUTEUR)
    slideTitre(presentation)
    slideQuestion(presentation, resultats, plats)
    slideBase(presentation, resultats, chemins)
    slideCriteres(presentation, plats)
    slideNutriscore(presentation, resultats)
    slideProfils(presentation, resultats, plats, chemins)
    slideModeles(presentation, resultats, chemins)
    slideTroisCriteres(presentation, resultats, plats)
    slideDemonstration(presentation, resultats, plats)
    slideSuite(presentation)
    numeroterPages(presentation)
    notesParSlide = notesDuTexte()
    for numero, diapo in enumerate(presentation.slides, start=1):
        notes(diapo, notesParSlide.get(numero, ""))
    chemin.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(chemin)
    return len(presentation.slides)


# --- Soutenance 2 : le SuperNutri-score ---

BASE_FINALE = "etendue"            # les chiffres de la soutenance finale portent sur nos 375 plats
LIBELLES_COURTS = {"en": "Énergie (kJ)", "sa": "AGS (g)", "su": "Sucres (g)", "so": "Sel (g)", "pr": "Protéines (g)",
                   "fi": "Fibres (g)", "fr": "Fruits et légumes (%)", "nova": "Groupe NOVA",
                   "additifs": "Nombre d'additifs", "aRisque": "Additifs à risque", "bio": "Bio"}
# d'où vient chaque seuil, en peu de mots (la version longue est dans projet_supernutri.SOURCES_DES_SEUILS)
SOURCES_COURTES = {"en": "barème du Nutri-Score 2023", "sa": "A′ : « faible teneur » (CE 1924/2006)",
                   "su": "A′ : « faible teneur » (CE 1924/2006)", "so": "A′ : « faible teneur » (CE 1924/2006)",
                   "pr": "barème du Nutri-Score 2023", "fi": "A′ « riche », B′ « source » (CE 1924/2006)",
                   "fr": "barème du Nutri-Score 2023 (40 et 60 %)", "nova": "pas d'ultra-transformé en A′ et B′",
                   "additifs": "aucun en A′, un au plus en B′", "aRisque": "nitrites, phosphates, carraghénanes",
                   "bio": "label bio exigé en A′ et B′"}


def nombreCourt(valeur):
    """Un nombre sans zéro inutile : 1 340, 6,8, 0,3."""
    if float(valeur).is_integer():
        return nombre(valeur, 0)
    return nombre(valeur, 2).rstrip("0").rstrip(",")


def seuilEcrit(critere, valeur, sens):
    """Un seuil de profil : « ≤ 335 » pour un critère à minimiser, « ≥ 12 » pour un critère à maximiser ; le bio est « exigé » ou non."""
    if critere == "bio":
        return "exigé" if valeur else "—"
    return f"{'≤' if sens == 'min' else '≥'} {nombreCourt(valeur)}"


def slideTitreFinale(presentation):
    """La page de titre de la soutenance finale : notre modèle, et ses cinq classes."""
    diapo = presentation.slides.add_slide(presentation.slide_layouts[6])
    largeur = LARGEUR - 2 * MARGE
    boite(diapo, MARGE, 0.7, largeur, 0.4, [[m(COURS, TEXTE, 14, ENCRE_SECONDAIRE)]], "Cours")
    filet(diapo, MARGE, 2.05, largeur, 12, "Filet de titre")
    boite(diapo, MARGE, 2.35, largeur, 1.9, [[m("Le SuperNutri-score", TITRE, 60)], [m("notre modèle MR-Sort", TITRE, 60)]],
          "Titre")
    sousTitre = "Comparer les plats préparés : composition, transformation et production"
    verifierUneLigne("Le sous-titre de la page de titre", sousTitre, DEMI_GRAS, 22, largeur)
    boite(diapo, MARGE, 4.6, largeur, 0.5, [[m(sousTitre, DEMI_GRAS, 22)]], "Sous-titre")
    for numero, lettre in enumerate(COULEURS_CLASSES):
        pastille(diapo, MARGE + numero * 0.62, 5.45, 0.55, lettre, f"Modèle {lettre}", modele=True)
    boite(diapo, MARGE, 6.35, largeur, 0.4, [[m(f"Soutenance finale, 27 novembre 2026. {GROUPE}.", TEXTE, 14)]], "Groupe")


def slidePiliers(presentation, supernutri):
    """Les onze critères en trois piliers : le poids de chaque critère, et ce qui le fonde."""
    modele = supernutri["modele"]
    diapo = nouvelleDiapo(presentation, f"Onze critères en trois piliers, et λ = {nombre(modele['lam'], 1)}",
                          "Un score de santé : la composition du plat, puis sa transformation et sa production.")
    largeur = (LARGEUR - 2 * MARGE - 2 * 0.4) / 3
    titres = {"à limiter": "À limiter", "à favoriser": "À favoriser", "transformation et production": "Transformation"}
    explications = {
        "à limiter": f"Au prorata des points maximaux du Nutri-Score : le sel ({POINTS_MAX['so']} points) pèse deux fois "
                     f"l'énergie ({POINTS_MAX['en']}).",
        "à favoriser": f"Même règle. Les protéines ne votent que si le Nutri-Score les compte : pas à partir de "
                       f"{SEUIL_PROTEINES} points négatifs.",
        "transformation et production": "NOVA d'abord ; les additifs, entre leur nombre et leur risque ; le bio pèse le "
                                        "moins, car son effet sur la santé est le moins établi.",
    }
    for rang, (pilier, (poidsDuPilier, criteres)) in enumerate(PILIERS.items()):
        x = MARGE + rang * (largeur + 0.4)
        colonne(diapo, x, 2.0, largeur, f"{titres[pilier]} : {nombre(poidsDuPilier, 2)}", pilier)
        lignes = [[LIBELLES_COURTS[critere].split(" (")[0], nombre(modele["poids"][critere], 3)] for critere in criteres]
        bas = tableauVerso(diapo, x, 2.75, [("Critère", largeur - 1.2, PP_ALIGN.LEFT), ("Poids", 1.2, PP_ALIGN.RIGHT)],
                           lignes, f"Poids {pilier}", taille=15, hauteurLigne=0.4)
        paragraphesMesures(diapo, x, bas + 0.2, largeur, [[m(explications[pilier], TEXTE, 14, ENCRE_SECONDAIRE)]],
                           f"Explication {pilier}")
    lam = modele["lam"]
    boite(diapo, MARGE, 6.2, LARGEUR - 2 * MARGE, 0.45,
          [[m(f"λ = {nombre(lam, 1)} : face à un profil, un plat peut rater au plus {nombre(1 - lam, 1)} du poids, "
              "par exemple tout un pilier.", DEMI_GRAS, 16)]], "Lambda", ancrage=MSO_ANCHOR.MIDDLE)


def slideSeuils(presentation, supernutri):
    """Les quatre seuils de chaque critère, de D′ à A′, et d'où ils viennent."""
    modele = supernutri["modele"]
    diapo = nouvelleDiapo(presentation, "Des seuils tirés du règlement européen et du Nutri-Score",
                          "A′ : les allégations « faible teneur » et « riche en fibres » du règlement CE 1924/2006. "
                          "Puis les barèmes de 2023.")
    lignes = []
    for critere in modele["criteres"]:
        sens = modele["sens"][critere]
        lignes.append([LIBELLES_COURTS[critere]] + [seuilEcrit(critere, profil[critere], sens) for profil in modele["profils"]]
                      + [SOURCES_COURTES[critere]])
    colonnes = [("Critère", 3.1, PP_ALIGN.LEFT), ("D′", 1.15, PP_ALIGN.RIGHT), ("C′", 1.15, PP_ALIGN.RIGHT),
                ("B′", 1.15, PP_ALIGN.RIGHT), ("A′", 1.15, PP_ALIGN.RIGHT), ("D'où vient le seuil", 4.2, PP_ALIGN.LEFT)]
    tableauVerso(diapo, MARGE, 1.95, colonnes, lignes, "Seuils", taille=13, hauteurLigne=0.34)


def slideSensDesClasses(presentation, supernutri, donnees):
    """Le sens des classes, comme au Nutri-Score, et leur répartition sur nos plats."""
    diapo = nouvelleDiapo(presentation, "Comme au Nutri-Score, des classes pour comparer, pas pour juger",
                          "Pas de « bons » ni de « mauvais » plats : des plats plus ou moins favorables à la santé.")
    repartition = donnees["repartition"]
    total = sum(repartition.values())
    colonne(diapo, MARGE, 2.0, 6.2, "Ce que dit chaque classe", "sens")
    colonne(diapo, 7.4, 2.0, LARGEUR - MARGE - 7.4, f"Sur nos {total} plats", "répartition")
    plusGrand = max(repartition.values())
    y = 2.8
    for lettre in ("A′", "B′", "C′", "D′", "E′"):
        pastille(diapo, MARGE, y, 0.46, lettre[0], f"Classe {lettre}", modele=True)
        boite(diapo, MARGE + 0.65, y, 5.5, 0.46, [[m(f"les plats {SENS_DES_CLASSES[lettre]}", TEXTE, 17)]],
              f"Sens {lettre}", ancrage=MSO_ANCHOR.MIDDLE)
        longueur = 2.6 * repartition[lettre] / plusGrand
        rectangle(diapo, 7.4, y + 0.08, max(longueur, 0.04), 0.3, f"Barre {lettre}", fond=couleurClasse(lettre[0]))
        boite(diapo, 7.4 + longueur + 0.12, y, 2.6, 0.46,
              [[m(f"{repartition[lettre]} ({pourcentage(repartition[lettre] / total, 1)})", DEMI_GRAS, 16)]],
              f"Nombre {lettre}", ancrage=MSO_ANCHOR.MIDDLE)
        y += 0.62
    paragraphesMesures(diapo, MARGE, y + 0.15, LARGEUR - 2 * MARGE, [[m(
        "La FAQ officielle du Nutri-Score ne range pas les aliments en bons ou mauvais : elle va des meilleurs pour la "
        "santé aux moins satisfaisants. Nous gardons ce sens, étendu à la transformation et à la production.",
        TEXTE, 15, ENCRE_SECONDAIRE)]], "Note du sens")


def slidePoeleeFinale(presentation, supernutri, plats):
    """Le plat suivi depuis le 30/10, face aux quatre profils du SuperNutri-score, et ce qui le ferait monter."""
    plat = platDExemple(plats)
    regle = supernutri["modele"]
    valeurs = valeursDuPlat(plat)
    detail = affecter(valeurs, regle)
    lettre = nomDeClasse(detail["classe"])
    bio = "bio" if plat.get("bio") == "oui" else "sans label bio"
    diapo = nouvelleDiapo(presentation, f"La {plat['nom']} : {plat['label']} au Nutri-Score, {lettre} au SuperNutri-score",
                          f"{plat['marque']}, {quantite(plat)}, NOVA {plat['nova']}, {plat['additifs']} additifs, {bio}.")
    largeur = 8.0
    bas = lignesDeConcordance(diapo, MARGE, 2.05, largeur, regle, valeurs, detail, "Concordance")
    sigles = ", ".join(f"{SIGLES[critere]} {NOMS_COURTS[critere]}" for critere in ("nova", "additifs", "aRisque", "bio"))
    paragraphesMesures(diapo, MARGE, bas + 0.25, largeur, [[m(
        f"Une case par critère, large comme son poids, noire quand il vote pour le plat. {sigles}.",
        TEXTE, 13, ENCRE_SECONDAIRE)]], "Lecture des barres")
    x = MARGE + largeur + 0.5
    colonne(diapo, x, 2.0, LARGEUR - MARGE - x, "Et si…", "et si")
    rates = ecartsAuNutriscore([plat], regle)["plats"][0]["rates"]
    moinsTransforme = nomDeClasse(affecter(valeursDuPlat(dict(plat, nova=3, additifs=1)), regle)["classe"])
    lignes = []
    if rates:
        lignes.append([m(f"Face à {plat['label']}′, elle rate {enToutesLettres(rates)}.", TEXTE, 16)])
    lignes.append([m(f"Moins transformée (NOVA 3) et avec un seul additif, elle serait en {moinsTransforme}.",
                     DEMI_GRAS, 16)])
    paragraphesMesures(diapo, x, 2.75, LARGEUR - MARGE - x, lignes, "Et si", apres=10)


def slideFaceAuNutriscore(presentation, donnees):
    """La matrice SuperNutri-score × Nutri-Score, et les critères qui font descendre les plats."""
    ecarts = donnees["ecarts"]
    total = sum(donnees["repartition"].values())
    diapo = nouvelleDiapo(presentation, f"Plus sévère que le Nutri-Score : {ecarts['descendent']} plats descendent, "
                                        f"{ecarts['montent']} montent",
                          f"Sur nos {total} plats, {ecarts['egaux']} gardent la classe du Nutri-Score. En ligne le "
                          "Nutri-Score, en colonne le SuperNutri-score.")
    matrice = donnees["comparaison"]["matrice"]
    colonnes = [("", 1.0, PP_ALIGN.LEFT)] + [(lettre, 0.95, PP_ALIGN.RIGHT) for lettre in ("A′", "B′", "C′", "D′", "E′")]
    lignes = [[lettre] + [str(valeur) for valeur in matrice[rang]] for rang, lettre in enumerate("ABCDE")]
    tableauVerso(diapo, MARGE, 2.05, colonnes, lignes, "Matrice", taille=17, hauteurLigne=0.5)
    x = 7.2
    largeur = LARGEUR - MARGE - x
    colonne(diapo, x, 2.0, largeur, "Pourquoi ils descendent", "raisons")
    raisons = sorted(ecarts["raisonsDesDescentes"].items(), key=lambda paire: -paire[1])[:5]
    bas = tableauVerso(diapo, x, 2.75, [("Critère raté", largeur - 1.3, PP_ALIGN.LEFT), ("Plats", 1.3, PP_ALIGN.RIGHT)],
                       [[majuscule(NOMS_COURTS[critere]), str(compte)] for critere, compte in raisons], "Raisons",
                       taille=15, hauteurLigne=0.38)
    montees = ecarts["montees"]
    paragraphesMesures(diapo, x, bas + 0.2, largeur, [[m(
        f"Sur les {ecarts['montent']} plats qui montent, {montees['chargees']} ont au moins 11 points négatifs. Le Nutri-Score "
        "les additionne ; MR-Sort, sans veto, ne retire que le poids des critères ratés.",
        TEXTE, 14, ENCRE_SECONDAIRE)]], "Lecture des raisons")


def slideSensibilitePoids(presentation, sensibilite, total):
    """La sensibilité aux poids : les tirages au hasard, un poids à la fois, et les plats au bord de leur classe."""
    poids = sensibilite["poids"]
    principal = [point for point in sensibilite["courbe"] if point["amplitude"] == poids["amplitude"]][0]
    diapo = nouvelleDiapo(presentation, f"Poids : à ± {nombreCourt(poids['amplitude'])}, {pourcentage(principal['partMoyenne'], 1)} "
                                        "des plats changent de classe",
                          f"{nombre(poids['tirages'])} tirages au hasard par amplitude ; les poids restent positifs, "
                          "de somme 1. En moyenne sur les tirages.")
    colonne(diapo, MARGE, 2.0, 5.6, "Tous les poids ensemble", "tirages")
    y = 2.75
    for point in sensibilite["courbe"]:
        boite(diapo, MARGE, y, 1.9, 0.6, [[m(f"± {nombreCourt(point['amplitude'])}", TITRE, 30)]],
              f"Amplitude {point['amplitude']}", ancrage=MSO_ANCHOR.MIDDLE)
        boite(diapo, MARGE + 2.0, y, 3.6, 0.6,
              [[m(f"{pourcentage(point['partMoyenne'], 1)} en moyenne, {pourcentage(point['partMax'], 1)} au plus", TEXTE, 16)]],
              f"Part {point['amplitude']}", ancrage=MSO_ANCHOR.MIDDLE)
        y += 0.72
    x = 6.9
    largeur = LARGEUR - MARGE - x
    colonne(diapo, x, 2.0, largeur, "Un poids à la fois", "un par un")
    lignes = []
    for variation in sorted(poids["unParUn"], key=lambda ligne: -ligne["plats"])[:5]:
        signeDuDelta = "+" if variation["delta"] > 0 else "−"
        lignes.append([f"{majuscule(NOMS_COURTS[variation['critere']])} {signeDuDelta} {nombreCourt(abs(variation['delta']))}",
                       f"{variation['plats']} plats"])
    tableauVerso(diapo, x, 2.75, [("Variation", largeur - 1.7, PP_ALIGN.LEFT), ("Changent", 1.7, PP_ALIGN.RIGHT)], lignes,
                 "Un par un", taille=15, hauteurLigne=0.38)
    auBord = sensibilite["auBord"]
    favoriser = set(PILIERS["à favoriser"][1])
    pourquoi = (" : ils ratent tout le pilier « à favoriser »" if auBord and all(set(p["rates"]) == favoriser for p in auBord)
                else "")
    paragraphesMesures(diapo, MARGE, 5.55, LARGEUR - 2 * MARGE, [[m(
        f"{len(auBord)} plats sont au bord de leur classe, sur {total} : leur concordance vaut λ pile{pourquoi}. Le moindre "
        "changement de poids les fait basculer.", DEMI_GRAS, 15)]], "Au bord")


def slideSensibiliteProfils(presentation, sensibilite, total):
    """La sensibilité aux profils : les décalages qui changent le plus de plats."""
    profils = sensibilite["profils"]
    diapo = nouvelleDiapo(presentation, f"Profils : {len(profils['plats'])} plats changent au moins une fois",
                          f"± 5 % sur les composantes : {profils['platsComposantes']} plats ; ± 1 sur NOVA et les additifs : "
                          f"{profils['platsEntiers']} plats.")
    lignes = []
    for scenario in sorted(profils["scenarios"], key=lambda s: -s["plats"])[:6]:
        numero = PROFILS.index(scenario["profil"])
        lignes.append([f"{scenario['profil']} ({nomDeClasse(numero + 1)})", LIBELLES_COURTS[scenario["critere"]],
                       f"{nombreCourt(scenario['ancienne'])} → {nombreCourt(scenario['nouvelle'])}", str(scenario["plats"])])
    colonnes = [("Profil", 1.8, PP_ALIGN.LEFT), ("Critère", 4.4, PP_ALIGN.LEFT), ("Seuil", 2.6, PP_ALIGN.RIGHT),
                ("Plats qui changent", 3.1, PP_ALIGN.RIGHT)]
    bas = tableauVerso(diapo, MARGE, 2.05, colonnes, lignes, "Décalages", taille=15, hauteurLigne=0.4)
    plusActif = max(profils["scenarios"], key=lambda scenario: scenario["plats"])
    noms = platsDuDecalage(profils, plusActif)
    paragraphesMesures(diapo, MARGE, bas + 0.25, LARGEUR - 2 * MARGE, [
        [m(f"Sous le décalage le plus actif, changent par exemple : {', '.join(noms[:-1])} et {noms[-1]}. La liste entière "
           "est dans l'Excel de la sensibilité.", DEMI_GRAS, 15)],
        [m(f"Sur {total} plats, une valeur de profil bouge à la fois, sans casser leur ordre. NOVA ne vaut que 3 ou 4 dans "
           "nos plats préparés : un cran sur son seuil change plus de plats que 5 % sur un seuil nutritionnel.",
           TEXTE, 15, ENCRE_SECONDAIRE)]], "Lecture des décalages")


def platsDuDecalage(profils, scenario, nombreDePlats=3):
    """
    Les plats dont un décalage change la classe, pour les nommer sur la slide : les noms les plus
    courts, pour tenir sur une ligne (la liste entière est dans supernutri_sensibilite.xlsx).
    """
    noms = [plat["nom"] for plat in profils["plats"] if plat["code"] in scenario["codes"]]
    return sorted(noms, key=lambda nom: (len(nom), nom))[:nombreDePlats]


def slideDeuxModeles(presentation, autre, total):
    """
    Deux SuperNutri-scores sur deux bases : leurs céréales et nos plats, rangés par chaque modèle,
    face au Nutri-Score (même classe, puis à une classe près), puis les deux modèles entre eux.
    """
    leurs, nos = autre["leurs"], autre["nos"]
    chacunChezSoi = (leurs["leurFaceAuNutriscore"]["exactitude"] > leurs["notreFaceAuNutriscore"]["exactitude"]
                     and nos["notreFaceAuNutriscore"]["exactitude"] > nos["leurFaceAuNutriscore"]["exactitude"])
    titre = "Chaque modèle colle mieux au Nutri-Score sur sa propre base" if chacunChezSoi else "Deux modèles sur deux bases"
    communs = autre["recoupement"][0]
    diapo = nouvelleDiapo(presentation, titre,
                          f"Leur modèle, recodé depuis leur note, redonne leurs {autre['reproduits']} classes. "
                          + ("Aucun produit en commun." if communs == 0 else f"{communs} produits en commun."))
    largeur = 1.4                                    # chacune des six colonnes de nombres
    x = MARGE + 3.5
    colonne(diapo, x, 2.0, 3 * largeur - 0.2, f"Leurs {autre['total']} céréales", "leurs céréales")
    colonne(diapo, x + 3 * largeur, 2.0, 3 * largeur, f"Nos {total} plats", "nos plats")
    mesures = [("pareil", "même classe"), ("plusSevere", "plus sévère"), ("plusPermissif", "plus permissif")]
    colonnes = [("Part des produits", 3.5, PP_ALIGN.LEFT)] + [(titre, largeur, PP_ALIGN.RIGHT) for _ in (leurs, nos)
                                                              for _, titre in mesures]
    lignes = []
    for cle, libelle in (("notreFaceAuNutriscore", "Notre modèle face au Nutri-Score"),
                         ("leurFaceAuNutriscore", "Leur modèle face au Nutri-Score"),
                         ("notreFaceALeur", "Notre modèle face au leur")):
        lignes.append([libelle] + [pourcentage(comparaison[cle]["sens"][mesure], 1) for comparaison in (leurs, nos)
                                   for mesure, _ in mesures])
    bas = tableauVerso(diapo, MARGE, 2.75, colonnes, lignes, "Deux modèles", taille=15, hauteurLigne=0.5)
    # λ et sa valeur ne se séparent pas en fin de ligne : espaces insécables
    lams = [f"λ\u00a0=\u00a0{nombreCourt(lam)}" for lam in (autre["modele"]["lam"], 0.7)]
    bas = paragraphesMesures(diapo, MARGE, bas + 0.2, LARGEUR - 2 * MARGE, [[m(
        f"Même référence des deux côtés : notre calcul du Nutri-Score de 2023 redonne leurs {autre['total']} labels. Leur "
        f"modèle a {len(autre['modele']['criteres'])} critères et {lams[0]} ; le nôtre, onze et {lams[1]}.",
        TEXTE, 15, ENCRE_SECONDAIRE)]], "Lecture des deux modèles")
    ecarts = [ecartSigne(comparaison[cle]["sens"]["ecartMoyen"])
              for comparaison, cle in ((nos, "notreFaceAuNutriscore"), (leurs, "leurFaceAuNutriscore"),
                                       (leurs, "notreFaceAuNutriscore"), (nos, "leurFaceAuNutriscore"))]
    paragraphesMesures(diapo, MARGE, bas + 0.2, LARGEUR - 2 * MARGE, [[m(
        f"Chaque modèle est un peu plus sévère que le Nutri-Score sur sa base (écart moyen {ecarts[0]} classe pour le nôtre, "
        f"{ecarts[1]} pour le leur), bien plus sur celle de l'autre ({ecarts[2]} et {ecarts[3]}). Ils ne donnent la même "
        f"classe qu'à {pourcentage(leurs['notreFaceALeur']['exactitude'], 1)} de leurs céréales.", DEMI_GRAS, 16)]],
        "Réponse au sujet")


def slideCategories(presentation, autre):
    """
    Ce qui bloque chaque modèle sur la base de l'autre : les critères les plus souvent ratés au
    seuil de B′, puis un produit de chaque base, vu par le Nutri-Score et les deux modèles.
    """
    diapo = nouvelleDiapo(presentation, "Chaque modèle porte la catégorie pour laquelle il est fait",
                          "Au seuil de B′, la part des produits de l'autre base qui ratent chaque critère.")
    largeur = (LARGEUR - 2 * MARGE - 0.6) / 2
    exemples = {exemple["base"]: exemple for exemple in autre["exemples"]}
    for rang, (base, modele, sujet, titre, lam) in enumerate(
            (("leurs", "notre", "Notre modèle", "Notre modèle sur leurs céréales", 0.7),
             ("nos", "leur", "Leur modèle", "Leur modèle sur nos plats", autre["modele"]["lam"]))):
        x = MARGE + rang * (largeur + 0.6)
        colonne(diapo, x, 2.0, largeur, titre, titre)
        parts = sorted(autre[base]["bloquants"][modele].items(), key=lambda paire: -paire[1])[:3]
        bas = tableauVerso(diapo, x, 2.7, [("Critère raté", largeur - 1.4, PP_ALIGN.LEFT), ("Produits", 1.4, PP_ALIGN.RIGHT)],
                           [[majuscule(NOMS_COURTS[critere]), pourcentage(part)] for critere, part in parts],
                           f"Bloquants {base}", taille=15, hauteurLigne=0.38)
        exemple = exemples.get(base)
        if exemple is None:
            continue
        y = bas + 0.35
        boite(diapo, x, y, largeur, 0.4, [[m(exemple["nom"], DEMI_GRAS, 16)]], f"Exemple {base}")
        y += 0.5
        for numero, (lettre, legende, duModele) in enumerate(((exemple["label"], "Nutri-Score", False),
                                                              (exemple["leur"][0], "leur modèle", True),
                                                              (exemple["notre"][0], "notre modèle", True))):
            gauche = x + numero * 1.75
            pastille(diapo, gauche, y, 0.5, lettre, f"Exemple {base} {legende}", modele=duModele)
            boite(diapo, gauche + 0.6, y, 1.1, 0.5, [[m(legende, TEXTE, 12, ENCRE_SECONDAIRE)]], f"Légende {legende}",
                  ancrage=MSO_ANCHOR.MIDDLE)
        auDessus = exemple[f"{modele}AuDessus"]
        if auDessus:                                   # ce qui empêche le produit de monter d'une classe
            classe = exemple[modele]
            dessus = nomDeClasse(4 - "ABCDE".index(classe[0]) + 1)
            rates = enToutesLettres(auDessus["rates"])
            if "pr" in auDessus["rates"] and not exemple["proteinesComptees"]:
                rates = rates.replace("les protéines", "les protéines (le Nutri-Score ne les compte pas)")
            paragraphesMesures(diapo, x, y + 0.7, largeur, [[m(
                f"{sujet} range ce produit en {classe} : face à {dessus}, il rate {rates}, soit "
                f"{nombre(auDessus['poids'], 2)} du poids, plus que les {nombre(1 - lam, 2)} permis.",
                TEXTE, 14, ENCRE_SECONDAIRE)]], f"Raison {base}")


def slideDemonstrationFinale(presentation, resultats, plats):
    """La démonstration de l'interface : quatre gestes numérotés, dont les classes sont calculées ici."""
    supernutri = resultats["supernutri"]
    plat = platDExemple(plats)
    regle = supernutri["modele"]
    avant = nomDeClasse(affecter(valeursDuPlat(plat), regle)["classe"])
    apres = nomDeClasse(affecter(valeursDuPlat(dict(plat, nova=3, additifs=1)), regle)["classe"])
    diapo = nouvelleDiapo(presentation, "L'interface : le SuperNutri-score à côté du Nutri-Score",
                          "Démonstration en direct : streamlit run projet_gui.py")
    gestes = [f"La {plat['nom']} : {plat['label']} au Nutri-Score, {avant} au SuperNutri-score, avec ses barres.",
              f"NOVA 3 et un seul additif dans la saisie : elle passe en {apres}."]
    for modele in resultats.get("mrsortEtenduProfils", {}).get("modeles", []):
        if modele["nom"] == "sept" and modele["lam"] == 0.6:
            appris = regleDuModele(modele)
            classes = [nomDeClasse(affecter(plat, dict(appris, lam=lam))["classe"]) for lam in (0.6, 0.7)]
            if classes[0] != classes[1]:
                gestes.append(f"λ au curseur : MR-Sort à 7 critères (profils appris sur 375 plats) passe de {classes[0]} "
                              f"à {classes[1]} à λ = 0,7.")
    gestes.append("L'onglet SuperNutri-score : le modèle, ses sources, et les deux analyses de sensibilité.")
    y = 2.1
    for rang, geste in enumerate(gestes):
        repere(diapo, MARGE, y, rang + 1, f"Repère {rang + 1}")
        bas = paragraphesMesures(diapo, MARGE + 0.6, y, LARGEUR - 2 * MARGE - 0.6, [[m(geste, TEXTE, 18)]], f"Geste {rang + 1}")
        y = max(bas, y + 0.42) + 0.35


def slideConclusionFinale(presentation, donnees, sensibilite, autre):
    """Ce que nous retenons, en trois colonnes (le modèle, la comparaison, les limites), puis le merci."""
    diapo = nouvelleDiapo(presentation, "Ce que nous retenons", "Un modèle à nous, transparent, et ses limites.")
    total = sum(donnees["repartition"].values())
    principal = [point for point in sensibilite["courbe"] if point["amplitude"] == sensibilite["poids"]["amplitude"]][0]
    ecarts = donnees["ecarts"]
    cereales = autre["leurs"]["notreFaceAuNutriscore"]
    descentes, montees = (round(cereales["sens"][cle] * cereales["total"]) for cle in ("plusSevere", "plusPermissif"))
    colonnes = [
        ("Un score de santé", "Onze critères en trois piliers, des seuils tirés de textes officiels, des classes au sens "
                              "du Nutri-Score, et les protéines comptées comme lui."),
        ("Plus sévère", f"Sur nos {total} plats, {ecarts['descendent']} descendent, surtout en haut, et {ecarts['montent']} "
                        f"montent. Sur leurs céréales, {descentes} descendent, "
                        + ("aucune ne monte." if montees == 0 else f"{montees} montent.")),
        ("Ses limites", f"Sans veto, un plat très salé ne perd que la case du sel. {len(donnees['secsEnAPrime'])} de nos "
                        f"{donnees['repartition']['A′']} plats A′ sont des produits secs. {len(sensibilite['auBord'])} plats "
                        f"sont au bord : à ± {nombreCourt(principal['amplitude'])}, {pourcentage(principal['partMoyenne'], 1)} "
                        "des plats changent."),
    ]
    largeur = (LARGEUR - 2 * MARGE - 2 * 0.4) / 3
    for rang, (titre, texte) in enumerate(colonnes):
        x = MARGE + rang * (largeur + 0.4)
        colonne(diapo, x, 2.0, largeur, titre, titre)
        paragraphesMesures(diapo, x, 2.75, largeur, [[m(texte, TEXTE, 17)]], f"Texte {titre}")
    boite(diapo, MARGE, 6.05, LARGEUR - 2 * MARGE, 0.6, [[m("Merci.", TITRE, 28)]], "Merci")


def slidesSoutenance2(chemin=SORTIES[2]):
    """
    Écrit les slides de la soutenance finale et renvoie leur nombre. L'ordre suit les trois
    parties de l'oral : le modèle (1 à 4), le plat suivi, la comparaison et les deux sensibilités
    (5 à 8), puis l'autre groupe, la démonstration et la conclusion (9 à 11). Les chiffres
    portent sur nos 375 plats ; les notes de chaque slide reprennent le texte de l'oral.
    """
    resultats = lireResultats()
    if "supernutri" not in resultats:
        raise ValueError("La clé « supernutri » manque : lancer d'abord python3 projet_supernutri.py.")
    supernutri = resultats["supernutri"]
    donnees, sensibilite = supernutri[BASE_FINALE], supernutri["sensibilite"][BASE_FINALE]
    total = sum(donnees["repartition"].values())
    plats = lireBase(FICHIER_BASE)
    presentation = Presentation()
    presentation.slide_width = Inches(LARGEUR)
    presentation.slide_height = Inches(HAUTEUR)
    slideTitreFinale(presentation)
    slidePiliers(presentation, supernutri)
    slideSeuils(presentation, supernutri)
    slideSensDesClasses(presentation, supernutri, donnees)
    slidePoeleeFinale(presentation, supernutri, plats)
    slideFaceAuNutriscore(presentation, donnees)
    slideSensibilitePoids(presentation, sensibilite, total)
    slideSensibiliteProfils(presentation, sensibilite, total)
    if "autreGroupe" not in supernutri:
        raise ValueError("La clé « autreGroupe » manque : déposer leur base, puis lancer python3 projet_supernutri.py.")
    slideDeuxModeles(presentation, supernutri["autreGroupe"], total)
    slideCategories(presentation, supernutri["autreGroupe"])
    slideDemonstrationFinale(presentation, resultats, plats)
    slideConclusionFinale(presentation, donnees, sensibilite, supernutri["autreGroupe"])
    numeroterPages(presentation, "soutenance finale")
    notesParSlide = notesDuTexte(2)
    for numero, diapo in enumerate(presentation.slides, start=1):
        notes(diapo, notesParSlide.get(numero, ""))
    chemin.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(chemin)
    return len(presentation.slides)


def main():
    """Écrit les slides de la soutenance demandée."""
    parseur = argparse.ArgumentParser(description="Slides des soutenances du projet MR-Sort.")
    parseur.add_argument("--soutenance", type=int, choices=[1, 2], default=1)
    arguments = parseur.parse_args()
    if arguments.soutenance == 1:
        total = slidesSoutenance1()
    else:
        total = slidesSoutenance2()
    print(f"{total} slides écrites dans {SORTIES[arguments.soutenance].relative_to(DOSSIER)}")


if __name__ == "__main__":
    main()
