# Projet MR-Sort : un modèle transparent d'évaluation des plats préparés

Projet du cours *Transparence des algorithmes pour la décision* (M2 MIAGE ID-SITN, Brice Mayag), année 2026-2027. Sujet : `docs/Projet_2026_2027.pdf`.

Le projet construit une base de 125 plats préparés tirée d'Open Food Facts, étendue ensuite à 375 plats, et implémente le Nutri-Score de 2023 dans tous ses cas. Il approche ensuite ce Nutri-Score par MR-Sort (`MRSort_sept`, `MRSort_trois`), puis propose un modèle à nous, le SuperNutri-score. Le planning, les rôles et l'avancement sont dans `PLANNING.md`.

Ce README est interne : il n'est pas rendu. Le rendu comprend le rapport, les fichiers Excel et le code.

## Arborescence

| Fichier | Rôle | Question | Rendu |
|---|---|---|---|
| `projet_base.py` | la base et la base étendue : Open Food Facts, cache, filtres, tirage, Excel, contrôles ; la lecture d'une fiche à la demande (code-barres, lien, nom) | 3.1, 3.5 | oui |
| `projet_nutriscore.py` | l'algorithme du Nutri-Score de 2023, tous ses cas, et sa vérification contre OFF | 3.2 | oui |
| `projet_mrsort.py` | MR-Sort, `MRSort_sept`, `MRSort_trois`, la comparaison des modèles | 3.3 | oui |
| `projet_apprentissage.py` | les apprentissages (programmes linéaires, HiGHS) | 3.3 | oui |
| `projet_supernutri.py` | le SuperNutri-score, les sensibilités, la base d'un autre groupe | 3.4 | oui |
| `projet_gui.py` | l'interface Streamlit | 3.2, 3.5 | oui |
| `.streamlit/config.toml` | le thème de l'interface (couleurs, angles, polices servies depuis `static/`) | 3.2, 3.5 | oui |
| `static/` | les quatre polices Archivo de l'interface | 3.2, 3.5 | oui |
| `projet_design.py` | les jetons de design « Verso » : couleurs, filets, polices, style Excel | toutes | oui |
| `projet_figures.py` | les figures du rapport et des slides | toutes | oui |
| `slides_projet.py` | les slides des deux soutenances | soutenances | non |
| `projet_soutenance.py` | les textes de la soutenance, du Markdown au PDF ; les notes des slides | soutenances | non |
| `soutenance/` | le texte de l'oral et le dossier de la démarche, en Markdown et en PDF | soutenances | non |
| `PRODUCT.md`, `DESIGN.md` | le contexte du produit et le système de design, lus par Impeccable | design | non |
| `projet_rapport.py` | les chiffres et les figures du rapport | rapport | non |
| `donnees/base_plats_prepares.xlsx` | **la base** (feuilles base, lisez-moi, contrôles) | 3.1 | oui |
| `donnees/base_etendue_plats_prepares.xlsx` | **la base étendue** : les 125 plats, plus 50 par classe tirés hors de la base (colonne « Lot ») | 3.1, 3.3 | oui |
| `donnees/brut/` | les réponses d'Open Food Facts, en cache : la base se reconstruit à l'identique, sans réseau | 3.1 | oui |
| `donnees/autre_groupe/` | la base de l'autre groupe (300 céréales du petit-déjeuner) et sa note, telles qu'ils nous les ont envoyées ; `base_cereales_completee.xlsx`, leurs colonnes plus ce qu'Open Food Facts ajoute (additifs, bio, type au Nutri-Score) | 3.4 | oui |
| `resultats/` | les Excel des résultats, `resultats_projet.json`, les slides | toutes | en partie |
| `rapport/` | le rapport LaTeX (`verso.sty`, `sections/`, `chiffres.tex` généré) | rapport | le PDF |
| `design/` | les polices Archivo (OFL) et `generer_polices.py` | design | non |
| `tests/` | les tests pytest et `fixtures/` (4 produits gardés du projet de 2025) | toutes | non |
| `requirements.txt` | les bibliothèques Python | toutes | oui |

Les modules suivent les règles du cours :
- tout est en français ;
- les fonctions sont en camelCase, sauf les noms imposés par le sujet ;
- chaque fonction a sa docstring, et les boucles restent simples, sans classes ;
- le code ne mentionne aucun outil d'IA ;
- tout chiffre cité vient de `resultats/resultats_projet.json`.

Ce que l'interface lit (vérifié le 29/10 sur une copie réduite du dossier) :
- `projet_gui.py` et les modules qu'il importe : `projet_base`, `projet_nutriscore`, `projet_mrsort`, `projet_supernutri`, `projet_design`, et `projet_apprentissage` s'il faut réapprendre les modèles ;
- `donnees/base_plats_prepares.xlsx` et, si elle est construite, `donnees/base_etendue_plats_prepares.xlsx`. Sans elles, l'interface ne propose que les deux exemples du sujet, sans modèle MR-Sort ;
- `donnees/brut/produits/`, pour chercher un produit sans réseau. Un produit absent du cache est demandé à Open Food Facts, sans rien écrire sur le disque ;
- `resultats/resultats_projet.json`. Sans lui, elle réapprend les modèles au lancement (avec scipy, en deux secondes) ;
- `.streamlit/config.toml` et `static/`, à côté de `projet_gui.py`. Sans eux, elle tourne avec le thème et les polices par défaut de Streamlit. `.streamlit/` est un dossier caché : dans le Finder, Cmd + Maj + point l'affiche.

Elle ne lit pas `design/`, qui sert aux figures, aux slides et au rapport. Le cache est rendu : avec lui, `python3 projet_base.py --depuis-cache` reconstruit exactement nos 125 plats, et `--etendue --depuis-cache` nos 375 plats. Sans lui, il faudrait tout retélécharger, et les fiches d'Open Food Facts auront changé.

## Commandes

Depuis `nutriscore-mrsort-projet-2026/`, avec le Python d'Anaconda :

```bash
/opt/anaconda3/bin/python3 -m pytest -q          # les tests
python3 projet_base.py                           # la base, depuis Open Food Facts (une quinzaine de minutes la première fois)
python3 projet_base.py --depuis-cache            # la même base, sans réseau
python3 projet_base.py --etendue --depuis-cache  # la base étendue (375 plats), sans réseau
python3 projet_nutriscore.py                     # les exemples du sujet, la vérification sur la base, les cas particuliers, le vivier étendu
python3 projet_mrsort.py                         # MRSort_sept et MRSort_trois, λ = 0,6 et 0,7, paires inversées, intervalles des poids ;
                                                 # avec la base étendue : les modèles sur 375 plats et le test sur les plats ajoutés
python3 projet_mrsort.py --courbe                # en plus, la courbe d'apprentissage (quelques minutes)
python3 projet_mrsort.py --profils               # en plus, les profils appris sur les 125 plats (5 min au plus par modèle)
python3 projet_mrsort.py --complet               # en plus, le modèle complet sur les 125 plats et la recherche d'un modèle exact (une heure au plus)
python3 projet_mrsort.py --etendue               # en plus, les profils appris et le modèle complet sur les 375 plats (1 h à 2 h)
python3 projet_mrsort.py --croisee               # en plus, la validation croisée des trois apprentissages sur les 375 plats (plusieurs heures)
                                                 # --limite SECONDES règle la limite de chaque apprentissage des profils (600 s par défaut)
python3 projet_supernutri.py                     # le SuperNutri-score sur les deux bases, ses deux sensibilités, et la comparaison
                                                 # avec l'autre groupe (donnees/autre_groupe/), sans réseau (quelques secondes)
python3 projet_supernutri.py --telecharger-autre-groupe   # range une fois dans le cache les fiches d'OFF de leurs 300 céréales (~20 min)
streamlit run projet_gui.py                      # l'interface
python3 slides_projet.py --soutenance 1          # les 10 slides du 30/10 et leurs figures
python3 slides_projet.py --soutenance 2          # les 13 slides du 27/11 (le SuperNutri-score), et leur PDF par PowerPoint
python3 projet_soutenance.py                     # le texte de l'oral et le dossier du 30/10, en PDF (soutenance/)
python3 projet_soutenance.py --soutenance 2      # le texte de l'oral du 27/11, en PDF
python3 design/generer_polices.py <dossier> design/polices   # les instances d'Archivo, depuis la police variable
cd rapport && latexmk -xelatex rapport.tex       # le rapport
```

