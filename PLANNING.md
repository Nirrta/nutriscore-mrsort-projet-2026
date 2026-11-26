# Planning de production : projet MR-Sort 2026-2027

Sujet : *Élaboration d'un modèle transparent d'évaluation des aliments, basé sur l'approche MR-Sort* (`docs/Projet_2026_2027.pdf`).
Cours : *Transparence des algorithmes pour la décision*, M2 MIAGE ID-SITN, Brice Mayag.

Ce fichier suit l'avancement. On coche une case quand le livrable est fait **et vérifié** : tests verts, chiffres repris du JSON. Mis à jour le 07/11/2026.

## Échéances

| Date | Livrable | Contenu exigé |
|---|---|---|
| **ven. 30/10/2026** | Soutenance intermédiaire, 15 min | la base, l'interface Nutri-Score, un modèle d'approximation à 7 ou 3 critères appliqué à la base, la comparaison avec le Nutri-Score |
| **ven. 27/11/2026** | Soutenance finale, 15 min | le SuperNutri-score, les réponses de la §3.4, l'interface |
| **dim. 10/01/2027, 23 h 59** | Rendu sur Teams | le rapport (avec la déclaration d'IA avant l'introduction), les fichiers Excel et le code source commenté |

Tout retard est sanctionné. Le gel interne est fixé au **dim. 03/01/2027**.

## Journal des décisions

