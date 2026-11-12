---
title: Texte de la soutenance intermédiaire
subtitle: Approcher le Nutri-Score par MR-Sort, vendredi 30 octobre 2026
---

# Le déroulé

Quinze minutes au plus, en trois parties. Le texte vise 13 minutes 50 secondes, pour garder une marge.

| Partie | Orateur | Slides | Durée |
|---|---|---|---|
| La base et le Nutri-Score | Daniel | 1 à 5 | 4 min 35 |
| MR-Sort | Anis | 6 à 8 | 4 min 45 |
| La démonstration et la suite | Biyao | 9 et 10 | 4 min 30 |

La répartition des orateurs n'est qu'une proposition : échangez les parties si vous le souhaitez.

Le texte de chaque slide est aussi dans les notes du fichier PowerPoint : il se lit en mode présentateur. On ne le récite pas mot pour mot. Les phrases sont courtes pour qu'on puisse les dire avec ses propres mots, mais les chiffres, eux, doivent être exacts.

À préparer avant de commencer :

- l'ordinateur avec les polices Archivo installées, et le PDF de secours sur une clé ;
- l'interface déjà lancée (`streamlit run projet_gui.py`), dans un onglet prêt, sur le calculateur ;
- le fichier PowerPoint ouvert en mode présentateur.

# Le texte, slide par slide

## Slide 1 : le titre (Daniel, 0 min 30)

**On montre :** le titre, les cinq pastilles du Nutri-Score à gauche, les cinq cadres de nos modèles à droite.

**On dit :**

Bonjour. Nous sommes Daniel Avila Haroche, Anis Islam Rezig et YIN Biyao. Notre question est simple : un modèle de tri multicritère facile à expliquer, MR-Sort, peut-il retrouver les classes du Nutri-Score sur des plats préparés ? Sur toutes nos slides, les classes officielles sont des pastilles pleines, et celles de nos modèles des cadres à barre de couleur, notés avec un prime : A prime, B prime, et ainsi de suite.

**Transition :** Pour comprendre la question, prenons un seul plat.

## Slide 2 : deux façons de ranger un plat (Daniel, 1 min 30)

**On montre :** la Poêlée Fermière de Cora : à gauche son détail de points, les négatifs en rouge et les positifs en vert, à droite ses barres de concordance.

**On dit :**

Voici la Poêlée Fermière de Cora. Le Nutri-Score compte des points négatifs, en rouge, sur ce qu'il faut limiter : énergie, graisses saturées, sucres et sel. Ici 3, dont 2 pour le sel. Et des points positifs, en vert, sur ce qu'il faut favoriser : protéines, fibres, fruits et légumes. Ici 2, pour les légumes. Le score est la différence : trois moins deux, un, classe B.

MR-Sort raisonne autrement. Il compare le plat à des profils, des plats fictifs qui marquent les frontières entre les classes. Pour franchir un profil, il faut que les critères où le plat est au moins aussi bon pèsent ensemble au moins λ, ici 0,6. La Poêlée Fermière franchit b3 avec 0,919, mais pas b4 : ses graisses saturées, qui pèsent 0,44 à elles seules, ne passent pas. Elle est donc en C prime.

Le Nutri-Score compense : un point de légumes efface un point de sel. MR-Sort ne compense pas : il fait voter les critères. Tout notre travail mesure ce que ce changement de logique garde et perd.

**Transition :** Pour le mesurer, il nous fallait une base.

## Slide 3 : la base (Daniel, 1 min 05)

**On montre :** l'entonnoir des filtres jusqu'au tirage, en cinq couleurs, puis le vivier de chaque classe.

**On dit :**

Notre base vient d'Open Food Facts. Nous avons repéré 732 candidats parmi les plats préparés vendus en France, en tirant des pages au hasard, pour ne pas prendre seulement les plats les plus populaires. Nous lisons ensuite chaque fiche par l'API produit, qui donne le calcul officiel du Nutri-Score de 2023.

Sept filtres s'appliquent. Le plus sévère, ce sont les fibres non déclarées : on passe de 594 à 237 plats. Nous écartons aussi les cas particuliers du Nutri-Score, viande rouge, fromages, boissons et matières grasses, qui ont leurs propres règles. Il reste 224 plats, et nous en tirons 25 par classe, soit 125 plats.

Toutes les réponses d'Open Food Facts sont gardées : la base se reconstruit à l'identique, sans réseau.

**Transition :** Pourquoi les plats préparés, et pas les céréales de l'exemple du sujet ?

## Slide 4 : les sept critères (Daniel, 0 min 45)

**On montre :** le tableau des minimums, médianes et maximums des sept critères.

**On dit :**