Pour une simple vérification, `projet_base.py --sortie <fichier temporaire>` construit la base sans toucher à `resultats_projet.json` (de même avec `--etendue`).

Les tests n'appellent jamais Open Food Facts : ceux de la recherche fixent `PROJET_HORS_LIGNE=1`, et ne lisent que le cache.

## Choix de conception

Chaque choix d'interprétation du sujet est couvert par un test.

**La version du Nutri-Score.** Le sujet décrit la « version de mars 2025 ». C'est la version actualisée du Nutri-Score, que Santé publique France nomme « Nutri-Score actualisé en 2023 », entrée en vigueur en France le 16 mars 2025 (FAQ officielle, version du 17 mars 2025, dans `docs/projet 2025/document_rapport/`). Les maximums du sujet, 55 points négatifs et 17 positifs, sont les siens : ceux de 2017 étaient 40 et 15. Le code et ce README l'appellent « l'algorithme de 2023 ». Test : `test_les_maximums_sont_ceux_de_l_algorithme_actualise`.

1. **La règle des protéines de 2023.** À partir de 11 points négatifs, les protéines ne comptent plus. La fig. 4 du sujet reprend la règle de 2017, qui gardait les protéines au-delà de 80 % de fruits, légumes et légumineuses. La FAQ officielle (version du 17 mars 2025, p. 29 et 30) et Open Food Facts ne gardent plus cette exception. `scoreNutriscore(..., exceptionFruits=True)` applique la fig. 4, et l'écart est mesuré sur la base. Tests : `test_exception_des_fruits_de_la_figure_4`, `test_les_proteines_ne_comptent_plus_a_11_points_negatifs`.
2. **Le sel en grammes.** Les barèmes de 2023 (fig. 3) sont en sel ; la colonne `so` contient donc le sel, et le sodium (sel / 2,5) est donné à part. Pour MR-Sort, sel et sodium rangent les plats dans le même ordre : les affectations ne changent pas. Test : `test_produits_off_de_2025`.
3. **Les fruits, légumes et légumineuses de 2023.** On prend la composante d'OFF pour 2023 (sans fruits à coque ni huiles), comme dans l'en-tête de la fig. 2. Test : `test_points_des_fruits_legumes_et_legumineuses`.
4. **Les seuils strictement dépassés.** Une valeur égale à un seuil reçoit les points du bas. Test : `test_une_valeur_egale_au_seuil_recoit_les_points_du_bas`.
5. **La base reste au cas général ; le calcul couvre tous les cas.** La base exclut les boissons, les fromages, les matières grasses et les viandes rouges, qui ont leurs propres règles ; le filtre est compté dans l'entonnoir. Le calcul, lui, suit tous les cas de l'algorithme de 2023 (FAQ, p. 17-20 et 28-34) : fromages (les protéines comptent toujours), viandes rouges (au plus 2 points de protéines), matières grasses, fruits à coque et graines (énergie des acides gras saturés, ratio AGS / lipides, A jusqu'à −6), boissons (leurs barèmes, 4 points pour les édulcorants, B jusqu'à 2) et eaux (A). Il est vérifié contre OFF sur les fiches du cache. Tests : `test_la_viande_rouge_plafonne_les_proteines_a_2_points`, `test_les_proteines_du_fromage_comptent_toujours`, `test_l_huile_d_olive_est_classee_B`, `test_les_boissons_ont_leurs_baremes_et_leurs_classes`, `test_l_eau_est_classee_A_sans_calcul`, `test_les_cas_particuliers_reproduisent_off`.
6. **Notre calcul n'est pas un filtre de la base.** Sinon, la vérification de la question 3.2 serait circulaire. Test : `test_la_base_est_reproduite`.
7. **Le recoupement avec une autre base** est rapporté à la plus petite des deux, la lecture la plus sévère de la règle des 25 %.

8. **Une égalité avec le profil compte comme « au moins aussi bon ».** C'est le ≥ et le ≤ du sujet (§2.2). Test : `test_concordance_partielle_compte_l_egalite`.
9. **Le seuil λ est comparé à 10⁻⁹ près.** En machine, 0,1 + 0,7 vaut 0,7999999999999999, et doit pourtant atteindre λ = 0,8. Test : `test_le_seuil_est_atteint_malgre_les_arrondis`.
10. **ε = 0,001.** C'est la marge de l'inégalité stricte « ne pas franchir le profil du haut » dans les programmes linéaires, comme le propose l'annexe B. Test : `test_poids_de_l_annexe_B`.
11. **Les poids appris sont arrondis au millième, pour rester lisibles.** Leur somme reste 1, et l'on vérifie que l'arrondi ne déplace aucun plat (sinon on garde plus de décimales). Test : `test_les_poids_sont_arrondis_au_millieme`.
12. **Les profils fixés sont le milieu des médianes des deux classes voisines.** C'est le plat-frontière typique ; l'ordre des profils est ensuite imposé. Test : `test_profils_par_medianes`. Deux limites, à écrire dans le rapport : dans les plats préparés, les médianes des protéines baissent quand la classe s'améliore (10 g en E, 3,7 g en A : plus de protéines veut dire plus de viande), si bien que l'ordre imposé met les quatre profils des protéines à 9,55 g, et ceux des fibres à 1,8 g, et que ces deux critères ne séparent plus les classes ; et 9 plats de la base sont mal rangés à cause des profils, quels que soient les poids. Apprendre les profils (phase 2) doit lever ces limites.

13. **La valeur exacte plutôt que la valeur arrondie d'OFF.** Le calcul d'OFF affiche des valeurs arrondies (0,4 g de sel), mais compte les points avec la valeur exacte du tableau nutritionnel (0,4043 g). La base reprend la valeur exacte quand elle correspond à la valeur arrondie : sans cela, la « Soupe pdt/courgette » aurait un point de sel de moins qu'OFF. Test : `test_la_valeur_exacte_remplace_la_valeur_arrondie`.