| Date | Décision | Pourquoi |
|---|---|---|
| 28/10 | Catégorie : **plats préparés** (`en:meals`, vendus en France) | Les 7 critères y varient tous, alors qu'avec les céréales la teneur en fruits et légumes vaut presque toujours 0 %, ce qui viderait `MRSort_trois`. Le vivier de chaque classe est grand, donc le recoupement avec les autres groupes reste faible |
| 28/10 | Direction visuelle **« Verso de l'emballage »** | Noir et blanc, filets de tableau nutritionnel, Archivo. La seule couleur vient des classes. On sort du style « carnet » crème des TP |
| 28/10 | Rapport et slides **générés par le code** | Les chiffres et les figures viennent toujours des résultats, et le design reste le même partout |
| 28/10 | SuperNutri-score : **7 composantes + NOVA + additifs** ; le Green-Score dans une **variante à part** | Les classes A′ à E′ gardent un sens nutritionnel ; la variante mesure l'effet de l'environnement sans le mêler au modèle principal |
| 28/10 | Nutri-Score : **règle des protéines de 2023** | La fig. 4 du sujet reprend la règle de 2017, alors que la FAQ officielle et Open Food Facts appliquent celle de 2023. L'écart sera mesuré sur la base |
| 28/10 | Base tirée de l'**API produit** d'OFF | L'index de recherche garde les classes de 2021, alors que l'API produit donne le calcul de 2023, composante par composante |
| 28/10 | Les **valeurs exactes** du tableau nutritionnel plutôt que les valeurs arrondies du calcul d'OFF | OFF compte les points avec la valeur exacte : 0,4043 g de sel donne 2 points, et non 1 comme 0,4 g. C'est ce qui permet de reproduire 125/125 plats |
| 28/10 | Titres en « Archivo Condensed » gras (graisse 800), et non une famille « Archivo Condensed ExtraBold » | Vérifié dans le vrai PowerPoint : il remplaçait cette famille par Calibri, alors qu'il trouve « Archivo Condensed » en gras |
| 28/10 | Poids appris : on garde la solution du solveur ; le départage par la plus grande marge est reporté en phase 2 | Plusieurs jeux de poids rangent aussi bien les plats ; c'est à dire à l'oral |
| 29/10 | La « version de mars 2025 » du sujet est l'**algorithme actualisé en 2023** : c'est bien celui que nous appliquons | La FAQ officielle (version du 17 mars 2025) le nomme « Nutri-Score actualisé en 2023 » et le fait entrer en vigueur en France le 16 mars 2025 ; les maximums du sujet (55 et 17 points) sont les siens. Précisé sur la slide 5, à l'oral et dans le code |
| 29/10 | Le rendu comprend le **cache d'Open Food Facts** (`donnees/brut/`, 4,3 Mo), `.streamlit/` et `static/` | Le cache permet au correcteur de reconstruire exactement la même base, sans réseau ; `.streamlit/` et `static/` donnent à l'interface son thème et ses polices |
| 29/10 | Les **points négatifs en rouge, les positifs en vert**, avec les en-têtes « Points négatifs N » et « Points positifs P » (slides et interface) | C'est la lecture des fig. 6 et 7 du sujet (captures d'OFF). Les couleurs sont celles des classes E et A, déjà dans la palette : la règle devient « la couleur vient du Nutri-Score » |
| 29/10 | **Oral allégé** : ni la règle des 25 %, ni la fig. 4, ni la soupe, ni la déclaration d'IA | Ce ne sont pas des résultats demandés pour la soutenance. Les réponses restent prêtes dans les questions du jury, et le dossier, le README et le code les gardent |
| 07/11 | **Base étendue à 375 plats** (la base du 30/10, plus 50 par classe tirés hors de la base) : on mesure sur des plats non vus, puis on réapprend sur tout | Sur le cache, l'exactitude sur des plats jamais vus monte de 60 % (25 plats appris) à 70 % (125) et plafonne vers 73 % : plus de plats aide un peu, le plafond vient du modèle. La base du 30/10 reste, et ses chiffres aussi. Le filtre des fibres reste : OFF compte 0 point pour des fibres non déclarées (50 des 123 plats sans fibres sont E) |
| 07/11 | **Tous les cas du Nutri-Score de 2023** (fromage, viande rouge, matières grasses, boissons, eaux), vérifiés contre OFF ; dans l'interface, le type est **proposé par OFF, mais modifiable** | « L'algorithme actuel » du sujet (§3.2) les comprend. OFF les déduit de ses catégories et se trompe sur des plats composés (des lasagnes en viande rouge), que la FAQ laisse au cas général |
| 07/11 | L'interface cherche un produit par **code-barres, lien OFF ou nom** ; le cache d'abord, puis OFF, sans rien écrire | La consigne du sujet (§3.5) est la saisie des 7 valeurs : la recherche s'y ajoute, et remplit ces mêmes champs |
| 07/11 | **Les poids ne sont pas uniques** : on rapporte leurs intervalles, et l'on départage par la plus grande marge (Leroy, Mousseau et Pirlot, 2011) | À 7 critères et λ = 0,6, le poids des AGS va de 0,334 à 0,498 parmi les modèles qui rangent 90 plats. La réponse du jury préparée pour le 30/10 (« les six autres critères ne font que 0,56, moins que λ ») ne vaut, à λ = 0,6, que pour la solution du solveur ; à 0,7, elle vaut pour tous les optimums. Le rapport et la soutenance du 27/11 citent les intervalles |
| 08/11 | **Vérification de l'interface** : premier écran sur la Poêlée Fermière ; une saisie impossible est signalée (AGS au-delà des lipides, code de moins de 8 ou de plus de 14 chiffres) ; les exemples du sujet sont hors du domaine de MR-Sort ; mise en page vérifiée de 375 à 1 440 px (colonnes, jauges, tableaux, « Appris sur » en grille) | 40 parcours de l'interface sans exception, mais six défauts : à 1 440 px, deux des quatre choix d'« Appris sur » étaient cachés ; sur un téléphone, les colonnes et le tableau des points étaient coupés ; un code trop court était cherché comme un nom ; des AGS au-delà des lipides passaient sans un mot ; le premier écran (fig. 6, des céréales) opposait B à E′ sans dire qu'il sort du domaine des modèles ; matplotlib avertissait à chaque titre |
| 08/11 | **Ergonomie de l'interface** : « Revenir aux valeurs du produit » (valeurs et type d'origine) ; la classe du plat rappelée au-dessus de chaque éditeur ; le pas à pas nomme le plat ; la barre des onglets reste en haut ; un seul vocabulaire des modèles (« Apprentissage », « 125 plats, profils appris ») ; chaque profil porte la classe qu'il ouvre, « b5 (A′) » ; aide des champs des fruits et des fibres ; choisir un plat vide la recherche ; meilleurs résultats en gras dans l'onglet Modèles | Revue faite à 1 440 × 900 et sous AppTest : rechoisir un plat ne rendait pas ses valeurs, alors que la démonstration modifie les AGS ; les éditeurs étaient à 1 000 px du verdict ; le calculateur et l'onglet Modèles nommaient autrement les mêmes modèles ; « b5 » ne disait pas qu'il ouvre A′. Écartés : ouvrir un plat depuis l'onglet Base (la liste « Partir d'un plat » filtre déjà par le nom), un bouton « Voir le pas à pas » (les onglets collés suffisent, sans relance), la fiche sous les champs (elle identifie le produit) |
| 09/11 | **Le domaine des modèles se voit** : hors des plats préparés du cas général, la classe MR-Sort est indicative (cadre en pointillés, encadré qui dit pourquoi) ; une eau n'en a pas. **Les trois apprentissages sur les 375 plats**, comparés par validation croisée (5 parts de 75, la même limite de temps pour tous) ; l'interface a deux choix, « Appris sur » et « Apprentissage », et montre par défaut le meilleur en validation croisée | Le Yop, un yaourt à boire (une boisson depuis 2023, FAQ p. 18), recevait une classe A′ comparée au barème des boissons, sous un avertissement discret. Un modèle appris sur les 375 plats les a tous vus : seule la validation croisée le mesure sur des plats nouveaux. Étendre encore la base est écarté : plus aucun plat A en réserve dans le cache, et 750 plats de test ne départageraient pas profils appris et tout appris |
| 09/11 | **La mise en veille ne coupe plus un apprentissage** : `resoudreCreux` recommence un calcul que la veille a coupé ; les lignes touchées de la validation croisée et les modèles sur 375 plats sont recalculés | L'horloge du solveur compte la veille du Mac dans sa limite de temps. Le premier `--etendue`, lancé la nuit, arrêtait le modèle complet à 3 critères et λ = 0,7 à 242 plats au lieu de 248, et dans la validation croisée, les apprentissages des profils à 3 critères s'arrêtaient après 8 à 16 s de calcul au lieu de 300 |
| 20/11 | **Le SuperNutri-score** : onze critères en trois piliers, à limiter 0,40, à favoriser 0,30, transformation et production 0,30 (NOVA 0,10, nombre d'additifs 0,075, additifs à risque 0,075, bio 0,05) ; profils tirés du règlement CE 1924/2006 (A′) et des barèmes du Nutri-Score de 2023 ; λ = 0,7 ; classes au sens du Nutri-Score | Un score de santé, dont chaque seuil a une source. Le bio fait en partie doublon avec NOVA et les additifs : il garde le plus petit poids, pour les pesticides qu'aucun autre critère ne mesure |
| 20/11 | **Pas de Green-Score**, ni en critère ni en variante | Il changerait le sens des classes, c'est un agrégat opaque, et il manque pour 43 plats sur 125 |
| 20/11 | **λ se règle au curseur** dans l'interface, avec les poids et les profils | Le §3.5 demande de saisir les paramètres d'un modèle à la main, et λ en est un |
| 25/11 | **Les protéines votent comme le Nutri-Score de 2023 les compte**, selon le type du produit (choix 37 du README) | Une revue de notre modèle a montré que les protéines votaient pour des plats gras et salés : la règle du Nutri-Score manquait. Ce n'est pas un veto, mais la valeur du critère |
| 25/11 | **La base de l'autre groupe** (300 céréales, Branchu, Becavin, Bundhoo, Castan) : leur modèle recodé dans notre moteur, leurs céréales complétées par OFF (additifs, bio), la comparaison sur les deux bases ; ils n'ont pas besoin de notre base | Le §3.4 demande nos résultats sur leur base, face aux leurs. Leur modèle redonne leurs 300 classes : la comparaison est loyale |
| 25/11 | **Deux slides de comparaison** dans la soutenance finale (12 slides, 14 min 40) | La comparaison au Nutri-Score et à l'autre groupe est la réponse au §3.4 |
| 26/11 | **Chaque comparaison dit son sens** : plus sévère, pareil, plus permissif, écart moyen (choix 34) | Le Nutri-Score n'est pas à copier, mais c'est la référence : on dit dans quel sens on s'en écarte. Notre modèle est plus sévère que lui (+0,43 classe en moyenne), surtout en haut ; plus permissif pour des plats chargés, faute de veto |
| 26/11 | **Des graphiques à la place des tableaux** dans huit slides de la soutenance finale : la barre des poids (2, 6, 10), les matrices grisées (7, 11), les barres (8, 9, 12) ; on ne coupe que le texte que le graphique dit déjà | Chaque slide prouvait son titre par un tableau de nombres : à lire, pas à voir. Les chiffres, les titres et le texte dit ne changent pas |

## Phase 0 : mise en place (mer. 28/10)

- [x] Arborescence de `PROJET/`, squelettes des modules avec les noms imposés (`MRSort_sept`, `MRSort_trois`)
- [x] Polices Archivo en instances statiques (`design/generer_polices.py`), jetons de design (`projet_design.py`)
- [x] Thème Streamlit (`.streamlit/config.toml`), squelette du rapport LaTeX, qui compile
- [x] `PLANNING.md`, `README.md`, entrée `projet-gui` dans `.claude/launch.json`, section Projet de `CLAUDE.md`

## Phase 1 : sprint de la soutenance intermédiaire (mer. 28/10 → ven. 30/10)

Le périmètre est figé : tout le reste attend la phase 2.

- [x] **(a) La base** (`projet_base.py`) : 732 candidats, 224 retenus, 125 tirés (25 par classe), toutes les conditions du sujet remplies, Excel au style Verso
- [x] **(b) Le Nutri-Score** (`projet_nutriscore.py`) : algorithme de 2023, tests sur les exemples du sujet et sur les produits de 2025
- [x] (b) Vérification sur la base : 125/125 plats reproduits ; la règle de la fig. 4 ne change aucun label
- [x] (c) Le cœur de MR-Sort (concordances, affectation), testé sur les annexes B et C ; l'apprentissage des poids (programme linéaire) et les profils par médianes, testés sur l'annexe B
- [x] **(c) MR-Sort sur la base** : 7 critères 90/125 (72 %), 3 critères 73/125 (58 %), à λ = 0,6 et 0,7 ; 143 paires inversées à 3 critères, aucune à 7
- [x] (d) L'interface : le calculateur du Nutri-Score (saisie, exemples du sujet, détail des points) et l'onglet Base, testés sous AppTest et vérifiés dans le navigateur
- [x] **(d) L'interface** : les panneaux MR-Sort à 7 et 3 critères, le choix de λ, les paramètres modifiables sur toute la largeur
- [x] (e) Les figures (diagramme des profils, matrice de confusion, entonnoir) et le générateur des 10 slides, avec la trame d'oral dans les notes de chaque slide
- [x] (e) Les 10 slides générées sur les résultats (`resultats/slides_soutenance_intermediaire.pptx`), relues sur un rendu approché, avec la capture de l'interface
- [x] (e) Ouverture dans PowerPoint avec les polices installées, et PDF de secours (`resultats/slides_soutenance_intermediaire.pdf`, polices incorporées)
- [x] Polices installées sur le Mac de soutenance (`~/Library/Fonts`, le 28/10)
- [x] ~~Si la soutenance se fait depuis un autre ordinateur : y installer les polices de `design/polices/`, ou présenter le PDF~~ (sans objet après le 30/10 ; repris pour le 27/11 en phase 3)
- [x] (e) Le texte de l'oral (trois orateurs, 14 min 15 s) et le dossier de la démarche, en Markdown et en PDF (`soutenance/`, `projet_soutenance.py`), chiffres vérifiés par `tests/test_soutenance.py` (29/10)
- [x] (d) L'interface enrichie (29/10) : la fiche du plat avec son code-barres, les jauges de points, les barres de concordance. Sous 1 400 px de large environ, la colonne MR-Sort passe sous les deux autres (vérifié de 1 024 à 1 920 px, détecteur d'Impeccable sans remarque)
- [x] (e) Les slides enrichies (29/10) : un plat suivi tout l'exposé (la Poêlée Fermière), points, barres de concordance, entonnoir et versos dessinés en formes PowerPoint, tableau des contrôles du Nutri-Score, frise des dates ; les notes reprennent le texte de l'oral ; export PDF par PowerPoint
- [x] `PRODUCT.md` et `DESIGN.md` : le contexte et le système « Verso » décrits pour Impeccable (29/10)
- [x] ~~Répétition le jeu. 29/10 au soir~~ (sans objet après le 30/10)