Parce que, dans les plats préparés, les sept critères varient tous : l'énergie va de 47 à 2 373 kJ, le sel de 0 à 5,20 g, les fruits et légumes de 0 à 97 %. Dans les céréales du petit-déjeuner, la teneur en fruits et légumes est presque toujours nulle. Le modèle à 3 critères du sujet, énergie, sodium et fruits, n'en aurait alors plus que deux.

**Transition :** Avant d'approcher le Nutri-Score, il fallait savoir le calculer exactement.

## Slide 5 : notre Nutri-Score (Daniel, 0 min 45)

**On montre :** le tableau des contrôles, les deux exemples du sujet puis la base. La colonne du calcul se lit points négatifs moins points positifs.

**On dit :**

Notre algorithme est celui que le sujet appelle la version de mars 2025 : le Nutri-Score actualisé en 2023, entré en vigueur en France le 16 mars 2025. Il retrouve les deux exemples du sujet, le Cruesli à 1 point et le Sésame Gerblé à 9 points. Surtout, il retrouve le score et le label d'Open Food Facts pour 125 plats sur 125. Et la base n'a pas été filtrée par notre calcul : la vérification n'est donc pas circulaire.

**Transition :** Anis va maintenant montrer comment MR-Sort range ces 125 plats.

## Slide 6 : MR-Sort en une image (Anis, 1 min 30)

**On montre :** le diagramme des profils de la Poêlée Fermière, et ses deux barres de concordance décisives.

**On dit :**

Voici MR-Sort en une image, toujours sur la Poêlée Fermière. Chaque axe vertical est un critère, avec le mieux toujours en haut. Les quatre traits de couleur sont les profils, de b2 à b5. Nous les avons fixés à partir des données : sur chaque critère, chaque profil est le milieu des médianes des deux classes qu'il sépare. Le trait noir, c'est le plat. En bas, sous chaque axe, le poids appris de chaque critère.

Sur un axe, si le plat est au-dessus d'un profil, ce critère compte pour lui. Les barres en dessous en font le total. Pour b3, tous les critères passent sauf les protéines : 0,919, au-dessus de λ. Pour b4, les graisses saturées ne passent plus, et il ne reste que 0,479. Le plat s'arrête donc en C prime.

**Transition :** Ces poids, nous ne les avons pas choisis à la main : ils sont appris.

## Slide 7 : les modèles (Anis, 1 min 45)

**On montre :** le tableau des quatre modèles et la matrice de confusion.

**On dit :**

Les poids sont appris par un programme linéaire en nombres entiers, résolu par HiGHS. Il cherche les poids qui rangent bien le plus de plats possible.

À 7 critères, 90 plats sur 125 sont rangés comme le Nutri-Score, soit 72 %, à λ = 0,6 comme à 0,7. Surtout, 97,6 % des plats sont à une classe près. Sur la matrice, presque tout est sur la diagonale ou juste à côté, et seuls 3 plats sont à plus d'une classe : MR-Sort se trompe aux frontières, pas sur le fond. À 3 critères, on tombe à 73 plats, 58,4 %.

Une remarque honnête : plusieurs jeux de poids donnent le même résultat, et le solveur en rend un. D'où des poids très inégaux, comme 0,44 pour les graisses saturées. Départager ces solutions fait partie de la suite.

**Transition :** À 3 critères, on peut aller plus loin : prouver qu'aucun modèle n'est exact.

## Slide 8 : à 3 critères, aucun modèle exact (Anis, 1 min 30)

**On montre :** les deux versos côte à côte, la purée et le colin.

**On dit :**

Pour le prouver, il suffit d'une paire de plats. La purée au beurre et à la crème de Picard fait mieux que le colin d'Alaska d'Auchan sur les trois critères du modèle : moins d'énergie, 741 contre 774 kJ, moins de sel, 0,49 contre 0,61 g, et autant de fruits et légumes, aucun.

Or MR-Sort est monotone : un plat au moins aussi bon partout est rangé au moins aussi haut. Le Nutri-Score, lui, met la purée en D et le colin en A, à cause de ce que le modèle ne voit pas : 9,8 g de graisses saturées contre 0,5, et 1,5 g de protéines contre 13. Aucun modèle à 3 critères ne peut donc reproduire le Nutri-Score, et notre base contient 143 paires de ce genre.

À 7 critères, il n'y en a aucune, puisque le Nutri-Score est lui-même monotone. La question d'un modèle exact reste donc ouverte. Nous la trancherons par un programme linéaire complet, qui apprend à la fois les poids, les profils et λ.

**Transition :** Biyao va vous montrer tout cela en direct.

## Slide 9 : l'interface (Biyao, 3 min 30)

**On montre :** la slide annotée quelques secondes, puis l'interface en direct (voir « La démonstration, pas à pas »).

**On dit :**