14. **La base étendue : mesurer sur des plats que le modèle n'a pas vus, puis réapprendre sur tout.** La base du 30/10 (125 plats) reste la base d'apprentissage, et ses chiffres restent vrais. On y ajoute 50 plats par classe, tirés hors de cette base avec les mêmes filtres et la même graine : 375 plats. Les modèles du 30/10 sont mesurés sur les 250 plats ajoutés ; la courbe d'apprentissage dit ce qu'un modèle gagne à apprendre sur plus de plats ; le modèle final est appris sur les 375 plats. On ne relâche pas le filtre des fibres : OFF compte 0 point pour des fibres non déclarées, et MR-Sort apprendrait « pas de fibres déclarées, donc E ». Tests : `test_la_base_etendue_contient_la_base_et_75_plats_par_classe`, `test_la_base_etendue_se_reconstruit_depuis_le_cache`, `test_la_courbe_d_apprentissage_du_json`.
15. **Le type d'un produit cherché est proposé par OFF, mais modifiable.** Il ne se devine pas à ses sept valeurs. OFF le déduit de ses catégories, et se trompe parfois : il marque « viande rouge » des lasagnes à la bolognaise, alors que la FAQ (p. 19-20) laisse les plats composés au cas général. L'interface dit la raison du type, ajoute la réserve de la FAQ pour un plat préparé, et laisse le changer. Tests : `test_produit_depuis_la_fiche_de_lasagnes_marquees_viande_rouge`, `test_un_lien_off_propose_le_type_d_off`.
16. **Une valeur manquante d'un produit cherché vaut 0, une valeur estimée par OFF est reprise, et la fiche le dit.** C'est ce que fait le calcul d'OFF : 0 point pour des fibres non déclarées, et des fibres qu'il a lui-même estimées. Sans tableau nutritionnel, les acides gras saturés et les lipides d'une matière grasse se déduisent de son calcul. La base garde son filtre : les sept composantes déclarées. Tests : `test_une_valeur_manquante_vaut_0_et_c_est_dit`, `test_les_valeurs_estimees_par_off_sont_reprises_et_signalees`.
17. **L'interface n'écrit rien.** Elle lit les fiches du cache avant de demander à OFF (une requête, 10 secondes au plus, sans relance), garde les fiches lues une heure en mémoire, et n'écrit pas dans `donnees/brut/` : le cache reste celui des bases. Hors ligne, seules les fiches gardées se trouvent. Tests : `test_une_fiche_absente_du_cache_hors_ligne_donne_un_message`, `test_open_food_facts_injoignable_donne_un_message`.
18. **Les poids appris ne sont pas uniques : on rapporte leurs intervalles, et l'on départage par la plus grande marge.** Plusieurs jeux de poids rangent aussi bien les plats. `intervallesDesPoids` donne le plus petit et le plus grand poids de chaque critère parmi ces optimums. Les modèles du 30/10 gardent la solution rendue par le solveur ; les modèles appris ensuite (375 plats, phase 2) prennent, parmi les optimums, celle dont la plus petite marge est la plus grande (Leroy, Mousseau et Pirlot, 2011) : les plats y sont le moins sensibles aux petites variations des poids. L'interface montre ces intervalles dans la colonne « Poids possibles » de l'éditeur, pour les seuls poids appris : les profils appris et le modèle complet n'en ont pas. Tests : `test_intervalles_des_poids_de_l_annexe_B`, `test_le_departage_par_la_marge_garde_l_optimum`, `test_le_poids_des_ags_n_est_indispensable_qu_a_0_7`, `test_les_poids_possibles_ne_sont_annonces_qu_avec_leur_colonne`.

19. **Les poids fixés du second apprentissage sont les points maximaux du Nutri-Score**, ramenés à une somme de 1 : (10, 10, 15, 20, 7, 5, 5) / 72 à 7 critères, (10, 20, 5) / 35 à 3 critères. Ce sont les poids implicites du Nutri-Score : les quatre critères négatifs pèsent 55/72, plus que λ, et les trois positifs (17/72) ne peuvent pas compenser. Test : `test_poids_des_points_max`.
20. **Un profil appris prend le milieu entre deux plats voisins.** Entre deux valeurs voisines de la base, un profil range les plats de la même façon où qu'il soit : le programme choisit, pour chaque profil et chaque critère, un seuil parmi les milieux (plus un seuil sous tous les plats et un au-dessus), comme l'annexe C prend une valeur entre deux produits. Les profils restent ordonnés. Les inégalités strictes ne portent plus que sur les concordances (ε), jamais sur les valeurs des plats. Tests : `test_seuils_candidats`, `test_profils_de_l_annexe_C`, `test_les_profils_appris_restent_ordonnes`.
21. **Le modèle complet se cherche de deux façons.** Pour un bon modèle, par alternance (à la manière de Sobrie, Mousseau et Pirlot) : profils appris à poids fixés, puis poids appris sur ces profils, et ainsi de suite tant que le nombre de plats bien rangés progresse ; on garde toujours le meilleur. Pour la question 1 du sujet (un modèle exact existe-t-il ?), par un seul programme, où poids, profils et λ sont des variables, et où tous les plats doivent être bien rangés : le solveur trouve un modèle exact, prouve qu'il n'y en a pas, ou s'arrête à la limite de temps sans réponse. Une paire inversée prouve déjà qu'il n'y en a pas. Tests : `test_l_alternance_garde_le_meilleur_modele`, `test_le_modele_complet_trouve_un_modele_exact_quand_il_existe`, `test_le_modele_complet_prouve_qu_aucun_modele_exact_n_existe`, `test_chercher_un_modele_exact`.
22. **Les programmes longs ont une limite de temps, et l'on dit ce qui est prouvé.** Les profils appris s'arrêtent au bout de cinq minutes, la recherche d'un modèle exact au bout de trente. Le JSON garde, à côté du meilleur modèle trouvé, le maximum prouvé par le solveur (« borne ») et s'il a fini (« optimal »). La limite compte le temps de calcul, et non la mise en veille de l'ordinateur. L'horloge du solveur, elle, continue de tourner quand le Mac dort : un calcul que la veille a coupé est donc recommencé (`resoudreCreux`). Tests : `test_les_modeles_aux_profils_appris`, `test_un_calcul_coupe_par_la_veille_est_recommence`, `test_un_calcul_arrete_sur_sa_limite_n_est_pas_recommence`.
23. **Nos modèles MR-Sort ont un domaine : les plats préparés du cas général.** Ils ne sont appris que sur eux. Hors de ce domaine, l'interface donne leur classe à titre indicatif, dans un cadre en pointillés, sans la comparer au Nutri-Score d'un autre barème, et un encadré dit pourquoi :
    - pour une boisson, qui a ses propres barèmes : les yaourts à boire comme le Yop en font partie depuis 2023 (FAQ, p. 18) ;
    - pour un fromage, une viande rouge ou une matière grasse, qui ont une règle à part ;
    - pour un produit cherché qui n'est pas un plat préparé ;
    - pour les céréales des fig. 6 et 7 du sujet.

    Une eau n'a pas de classe MR-Sort : le Nutri-Score la classe A sans calcul. Tests : `test_la_raison_hors_domaine_depend_du_produit`, `test_une_boisson_a_une_classe_indicative`, `test_une_eau_n_a_pas_de_classe_mrsort`, `test_un_plat_prepare_n_a_rien_d_indicatif`, `test_le_type_boisson_change_le_calcul`, `test_un_lien_off_propose_le_type_d_off`, `test_un_exemple_du_sujet_sort_du_domaine_de_mr_sort`.
24. **Une saisie impossible est signalée, sans bloquer le calcul.** Pour une matière grasse, des acides gras saturés au-delà des lipides (un rapport de plus de 100 %) donnent un avertissement, et le Nutri-Score reste calculé avec les valeurs saisies. Un nombre qui n'a pas de 8 à 14 chiffres est dit mal recopié, au lieu d'être cherché comme un nom. Tests : `test_des_ags_au_dela_des_lipides_sont_signales`, `test_un_code_trop_court_le_dit`.
25. **Un profil porte le nom de la classe qu'il ouvre.** Dans MR-Sort, le profil bk est le seuil de la classe Ck (sujet, §2) : un plat qui le franchit est au moins dans cette classe. L'interface écrit donc « b2 (D′) » à « b5 (A′) » dans les barres de concordance, les éditeurs des paramètres et les tableaux du pas à pas. La raison d'une classe nomme le seuil franchi ; pour la Poêlée Fermière, avec le modèle du 30/10 à λ = 0,6 : « Franchit le seuil de C′ (b3, concordance 0,919 ≥ λ = 0,6), pas celui de B′ (b4, 0,479 < 0,6). » Les formules du pas à pas gardent b_k. Tests : `test_la_phrase_nomme_le_seuil_de_la_classe`, `test_les_profils_portent_leur_classe`, `test_le_pas_a_pas_nomme_les_seuils`, `test_barres_de_concordance_de_la_poelee_fermiere`.
26. **Revenir au produit d'origine défait toute la saisie.** Rechoisir le même plat dans la liste ne fait rien, car Streamlit ne réagit qu'à un changement de choix. Le bouton « Revenir aux valeurs du produit » rend donc les valeurs et le type d'origine : celui proposé par OFF pour un produit cherché, le cas général pour un exemple. Pour un produit cherché, une modification des lipides (matières grasses) ou des édulcorants (boissons) compte comme celle des sept composantes : la fiche ne compare plus alors notre calcul au résultat d'OFF. Tests : `test_revenir_aux_valeurs_du_plat`, `test_revenir_aux_valeurs_d_un_produit_cherche`, `test_des_lipides_modifies_comptent_comme_une_modification`.
27. **Les trois apprentissages se comparent par validation croisée, à temps de calcul égal.** Un modèle appris sur les 375 plats les a tous vus : on ne peut pas le mesurer sur des plats nouveaux.
    - On répartit donc les 375 plats en 5 parts de 75, avec 15 plats par classe dans chaque part, tirés avec la graine de la base.
    - On apprend sur 4 parts (300 plats), puis on range la cinquième, et cela cinq fois : chaque plat est rangé une fois, par un modèle qui ne l'a pas vu.
    - Chaque apprentissage des profils a la même limite de temps : 300 s dans la validation croisée (`--croisee --limite 300`, soit plusieurs heures de calcul), 600 s pour les modèles finaux sur les 375 plats (`--etendue`, `LIMITE_ETENDUE`). En deux minutes, sur 375 plats, le solveur restait loin du maximum qu'il prouve. L'Excel rapporte, pour chaque apprentissage, les parts où l'optimum est prouvé.
    - Le modèle complet fait au plus 3 tours dans la validation croisée.
    - Par défaut, l'interface montre l'apprentissage qui a la meilleure exactitude moyenne à 7 critères et λ = 0,6.

    Tests : `test_les_parts_de_la_validation_croisee_sont_stratifiees`, `test_la_validation_croisee_range_chaque_plat_une_fois`, `test_la_limite_de_temps_va_jusqu_au_solveur`, `test_l_excel_de_la_validation_croisee`, `test_la_validation_croisee_du_json`, `test_l_apprentissage_par_defaut_est_le_meilleur_en_validation_croisee`.