Déroulé du 30/10 (le texte complet est dans `soutenance/texte_soutenance_1.md`) :

1. Le titre (Daniel).
2. Deux façons de ranger la Poêlée Fermière : B pour le Nutri-Score, C′ pour MR-Sort (Daniel).
3. La base : l'entonnoir des filtres, puis le tirage de 25 plats par classe (Daniel).
4. Les sept critères varient tous dans les plats préparés (Daniel).
5. Notre Nutri-Score : les exemples du sujet, 125/125 sur la base (Daniel).
6. MR-Sort en une image : le diagramme des profils et les deux profils décisifs (Anis).
7. Les quatre modèles et la matrice de confusion (Anis).
8. À 3 critères, aucun modèle exact : la purée et le colin (Anis).
9. La démonstration de l'interface (Biyao).
10. La suite : le SuperNutri-score, et les dates (Biyao).

## Phase 2 : les modèles complets (lun. 02/11 → ven. 13/11)

- [x] Poids fixés (points maximaux), profils appris : `apprendreProfils`, `python3 projet_mrsort.py --profils` (07/11)
- [x] Modèle complet (poids, profils et λ appris) : par alternance (`apprendreParAlternance`), et la recherche d'un modèle exact (`apprendreModeleComplet`, `chercherUnModeleExact`), `python3 projet_mrsort.py --complet` (07/11)
- [x] La base étendue (375 plats), la courbe d'apprentissage et le test des modèles du 30/10 sur les 250 plats ajoutés (`resultats/generalisation.xlsx`) ; les modèles réappris sur 375 plats (07/11)
- [x] Les intervalles des poids et le départage par la plus grande marge (07/11)
- [x] L'interface : recherche par code-barres, lien OFF ou nom, tous les cas du Nutri-Score de 2023, « Appris sur » (07/11)
- [x] Comparaison des modèles appris sur la base (les deux apprentissages, le modèle complet), sur la base et sur les 250 plats ajoutés : première feuille de `resultats/generalisation.xlsx` (07/11)
- [x] Interface : onglet Modèles (comparaison, modèle exact, courbe) ; « Appris sur » propose aussi les profils appris et le modèle complet (07/11)
- [x] Interface : onglet Pas à pas, pour le plat et le modèle du calculateur : les profils sur leur diagramme, les concordances partielles, la concordance, l'affectation (08/11)
- [x] Interface, ergonomie : « Revenir aux valeurs du produit », la classe au-dessus de chaque éditeur, le pas à pas qui nomme le plat, les onglets collés en haut, un seul vocabulaire des modèles (« Apprentissage »), les profils nommés par leur classe, l'aide des champs des fruits et des fibres (08/11)
- [x] Interface : le domaine des modèles (classe indicative, raison précise, pas de classe pour une eau) (09/11)
- [x] Les trois apprentissages sur les 375 plats et leur validation croisée (`--etendue`, `--croisee`) ; l'interface : « Appris sur » et « Apprentissage » (09/11)
- [x] Contacter un autre groupe et échanger les bases (leur base est arrivée le 25/11, avec les codes-barres)