L'interface reprend tout ce que vous venez de voir, pour n'importe quel plat. Je pars d'un plat de la base, la Poêlée Fermière : sa fiche s'affiche, avec son code-barres, et les sept valeurs se remplissent. Au centre, le Nutri-Score : la bande des lettres, le score de 1, et le détail des points avec leurs jauges. À droite, les deux modèles MR-Sort : C prime à 7 critères, et la barre de concordance montre pourquoi.

Je baisse maintenant les graisses saturées, de 1,6 à 1,4 g. Le Nutri-Score ne bouge pas, toujours B. Mais le plat franchit b4 et passe en B prime, comme le Nutri-Score : on voit le seuil de MR-Sort à l'œuvre. Je change λ, et le modèle appris à 0,7 se charge. Enfin, en bas, tous les paramètres sont modifiables, poids et profils. À chaque fois, on voit pourquoi un plat est classé.

**Transition :** Pour finir, la suite du projet.

## Slide 10 : la suite (Biyao, 1 min)

**On montre :** la frise des trois dates.

**On dit :**

Le 27 novembre, nous présenterons le SuperNutri-score : un modèle MR-Sort à nous, sur 9 critères. Ce sont les 7 composantes, le degré de transformation, NOVA, et le nombre d'additifs, avec des profils ancrés sur les seuils des allégations nutritionnelles. Une variante ajoutera le Green-Score, pour mesurer l'effet de l'environnement. D'ici là, nous apprendrons aussi les profils à poids fixés, puis tous les paramètres à la fois. Le rapport sera rendu le 10 janvier. Merci de votre attention.

# La démonstration, pas à pas

1. Ouvrir l'onglet de l'interface, sur le calculateur.
2. Dans « Partir d'un plat », taper « Poêlée » et choisir « Base, classe B : Poêlée Fermière (Cora) ».
3. Montrer la fiche du plat et son code-barres, puis le Nutri-Score : B, score 1, et au détail des points, 3 points négatifs en rouge et 2 points positifs en vert.
4. Montrer le panneau « MR-Sort à 7 critères » : C′, avec la phrase « franchit b3, pas b4 » et les barres de concordance. La grande case des graisses saturées est blanche pour b4.
5. Changer « Acides gras saturés » de 1,6 à 1,4 : le Nutri-Score reste B, et le modèle passe en B′. Dire « comme le Nutri-Score ».
6. Cliquer sur λ = 0,7 : la classe reste B′ avec le modèle appris à 0,7.
7. Descendre aux « Paramètres des modèles MR-Sort », montrer les poids et les profils, puis cliquer « Revenir aux paramètres appris ».

Si l'interface ne répond pas : dérouler les étapes sur la slide 9 (captures numérotées, et le geste de l'étape 5 écrit en bas), puis revenir aux slides 2 et 6, qui montrent en grand les mêmes calculs : le détail des points et les barres de concordance.

# Questions probables du jury

**Pourquoi les plats préparés, et pas les céréales ?** Parce que les sept critères y varient. Dans les céréales, les fruits et légumes valent presque toujours 0 %, et le modèle à 3 critères n'en aurait que deux. La catégorie est aussi large, ce qui permet un vrai tirage au hasard.

**Comment êtes-vous sûrs de rester sous 25 % de recoupement ?** Les candidats viennent de pages tirées au hasard, et les 125 plats d'un tirage au hasard parmi 224. Dès qu'un autre groupe nous transmet sa base, une fonction mesure le recoupement par code-barres, rapporté à la plus petite des deux bases.

**Le sujet parle de la version de mars 2025, vous de 2023 : lequel avez-vous appliqué ?** C'est le même algorithme. Santé publique France l'appelle « Nutri-Score actualisé en 2023 », et il est entré en vigueur en France le 16 mars 2025 ; la FAQ officielle qui le décrit est datée du 17 mars 2025. Le sujet lui-même le confirme : ses composantes vont de 0 à 55 et de 0 à 17 points, les maximums de l'algorithme actualisé, contre 40 et 15 en 2017.

**Pourquoi la règle de 2023 et pas celle de la figure 4 ?** C'est la règle officielle actuelle : la FAQ de Santé publique France du 17 mars 2025, pages 29 et 30, et le calcul d'Open Food Facts. La figure 4 reprend la règle de 2017. Notre code sait appliquer les deux, et sur notre base, la figure 4 ne changerait le label d'aucun plat.

**Avez-vous eu des écarts avec Open Food Facts ?** Un seul, que nous avons corrigé. Pour une soupe, Open Food Facts affichait 0,4 g de sel dans son calcul, mais comptait 0,4043 g, juste au-dessus du seuil : un point de plus. Open Food Facts arrondit l'affichage, pas le calcul. L'API donne les deux valeurs, et notre base prend la valeur exacte du tableau nutritionnel.

**Pourquoi le sel et pas le sodium ?** Les barèmes de 2023 sont en sel, et le sodium vaut le sel divisé par 2,5. Comme les deux rangent les plats dans le même ordre, MR-Sort donne exactement les mêmes classes.