28. **Le SuperNutri-score garde la santé, et y ajoute la transformation et la production.** Le sujet (§3.4) nous laisse proposer notre propre modèle. Le nôtre range les plats selon onze critères, en trois piliers : à limiter (énergie, acides gras saturés, sucres, sel), à favoriser (protéines, fibres, fruits, légumes et légumineuses), transformation et production (groupe NOVA, nombre d'additifs, additifs à risque, bio). Facteurs écartés, et pourquoi (choix du groupe, 20/11) :
    - le Green-Score : il changerait le sens des classes (l'environnement n'est pas la santé), c'est lui-même un agrégat opaque (analyse du cycle de vie, labels, origine, emballage), et il manque pour 43 plats sur 125 (34 %). Toute règle pour ces plats fausserait le résultat ;
    - la liste des ingrédients, l'huile de palme et l'origine : notre cache d'Open Food Facts ne les garde pas.

    Le bio est gardé avec le plus petit poids : il apporte la seule chose qu'aucun autre critère ne mesure, l'absence de pesticides de synthèse, mais il fait en partie doublon avec la transformation (7 plats bio sur 40 sont ultra-transformés (NOVA 4), contre 250 sur 335 pour les autres, dans la base étendue). « Non » veut dire « aucun label bio enregistré sur OFF », ce qui peut être une donnée manquante. Tests : `test_les_onze_criteres_dans_l_ordre`, `test_le_readme_justifie_le_bio_et_l_ecart_du_green_score`.

    Le groupe NOVA (Université de São Paulo, 2009) range les aliments selon leur transformation, pas selon leurs nutriments : 1, brut ou peu transformé ; 2, ingrédient culinaire (huile, beurre, sucre, sel) ; 3, transformé (conserve, fromage, pain) ; 4, ultra-transformé (formulation industrielle, souvent avec des additifs). Il complète le Nutri-Score sans le répéter, et Open Food Facts le calcule à partir des ingrédients. C'est un critère de santé : la cohorte NutriNet-Santé associe une part plus grande d'aliments ultra-transformés à plus de cancers (Fiolet et al., BMJ, 2018) et de maladies cardiovasculaires (Srour et al., BMJ, 2019). Ce sont des associations, pas des causes prouvées. Dans nos 375 plats, NOVA ne vaut que 3 (118 plats) ou 4 (257 plats). Tests : `test_la_transformation_des_plats`, `test_le_readme_explique_nova_et_les_additifs_a_risque`.
29. **Les poids : trois piliers, au prorata des points du Nutri-Score.** À limiter 0,40, à favoriser 0,30, transformation et production 0,30. À limiter pèse le plus, comme au Nutri-Score, où les points négatifs (55 au plus) dépassent les positifs (17 au plus). La transformation et la production pèsent 0,30, soit 1 − λ : à elles seules, elles ne font jamais perdre une classe à un plat, et elles départagent des plats de composition proche. Dans les deux piliers nutritionnels, chaque critère pèse au prorata de ses points maximaux dans le Nutri-Score : le sel (20 points) pèse deux fois l'énergie (10). Dans le troisième : NOVA 0,10 ; les additifs 0,15 en tout, partagés entre leur nombre et les additifs à risque (0,075 chacun), pour ajouter « lesquels » à « combien » sans compter deux fois les additifs ; bio 0,05, le plus faible, car son effet sur la santé est le moins établi. Tests : `test_les_poids_suivent_les_trois_piliers`, `test_dans_un_pilier_nutritionnel_les_poids_suivent_les_points_maximaux`, `test_les_poids_de_la_transformation_et_de_la_production`.
30. **Les profils viennent des textes officiels, et λ = 0,7.** Pour A′, les seuils des allégations du règlement CE 1924/2006 : « faible teneur » en graisses saturées (1,5 g), en sucres (5 g) et en sel (0,3 g), « riche en fibres » (6 g) ; « source de fibres » (3 g) pour B′. Pour les autres classes, les seuils de points du Nutri-Score de 2023 (par exemple 670 kJ pour B′, au plus un point d'énergie). Pas de texte pour les fibres de C′ et D′ (2 et 1 g) ni pour les fruits de C′ (20 %) : ce sont des choix du groupe. NOVA : au plus transformé (NOVA 3) pour A′ et B′. Additifs : 0, 1, 3 et 5 ; additifs à risque : 0, 0, 1 et 2 ; bio exigé pour A′ et B′. Avec λ = 0,7, un plat peut rater au plus 0,3 du poids face à un profil, par exemple tout le pilier de la transformation et de la production. Une valeur absente prend la pire valeur possible : elle ne vote jamais pour le plat. Tests : `test_les_profils_sont_ordonnes`, `test_les_seuils_de_a_prime_viennent_des_allegations`, `test_lambda_vaut_0_7`, `test_rater_toute_la_transformation_laisse_a_prime_possible`, `test_une_valeur_absente_ne_vote_pas_pour_le_plat`.
31. **Les additifs à risque sont ceux qu'une autorité sanitaire signale** :
    - les nitrites et nitrates, E249 à E252 : l'ANSES (avis du 12 juillet 2022) confirme leur association avec le cancer colorectal, et recommande de réduire l'exposition ;
    - les phosphates, E338 à E341, E343 et E450 à E452 : l'EFSA (réévaluation de 2019) fixe une dose journalière admissible de groupe, que l'apport total de phosphore des enfants dépasse ;
    - les carraghénanes, E407 : l'EFSA (réévaluation de 2018) garde leur dose journalière admissible, mais la juge provisoire, faute de données suffisantes.

    Dans nos 375 plats, 86 ont au moins un additif à risque (44 des nitrites ou nitrates, 28 des phosphates, 26 des carraghénanes) ; 140 n'ont aucun additif. Exemples : la Poêlée Fermière a trois additifs (amidon modifié, gomme guar, gomme xanthane), aucun à risque ; la pizza Regina de Buitoni en a deux à risque, le nitrite de sodium du jambon (E250) et des polyphosphates (E452). Ils se comptent dans la liste des additifs de la base ; l'interface les fait saisir directement. Tests : `test_les_additifs_a_risque`, `test_un_nombre_d_additifs_a_risque_saisi_prime_sur_la_liste`.
32. **Les classes ont le sens de celles du Nutri-Score.** La FAQ officielle du Nutri-Score ne range pas les aliments en bons ou mauvais : ses classes vont des plus favorables à la santé aux moins favorables, du point de vue nutritionnel. Nous gardons ce sens, étendu à la transformation et à la production : A′, les plats les plus favorables à la santé ; C′, les plats moyens ; E′, les moins favorables. Les classes servent à comparer des plats préparés entre eux. Nous n'en faisons pas des fréquences de consommation : ce serait un conseil, sans source. Test : `test_l_onglet_super_nutri_score`.
33. **Les deux analyses de sensibilité.** Les poids : chacun gagne ou perd 0,05, les autres étant rajustés pour garder une somme de 1 et des poids positifs ; puis 1 000 tirages au hasard (graine 2026), où tous les poids bougent ensemble d'au plus ± 0,01, ± 0,02 et ± 0,05. Les profils : une valeur bouge à la fois, de ± 5 % pour les sept composantes et de ± 1 pour NOVA et les deux nombres d'additifs (des entiers) ; le bio ne bouge pas ; un décalage qui casserait l'ordre des profils est écarté. On compte aussi les plats au bord de leur classe, dont la concordance vaut λ pile. Tests : `test_sans_amplitude_aucun_plat_ne_change`, `test_un_plat_au_bord_change_quand_un_de_ses_criteres_pese_moins`, `test_un_tirage_se_refait_a_l_identique`, `test_un_plat_au_seuil_change_quand_le_seuil_bouge`, `test_un_decalage_qui_casserait_l_ordre_est_ecarte`, `test_les_plats_au_bord_de_leur_classe`.
34. **La comparaison au Nutri-Score se fait plat par plat, et dans les deux sens.** Le Nutri-Score n'est pas à copier, mais c'est la référence. Un plat qui descend est expliqué par les critères qu'il rate face au profil de la classe que lui donne le Nutri-Score (pour un plat B, celui de B′) ; un plat qui monte, par ceux qu'il rate face au profil de sa classe, qu'il franchit pourtant. Chaque comparaison dit aussi son sens, lu dans la matrice de confusion : la part des produits rangés plus bas que la référence (plus sévère), pareil, plus haut (plus permissif), et l'écart moyen en classes, positif quand le modèle est plus sévère. Tests : `test_un_plat_qui_monte_et_un_plat_qui_descend`, `test_la_poelee_fermiere_descend_d_une_classe`, `test_le_sens_des_ecarts_d_une_matrice`, `test_pourquoi_un_plat_descend_et_pourquoi_un_autre_monte`, `test_chaque_comparaison_dit_son_sens`.
35. **La base d'un autre groupe : « leurs résultats » sont les classes de leur SuperNutri-score.** Leur base est arrivée le 25/11 : 300 céréales du petit-déjeuner (Branchu, Becavin, Bundhoo, Castan), dans `donnees/autre_groupe/`, avec la note de leur modèle. Leurs colonnes gardent leurs noms : une table de correspondance les relie aux nôtres.
    - **Leur modèle, recodé dans notre moteur** depuis leur feuille `notre_modele` : cinq critères (sucres, fibres, groupe NOVA, acides gras saturés, sodium), λ = 0,63 ; un NOVA inconnu ne vote pas, comme chez eux. Il redonne leurs 300 classes. Pour nos plats, leur sodium se tire du sel : le sel vaut 2,5 fois le sodium (règlement UE 1169/2011), soit 400 mg de sodium par gramme de sel.
    - **Leurs céréales complétées par Open Food Facts.** Leur base n'a ni les additifs ni le bio, que notre modèle demande. Ils se lisent dans la fiche d'OFF du code-barres (300 fiches, rangées une fois dans le cache par `--telecharger-autre-groupe`, aucune introuvable), avec le type du produit au Nutri-Score (le cas général pour les 300). Leur groupe NOVA est gardé ; celui d'OFF ne sert que s'il manquait. Le tout s'écrit dans `donnees/autre_groupe/base_cereales_completee.xlsx` : leurs colonnes, puis les nôtres, et une feuille « lisez-moi ».
    - **Le même Nutri-Score des deux côtés** : notre calcul de 2023 redonne leurs 300 labels.
    - **Aucun produit en commun** avec nos plats : le recoupement, mesuré par code-barres, reste sous les 25 % du §3.1.

    Tests : `test_leur_modele_se_lit_dans_leur_feuille`, `test_leur_modele_recode_redonne_leurs_300_classes`, `test_leur_modele_lit_le_sodium_de_nos_plats_dans_le_sel`, `test_l_import_lit_aussi_le_type_au_nutriscore`, `test_la_base_completee_garde_leurs_colonnes_et_ajoute_les_notres`, `test_deux_modeles_comparés_sur_une_base`, `test_l_analyse_de_l_autre_groupe_compare_les_deux_bases`, `test_l_excel_de_l_autre_groupe_a_trois_feuilles`, `test_importer_une_base_aux_colonnes_differentes`, `test_importer_un_csv_a_point_virgule`, `test_l_import_rend_les_classes_de_nos_250_plats_ajoutes`, `test_un_code_se_retrouve_meme_ecrit_avec_d_autres_zeros`, `test_le_telechargement_ne_redemande_pas_une_fiche_gardee`.
36. **λ se règle au curseur, avec les poids et les profils.** Le §3.5 demande de saisir à la main les paramètres d'un modèle, et λ en est un (§2.2). Le choix 0,6 / 0,7 de l'en-tête choisit le modèle appris ; le curseur des paramètres règle ensuite λ, de 0,51 à 1 (le sujet veut λ dans ]0,5 ; 1]), en partant du λ appris, et « Revenir aux paramètres appris » le remet. Un modèle appris ne vaut que pour son λ : ailleurs, la classe est une exploration. Le SuperNutri-score a son propre curseur. Tests : `test_lambda_se_regle_au_curseur`, `test_revenir_aux_parametres_appris_remet_lambda`, `test_le_pas_a_pas_suit_lambda_du_curseur`, `test_lambda_du_super_nutri_score_se_regle_aussi`.
37. **Les protéines votent comme le Nutri-Score de 2023 les compte** (ajouté le 25/11, après une revue de notre modèle). Le Nutri-Score ne compte pas les protéines d'un produit qui a 11 points négatifs ou plus (7 pour une matière grasse, un fruit à coque ou une graine) ; il les compte toujours pour un fromage et une boisson ; pour une viande rouge, il en garde au plus 2 points (FAQ officielle de 2023). Sans cette règle, les protéines votaient pour des plats gras et salés. La performance de notre critère est donc « les protéines que retient le Nutri-Score » : aucune (le critère ne vote pas) ou, pour une viande rouge, 4,8 g au plus. Ce n'est pas un veto : MR-Sort reste simple, seule la valeur du critère change. Le type du produit vient des marqueurs d'OFF ou, dans l'interface, du « Type de produit » ; si une des sept composantes manque, on garde les protéines du produit. Le Nutri-Score ne compte pas les protéines de 153 de nos 375 plats, ni de 163 des 300 céréales de l'autre groupe. Tests : `test_les_proteines_ne_votent_plus_a_partir_de_11_points_negatifs`, `test_les_proteines_d_un_fromage_votent_toujours`, `test_les_proteines_d_une_viande_rouge_comptent_au_plus_comme_deux_points`, `test_les_proteines_d_une_matiere_grasse_ne_votent_plus_a_partir_de_7_points`, `test_le_type_vient_du_produit_s_il_n_est_pas_donne`, `test_les_proteines_du_super_nutri_score_suivent_le_type_de_produit`, `test_le_readme_cite_la_regle_des_proteines`.

