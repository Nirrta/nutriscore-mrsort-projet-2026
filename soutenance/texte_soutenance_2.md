---
title: Texte de la soutenance finale
subtitle: Le SuperNutri-score, vendredi 27 novembre 2026
---

# Le déroulé

Quinze minutes au plus, en trois parties. Le texte vise 14 minutes 50 secondes, pour garder une marge.

| Partie | Orateur | Slides | Durée |
|---|---|---|---|
| Le modèle et la transformation | Daniel | 1 à 5 | 4 min 55 |
| Le plat suivi, la comparaison et les deux sensibilités | Anis | 6 à 9 | 5 min 00 |
| L'autre groupe, la démonstration et la conclusion | Biyao | 10 à 14 | 4 min 55 |

La répartition des orateurs n'est qu'une proposition : échangez les parties si vous le souhaitez.

Comment lire ce texte, slide par slide :

- **On montre** : ce que l'on pointe sur la slide ;
- **On dit** : le texte à dire, en phrases courtes. Il est aussi dans les notes du PowerPoint, en mode présentateur. On ne le récite pas : on le raconte ;
- **Pour comprendre** : pour nous seulement, à ne pas dire. Les définitions, le détail des calculs et les questions possibles. Ce bloc n'est pas dans les notes du PowerPoint.

À préparer avant de commencer :

- l'ordinateur avec les polices Archivo installées, et le PDF de secours sur une clé ;
- l'interface déjà lancée (`streamlit run projet_gui.py`), dans un onglet prêt, sur le calculateur ;
- le fichier PowerPoint ouvert en mode présentateur.

Tous les chiffres viennent de `python3 projet_supernutri.py` : nos 375 plats, et les 300 céréales de l'autre groupe.

# Les mots à connaître

- **MR-Sort** (Majority Rule Sorting) : une méthode qui range des produits dans des classes ordonnées, ici de A′ à E′. Elle vient de la famille ELECTRE TRI (chapitre 4 du cours). Chaque critère a un poids, et les poids font 1 en tout.
- **Profil** : la frontière entre deux classes. b5 ouvre A′, b4 ouvre B′, b3 ouvre C′ et b2 ouvre D′ ; sous b2, c'est E′. Pour chaque critère, le profil donne la valeur à atteindre.
- **Concordance** : face à un profil, la somme des poids des critères où le produit vaut au moins le profil. Ces critères « votent pour » le produit : ce sont les cases noires des barres.
- **λ (le seuil majoritaire)** : un produit franchit un profil si sa concordance vaut au moins λ, 0,7 chez nous. Sa classe est celle du plus haut profil qu'il franchit.
- **Veto** : dans un MR-Sort complet, un critère très raté interdit de franchir le profil, quoi que disent les autres. Notre modèle n'en a pas : c'est le MR-Sort simple que le sujet demande.
- **Classe prime** : A′ à E′ sont les classes de nos modèles, des cadres noirs à barre de couleur. Les pastilles pleines sont les classes du Nutri-Score. À l'oral, on dit « A prime ».
- **Nutri-Score 2023** : l'algorithme actualisé en 2023, en vigueur en France depuis mars 2025. Ses points négatifs vont jusqu'à 55, ses points positifs jusqu'à 17. C'est notre référence.
- **NOVA** : la classification des aliments selon leur transformation, de 1 (brut) à 4 (ultra-transformé). Open Food Facts la calcule à partir des ingrédients.
- **Matrice de confusion** : un tableau qui croise deux classements. En ligne, la classe du Nutri-Score ; en colonne, celle du modèle. La diagonale compte les produits rangés dans la même classe.
- **Écart moyen** : la moyenne, en classes, de la classe du modèle moins celle du Nutri-Score, avec A = 0 et E = 4. Positif : le modèle est plus sévère.
- **Exactitude**, ou « même classe » : la part des produits que le modèle range dans la même classe que le Nutri-Score.
- **Analyse de sensibilité** : on bouge un peu les poids, ou les profils, et l'on compte les plats qui changent de classe.

# Le texte, slide par slide
## Slide 1 : le titre (Daniel, 0 min 30)

**On montre :** le titre et les cinq classes de notre modèle, des cadres à barre de couleur.

**On dit :**

Bonjour. Le 30 octobre, nous approchions le Nutri-Score par MR-Sort.

