---
title: La démarche jusqu'à la soutenance intermédiaire
subtitle: Ce qui a été fait, comment, et pourquoi (état au 29 octobre 2026)
---

# Ce que demande la soutenance

Le sujet (§3.7) demande, pour la soutenance intermédiaire du 30 octobre, une présentation de 15 minutes au plus. Le tableau donne chaque attendu et l'endroit où il est couvert.

| Attendu du sujet | Où il est couvert |
|---|---|
| La base de données construite | slides 3 et 4 ; `donnees/base_plats_prepares.xlsx` |
| L'interface graphique du Nutri-Score | slide 9 et la démonstration ; `projet_gui.py` |
| Un modèle d'approximation, à 7 ou 3 critères, appliqué à la base | slides 6 à 8 ; nous présentons les deux |
| La comparaison avec le Nutri-Score | slides 7 et 8 : exactitude, matrice de confusion, paires inversées |

La slide 2 pose la question sur un plat réel, et la slide 10 annonce la suite : le SuperNutri-score, le 27 novembre.

# Le choix de la catégorie

Le sujet demande au moins 100 aliments, « le plus possible d'une même catégorie », dont au moins 20 par label. Nous avons comparé plusieurs catégories d'Open Food Facts (OFF) vendues en France avant de retenir les **plats préparés**, pour trois raisons.

- **Les sept critères y varient tous.** Dans les céréales du petit-déjeuner, l'exemple du sujet, la teneur en fruits et légumes est presque toujours nulle. Le modèle à 3 critères demandé par le sujet (énergie, sodium, fruits et légumes) n'en aurait plus que deux.
- **Le vivier est large dans chaque classe.** On peut donc vraiment tirer au hasard, et rester loin de la règle des 25 % de recoupement avec les autres groupes.
- **Les plats préparés se prêtent au SuperNutri-score.** Beaucoup sont ultra-transformés et contiennent des additifs, deux critères que le Nutri-Score ignore.

# La base : 125 plats tirés au hasard

La base est construite par `projet_base.py`, en quatre étapes.

1. **Le repérage.** L'index de recherche d'OFF donne des codes-barres de plats préparés vendus en France. Cet index range encore les produits selon le Nutri-Score de 2021 : il sert seulement à trouver des candidats de chaque classe. On y tire des pages au hasard (graine 2026), pour ne pas prendre seulement les plats les plus populaires. Au total : 732 candidats repérés.
2. **La lecture des fiches.** Pour chaque candidat, l'API produit d'OFF donne le calcul officiel du Nutri-Score de 2023, composante par composante. C'est la seule source retenue pour le score et le label. OFF limite le débit, à environ 15 fiches par minute en pratique : le script fait des pauses et réessaie quand OFF refuse.
3. **Les filtres**, dans l'ordre. L'entonnoir compte les candidats qui restent après chaque étape :

| Étape | Plats restants |
|---|---|
| Candidats repérés | 732 |
| Fiche disponible | 730 |
| Plat préparé vendu en France | 696 |
| Nutri-Score 2023 calculé | 686 |
| Cas général du Nutri-Score | 594 |
| Sept composantes connues | 237 |
| NOVA et additifs connus | 230 |
| Valeurs plausibles | 224 |
| Sans doublon | 224 |

Le filtre le plus sévère, ce sont les fibres non déclarées. Le cas général écarte la viande rouge, les fromages, les boissons et les matières grasses, qui suivent d'autres règles. **Notre propre calcul n'est pas un filtre** : sinon, la vérification du Nutri-Score serait circulaire.

4. **Le tirage.** Parmi les 224 plats retenus (47 A, 50 B, 58 C, 33 D, 36 E), on en tire 25 par classe : 125 plats. Les plats E étaient les plus rares : beaucoup de plats classés E sont à la viande rouge ou sans fibres déclarées. Le script a donc ajouté une page de candidats E.

La base est un classeur Excel de trois feuilles :

- « base » : une ligne par plat, avec les 7 composantes, le score et le label d'OFF, NOVA, les additifs, le Green-Score ;
- « lisez-moi » : les sources, la méthode et les unités ;
- « contrôles » : l'entonnoir et les conditions du sujet, toutes remplies.

Toutes les réponses d'OFF sont gardées dans `donnees/brut/`, et `python3 projet_base.py --depuis-cache` reconstruit exactement la même base, sans réseau.

# Le Nutri-Score de 2023

`projet_nutriscore.py` applique les barèmes des figures 2, 3 et 5 du sujet. Ce sont ceux de l'algorithme actualisé en 2023, celui que le sujet appelle « version de mars 2025 » : il est entré en vigueur en France le 16 mars 2025, et la FAQ officielle qui le décrit est datée du 17 mars 2025. Ses maximums, 55 points négatifs et 17 positifs, sont ceux que donne le sujet (ceux de 2017 étaient 40 et 15).

- **Les points.**
  - Énergie, acides gras saturés, sucres et sel donnent de 0 à 55 points négatifs.
  - Protéines, fibres, et fruits, légumes et légumineuses donnent de 0 à 17 points positifs.
  - Une valeur égale à un seuil reçoit les points du bas.