## La direction visuelle « Verso de l'emballage »

- **Le principe** : chaque production se lit comme le verso d'un emballage. Le noir et blanc porte la structure (papier #FFFFFF, encre #000000, trame #E9E9E6), et la couleur vient du Nutri-Score : ses classes (A #038141, B #85BB2F, C #FECB02, D #EE8100, E #E63E11), et ses points, avec le rouge de E pour les négatifs et le vert de A pour les positifs, comme dans les fig. 6 et 7 du sujet.
- **Les filets** codent la hiérarchie : 8 px en tête de panneau, 4 px entre groupes, 1 px entre lignes.
- **Les classes** : celles de nos modèles (A′ à E′) sont des cadres noirs avec une barre de couleur, jamais des pastilles pleines.
- **La police** est la seule famille Archivo : Archivo Condensed en gras (graisse 800) pour les titres, Archivo pour le texte. Elle n'a pas de lettres grecques, donc λ passe par une police de repli (et par le mode mathématique dans LaTeX).
- **Où sont les jetons** : dans `projet_design.py`, repris par `.streamlit/config.toml` et `rapport/verso.sty`. `DESIGN.md` décrit le système entier.
- **Les slides se lisent de loin.** Ce qu'il faut lire depuis le fond de la salle est dessiné en formes PowerPoint, à sa taille réelle : l'entonnoir, le détail des points, les barres de concordance, les versos. Le diagramme des profils est tracé à sa taille d'affichage (`figureProfils(..., taille, zoom)`). Les apostrophes deviennent typographiques à l'affichage.
- **L'interface a quatre onglets**, dont la barre reste en haut de l'écran pendant le défilement (au premier affichage, le calculateur montre la Poêlée Fermière, le plat suivi par la soutenance ; sans la base, l'exemple de la fig. 6) : Calculateur, Pas à pas (MR-Sort étape par étape, pour le plat et le modèle du calculateur, tels qu'ils y sont édités, et nommés : le diagramme des profils, les concordances partielles, la concordance, l'affectation), Modèles (la comparaison des modèles, meilleurs résultats en gras, la question du modèle exact, la courbe d'apprentissage), Base.
- **Le calculateur parle la langue du consommateur.** Deux choix donnent le modèle : « Appris sur » (375 plats, ou les 125 du 30/10) et « Apprentissage » (poids appris, profils appris, tout appris), avec les mots du tableau de l'onglet Modèles. Par défaut : 375 plats, avec l'apprentissage le meilleur en validation croisée (choix 27). Chaque profil porte la classe qu'il ouvre (choix 25). La ligne de titre de chaque éditeur des paramètres rappelle la classe du plat, pour la voir changer avec un poids. Les champs des fruits et des fibres disent où trouver leur valeur. « Revenir aux valeurs du produit » défait une saisie (choix 26), et choisir un plat dans la liste efface la recherche précédente.
- **L'interface s'adapte à l'écran.** À partir de 640 px, les colonnes du calculateur font au moins 24rem : sous 1 400 px de large environ (un vidéoprojecteur en 1280 ou 1024 px), la colonne MR-Sort passe sous les deux autres, au lieu de déborder. Sur un téléphone, les colonnes s'empilent, une jauge de plus de dix cases (sucres, sel) passe à la ligne toutes les dix cases, et un tableau trop large (les sept critères du pas à pas) défile dans son cadre. Un groupe de boutons trop large pour sa colonne passe à la ligne ; sur un téléphone, les trois choix d'« Apprentissage » prennent chacun une ligne. Vérifié à 375, 768, 1 024 et 1 440 px.

