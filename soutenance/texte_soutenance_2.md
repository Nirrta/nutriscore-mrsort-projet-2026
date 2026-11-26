---
title: Texte de la soutenance finale
subtitle: Le SuperNutri-score, vendredi 27 novembre 2026
---

# Le déroulé

Quinze minutes au plus, en trois parties. Le texte vise 14 minutes 50 secondes, pour garder une marge.

| Partie | Orateur | Slides | Durée |
|---|---|---|---|
| Le modèle et la transformation | Daniel | 1 à 5 | 4 min 55 |
| Le plat suivi, la comparaison et les deux sensibilités | Anis | 6 à 9 | 5 min 20 |
| L'autre groupe, la démonstration et la conclusion | Biyao | 10 à 13 | 4 min 35 |

La répartition des orateurs n'est qu'une proposition : échangez les parties si vous le souhaitez.

Le texte de chaque slide est aussi dans les notes du fichier PowerPoint : il se lit en mode présentateur. On ne le récite pas : on le raconte.

À préparer avant de commencer :

- l'ordinateur avec les polices Archivo installées, et le PDF de secours sur une clé ;
- l'interface déjà lancée (`streamlit run projet_gui.py`), dans un onglet prêt, sur le calculateur ;
- le fichier PowerPoint ouvert en mode présentateur.

Tous les chiffres viennent de `python3 projet_supernutri.py` : nos 375 plats, et les 300 céréales de l'autre groupe.

# Le texte, slide par slide
## Slide 1 : le titre (Daniel, 0 min 30)

**On montre :** le titre et les cinq classes de notre modèle, des cadres à barre de couleur.

**On dit :**

Bonjour. Le 30 octobre, nous approchions le Nutri-Score par MR-Sort. Aujourd'hui, nous ne cherchons plus à le copier : nous proposons notre propre modèle MR-Sort, le SuperNutri-score. Il compare les plats préparés par leur composition, comme le Nutri-Score, mais aussi par leur transformation et leur mode de production.

**Transition :** Voici ses critères.

## Slide 2 : les trois piliers (Daniel, 1 min 25)

**On montre :** les trois colonnes des piliers, avec le poids de chaque critère, puis la phrase sur λ.

**On dit :**

Le SuperNutri-score a onze critères, groupés en trois piliers. À limiter, 0,40 : l'énergie, les graisses saturées, les sucres et le sel. À favoriser, 0,30 : les protéines, les fibres, les fruits et légumes. Ces sept critères sont ceux du Nutri-Score.

Pourquoi ces poids ? À limiter pèse le plus, comme au Nutri-Score, où les points négatifs, 55 au plus, dépassent les positifs, 17. Dans un pilier, chaque critère pèse au prorata de ses points : le sel, qui peut coûter 20 points, pèse deux fois l'énergie, qui en coûte 10. Et les protéines comptent comme dans le Nutri-Score de 2023 : il ne les compte pas pour un produit qui a 11 points négatifs ou plus, et chez nous, elles ne votent pas non plus.

Le seuil majoritaire vaut 0,7 : face à un profil, un plat peut rater au plus 0,3 du poids. Le troisième pilier, la transformation et la production, notre ajout, pèse justement 0,30 : à lui seul, il ne fait jamais perdre une classe ; il départage des plats de composition proche.

**Transition :** Ce troisième pilier mérite une slide.

## Slide 3 : la transformation (Daniel, 1 min 10)

**On montre :** les quatre groupes NOVA à gauche, les trois familles d'additifs à risque à droite, puis les deux plats en exemple.

**On dit :**

Le groupe NOVA range les aliments selon leur transformation, pas selon leurs nutriments : de 1, brut, à 4, ultra-transformé. Nos plats sont tous NOVA 3 ou 4, et 257 sur 375 sont ultra-transformés. Pourquoi le compter ? La cohorte française NutriNet-Santé associe l'ultra-transformé à plus de cancers et de maladies cardiovasculaires. Le groupe NOVA pèse 0,10.

Les additifs pèsent 0,15 en tout : leur nombre, et ceux qu'une autorité sanitaire a signalés, les nitrites, les phosphates et les carraghénanes. La Poêlée Fermière a 3 additifs, aucun à risque ; la pizza Regina en a 2 à risque, dont le nitrite du jambon. Enfin le bio, 0,05 : c'est le plus petit poids, car son effet sur la santé est le moins établi.

**Transition :** Restent les profils, les frontières entre les classes.

## Slide 4 : les seuils (Daniel, 0 min 55)

**On montre :** le tableau des seuils, de D prime à A prime, et la colonne des sources.

**On dit :**