Aujourd'hui, nous ne cherchons plus à le copier. Nous proposons notre propre modèle MR-Sort : le SuperNutri-score.

Il compare les plats préparés par leur composition, comme le Nutri-Score. Mais aussi par leur transformation et leur mode de production.

**Transition :** Voici ses critères.

**Pour comprendre :**

- Le 30 octobre, nous avions approché le Nutri-Score : des modèles MR-Sort appris pour redonner ses classes. Aujourd'hui, c'est la partie 3.4 du sujet : notre propre modèle, qui ne cherche pas à le copier.
- Le Nutri-Score reste la référence : nous disons dans quel sens nous nous en écartons (slides 7 et 11).
- Les cinq cadres de la page de titre sont nos classes, A′ à E′. Les pastilles pleines, plus loin, sont celles du Nutri-Score.

## Slide 2 : les trois piliers (Daniel, 1 min 25)

**On montre :** la barre des poids, une case par critère sous son pilier, puis le repère de λ et ses deux accolades.

**On dit :**

Onze critères, en trois piliers. Chaque case de la barre est un critère, large comme son poids.

À limiter, 0,40 : l'énergie, les graisses saturées, les sucres et le sel. À favoriser, 0,30 : les protéines, les fibres, les fruits et légumes. Ce sont les sept critères du Nutri-Score.

Pourquoi ces poids ? À limiter pèse le plus, comme au Nutri-Score : ses points négatifs vont jusqu'à 55, les positifs jusqu'à 17.

Dans un pilier, chaque critère pèse au prorata de ses points. Le sel, 20 points, pèse deux fois l'énergie, 10 points.

Les protéines comptent comme au Nutri-Score de 2023 : pas pour un produit qui a 11 points négatifs ou plus.

Le seuil majoritaire vaut 0,7 : c'est le trait sur la barre. Pour franchir un profil, il faut 0,7 du poids.

On peut donc rater 0,3. Le troisième pilier, notre ajout, pèse justement 0,30 : à lui seul, il ne fait jamais perdre une classe. Il départage des plats de composition proche.

**Transition :** Ce troisième pilier mérite une slide.

**Pour comprendre :**

- La concordance d'un plat face à un profil : la somme des poids des critères où il vaut au moins le profil. Un plat qui ne rate que les protéines a 1 − 0,124 = 0,876.
- Les poids dans un pilier suivent les points maximums du Nutri-Score de 2023. À limiter : énergie 10, graisses saturées 10, sucres 15, sel 20, soit 55 points ; le sel pèse donc 0,40 × 20 / 55 = 0,145. À favoriser : protéines 7, fibres 5, fruits et légumes 5, soit 17 points.
- Les trois piliers : la composition garde la majorité (0,70), comme le Nutri-Score, qui ne regarde qu'elle. La transformation pèse 0,30, soit exactement 1 − λ : seule, elle ne fait jamais perdre une classe.
- Dans la transformation : NOVA 0,10, nombre d'additifs 0,075, additifs à risque 0,075, bio 0,05.
- Les protéines (règle de 2023) : le Nutri-Score ne les compte pas à partir de 11 points négatifs, 7 pour les matières grasses ; une viande rouge en garde au plus 2 points ; un fromage les garde toujours. Quand il ne les compte pas, notre critère des protéines ne vote pas pour le plat. Ce n'est pas un veto : le plat perd seulement ce poids, 0,124.
- Question possible : pourquoi λ = 0,7 ? Parce qu'alors la transformation pèse exactement 1 − λ : elle départage sans dominer. Les slides 8 et 9 montrent ce qui bouge quand les poids ou les seuils changent.

## Slide 3 : la transformation (Daniel, 1 min 10)

**On montre :** les quatre groupes NOVA à gauche, les trois familles d'additifs à risque à droite, puis les deux plats en exemple.

**On dit :**

Le groupe NOVA range les aliments selon leur transformation, pas selon leurs nutriments. Il va de 1, brut, à 4, ultra-transformé.

Nos plats sont tous NOVA 3 ou 4. Et 257 sur 375 sont ultra-transformés.

Pourquoi le compter ? La cohorte française NutriNet-Santé associe l'ultra-transformé à plus de cancers et de maladies cardiovasculaires. Le groupe NOVA pèse 0,10.