## Le projet de 2025

`docs/projet 2025/` contient le rapport de fin de L3 sur le Green-Score, avec une base de 496 céréales. Ce qu'on en garde :

- le principe de l'extraction par l'API d'OFF ;
- les champs NOVA, additifs et Green-Score ;
- les colonnes de comparaison avec OFF ;
- quatre produits comme jeux de test (`tests/fixtures/`) ;
- la FAQ officielle de l'algorithme actualisé en 2023, version du 17 mars 2025 (`document_rapport/FAQ-updatedAlgo-FR_V11.pdf`).

Son calcul du Nutri-Score suivait les barèmes de 2017 : il ne retrouvait la classe d'OFF que pour 49,8 % des céréales.

## Résultats

Ces chiffres viennent de `resultats/resultats_projet.json`, et `tests/test_readme.py` vérifie qu'ils y correspondent.

**La base.** 732 candidats repérés, 224 plats retenus après les filtres, puis 125 plats tirés, 25 par classe (graine 2026). Les données ont été extraites le 2026-10-28.

Plats retenus avant le tirage, par classe :

| A | B | C | D | E |
|---|---|---|---|---|
| 47 | 50 | 58 | 33 | 36 |

Les filtres les plus sévères sont les fibres non déclarées et le cas général : on écarte la viande rouge, les fromages, les boissons et les matières grasses.

**La base étendue.** 1632 candidats repérés (les pages de la base, plus 9 pages tirées dans le même ordre), 438 plats retenus, puis 50 plats par classe tirés hors de la base : 375 plats, 75 par classe (graine 2026, ajout extrait le 2026-11-07).

Plats retenus hors de la base, par classe :

| A | B | C | D | E |
|---|---|---|---|---|
| 50 | 62 | 92 | 53 | 56 |

**Le Nutri-Score.** Notre calcul retrouve le score et le label d'OFF pour 125/125 plats. La règle de la fig. 4 ne change le label d'aucun plat de la base. Sur tous les plats retenus de la base étendue, il retrouve OFF pour 437/438 plats du vivier étendu.

Les cas particuliers, vérifiés contre OFF sur les fiches du cache (`python3 projet_nutriscore.py`) :

| Type de produit | Fiches reproduites |
|---|---|
| Fromage | 49/50 |
| Viande rouge | 182/183 |
| Matière grasse, fruit à coque ou graine | 82/82 |
| Boisson | 19/20 |
| Eau | 14/14 |

Chaque écart vient d'OFF, et le programme l'explique. Soit OFF marque le produit de deux types à la fois et cumule leurs règles, ce que la FAQ ne fait jamais : une piadina au fromage et au speck (fromage et viande rouge), une gardiane de taureau rangée parmi les boissons. Soit il compte un point de plus pour une valeur pile sur un seuil (« Voyage aux Antilles », 0,8 g de sel), sans doute une valeur plus précise que celle de sa fiche. Ce cas est rare : OFF lit « > » 449 fois sur 453 pour le sel, comme notre choix 4.

**MR-Sort.** Les profils sont fixés par les médianes et les poids sont appris (`python3 projet_mrsort.py`) :

| Modèle | λ | Bien rangés | Exactitude | À une classe près |
|---|---|---|---|---|
| 7 critères | 0,6 | 90/125 | 72,0 % | 97,6 % |
| 7 critères | 0,7 | 90/125 | 72,0 % | 96,8 % |
| 3 critères | 0,6 | 73/125 | 58,4 % | 92,8 % |
| 3 critères | 0,7 | 73/125 | 58,4 % | 92,8 % |

**Les paires de dominance inversées.** Il y en a 0 à 7 critères et 143 à 3 critères : aucun MR-Sort à 3 critères ne peut reproduire exactement le Nutri-Score. Par exemple, la « Purée de pomme de terre, beurre et crème d'Isigny » (D) vaut au moins le « Colin d'Alaska » (A) sur l'énergie, le sel et les fruits et légumes. À 7 critères, voir le modèle complet, plus bas.

**Ce qu'on lit dans les modèles.** Dans les plats préparés, les plats E sont souvent riches en protéines (viande, fromage). Comme les profils doivent rester ordonnés, les profils de protéines et de fibres sont plats (9,55 g et 1,8 g), et ces critères pèsent peu. Plusieurs jeux de poids rangent aussi bien les plats : le solveur en rend un, ce qui explique les poids très inégaux (acides gras saturés 0,4396 à λ = 0,6). Parmi les modèles qui rangent bien 90 plats, le poids des acides gras saturés va de 0,334 à 0,498 à λ = 0,6, et de 0,501 à 0,623 à λ = 0,7 (choix 18). Ils restent le critère le plus lourd ; mais à λ = 0,6, les six autres critères peuvent ensemble atteindre λ, alors qu'à λ = 0,7 aucun profil n'est franchi sans eux.

**Le second apprentissage : poids fixés, profils appris** (`python3 projet_mrsort.py --profils`, cinq minutes au plus par modèle ; « prouvé » : le solveur a prouvé le maximum) :