- **La règle des protéines.** À partir de 11 points négatifs, les protéines ne comptent plus.
  - La figure 4 du sujet reprend la règle de 2017, qui les gardait au-delà de 80 % de fruits et légumes.
  - L'algorithme de 2023 a supprimé cette exception (FAQ officielle du 17 mars 2025, pages 29 et 30), et c'est lui que nous appliquons.
  - Le code sait appliquer les deux : sur notre base, la règle de la figure 4 ne changerait le label d'aucun plat.
- **La vérification.**
  - Le calcul retrouve les deux exemples du sujet : le Cruesli à 9 − 8 = 1 (B), le Sésame Gerblé à 11 − 2 = 9 (C).
  - Il retrouve aussi le score et le label d'OFF pour 125 plats sur 125.
- **Ce que la vérification nous a appris.** Une « Soupe pdt/courgette » avait d'abord un point de sel de moins qu'OFF. OFF affiche 0,4 g de sel dans son calcul, mais compte les points avec la valeur exacte, 0,4043 g, juste au-dessus du seuil de 0,4. La base reprend donc les valeurs exactes du tableau nutritionnel.

# MR-Sort

**Le modèle** (`projet_mrsort.py`).

- MR-Sort range un plat dans l'une de cinq classes ordonnées, de E′ à A′. Quatre profils, de b2 à b5, sont des plats fictifs qui marquent les frontières entre classes.
- Un plat franchit un profil quand les critères où il est au moins aussi bon que ce profil pèsent ensemble au moins λ.
- Il est rangé dans la classe du meilleur profil qu'il franchit : A′ s'il franchit b5, et ainsi de suite.
- Ce modèle ne compense pas : un excellent score sur un critère ne rattrape pas un mauvais score sur un autre, contrairement au Nutri-Score, qui additionne des points.

**Les profils sont fixés à partir des données** (`projet_apprentissage.py`).

- Sur chaque critère, le profil qui sépare deux classes voisines est le milieu de leurs médianes : c'est le plat-frontière typique.
- Les profils doivent ensuite rester ordonnés, un profil plus haut étant au moins aussi bon que le précédent.
- Conséquence visible : dans les plats préparés, les plats E sont souvent riches en protéines (viande, fromage). Les profils de protéines et de fibres sont donc plats, et ces critères pèsent peu.

**Les poids sont appris par un programme linéaire en nombres entiers**, résolu par HiGHS.

- Pour chaque plat, une variable dit s'il doit être bien rangé.
- Pour un plat de la classe C_k, bien rangé veut dire : il franchit le profil du bas de sa classe, et ne franchit pas celui du haut, avec une marge ε = 0,001 pour l'inégalité stricte.
- On maximise le nombre de plats bien rangés.
- Les poids sont ensuite arrondis au millième, ou au dix-millième si l'arrondi déplaçait un plat.

**Les résultats.**

| Modèle | λ | Bien rangés | Exactitude | À une classe près |
|---|---|---|---|---|
| 7 critères | 0,6 | 90/125 | 72,0 % | 97,6 % |
| 7 critères | 0,7 | 90/125 | 72,0 % | 96,8 % |
| 3 critères | 0,6 | 73/125 | 58,4 % | 92,8 % |
| 3 critères | 0,7 | 73/125 | 58,4 % | 92,8 % |

À 7 critères, seuls 3 plats sont à plus d'une classe du Nutri-Score : MR-Sort se trompe aux frontières, pas sur le fond.

**L'existence d'un modèle exact.**

- MR-Sort est monotone : un plat au moins aussi bon partout est rangé au moins aussi haut. Il suffit donc d'une paire de plats où le meilleur partout est le moins bien classé pour prouver qu'aucun MR-Sort n'est exact.
- **À 3 critères, notre base contient 143 paires de ce type.**
  - Par exemple, la « Purée de pomme de terre, beurre et crème d'Isigny » (Picard, classe D) fait mieux que le « Colin d'Alaska » (Auchan, classe A) sur l'énergie (741 contre 774 kJ), sur le sel (0,49 contre 0,61 g), et fait jeu égal sur les fruits et légumes (0 %).
  - Ce que le modèle ne voit pas fait la différence : 9,8 g de graisses saturées contre 0,5, et 1,5 g de protéines contre 13.
- **À 7 critères, il n'y a aucune paire de ce type**, puisque le Nutri-Score est lui-même monotone. La question reste ouverte. Un programme linéaire complet, qui apprend à la fois les poids, les profils et λ, la tranchera en phase 2.

**Une limite.**

- Plusieurs jeux de poids rangent aussi bien les plats, et le solveur en rend un. D'où des poids très inégaux : 0,4396 pour les graisses saturées à λ = 0,6, 0,549 à λ = 0,7.
- Choisir parmi ces solutions celle qui laisse le plus de marge aux plats est prévu pour la suite.

**L'exemple suivi dans tout l'exposé** est la Poêlée Fermière de Cora.