Les additifs pèsent 0,15 en tout : leur nombre, et ceux qu'une autorité sanitaire a signalés. Ce sont les nitrites, les phosphates et les carraghénanes.

La Poêlée Fermière a 3 additifs, aucun à risque. La pizza Regina en a 2 à risque, dont le nitrite du jambon.

Enfin le bio, 0,05. C'est le plus petit poids : son effet sur la santé est le moins établi.

**Transition :** Restent les profils, les frontières entre les classes.

**Pour comprendre :**

- NOVA : la classification de l'équipe de Carlos Monteiro (Université de São Paulo, 2009). 1 : brut ou peu transformé. 2 : ingrédient culinaire (huile, sucre, sel). 3 : transformé (conserves, fromages, pain). 4 : ultra-transformé, des recettes industrielles avec des ingrédients ou des additifs que l'on n'a pas en cuisine.
- Open Food Facts calcule le groupe NOVA à partir de la liste des ingrédients et des additifs. Nous le lisons tel quel.
- NutriNet-Santé est une cohorte de l'Inserm : un article du BMJ en 2018 pour les cancers, un autre en 2019 pour les maladies cardiovasculaires. Ce sont des associations observées, pas une preuve de cause : on dit « associe ».
- Les trois familles à risque. Nitrites et nitrates (E249 à E252) : l'ANSES, en 2022, les associe au cancer colorectal et recommande d'en réduire l'exposition. Phosphates (E338 à E341, E343, E450 à E452) : l'EFSA, en 2019, fixe une dose admise que l'apport total des enfants peut dépasser. Carraghénanes (E407) : l'EFSA, en 2018, ne donne qu'une dose admise provisoire, faute de données.
- Deux critères : le nombre d'additifs (tous) et le nombre d'additifs à risque. Un additif à risque compte donc deux fois.
- Sur nos 375 plats : 140 sans additif, et 86 avec au moins un additif à risque (nitrites 44, phosphates 28, carraghénanes 26 ; un plat peut en avoir plusieurs).
- Question possible : un additif autorisé est-il dangereux ? Non : il est autorisé à une dose admise. Nous comptons à part les familles qu'une autorité a signalées.

## Slide 4 : les seuils (Daniel, 0 min 55)

**On montre :** le tableau des seuils, de D prime à A prime, et la colonne des sources.

**On dit :**

Chaque seuil vient d'un texte officiel.

Pour A prime, les allégations du règlement européen de 2006. Faible teneur en graisses saturées : 1,5 gramme pour 100 grammes. En sucres : 5 grammes. En sel : 0,3 gramme. Riche en fibres : 6 grammes.

Pour les autres classes, les barèmes du Nutri-Score de 2023. Par exemple, 670 kilojoules pour B prime : au plus un point d'énergie.

Et A prime comme B prime refusent l'ultra-transformé et exigent le bio.

**Transition :** Que veulent dire ces classes ?

**Pour comprendre :**

- Un profil donne la valeur minimale à atteindre, critère par critère, pour entrer dans une classe. Les valeurs sont pour 100 g de produit tel que vendu, comme au Nutri-Score.
- Le règlement CE 1924/2006 encadre les allégations nutritionnelles : « faible teneur en graisses saturées » (1,5 g), « en sucres » (5 g), « en sel » (0,3 g), « source de fibres » (3 g), « riche en fibres » (6 g). Un plat A′ pourrait porter ces allégations.
- Les barèmes du Nutri-Score de 2023 : un point d'énergie tous les 335 kJ, donc B′ demande au plus 670 kJ. Protéines : 2,4, 4,8, 7,2 et 12 g, de D′ à A′. Fruits et légumes : 40 et 60 %.
- Transformation : NOVA 3 au plus en A′ et B′ ; aucun additif en A′, un au plus en B′ ; aucun additif à risque en A′ et B′.
- « Exigé » ne veut pas dire obligatoire : un plat sans label bio perd seulement 0,05 du poids. Il peut rester en A′ s'il réussit le reste.
- Question possible : pourquoi de telles exigences en haut ? A′ et B′ sont le haut de l'échelle : un plat bien composé, peu transformé et bio. C'est pourquoi il y a peu de plats A′.

## Slide 5 : le sens des classes (Daniel, 0 min 55)

**On montre :** les cinq classes avec leur sens, et leur répartition sur nos 375 plats.

**On dit :**