## Phase 3 : le SuperNutri-score (lun. 09/11 → ven. 27/11)

- [x] Les choix du SuperNutri-score : critères, poids, profils, λ, sens des classes A′ à E′ (20/11, voir les décisions)
- [x] Le modèle, onze critères en trois piliers (20/11)
- [x] Sensibilité aux poids et aux profils (20/11)
- [x] Comparaison au Nutri-Score, plat par plat (20/11)
- [x] La base d'un autre groupe (25-26/11) : leurs 300 céréales complétées par OFF, leur modèle recodé, les deux modèles sur les deux bases, le sens des écarts
- [x] La règle des protéines du Nutri-Score de 2023 (25/11)
- [x] ~~Variante verte~~ : écartée le 20/11 (voir les décisions)
- [x] Interface : le SuperNutri-score au calculateur, son onglet, λ au curseur (20/11)
- [x] Slides finales et texte de l'oral, 11 slides, 13 min 50 (20/11), puis 14 slides, 14 min 50 (26/11) : la transformation (NOVA, additifs à risque) et le modèle de l'autre groupe ont chacun leur slide ; les tableaux de huit slides deviennent des graphiques (26/11)
- [ ] Répétition (23-26/11)
- [ ] Avant le 27/11 : si la soutenance se fait depuis un autre ordinateur, y installer les polices de `design/polices/`, ou présenter le PDF
- [ ] **Soutenance finale le 27/11**