Chaque seuil vient d'un texte officiel. Pour A prime, les allégations nutritionnelles du règlement européen de 2006 : faible teneur en graisses saturées, 1,5 gramme pour 100 grammes ; en sucres, 5 grammes ; en sel, 0,3 gramme ; riche en fibres, 6 grammes. Pour les autres classes, les barèmes du Nutri-Score de 2023 : par exemple 670 kilojoules pour B prime, soit au plus un point d'énergie. Et A prime comme B prime refusent l'ultra-transformé et exigent le bio.

**Transition :** Que veulent dire ces classes ?

## Slide 5 : le sens des classes (Daniel, 0 min 55)

**On montre :** les cinq classes avec leur sens, et leur répartition sur nos 375 plats.

**On dit :**

Nous avons repris le sens que la FAQ officielle donne au Nutri-Score : il ne range pas les aliments en bons ou mauvais, il va des plus favorables à la santé aux moins favorables. Nous l'étendons à la transformation et à la production. Les classes servent à comparer des plats préparés entre eux, pas à juger un plat seul.

Sur nos 375 plats, 12 sont en A prime, 41 en B prime, et près de la moitié, 171, en C prime. Notre modèle est exigeant en haut.

**Transition :** Anis va suivre le plat que nous suivons depuis octobre.

## Slide 6 : la Poêlée Fermière (Anis, 1 min 35)

**On montre :** les quatre barres de concordance de la Poêlée Fermière, puis la colonne « Et si… ».

**On dit :**

Voici à nouveau la Poêlée Fermière de Cora : B au Nutri-Score. Elle est ultra-transformée, NOVA 4, avec 3 additifs, et sans label bio.

Chaque barre la compare à un profil. Une case par critère, large comme son poids, noire quand le critère vote pour le plat. Face à b3, le seuil de C prime, seuls les protéines manquent : 0,876, au-dessus de 0,7. Elle franchit b3. Face à b4, le seuil de B prime, elle rate les protéines, les fibres, le groupe NOVA, le nombre d'additifs et le label bio : 0,563 seulement. Elle reste en C prime.

Et si elle était moins transformée ? Avec NOVA 3 et un seul additif, elle passerait en B prime. C'est exactement ce que nous voulions : à composition égale, la transformation compte.

**Transition :** Sur toute la base, que change notre modèle par rapport au Nutri-Score ?

## Slide 7 : face au Nutri-Score (Anis, 1 min 30)

**On montre :** la matrice, Nutri-Score en ligne et SuperNutri-score en colonne, puis les raisons des descentes.

**On dit :**

Notre modèle est plus sévère que le Nutri-Score. Sur nos 375 plats, 210 gardent sa classe, 145 descendent et 20 montent : en moyenne, un plat perd 0,43 classe.

Les descentes se font surtout en haut : 64 des 75 plats A descendent, et 60 des 75 plats B. Face au profil de leur classe au Nutri-Score, les plats qui descendent ratent surtout les fibres, pour 125 plats, les protéines, pour 113, le label bio, pour 108, le sel, pour 105, et le groupe NOVA, pour 87. C'est voulu : A prime reprend les allégations du règlement européen.

Et ceux qui montent ? 19 des 20 ont au moins 11 points négatifs : des pizzas, des feuilletés. Le Nutri-Score additionne leurs points ; MR-Sort, sans veto, ne leur retire que le poids des critères ratés, de peu ou de beaucoup. C'est une limite du MR-Sort simple que le sujet impose.

**Transition :** Nos poids sont un choix. Que se passe-t-il s'ils bougent un peu ?

## Slide 8 : la sensibilité aux poids (Anis, 1 min 15)

**On montre :** les trois amplitudes à gauche, les variations un poids à la fois à droite, puis la phrase des plats au bord.

**On dit :**

Le sujet demande de modifier légèrement les poids, en gardant des poids positifs de somme 1. Un poids à la fois, d'abord : il gagne ou perd 0,05, et les autres sont rajustés. Le plus sensible est celui des protéines : quand il gagne 0,05, 74 plats changent de classe.

Puis tous les poids ensemble, au hasard, mille fois par amplitude : à plus ou moins 0,01, 3,5 % des plats changent en moyenne ; à plus ou moins 0,02, 4,8 % ; à plus ou moins 0,05, 11,5 %.

Pourquoi des changements dès 0,01 ? Parce que 13 plats sont au bord de leur classe : ils ratent tout le pilier à favoriser, et leur concordance vaut 0,7 pile. Le moindre souffle sur les poids les fait basculer.

**Transition :** Et si ce sont les seuils qui bougent ?