Nous reprenons le sens que la FAQ officielle donne au Nutri-Score. Il ne range pas les aliments en bons ou mauvais. Il va des plus favorables à la santé aux moins favorables.

Nous l'étendons à la transformation et à la production. Les classes servent à comparer des plats préparés entre eux, pas à juger un plat seul.

Sur nos 375 plats, 12 sont en A prime et 41 en B prime. Près de la moitié, 171, sont en C prime. Notre modèle est exigeant en haut.

**Transition :** Anis va suivre le plat que nous suivons depuis octobre.

**Pour comprendre :**

- La FAQ officielle du Nutri-Score (version du 17 mars 2025) : le logo classe les aliments du plus favorable au moins favorable, pour comparer des produits d'une même catégorie.
- La répartition : 12 A′, 41 B′, 171 C′, 74 D′ et 77 E′. Notre base a 75 plats par classe du Nutri-Score : 75 A et 75 B, contre 12 A′ et 41 B′ chez nous.
- Pourquoi si peu de A′ : il faut à la fois une bonne composition, peu de transformation et le bio.

## Slide 6 : la Poêlée Fermière (Anis, 1 min 35)

**On montre :** les quatre barres de concordance de la Poêlée Fermière, leurs cases dans l'ordre des piliers de la slide 2, puis la colonne « Et si… ».

**On dit :**

Voici à nouveau la Poêlée Fermière de Cora : B au Nutri-Score. Elle est ultra-transformée, NOVA 4. Elle a 3 additifs et pas de label bio.

Chaque barre la compare à un profil. Les cases sont les onze critères de la slide 2, dans le même ordre. Une case est noire quand le critère vote pour le plat.

Face à b3, le seuil de C prime, seules les protéines manquent. Sa concordance vaut 0,876, au-dessus de 0,7. Elle franchit b3.

Face à b4, le seuil de B prime, elle rate cinq critères. Les protéines, les fibres, le groupe NOVA, le nombre d'additifs et le label bio. Il ne reste que 0,563 du poids. Elle reste en C prime.

Et si elle était moins transformée ? Avec NOVA 3 et un seul additif, elle passerait en B prime.

C'est ce que nous voulions : à composition égale, la transformation compte.

**Transition :** Sur toute la base, que change notre modèle par rapport au Nutri-Score ?

**Pour comprendre :**

- Lire une barre : une case par critère, large comme son poids. Noire, le plat vaut au moins le profil sur ce critère. La concordance est la largeur noire totale.
- Ses protéines : 1,6 g pour 100 g, sous le seuil de b2 (2,4 g). Le critère ne vote pour elle face à aucun profil : 0,876 face à b2 comme face à b3.
- Face à b4, elle rate les protéines, les fibres, NOVA, les additifs et le bio : 0,124 + 0,088 + 0,100 + 0,075 + 0,050 = 0,437, donc 0,563 de concordance.
- Sa classe : le plus haut profil qu'elle franchit est b3, donc C′.
- Et si : avec NOVA 3 et un seul additif, elle gagne NOVA et le nombre d'additifs face à b4 : 0,563 + 0,100 + 0,075 = 0,738, au-dessus de 0,7. Elle passe en B′.
- Question possible : elle est B au Nutri-Score, pourquoi C′ chez vous ? Face à b4, elle rate deux critères de composition (protéines, fibres) et trois de transformation et de production. La transformation seule ne l'aurait pas fait descendre.

## Slide 7 : face au Nutri-Score (Anis, 1 min 20)

**On montre :** la matrice grisée, Nutri-Score en ligne et SuperNutri-score en colonne : la diagonale encadrée, plus sévère à droite ; puis les raisons des descentes, en barres.

**On dit :**

Notre modèle est plus sévère que le Nutri-Score. Sur la matrice, la diagonale encadrée compte les plats qui gardent leur classe.

Sur nos 375 plats, 210 gardent sa classe, 145 descendent et 20 montent. En moyenne, un plat perd 0,43 classe.

Les descentes se font surtout en haut. 64 des 75 plats A descendent, et 60 des 75 plats B.

Face au profil de leur classe au Nutri-Score, ils ratent surtout les fibres, pour 125 plats. Puis les protéines, pour 113. Le label bio, pour 108. Le sel, pour 105. Et le groupe NOVA, pour 87.

C'est voulu : A prime reprend les allégations du règlement européen.