| Modèle | λ | Bien rangés | Maximum prouvé | À une classe près |
|---|---|---|---|---|
| 7 critères | 0,6 | 114/125 | 121 | 100,0 % |
| 7 critères | 0,7 | 120/125 | 120 (prouvé) | 99,2 % |
| 3 critères | 0,6 | 92/125 | 92 (prouvé) | 95,2 % |
| 3 critères | 0,7 | 92/125 | 92 (prouvé) | 95,2 % |

Apprendre les profils fait sauter le plafond des profils par les médianes : à 7 critères, 120 plats sur 125 sont bien rangés à λ = 0,7, contre 90.

**Sur des plats que les modèles n'ont pas vus.** Les modèles appris sur les 125 plats de la base rangent ainsi les 250 plats que la base étendue ajoute (`python3 projet_mrsort.py`, première feuille de `resultats/generalisation.xlsx`) :

| Modèle | Apprentissage | λ | Bien rangés, base | Bien rangés, plats ajoutés | Exactitude, plats ajoutés |
|---|---|---|---|---|---|
| 7 critères | profils fixés (médianes), poids appris | 0,6 | 90/125 | 137/250 | 54,8 % |
| 7 critères | profils fixés (médianes), poids appris | 0,7 | 90/125 | 136/250 | 54,4 % |
| 3 critères | profils fixés (médianes), poids appris | 0,6 | 73/125 | 136/250 | 54,4 % |
| 3 critères | profils fixés (médianes), poids appris | 0,7 | 73/125 | 136/250 | 54,4 % |
| 7 critères | poids fixés (points maximaux), profils appris | 0,6 | 114/125 | 170/250 | 68,0 % |
| 7 critères | poids fixés (points maximaux), profils appris | 0,7 | 120/125 | 168/250 | 67,2 % |
| 3 critères | poids fixés (points maximaux), profils appris | 0,6 | 92/125 | 134/250 | 53,6 % |
| 3 critères | poids fixés (points maximaux), profils appris | 0,7 | 92/125 | 134/250 | 53,6 % |
| 7 critères | poids et profils appris (alternance) | 0,6 | 122/125 | 173/250 | 69,2 % |
| 7 critères | poids et profils appris (alternance) | 0,7 | 120/125 | 168/250 | 67,2 % |
| 3 critères | poids et profils appris (alternance) | 0,6 | 92/125 | 134/250 | 53,6 % |
| 3 critères | poids et profils appris (alternance) | 0,7 | 92/125 | 134/250 | 53,6 % |

Le modèle à 7 critères perd 17 points sur des plats nouveaux. Celui aux profils appris tient mieux : sur les plats ajoutés, jamais vus, 68,0 % au lieu de 54,8 % (λ = 0,6). À 3 critères, apprendre les profils n'aide que sur la base.

**Le modèle complet** (`python3 projet_mrsort.py --complet`) : poids et profils appris tour à tour, en partant des poids des points maximaux. À 7 critères et λ = 0,6, les étapes donnent 114 → 119 → 122 plats bien rangés ; c'est aussi le meilleur sur les plats jamais vus (69,2 %).

**Existe-t-il un modèle exact ?** (question 1 du sujet). À 3 critères, non : 143 paires inversées. À 7 critères, aucune paire n'est inversée ; le meilleur modèle trouvé range 122 plats sur 125, et le solveur, en 30 minutes, n'a ni trouvé de modèle exact ni prouvé qu'il n'en existe pas. La question reste ouverte. Une estimation faite sur le seul cache (les 99 plats retenus mais non tirés) en promettait moins : ces plats venaient des mêmes pages de l'index que la base, et lui ressemblaient plus que ceux des pages nouvelles.

**La courbe d'apprentissage** (`python3 projet_mrsort.py --courbe` : base étendue, λ = 0,6, 15 plats par classe tenus à part, 10 tirages par taille). À 7 critères, l'exactitude sur des plats jamais vus passe de 59,2 % (25 plats appris) à 65,3 % (300 plats appris). À 3 critères, l'exactitude sur des plats jamais vus passe de 56,1 % (25 plats appris) à 63,2 % (300 plats appris). Entre les deux, la courbe plafonne vite, et les tirages varient de plusieurs points : apprendre sur plus de plats aide un peu, puis plus guère. Le plafond vient du modèle (des profils fixés par les médianes), pas du nombre de plats.

**Les modèles appris sur les 375 plats, poids appris** (profils par les médianes), départagés par la plus grande marge :

| Modèle | λ | Bien rangés | Exactitude | À une classe près |
|---|---|---|---|---|
| 7 critères | 0,6 | 259/375 | 69,1 % | 94,9 % |
| 7 critères | 0,7 | 240/375 | 64,0 % | 94,1 % |
| 3 critères | 0,6 | 233/375 | 62,1 % | 92,3 % |
| 3 critères | 0,7 | 233/375 | 62,1 % | 92,3 % |

Sur les 375 plats, il y a 0 paires inversées à 7 critères et 997 à 3 critères. Les poids s'y répartissent autrement : à 7 critères et λ = 0,6, l'énergie, les acides gras saturés et le sel portent l'essentiel (0,237, 0,276 et 0,276), et chacun garde au moins 0,2 dans tous les modèles optimaux. Le poids écrasant des acides gras saturés appris sur 125 plats tenait donc en partie à la petite taille de la base.

**Les profils appris et le modèle complet sur les 375 plats** (`python3 projet_mrsort.py --etendue`, 600 s au plus par apprentissage des profils ; « prouvé » : le solveur a prouvé le maximum) :

| Modèle | Apprentissage | λ | Bien rangés | Maximum garanti | À une classe près |
|---|---|---|---|---|---|
| 7 critères | profils appris | 0,6 | 296/375 | 362 | 97,9 % |
| 7 critères | profils appris | 0,7 | 301/375 | 360 | 95,5 % |
| 3 critères | profils appris | 0,6 | 248/375 | 248 (prouvé) | 90,4 % |
| 3 critères | profils appris | 0,7 | 248/375 | 248 (prouvé) | 90,4 % |
| 7 critères | tout appris | 0,6 | 316/375 | — | 98,7 % |
| 7 critères | tout appris | 0,7 | 322/375 | — | 98,1 % |
| 3 critères | tout appris | 0,6 | 267/375 | — | 93,3 % |
| 3 critères | tout appris | 0,7 | 248/375 | — | 90,4 % |

Comme sur les 125 plats, la méthode compte plus que le nombre de plats. À 7 critères et λ = 0,6, on passe de 259 plats bien rangés (poids appris) à 296 (profils appris), puis à 316 (tout appris : 297 → 301 → 307 → 309 → 316).
- Ces modèles ont vu les 375 plats : seule la validation croisée les mesure sur des plats nouveaux.
- À 7 critères, en 600 s, le solveur reste loin du maximum qu'il garantit. Un apprentissage arrêté par sa limite de temps peut donc finir sur une solution un peu différente d'une exécution à l'autre : le premier tour du modèle complet refait l'apprentissage des profils (mêmes poids, même limite), et trouve 297 plats au lieu de 296.
- Un premier calcul, lancé la nuit du 08 au 09/11, arrêtait le modèle complet à 3 critères et λ = 0,7 à 242 plats, sous les 248 des profils appris seuls (maximum prouvé). La mise en veille du Mac l'avait coupé : l'horloge du solveur la compte dans sa limite de temps (choix 22). Recalculé, il atteint 248 plats, et l'apprentissage des poids qui suit n'en range pas plus.

**La validation croisée sur les 375 plats** (`python3 projet_mrsort.py --croisee`, protocole du choix 27). Chaque plat y est rangé une fois, par un modèle appris sur les 300 autres. L'exactitude moyenne est celle des 5 parts, et l'écart-type dit combien elle varie d'une part à l'autre. « Parts prouvées » : celles où le solveur a prouvé l'optimum de l'apprentissage des profils, en 300 s au plus ; le modèle complet ne prouve rien.