## Slide 9 : la sensibilité aux profils (Anis, 1 min 00)

**On montre :** le tableau des décalages qui changent le plus de plats, puis les plats nommés.

**On dit :**

Nous déplaçons une valeur de profil à la fois, sans casser leur ordre : 5 % pour les composantes nutritionnelles, un cran pour NOVA et les additifs. Au total, 116 plats changent au moins une fois : 43 par les seuils nutritionnels, 91 par NOVA et les additifs.

Le décalage le plus actif : exiger NOVA 3 dès C prime ferait changer 52 plats, par exemple les 5 fromaggi de Carrefour, la Ratatouille et la Tartiflette, qui passeraient de C prime à D prime. NOVA ne vaut que 3 ou 4 dans nos plats : un cran, c'est la moitié de l'échelle.

**Transition :** Biyao compare notre modèle à celui d'un autre groupe.

## Slide 10 : deux modèles, deux bases (Biyao, 1 min 15)

**On montre :** le tableau croisé, puis la phrase en gras.

**On dit :**

Le sujet demande de tester notre modèle sur la base d'un autre groupe. Nous avons reçu celle de Branchu, Becavin, Bundhoo et Castan : 300 céréales du petit-déjeuner, aucune en commun avec nos plats. Leur base n'avait ni les additifs ni le bio : nous les avons lus sur Open Food Facts, par le code-barres. Nous avons aussi recodé leur modèle dans notre moteur : il redonne leurs 300 classes.

Résultat : chaque modèle colle mieux au Nutri-Score sur sa propre base, et y est un peu plus sévère que lui, de 0,43 classe en moyenne pour le nôtre, 0,37 pour le leur. Sur la base de l'autre, chacun devient bien plus sévère : 0,90 classe pour le nôtre, 1,16 pour le leur. Et les deux modèles ne donnent la même classe qu'à 52 % de leurs céréales : nos résultats diffèrent bien des leurs.

**Transition :** Pourquoi ?

## Slide 11 : chaque modèle porte sa catégorie (Biyao, 1 min 10)

**On montre :** les deux colonnes, puis les deux produits et leurs trois classes.

**On dit :**

Chaque modèle porte la catégorie pour laquelle il est fait. Sur leurs céréales, notre seuil d'énergie, pensé pour des plats préparés, ne vote pour aucune au seuil de B prime : une céréale sèche dépasse toujours 670 kilojoules pour 100 grammes. Prenez ce muesli croustillant, bio et sans additif : C au Nutri-Score, B prime chez eux, E prime chez nous. Il rate l'énergie, les sucres, et les protéines, que le Nutri-Score ne compte pas : 0,31 du poids, plus que les 0,30 permis.

À l'inverse, leur modèle exige des fibres : 96 % de nos plats ratent leur seuil de fibres pour B prime. Notre Poêlée Fermière tombe chez eux en E prime : peu de fibres et ultra-transformée, elle rate 0,47 du poids, quand leur seuil n'en permet que 0,37.

**Transition :** Place à la démonstration.

## Slide 12 : l'interface (Biyao, 1 min 10)

**On montre :** l'interface en direct, geste par geste, en suivant les repères de la slide.

**On dit :**

Dans le calculateur, le SuperNutri-score est sous le Nutri-Score. La Poêlée Fermière y est en C prime, avec ses barres. Je passe NOVA à 3 et les additifs à 1 : elle monte en B prime, en direct.

Le seuil λ se règle au curseur, avec les poids et les profils. Avec les profils appris sur 375 plats, MR-Sort à 7 critères range la Poêlée en B prime à 0,6 ; à 0,7, elle passe en C prime.

Enfin, l'onglet SuperNutri-score montre le modèle, la source de chaque seuil, les sensibilités et le tableau croisé avec l'autre groupe.

**Transition :** Pour finir, ce que nous retenons.

## Slide 13 : ce que nous retenons (Biyao, 1 min 00)

**On montre :** les trois colonnes, puis le merci.

**On dit :**

Trois choses. Le SuperNutri-score est un score de santé : onze critères, des seuils tirés de textes officiels, des classes au sens du Nutri-Score. Il est plus sévère que le Nutri-Score, surtout en haut : sur nos 375 plats, 145 descendent et 20 montent ; sur leurs céréales, 196 descendent et aucune ne monte. Et il a ses limites : sans veto, un plat très salé ne perd que la case du sel ; 5 de nos 12 plats en A prime sont des produits secs, des couscous et un velouté déshydraté, car nos seuils lisent 100 grammes tels que vendus ; et 13 plats sont au bord de leur classe. Nos poids sont un choix, et nous le disons. Merci.