Et ceux qui montent ? 19 des 20 ont au moins 11 points négatifs : des pizzas, des feuilletés.

Le Nutri-Score additionne leurs points. MR-Sort, sans veto, ne leur retire que le poids des critères ratés, de peu ou de beaucoup. C'est une limite du MR-Sort simple que le sujet impose.

**Transition :** Nos poids sont un choix. Que se passe-t-il s'ils bougent un peu ?

**Pour comprendre :**

- La matrice : en ligne, la classe du Nutri-Score (pastilles pleines) ; en colonne, la nôtre (cadres). Chaque case compte des plats ; plus elle est foncée, plus elle en compte.
- La diagonale, c'est la même classe : 210 plats. À droite de la diagonale, notre classe est plus basse : nous sommes plus sévères (145 plats). À gauche, plus permissifs (20 plats).
- L'écart moyen, + 0,43 classe : on numérote A = 0 jusqu'à E = 4, et l'on fait la moyenne de notre classe moins celle du Nutri-Score.
- Pourquoi en haut : un plat A ou B doit franchir b5 ou b4, qui demandent des fibres, des protéines, le bio et peu de transformation. Beaucoup de plats A ont peu de fibres et pas de label bio.
- Pourquoi 20 plats montent : le Nutri-Score additionne des points, et un plat très salé en accumule beaucoup. MR-Sort compte des critères : rater le sel de beaucoup coûte autant que de peu, 0,145.
- Question possible : pourquoi pas de veto ? Le sujet demande un MR-Sort simple. Un veto sur le sel ou les graisses saturées empêcherait ces montées : c'est une amélioration possible.

## Slide 8 : la sensibilité aux poids (Anis, 1 min 05)

**On montre :** à gauche, une barre par amplitude, la moyenne en noir sur le maximum en gris ; à droite, les variations d'un seul poids, en barres ; puis la phrase des plats au bord.

**On dit :**

Le sujet demande de modifier légèrement les poids. Ils restent positifs, et leur somme reste 1.

Un poids à la fois, d'abord : il gagne ou perd 0,05, et les autres sont rajustés. Le plus sensible est celui des protéines : quand il gagne 0,05, 74 plats changent de classe.

Puis tous les poids ensemble, au hasard, mille fois par amplitude. À plus ou moins 0,01, 3,5 % des plats changent en moyenne. À plus ou moins 0,02, 4,8 %. À plus ou moins 0,05, 11,5 %.

Pourquoi des changements dès 0,01 ? 13 plats sont au bord de leur classe : ils ratent tout le pilier à favoriser. Leur concordance vaut 0,7 pile. Le moindre souffle sur les poids les fait basculer.

**Transition :** Et si ce sont les seuils qui bougent ?

**Pour comprendre :**

- Un poids à la fois : un poids gagne ou perd 0,05, et les dix autres sont multipliés par un même facteur, pour que la somme reste 1. On compte les plats qui changent de classe.
- Au hasard : chaque poids bouge d'au plus plus ou moins l'amplitude, sans descendre sous 0, puis tous sont divisés par leur somme. Mille tirages par amplitude, avec une graine fixée : le calcul se rejoue à l'identique.
- Sur la slide, la barre noire est la part moyenne des plats qui changent ; la barre grise, la plus forte des mille tirages (7,7 %, 16,5 % et 27,2 %).
- Les 13 plats au bord ratent exactement les protéines, les fibres et les fruits et légumes : 0,30 du poids. Leur concordance vaut 0,7, juste λ. Un poids qui bouge les fait tomber, ou monter.
- Ce que cela dit : le classement est stable pour la plupart des plats ; ceux qui changent sont près d'un seuil.
- Question possible : les protéines pèsent-elles trop ? Elles sont le poids le plus sensible, car beaucoup de plats sont près de leur seuil. Leur poids vient du barème du Nutri-Score : 7 points sur 17.

## Slide 9 : la sensibilité aux profils (Anis, 1 min 00)

**On montre :** les décalages qui changent le plus de plats, en barres, NOVA en tête, puis les plats nommés.

**On dit :**

Nous déplaçons une valeur de profil à la fois, sans casser leur ordre. Cinq pour cent pour les composantes nutritionnelles. Un cran pour NOVA et les additifs.