## Phase 4 : le rapport et le rendu (sam. 28/11 → dim. 10/01)

- [ ] `projet_rapport.py` : `chiffres.tex` et les figures générés (fin novembre)
- [ ] `figurePoints` (la figure des points du rapport) alignée sur le tableau en couleur des slides : en-têtes signés, jauges rouges et vertes
- [ ] Sections 1 à 3 : introduction, Nutri-Score, MR-Sort (01-11/12)
- [ ] Sections 4 à 6 : SuperNutri-score, visualisation, conclusion (12-20/12)
- [ ] Déclaration d'usage de l'IA, relue par tout le groupe
- [ ] Relecture du code et des commentaires, nettoyage des fichiers non rendus (21/12-03/01)
- [ ] **Gel interne le 03/01**, puis dépôt sur Teams : le PDF, `donnees/base_plats_prepares.xlsx`, les Excel de résultats, les `.py`

## Rôles (à répartir)

| Rôle | Périmètre | Membre |
|---|---|---|
| Données | base, filtres, échange avec l'autre groupe | à attribuer |
| Algorithmes | Nutri-Score, MR-Sort, apprentissages, tests | à attribuer |
| Interface | `projet_gui.py`, démonstrations | à attribuer |
| Oral | slides, trame, répétitions | à attribuer |
| Rapport | rédaction, relecture, déclaration d'IA | à attribuer |

## Risques

| Risque | Parade |
|---|---|
| Open Food Facts lent ou limité (erreurs 503) | toutes les réponses sont en cache (`donnees/brut/`), avec des pauses et des relances ; l'extraction n'est faite qu'une fois |
| Trop peu de plats A ou E après les filtres | des repérages complémentaires automatiques ; les fibres manquantes restent un motif d'exclusion |
| Programmes linéaires trop longs | une limite de temps, la borne prouvée rapportée, et une recherche locale en secours pour les profils |
| Base de l'autre groupe dans un autre format | une table de correspondance des colonnes, avec NOVA et additifs récupérés par code-barres |
| Polices absentes sur l'ordinateur de soutenance | installation d'Archivo, plus un PDF de secours |
| Recoupement de plus de 25 % avec un autre groupe | le tirage au hasard, et `intersectionAvecAutreBase` dès l'échange des bases |

## Questions ouvertes

- La répartition des rôles.
- Le groupe avec qui échanger les bases.
- La date de l'atelier SuperNutri-score (09/11 proposé).
