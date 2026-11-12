# Product

<!-- impeccable:product-schema 1 -->

Projet du cours « Transparence des algorithmes pour la décision » (M2 MIAGE ID-SITN, université Paris Dauphine-PSL, Brice Mayag), année 2026-2027. Faits confirmés par le groupe entre le 28 et le 29/10/2026 : choix de la catégorie, de la direction, du format des productions et de leur portée.

## Platform

web

L'interface est une application Streamlit (`projet_gui.py`). Les autres productions sont des documents générés par le code : les slides PowerPoint (`slides_projet.py`), le rapport PDF (XeLaTeX), les textes de soutenance (PDF) et les classeurs Excel.

## Users

- **Le jury**, c'est-à-dire l'enseignant. Il lit le code, le rapport et les Excel, et assiste aux deux soutenances. Son travail : vérifier que chaque résultat est juste, compris et expliqué.
- **La promotion**, qui assiste aux soutenances et à la démonstration de l'interface.
- **Le consommateur du sujet** (§3.5). Il saisit les 7 composantes d'un aliment et lit le Nutri-Score, puis les classes données par les modèles MR-Sort, avec des paramètres qu'il peut modifier.

## Product Purpose

Approcher le Nutri-Score par un modèle de tri multicritère transparent, MR-Sort, puis proposer notre propre modèle, le SuperNutri-score. On travaille sur une base de 125 plats préparés vendus en France, tirée d'Open Food Facts. Le projet réussit si la base respecte le sujet, si le Nutri-Score est reproduit, si les questions du sujet reçoivent une réponse démontrée, et si chaque classe donnée par un modèle peut être expliquée.

## Positioning

Le projet ne se contente pas d'un taux de bonne classification : il montre pourquoi un plat est classé. Les classes s'expliquent par les profils franchis ou non, et l'existence d'un modèle exact est démontrée : 143 paires inversées prouvent qu'aucun MR-Sort à 3 critères n'est exact. Toutes les valeurs viennent d'un calcul reproductible depuis le cache d'Open Food Facts.

## Operating Context

- Les soutenances durent 15 minutes chacune, devant toute la promotion : intermédiaire le 30/10/2026, finale le 27/11/2026. La démonstration de l'interface se fait en direct, en mode présentateur.
- Le rendu final a lieu le 10/01/2027 sur Teams : le rapport, les Excel et le code source commenté.
- Le correcteur lit le code : il doit rester simple, commenté en français, avec les noms de fonctions imposés (`MRSort_sept`, `MRSort_trois`).

## Capabilities and Constraints

- La base : 125 plats préparés, 25 par classe A à E, avec les 7 composantes du Nutri-Score de 2023, NOVA, les additifs et le Green-Score.
- Le Nutri-Score de 2023, cas général seulement : ni boisson, ni fromage, ni matière grasse, ni viande rouge.
- MR-Sort à 7 et à 3 critères, à λ = 0,6 et 0,7 : profils fixés par les médianes, poids appris par programme linéaire. Restent à venir l'apprentissage des profils et le modèle complet (phase 2).
- Le SuperNutri-score : les 7 composantes, NOVA et les additifs ; une variante ajoute le Green-Score (phase 3, pas encore construit).
- Langue : tout est en français, interface, textes et code.
- L'usage de l'IA générative est autorisé, et déclaré dans le rapport.

## Brand Commitments

- Les noms imposés par le sujet : « SuperNutri-score », les classes A′ à E′ pour les modèles, A à E pour le Nutri-Score.
- Les classes officielles et celles des modèles ne doivent jamais se confondre.

## Evidence on Hand

- La base : `donnees/base_plats_prepares.xlsx` et le cache `donnees/brut/`.
- Les résultats : `resultats/resultats_projet.json`, les Excel des modèles, `resultats/figures/`.
- Les slides : `resultats/slides_soutenance_intermediaire.pptx` et leur PDF.
- Les textes : `soutenance/texte_soutenance_1.md` et `soutenance/dossier_soutenance_1.md`.
- Aucun avis d'utilisateur ni aucune mesure d'usage n'existe : rien de tel ne doit être inventé.

## Product Principles

1. **Chaque nombre montre sa raison.** Une classe s'accompagne toujours de ce qui la cause : profil franchi ou non, critères qui passent, poids.
2. **Tout chiffre cité vient du code.** Les textes et les slides citent `resultats_projet.json`, et des tests le vérifient.
3. **La démarche est honnête.** Les limites sont dites, comme les solutions de poids multiples ou les données collaboratives d'OFF, et les écarts trouvés en route aussi, comme l'arrondi d'OFF.
4. **Le code reste lisible par un humain** : des boucles simples, une docstring par fonction, pas de classes dans le calcul.