| Modèle | Apprentissage | λ | Exactitude moyenne | Écart-type entre les parts | Bien rangés | À une classe près | Parts prouvées |
|---|---|---|---|---|---|---|---|
| 7 critères | poids appris | 0,6 | 64,5 % | 4,4 points | 242/375 | 93,6 % | 5/5 |
| 7 critères | poids appris | 0,7 | 61,1 % | 2,2 points | 229/375 | 92,8 % | 5/5 |
| 7 critères | profils appris | 0,6 | 70,4 % | 3,5 points | 264/375 | 97,3 % | 0/5 |
| 7 critères | profils appris | 0,7 | 70,7 % | 3,7 points | 265/375 | 96,0 % | 0/5 |
| 7 critères | tout appris | 0,6 | 64,0 % | 6,0 points | 240/375 | 98,4 % | — |
| 7 critères | tout appris | 0,7 | 70,9 % | 5,1 points | 266/375 | 96,5 % | — |
| 3 critères | poids appris | 0,6 | 60,5 % | 4,7 points | 227/375 | 92,5 % | 5/5 |
| 3 critères | poids appris | 0,7 | 60,5 % | 4,7 points | 227/375 | 92,5 % | 5/5 |
| 3 critères | profils appris | 0,6 | 55,7 % | 4,6 points | 209/375 | 87,7 % | 4/5 |
| 3 critères | profils appris | 0,7 | 56,3 % | 4,9 points | 211/375 | 86,7 % | 4/5 |
| 3 critères | tout appris | 0,6 | 59,5 % | 6,3 points | 223/375 | 90,4 % | — |
| 3 critères | tout appris | 0,7 | 57,9 % | 4,1 points | 217/375 | 89,1 % | — |

- **À 7 critères, apprendre les profils fait mieux qu'apprendre les poids** : 70,4 % contre 64,5 % à λ = 0,6, mieux dans 4 parts sur 5 et aussi bien dans la cinquième ; à λ = 0,7, mieux dans les 5 parts (70,7 % contre 61,1 %). C'est l'apprentissage que l'interface montre par défaut. Aucun de ces apprentissages des profils n'est prouvé optimal en 300 s : ces chiffres sont ceux de la méthode à ce temps de calcul.
- **Tout apprendre n'aide pas sur des plats nouveaux** : 64,0 % à λ = 0,6 et 70,9 % à λ = 0,7, contre 70,4 % et 70,7 % pour les profils appris. Sur les 375 plats, le modèle complet range pourtant le plus de plats (316 et 322) : ce qu'il gagne sur les plats appris ne se retrouve pas sur des plats nouveaux.
- **À 3 critères, les poids appris ont la meilleure moyenne** (60,5 %, contre 55,7 % et 56,3 % pour les profils appris), mais pas dans toutes les parts : les profils appris font mieux qu'eux dans 2 parts sur 5, aux deux valeurs de λ. Sur les 375 plats, les profils appris rangeaient pourtant plus de plats que les poids appris (248 contre 233).
- **D'une part à l'autre, l'exactitude varie** : son écart-type va de 2,2 à 6,3 points. Un écart de 1 ou 2 points entre deux apprentissages ne les départage donc pas.

**Le SuperNutri-score** (`python3 projet_supernutri.py`, choix 28 à 37) :

| Base | A′ | B′ | C′ | D′ | E′ | Comme le Nutri-Score | À une classe près |
|---|---|---|---|---|---|---|---|
| 125 plats | 4 | 14 | 53 | 27 | 27 | 70/125 | 90,4 % |
| 375 plats | 12 | 41 | 171 | 74 | 77 | 210/375 | 89,9 % |

- Il ne cherche pas à reproduire le Nutri-Score. Sur les 375 plats, 20 montent, 145 descendent. Face au profil de leur classe au Nutri-Score, les plats qui descendent ratent surtout les fibres (125), les protéines (113), le bio (108), le sel (105) et le groupe NOVA (87).
- La Poêlée Fermière, B au Nutri-Score, est C′ : face à B′, elle rate les protéines, les fibres, NOVA, les additifs et le bio. Avec NOVA 3 et un seul additif, elle serait B′.
- 5 des 12 plats A′ sont des produits secs, à plus de 1 340 kJ pour 100 g : Couscous, Couscous Complet, Couscous fin, Couscous Moyen et Velouté de pois cassés. Nos seuils lisent 100 g du produit tel qu'il est vendu, et λ = 0,7 laisse rater l'énergie : c'est une limite du modèle.

**Plus sévère ou plus permissif que le Nutri-Score ?** Plus sévère : une classe plus basse que la référence. L'écart moyen se compte en classes, positif quand le modèle est plus sévère (choix 34).

| Comparaison | Base | Même classe | Plus sévère | Plus permissif | Écart moyen |
|---|---|---|---|---|---|
| Notre modèle face au Nutri-Score | nos 375 plats | 56,0 % | 38,7 % | 5,3 % | +0,43 |
| Leur modèle face au Nutri-Score | leurs 300 céréales | 47,0 % | 41,0 % | 12,0 % | +0,37 |
| Notre modèle face au Nutri-Score | leurs 300 céréales | 34,7 % | 65,3 % | 0,0 % | +0,90 |
| Leur modèle face au Nutri-Score | nos 375 plats | 27,7 % | 64,5 % | 7,7 % | +1,16 |
| Notre modèle face au leur | leurs 300 céréales | 52,0 % | 43,0 % | 5,0 % | +0,52 |
| Notre modèle face au leur | nos 375 plats | 32,5 % | 11,7 % | 55,7 % | −0,72 |

- **Notre modèle est plus sévère que le Nutri-Score, surtout en haut.** 64 des 75 plats A descendent : 61 ont moins de 6 g de fibres, 53 plus de 0,3 g de sel. 60 des 75 plats B descendent : 56 ne sont pas bio, 51 sont ultra-transformés (NOVA 4). C'est voulu : A′ reprend les allégations du règlement CE 1924/2006, et A′ comme B′ exigent le bio et peu de transformation (choix 30).
- **Il est plus permissif pour 20 plats, presque tous chargés** : 19 ont au moins 11 points négatifs (pizzas, feuilletés). Le Nutri-Score additionne leurs points ; MR-Sort, sans veto (le sujet l'impose), ne retire que le poids des critères ratés, que le seuil soit dépassé de peu ou de beaucoup.
- **Chaque modèle porte la catégorie pour laquelle il est fait.** Chacun est un peu plus sévère que le Nutri-Score sur sa propre base, et bien plus sur celle de l'autre. Sur leurs céréales, notre seuil d'énergie de B′ (670 kJ) ne vote pour aucune ; sur nos plats, leur seuil de fibres de B′ bloque 96 % des plats.
- **Nos résultats diffèrent des leurs** (§3.4) : les deux modèles ne donnent la même classe qu'à 52,0 % de leurs céréales et 32,5 % de nos plats. Les deux produits suivis : un muesli croustillant bio sans additif, C au Nutri-Score, B′ chez eux, E′ chez nous ; la Poêlée Fermière, B au Nutri-Score, C′ chez nous, E′ chez eux. Le détail, produit par produit, est dans `resultats/supernutri_autre_groupe.xlsx`.

**Les deux sensibilités, sur 375 plats.** Tous les poids ensemble, 1 000 tirages par amplitude :

| Amplitude | Plats qui changent de classe, en moyenne | Au plus |
|---|---|---|
| ± 0,01 | 3,5 % | 7,7 % |
| ± 0,02 | 4,8 % | 16,5 % |
| ± 0,05 | 11,5 % | 27,2 % |

- Un poids à la fois, le plus sensible est celui des protéines (+ 0,05 : 74 plats).
- 13 plats sont au bord de leur classe : ils ratent tout le pilier « à favoriser », et leur concordance vaut λ pile. Le moindre changement de poids les fait basculer, d'où des changements dès ± 0,01.
- Les profils : 116 plats changent au moins une fois ; 43 par les composantes (± 5 %), 91 par NOVA et les additifs (± 1). Le décalage le plus actif : NOVA 3 exigé dès C′ (52 plats). NOVA ne vaut que 3 ou 4 dans nos plats préparés : un cran, c'est la moitié de son échelle.
