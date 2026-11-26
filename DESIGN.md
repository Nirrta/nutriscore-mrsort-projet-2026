---
name: Projet MR-Sort
description: Le verso de l'emballage, un tableau nutritionnel bien composé, pour expliquer pourquoi un plat est classé
colors:
  papier: "#FFFFFF"
  encre: "#000000"
  trame: "#E9E9E6"
  encre-secondaire: "#5C5C58"
  classe-a: "#038141"
  classe-b: "#85BB2F"
  classe-c: "#FECB02"
  classe-d: "#EE8100"
  classe-e: "#E63E11"
typography:
  display:
    fontFamily: "Archivo Condensed, Archivo, sans-serif"
    fontWeight: 800
    fontSize: "3.2rem"
    lineHeight: 1
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Archivo Condensed, Archivo, sans-serif"
    fontWeight: 800
    fontSize: "1.7rem"
    lineHeight: 1.1
  body:
    fontFamily: "Archivo, sans-serif"
    fontWeight: 400
    fontSize: "1rem"
    lineHeight: 1.5
  label:
    fontFamily: "Archivo, sans-serif"
    fontWeight: 600
    fontSize: "0.92rem"
  data:
    fontFamily: "Archivo, sans-serif"
    fontWeight: 400
    fontFeature: "tnum"
rounded:
  none: "0px"
spacing:
  filet-panneau: "8px"
  filet-groupe: "4px"
  filet-ligne: "1px"
components:
  pastille-nutriscore:
    backgroundColor: "{colors.classe-a}"
    textColor: "{colors.papier}"
    rounded: "{rounded.none}"
  cadre-modele:
    backgroundColor: "{colors.papier}"
    textColor: "{colors.encre}"
    rounded: "{rounded.none}"
  champ-saisie:
    backgroundColor: "{colors.trame}"
    textColor: "{colors.encre}"
    rounded: "{rounded.none}"
---

# Design System: Projet MR-Sort

## Overview

**Idée directrice : « le verso de l'emballage ».** Chaque production se lit comme le dos d'un paquet : un tableau nutritionnel bien composé, des filets épais et maigres, des chiffres alignés.

Le noir et blanc porte toute la structure, et la couleur vient du Nutri-Score : ses classes, et ses points (rouge pour les négatifs, vert pour les positifs). L'ambiance est sobre, précise et lisible, celle d'une notice qu'on peut vérifier.

La direction a été choisie par le groupe le 28/10/2026, parmi trois propositions. Elle rompt volontairement avec le style « carnet » des TP (fond crème, serif, accent terracotta, petites capitales en chasse fixe), jugé trop proche des productions générées par défaut.

Les jetons font foi dans `projet_design.py`. `.streamlit/config.toml` et `rapport/verso.sty` les reprennent.

## Colors

### Primary