Au total, 116 plats changent au moins une fois : 43 par les seuils nutritionnels, 91 par NOVA et les additifs.

Le décalage le plus actif, c'est la première barre. Exiger NOVA 3 dès C prime ferait changer 52 plats.

Par exemple les 5 fromaggi de Carrefour, la Ratatouille et la Tartiflette, qui passeraient de C prime à D prime.

NOVA ne vaut que 3 ou 4 dans nos plats : un cran, c'est la moitié de l'échelle.

**Transition :** Biyao compare notre modèle à celui d'un autre groupe.

**Pour comprendre :**

- Un décalage : une seule valeur d'un profil change, par exemple le seuil de sel de b3, de 1 à 0,95 g. On garde l'ordre des profils, b2 le moins exigeant et b5 le plus : un décalage qui le casserait est écarté.
- Les composantes nutritionnelles bougent de 5 % ; NOVA et les nombres d'additifs, des entiers, bougent d'un cran ; le bio ne bouge pas.
- « b3, groupe NOVA, de 4 à 3 » : C′ demanderait NOVA 3 au lieu de 4. Les plats NOVA 4 qui étaient en C′ ratent un critère de plus (0,10), et 52 d'entre eux tombent en D′.
- Le sujet demande d'identifier les produits qui changent : la liste entière est dans l'Excel de la sensibilité, `resultats/supernutri_sensibilite.xlsx`.
- Question possible : vos seuils sont-ils fragiles ? Les seuils nutritionnels, peu : 5 % ne change que 43 plats. NOVA, davantage, parce qu'il n'a que deux valeurs dans nos plats.

## Slide 10 : leur modèle (Biyao, 0 min 50)

**On montre :** leur barre des poids sous la nôtre, cinq cases avec leurs points sur 15 et leur repère λ, puis leurs seuils et les phrases de droite.

**On dit :**

Nous avons reçu la base de Branchu, Becavin, Bundhoo et Castan : 300 céréales du petit-déjeuner.

Leur SuperNutri-score est aussi un MR-Sort simple, à cinq critères. Sur leur barre, les sucres pèsent le plus, 5 points sur 15. Puis les fibres, 4, le groupe NOVA, 3, les graisses saturées, 2, et le sodium, 1.

Un produit franchit un profil avec 10 points sur 15.

Pour A prime, ils reprennent les allégations européennes, comme nous. Mais ils n'ont ni énergie, ni protéines, ni additifs, ni bio.

Recodé dans notre moteur, leur modèle redonne leurs 300 classes.

**Transition :** Que donnent les deux modèles sur les deux bases ?

**Pour comprendre :**

- Leur modèle suit les mêmes règles que le nôtre, un MR-Sort sans veto, avec des poids en points entiers : sucres 5, fibres 4, NOVA 3, graisses saturées 2, sodium 1, sur 15.
- Leur λ vaut 0,63, soit 9,45 points sur 15. Les points sont entiers : il en faut donc 10. Les sucres et les fibres ensemble (9 points) ne suffisent pas : c'est pourquoi leur repère tombe dans la case NOVA.
- Leurs seuils de A′ viennent aussi du règlement CE 1924/2006 : sucres 5 g, graisses saturées 1,5 g, sodium 120 mg, fibres 6 g.
- Leurs classes vont de « très bon choix » (A′) à « à limiter » (E′) : c'est la colonne du sens des classes de leur fichier Excel.
- Leur base : 300 céréales, soit 65 A, 64 B, 64 C, 64 D et 43 E au Nutri-Score. Notre calcul du Nutri-Score de 2023 redonne leurs 300 labels : la référence est la même des deux côtés.
- « Recodé » : nous avons écrit leurs poids, leurs profils et leur λ dans notre moteur MR-Sort. Il range leurs 300 céréales exactement comme leur fichier.

## Slide 11 : deux modèles, deux bases (Biyao, 0 min 55)

**On montre :** les quatre matrices : chacun sur sa base, près de la diagonale ; chacun sur la base de l'autre, tiré vers E prime ; l'écart sous chacune, puis la phrase en gras.

**On dit :**

Aucun produit n'est commun aux deux bases. Leur base n'avait ni les additifs ni le bio : nous les avons lus sur Open Food Facts, par le code-barres.

Chaque matrice croise le Nutri-Score et un modèle. À gauche, chacun sur sa base : près de la diagonale.