- Nutri-Score : 3 − 2 = 1, classe B.
- MR-Sort à 7 critères, λ = 0,6 : elle franchit b3 (0,919) mais pas b4 (0,479), à cause des graisses saturées, d'où la classe C′.
- Avec 1,4 g de graisses saturées au lieu de 1,6, elle franchit b4 et passe en B′, alors que le Nutri-Score reste en B.

# L'interface

`projet_gui.py` (Streamlit) suit le modèle des interfaces des TP : les calculs restent dans les modules, et l'interface ne fait que les mettre en forme. Ses deux onglets :

- **Le calculateur**, en trois colonnes :
  - la saisie des 7 composantes, ou un plat de la base, avec sa fiche ;
  - le Nutri-Score : la bande des lettres, le score et le détail des points ;
  - les deux modèles MR-Sort : la classe, sa raison et les barres de concordance, avec le choix de λ.

  Les poids et les profils se modifient en bas de la page, et les classes suivent.
- **La base** : la répartition par classe, l'entonnoir, la vérification du Nutri-Score et le tableau des 125 plats.

Lancement : `streamlit run projet_gui.py` ; le thème est lu dans `.streamlit/config.toml`.

# Les slides et le design

Les 10 slides sont générées par `slides_projet.py` : tous leurs chiffres viennent du code, et la génération s'arrête si un texte déborde. Elles ont été vérifiées dans PowerPoint, et un PDF de secours, polices incorporées, est dans `resultats/`.

Les éléments que l'on doit lire de loin sont dessinés en formes PowerPoint, à leur taille réelle : l'entonnoir de la base, le détail des points, les barres de concordance et les deux versos de la slide 8. Le diagramme des profils est tracé à la taille où il s'affiche, pour que ses textes restent lisibles. Les notes de chaque slide reprennent le texte de l'oral.

**La direction visuelle, « Verso de l'emballage »**, est la même partout : interface, slides, figures, rapport et Excel.

- Chaque production se lit comme le verso d'un emballage : noir et blanc, filets épais et maigres comme un tableau nutritionnel, police Archivo seule, et la couleur réservée aux classes.
- Les classes officielles sont des pastilles pleines, celles de nos modèles des cadres à barre de couleur.
- Les jetons de design sont dans `projet_design.py`.
- Les polices Archivo (licence OFL) sont des instances statiques tirées de la police variable. Les titres utilisent le gras d'« Archivo Condensed », car PowerPoint ne trouvait pas une famille nommée « Archivo Condensed ExtraBold ».

# Les tests et les commandes

La suite de tests (`python3 -m pytest -q`, depuis `PROJET/`) vérifie :

- les exemples du sujet et les annexes B et C ;
- les filtres et le tirage de la base, et sa reconstruction depuis le cache ;
- la reproduction du Nutri-Score sur les 125 plats ;
- les apprentissages, l'interface sous AppTest et la génération des slides ;
- les chiffres cités dans le README et dans ces textes.

| Commande | Effet |
|---|---|
| `python3 projet_base.py --depuis-cache` | reconstruit la base, sans réseau |
| `python3 projet_nutriscore.py` | exemples du sujet, puis vérification sur la base |
| `python3 projet_mrsort.py` | les quatre modèles et les paires inversées |
| `streamlit run projet_gui.py` | l'interface |
| `python3 slides_projet.py --soutenance 1` | les slides |
| `python3 projet_soutenance.py` | le PDF de ce dossier et du texte d'oral |

# Ce qui reste à faire

- **Phase 2, jusqu'au 13 novembre** :
  - apprendre les profils à poids fixés, ces poids étant proportionnels aux points maximaux du Nutri-Score ;
  - apprendre le modèle complet, pour savoir si un modèle exact existe à 7 critères ;
  - comparer les huit modèles et tester leur généralisation ;
  - ajouter le pas à pas à l'interface ;
  - échanger les bases avec un autre groupe avant le 6 novembre.
- **Phase 3, jusqu'au 27 novembre** :
  - construire le SuperNutri-score, sur 9 critères : les 7 composantes, NOVA et les additifs ;
  - ajouter sa variante avec le Green-Score ;
  - faire les analyses de sensibilité aux poids et aux profils ;
  - le tester sur la base de l'autre groupe ;
  - préparer la soutenance finale.
- **Phase 4, jusqu'au 10 janvier** : le rapport, avec la déclaration d'usage de l'IA avant l'introduction. Le gel interne est fixé au 3 janvier.

# Comment ce travail a été produit

Le travail a été réalisé avec un assistant d'IA générative, Claude (Anthropic), dans l'outil Claude Code. Le groupe a donné les orientations et pris les décisions :

- la catégorie, retenue sur une analyse préliminaire ;
- la direction visuelle, choisie parmi trois propositions ;
- la production des slides et du rapport par le code ;
- les critères du SuperNutri-score.

L'assistant a écrit, sous ces orientations :

- le plan de production ;
- l'extraction des données ;
- le code des algorithmes et des apprentissages, et les tests ;
- l'interface, les slides et ces documents.

Chaque membre du groupe doit relire et comprendre chaque partie, car le sujet exige que le code soit « parfaitement compréhensible par ses auteurs ». Cette section sert de base à la déclaration exigée par le sujet (§4), à placer dans le rapport avant l'introduction.