- **Encre** (#000000) : un vrai noir, comme sur un tableau nutritionnel. Texte, filets, cadres et cases pleines.

### Neutral

- **Papier** (#FFFFFF) : le fond de toutes les productions.
- **Trame** (#E9E9E6) : les champs de saisie, les en-têtes de tableau et ce que le modèle ne voit pas (sur la slide des deux versos).
- **Encre secondaire** (#5C5C58) : les légendes, les unités et les notes. Contraste suffisant sur le papier.

### Named Rules

- **La couleur vient du Nutri-Score.** Les cinq couleurs officielles, de A (#038141) à E (#E63E11), disent une classe, jamais une décoration.
- **Les points du Nutri-Score ont deux couleurs** (29/10), comme dans les captures d'Open Food Facts des fig. 6 et 7 du sujet : le rouge de E pour les points négatifs, le vert de A pour les positifs (`COULEUR_NEGATIFS`, `COULEUR_POSITIFS`).
  - Ces couleurs remplissent les cases pleines des jauges, et les repères carrés « − » et « + » des en-têtes « Points négatifs N » et « Points positifs P ».
  - Elles ne colorent jamais un texte : le rouge de E est trop clair pour un petit texte. Le sens reste écrit dans les en-têtes, pour qui confond le rouge et le vert.
- **La lettre posée sur une classe** est blanche sur A et E, noire sur B, C et D.

## Typography

Une seule famille, Archivo (Omnibus-Type, licence OFL), en instances statiques tirées de la police variable par `design/generer_polices.py`.

### Hierarchy

- **Display et headline** : Archivo Condensed en gras, de graisse 800. Titres, grandes lettres de classe et chiffres clés (le score, « 125/125 »).
- **Body** : Archivo 400.
- **Label** : Archivo SemiBold 600, pour les intertitres et les en-têtes de tableau.
- **Data** : Archivo avec ses chiffres tabulaires, alignés à droite, et la virgule décimale.

L'échelle va de 12 à 72 dans l'interface, de 18 à 96 dans les slides, et de 9 à 18 dans le rapport.

### Named Rules

- **Le gras condensé s'appelle « Archivo Condensed ».** PowerPoint remplace par Calibri une famille nommée « Archivo Condensed ExtraBold » : on désigne donc la famille « Archivo Condensed », en gras.
- **λ, ε et Σ passent par une police de repli** (Arial, ou DejaVu Sans dans matplotlib), car Archivo n'a pas de lettres grecques.
- **Pas de capitales espacées en surtitre, ni d'étiquettes en chasse fixe.** Le texte est en minuscules, avec la seule majuscule initiale.
- **L'apostrophe est typographique (’)** dans les slides, et les paragraphes de l'interface évitent le mot seul en dernière ligne (`text-wrap: pretty`).

## Layout

- Le texte est aligné à gauche, avec de larges marges blanches. Les lignes de texte font moins de 65 caractères.
- Dans l'interface, le calculateur a trois colonnes : la saisie, le Nutri-Score, les modèles MR-Sort. Les paramètres des modèles occupent toute la largeur en dessous. Chaque colonne fait au moins 24rem : sous 1 400 px de large environ, la colonne MR-Sort passe sous les deux autres, sur toute la largeur, et sous 970 px environ, les trois s'empilent.
- Dans les slides : un titre qui énonce le constat, une seule figure ou un seul tableau par slide, la page en bas à droite. Ce qui doit se lire de loin est dessiné en formes PowerPoint, à sa taille réelle ; une figure matplotlib est tracée à sa taille d'affichage, avec des textes d'au moins 12 points.

## Elevation & Depth

Tout est plat : pas d'ombre, pas de dégradé. La profondeur vient des filets et de la trame.

## Shapes

- Aucun angle arrondi : `baseRadius = "none"` dans le thème.
- **Les filets codent la hiérarchie** : 8 px en tête de panneau, 4 px entre groupes, 1 px entre lignes.

## Components

### Pastille du Nutri-Score

Un carré plein de la couleur officielle de la classe, avec sa lettre. Dans la bande A à E, la lettre obtenue est agrandie et cernée de noir.

### Cadre d'une classe de modèle

Un carré blanc à bord noir de 3 px, avec la lettre et son prime (A′), et une barre de 7 px de la couleur de la classe en bas. Il ne doit jamais se confondre avec la pastille officielle.

### Tableaux

Chaque tableau a un filet de 4 px sous son en-tête et un filet de 1 px entre ses lignes. Ses nombres sont alignés à droite, avec leur unité.

### Champs de saisie

Des champs Streamlit sur fond trame, à bord noir, avec le libellé et l'unité (« Énergie (kJ) »).

### Barre de concordance (composant signature)

Pour un profil, une barre faite d'une case par critère, de largeur égale à son poids. La case est noire si le plat vaut au moins le profil sur ce critère, blanche sinon, et la barre est suivie de son verdict (« 0,919 ≥ 0,6, franchi »). C'est le geste fort du système : elle montre pourquoi MR-Sort classe un plat. Dans les slides, elle est dessinée en formes PowerPoint, avec les mêmes cases que dans l'interface.

### Graphiques des slides

Un graphique est un tableau Verso qui se met à dessiner : mêmes filets (4 px sous l'en-tête, 1 px entre les lignes), même Archivo, et la colonne des nombres devient une barre noire, carrée, avec sa valeur écrite au bout. Pas d'axe : les nombres qui comptent sont écrits. La trame grise porte le « tout » derrière une barre (100 %, les plats qui descendent, le maximum des tirages).

- **La barre des poids** : une case blanche par critère, large comme son poids, sous le titre de son pilier ; le repère de λ est un trait noir vertical. C'est la barre de concordance avant qu'un plat la remplisse.
- **La matrice face au Nutri-Score** : en ligne les pastilles pleines du Nutri-Score, en colonne les cadres du modèle ; chaque case est grise, d'autant plus foncée qu'elle compte de produits (1 − 0,85 × part) ; la diagonale, la même classe, est encadrée de noir ; les zéros ne s'écrivent pas.
- La couleur reste aux classes du Nutri-Score : aucune barre de graphique n'est en couleur, sauf la répartition par classe.

### Diagramme des profils

Un axe vertical par critère, le mieux toujours en haut, les profils b2 à b5 en traits de couleur, et le plat en trait noir épais. Le poids de chaque critère est écrit sous son axe.

## Do's and Don'ts

### Do:

- Accompagner chaque classe de sa raison : barre de concordance, profils, points.
- Réserver la couleur au Nutri-Score (ses classes, ses points), et garder le noir et blanc pour la structure.
- Prendre tout chiffre affiché dans `resultats_projet.json` ou dans les modules de calcul.

### Don't:

- Pas de fond crème, de serif, d'accent terracotta, ni d'ombre ou de dégradé.
- Pas de numéros 01, 02 hors d'une vraie séquence, ni de « → » dans les boutons.
- Pas de bande latérale pour signaler un encadré ou une erreur : un filet de 4 px en tête, comme les panneaux.
- Ne pas employer de couleur de classe pour décorer, ni mettre une pastille pleine pour une classe de modèle.