Chacun colle mieux au Nutri-Score chez lui. Il y est un peu plus sévère : de 0,43 classe en moyenne pour le nôtre, 0,37 pour le leur.

À droite, chacun sur la base de l'autre : les produits glissent vers E prime. 0,90 classe pour le nôtre, 1,16 pour le leur.

Et les deux modèles ne donnent la même classe qu'à 52 % de leurs céréales.

**Transition :** Pourquoi ?

**Pour comprendre :**

- Quatre matrices, quatre cas. À gauche, chez soi : notre modèle sur nos plats, le leur sur leurs céréales. À droite, chez l'autre : notre modèle sur leurs céréales, le leur sur nos plats.
- Chaque matrice est grisée ligne par ligne : on voit où vont les produits de chaque classe du Nutri-Score. Les chiffres sont des nombres de produits.
- « Même classe » est la part des produits sur la diagonale : 56,0 % et 47,0 % chez soi, 34,7 % et 27,7 % chez l'autre.
- L'écart moyen se lit comme à la slide 7 : positif, le modèle est plus sévère. Chez l'autre, il double ou triple : la colonne E′ se remplit.
- L'accord entre les deux modèles, sans le Nutri-Score : 52,0 % des céréales et 32,5 % des plats reçoivent la même classe des deux modèles.
- Question possible : lequel est le meilleur ? Aucun en général : chacun est fait pour sa catégorie, c'est la slide suivante. Le Nutri-Score sert de référence, pas de vérité.

## Slide 12 : chaque modèle porte sa catégorie (Biyao, 1 min 10)

**On montre :** les critères ratés en barres dans les deux colonnes, puis les deux produits et leurs trois classes.

**On dit :**

Chaque modèle porte la catégorie pour laquelle il est fait.

Sur leurs céréales, notre seuil d'énergie ne vote pour aucune au seuil de B prime. Il est pensé pour des plats préparés. Une céréale sèche dépasse toujours 670 kilojoules pour 100 grammes.

Prenez ce muesli croustillant, bio et sans additif. Il est C au Nutri-Score, B prime chez eux, E prime chez nous.

Il rate l'énergie, les sucres, et les protéines, que le Nutri-Score ne compte pas. Cela fait 0,31 du poids, plus que les 0,30 permis.

À l'inverse, leur modèle exige des fibres. 96 % de nos plats ratent leur seuil de fibres pour B prime.

Notre Poêlée Fermière tombe chez eux en E prime. Peu de fibres et ultra-transformée : elle rate 0,47 du poids, quand leur seuil n'en permet que 0,37.

**Transition :** Place à la démonstration.

**Pour comprendre :**

- Les barres : la part des produits de l'autre base qui ratent chaque critère au seuil de B′, le profil b4.
- L'énergie : nos seuils viennent du barème du Nutri-Score, pour 100 g tel que vendu. Une céréale sèche dépasse de loin 670 kJ ; un plat préparé, humide, non.
- Le muesli, face à D′ : il rate l'énergie, les sucres et les protéines, que le Nutri-Score ne compte pas pour lui. Leurs poids font 0,305, arrondi à 0,31 : plus que 1 − λ = 0,30. Il tombe en E′.
- La Poêlée chez eux, face à D′ : elle rate les fibres (4 points) et NOVA (3 points). Cela fait 7 points sur 15, soit 0,47, plus que 1 − 0,63 = 0,37.
- La leçon : un modèle MR-Sort se règle pour une catégorie de produits. Ses seuils pour 100 g ne se transposent pas à une autre catégorie. Le Nutri-Score le sait : il a des règles par type de produit (fromages, matières grasses, boissons).

## Slide 13 : l'interface (Biyao, 1 min 00)

**On montre :** l'interface en direct, geste par geste, en suivant les repères de la slide.

**On dit :**

Dans le calculateur, le SuperNutri-score est sous le Nutri-Score. La Poêlée Fermière y est en C prime, avec ses barres.

Je passe NOVA à 3 et les additifs à 1. Elle monte en B prime, en direct.

Le seuil λ se règle au curseur, avec les poids et les profils. Prenons MR-Sort à 7 critères, avec les profils appris sur 375 plats. Il range la Poêlée en B prime à 0,6 ; à 0,7, elle passe en C prime.