**Pourquoi exclure la viande rouge, les fromages, les boissons et les matières grasses ?** Ils ont leurs propres règles : par exemple, les protéines de la viande rouge sont plafonnées à 2 points. Le sujet demande un calculateur à 7 composantes : nous restons dans le cas général, et les exclusions sont comptées dans l'entonnoir.

**Pourquoi fixer les profils par les médianes ?** C'est la définition la plus simple d'un plat-frontière : sur chaque critère, le milieu des médianes des deux classes voisines. Les profils doivent ensuite rester ordonnés. Limite : dans les plats préparés, les plats E sont souvent riches en protéines, si bien que les profils de protéines et de fibres sont plats, et ces critères pèsent peu.

**Comment le programme linéaire apprend-il les poids ?** Chaque plat donne deux conditions sur les poids. Un plat B, par exemple, doit franchir b4 : face à b4, les poids des critères qui votent pour lui doivent faire au moins λ. Et il ne doit pas franchir b5 : face à b5, ils doivent rester sous λ, à une marge ε = 0,001 près, comme le propose l'annexe B du sujet. Les profils étant fixés, on sait déjà quels critères votent : ces conditions sont de simples sommes de poids. Avec 125 plats, elles se contredisent. Le programme donne donc à chaque plat une variable qui vaut 1 s'il est bien rangé et 0 sinon, puis il maximise le nombre de plats bien rangés : c'est pour cela qu'il est en nombres entiers. Le solveur prouve qu'avec ces profils, 90 est le maximum, à λ = 0,6 comme à 0,7.

**Pourquoi la Poêlée Fermière ne peut-elle pas être en B prime ?** Avec nos profils, c'est impossible, quels que soient les poids. Face à b4 comme face à b5, ce sont les mêmes critères qui votent pour elle : l'énergie, les sucres, le sel, les fibres, et les fruits et légumes. Sa concordance est donc la même face aux deux profils : soit elle les franchit tous les deux, et elle est en A prime, soit elle n'en franchit aucun. 9 plats de la base sont dans ce cas. Sur nos 35 erreurs à 7 critères, 9 viennent donc des profils eux-mêmes, et 26 des conflits entre plats. C'est pourquoi nous apprendrons aussi les profils.

**Pourquoi des poids si inégaux ?** Plusieurs jeux de poids rangent aussi bien les plats, et le solveur en rend un. Nous prévoyons de choisir, parmi les meilleures solutions, celle qui laisse le plus de marge aux plats.

**Un plat qui passe la frontière sur un seul critère change-t-il de classe ?** Pas forcément. MR-Sort ne demande ni un critère, ni la majorité des critères, mais une majorité pondérée : les poids des critères qui votent pour le plat doivent faire au moins λ. Ce n'est pas le nombre de critères qui compte, mais leur poids. Un seul critère peut donc faire basculer le plat, s'il complète la coalition. C'est ce qu'on voit en démonstration : à 1,4 g, les graisses saturées votent pour le plat face à b4, et leurs 0,44 portent la concordance de 0,479 à 0,919. Nos poids donnent même un rôle à part aux graisses saturées : dans le modèle à λ = 0,6, les six autres critères ne font ensemble que 0,56, moins que λ, et c'est aussi vrai à 0,7. Aucun plat ne franchit donc un profil s'il ne le vaut pas au moins sur les graisses saturées.

**Que change λ ?** Un λ plus haut exige des coalitions de critères plus larges pour franchir un profil. Ici, les deux seuils rangent 90 plats sur 125, avec des poids différents.

**Existe-t-il un modèle exact à 7 critères ?** Nous ne le savons pas encore. Aucune paire inversée ne l'exclut, car le Nutri-Score est monotone. Un programme linéaire complet, qui apprend aussi les profils et λ, donnera le meilleur modèle possible, ou une borne qui prouve qu'il n'existe pas.

**Les données d'Open Food Facts sont-elles fiables ?** Elles sont collaboratives. Nous écartons les valeurs impossibles, et la teneur en fruits et légumes est estimée par OFF à partir des ingrédients. Le 125 sur 125 prouve que notre calcul est fidèle à celui d'OFF, pas que les étiquettes sont exactes.

**Votre base est-elle reproductible ?** Oui. Toutes les réponses d'Open Food Facts sont en cache, et un test vérifie qu'on retrouve les mêmes 125 codes-barres sans réseau.

**Avez-vous utilisé l'intelligence artificielle ?** Oui, et le rapport le déclarera avant l'introduction, comme le demande le sujet. Un assistant d'IA générative nous a aidés à écrire le code, les tests, l'interface et les documents. Les décisions sont celles du groupe, et nous devons pouvoir expliquer chaque partie.