Enfin, l'onglet SuperNutri-score montre le modèle, la source de chaque seuil, les sensibilités et le tableau croisé avec l'autre groupe.

**Transition :** Pour finir, ce que nous retenons.

**Pour comprendre :**

- Avant la soutenance : `streamlit run projet_gui.py` dans le dossier du projet. L'interface s'ouvre dans le navigateur, sur le calculateur.
- Sans réseau, l'interface marche : la recherche d'un produit lit d'abord le cache, et les plats de la base y sont tous.
- Le curseur λ change le seuil de MR-Sort à 7 critères, le modèle appris pour approcher le Nutri-Score. À 0,6, il suffit de 0,6 du poids pour franchir un profil : les classes montent.
- Si la démonstration plante : montrer les slides 6 et 13, puis passer à la conclusion.

## Slide 14 : ce que nous retenons (Biyao, 1 min 00)

**On montre :** les trois colonnes, puis le merci.

**On dit :**

Trois choses.

Le SuperNutri-score est un score de santé : onze critères, des seuils tirés de textes officiels, des classes au sens du Nutri-Score.

Il est plus sévère que le Nutri-Score, surtout en haut. Sur nos 375 plats, 145 descendent et 20 montent ; sur leurs céréales, 196 descendent et aucune ne monte.

Et il a ses limites. Sans veto, un plat très salé ne perd que la case du sel.

5 de nos 12 plats en A prime sont des produits secs : des couscous et un velouté déshydraté. Nos seuils lisent 100 grammes tels que vendus.

Et 13 plats sont au bord de leur classe. Nos poids sont un choix, et nous le disons. Merci.

**Pour comprendre :**

- Les produits secs en A′ : un couscous ou un velouté déshydraté, pour 100 g tels que vendus, a peu de sel et de sucres, et beaucoup de fibres et de protéines. Une fois préparé, il se comparerait autrement.
- Le veto : dans un MR-Sort complet, un critère trop raté, le sel par exemple, interdirait de franchir le profil. Nous ne l'avons pas, car le sujet demande un MR-Sort simple.
- « Nos poids sont un choix » : ils suivent le barème du Nutri-Score dans chaque pilier, et les piliers suivent une règle, la transformation égale à 1 − λ. Les slides 8 et 9 disent ce qui changerait avec d'autres poids ou d'autres seuils.

# Les questions probables du jury

- **Pourquoi ces poids ?** Dans chaque pilier, au prorata des points maximums du Nutri-Score de 2023. Entre les piliers : la composition garde 0,70, et la transformation pèse 1 − λ, pour départager sans dominer.
- **Pourquoi λ = 0,7 ?** Pour qu'un plat puisse rater au plus un pilier de 0,30 et franchir quand même. Le pilier de la transformation ne fait donc jamais perdre une classe à lui seul.
- **Pourquoi pas de veto ?** Le sujet demande un MR-Sort simple. Un veto sur le sel ou les graisses saturées corrigerait les 20 plats qui montent : c'est une amélioration possible.
- **Pourquoi votre modèle est-il plus sévère ?** A′ reprend les allégations européennes, et le haut de l'échelle demande peu de transformation et le bio. Les plats A du Nutri-Score ont souvent peu de fibres et pas de label bio.
- **Comment avez-vous choisi les additifs à risque ?** Seulement les familles qu'une autorité sanitaire a signalées : l'ANSES pour les nitrites, l'EFSA pour les phosphates et les carraghénanes. Les autres comptent dans le nombre d'additifs.
- **Le bio est-il meilleur pour la santé ?** Son effet est le moins établi : c'est pourquoi il a le plus petit poids, 0,05.
- **Vos données sont-elles fiables ?** Elles viennent d'Open Food Facts, des données déclarées par les marques et les contributeurs. Notre calcul du Nutri-Score de 2023 est vérifié contre celui d'Open Food Facts, et il redonne les 300 labels des céréales de l'autre groupe.
- **Comment comparer deux modèles qui n'ont pas les mêmes critères ?** On applique chaque modèle aux deux bases, avec la même référence, le Nutri-Score de 2023. Leur modèle est recodé dans notre moteur, et il redonne leurs 300 classes.
- **Que changeriez-vous ?** Un veto sur le sel et les graisses saturées ; des seuils par type de produit, comme le Nutri-Score ; et des seuils pour le produit préparé, pas tel que vendu, pour les produits secs.
