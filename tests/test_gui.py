"""Tests de l'interface (questions 3.2 et 3.5), lancée sans navigateur par AppTest."""

import pytest
from streamlit.testing.v1 import AppTest

import projet_base


def lancer():
    """Lance l'interface et renvoie l'AppTest après un premier affichage."""
    return AppTest.from_file("../projet_gui.py", default_timeout=20).run()


def test_l_interface_demarre_sans_erreur():
    """Premier affichage : pas d'exception ; le plat prérempli (la Poêlée Fermière, ou sans la base la fig. 6) a le score 1, label B."""
    at = lancer()
    assert not at.exception
    assert (at.session_state["nutriscore"]["score"], at.session_state["nutriscore"]["label"]) == (1, "B")


def test_la_saisie_recalcule_le_nutriscore():
    """On saisit l'exemple de la fig. 7 à la main : 11 points négatifs, score 9, label C."""
    at = lancer()
    for composante, valeur in {"en": 1961, "sa": 2, "su": 17, "so": 0.38, "pr": 10, "fi": 4.6, "fr": 0}.items():
        at.number_input(key=f"saisie_{composante}").set_value(valeur)
    at.run()
    assert not at.exception
    resultat = at.session_state["nutriscore"]
    assert (resultat["N"], resultat["score"], resultat["label"]) == (11, 9, "C")
    assert not resultat["proteinesComptees"]


def test_partir_d_un_exemple_recopie_ses_valeurs():
    """Choisir l'exemple de la fig. 7 recopie ses sept composantes dans les champs de saisie."""
    at = lancer()
    choix = [option for option in at.selectbox(key="exemple").options if "figure 7" in option][0]
    at.selectbox(key="exemple").select(choix).run()
    assert not at.exception
    assert at.number_input(key="saisie_so").value == 0.38
    assert at.session_state["nutriscore"]["label"] == "C"


def test_vider_le_choix_garde_les_valeurs_saisies():
    """Vider « Partir d'un plat » (la croix de la liste) ne lève pas d'erreur : les valeurs saisies restent."""
    at = lancer()
    choix = [option for option in at.selectbox(key="exemple").options if "figure 7" in option][0]
    at.selectbox(key="exemple").select(choix).run()
    at.selectbox(key="exemple").set_value(None).run()
    assert not at.exception
    assert at.number_input(key="saisie_so").value == 0.38
    assert at.session_state["nutriscore"]["label"] == "C"


baseConstruite = pytest.mark.skipif(not projet_base.FICHIER_BASE.exists(), reason="la base n'est pas encore construite")


@baseConstruite
def test_vider_le_choix_retire_la_fiche_du_plat():
    """Après la Poêlée Fermière, vider le choix retire sa fiche, et ses valeurs restent dans les champs."""
    at = lancer()
    choix = [option for option in at.selectbox(key="exemple").options if "Poêlée Fermière" in option][0]
    at.selectbox(key="exemple").select(choix).run()
    assert at.session_state["platChoisi"] is not None
    at.selectbox(key="exemple").set_value(None).run()
    assert not at.exception
    assert at.session_state["platChoisi"] is None
    assert at.number_input(key="saisie_sa").value == 1.6


@baseConstruite
def test_les_deux_modeles_mrsort_rangent_le_plat():
    """Avec la base, les panneaux MR-Sort à 7 et 3 critères rangent le plat saisi dans une classe A′ à E′."""
    at = lancer()
    assert not at.exception
    for nom in ("sept", "trois"):
        resultat = at.session_state[f"mrsort_{nom}"]
        assert resultat["lam"] == 0.6 and 0 <= resultat["classe"] <= 4


@baseConstruite
def test_le_seuil_majoritaire_se_choisit():
    """Choisir λ = 0,7 range le plat avec le modèle appris à 0,7."""
    at = AppTest.from_file("../projet_gui.py", default_timeout=20)
    at.session_state["lam_sept"] = 0.7
    at.run()
    assert not at.exception
    assert at.session_state["mrsort_sept"]["lam"] == 0.7


# --- Les éléments enrichis de l'interface ---

import projet_gui as gui
import projet_nutriscore as ns


def test_motif_ean13_d_un_code_connu():
    """4006381333931 : 95 modules, les trois gardes, et les deux premiers chiffres codés L puis G (premier chiffre 4)."""
    motif = gui.motifEan13("4006381333931")
    assert len(motif) == 95
    assert motif[:3] == "101" and motif[45:50] == "01010" and motif[-3:] == "101"
    assert motif[3:10] == gui.CODE_L[0] and motif[10:17] == gui.CODE_G[0]


def test_motif_ean13_refuse_un_code_faux():
    """Une clé de contrôle fausse, ou un code à 8 chiffres, ne donne pas de code-barres."""
    assert gui.motifEan13("4006381333932") is None
    assert gui.motifEan13("20081324") is None
    assert "Code 20081324" in gui.codeBarresSvg("20081324")


def test_jauge_des_points():
    """2 points sur 20 : 20 cases, dont 2 pleines ; la jauge porte la couleur de son groupe."""
    jauge = gui.jaugeHtml(2, 20)
    assert jauge.count("<i") == 20 and jauge.count("class='point'") == 2
    assert "class='jauge negatif'" in gui.jaugeHtml(2, 20, "negatif")
    assert "class='jauge'" in jauge


def test_les_points_s_ouvrent_sur_l_en_tete_de_leur_groupe():
    """Fig. 7 : l'en-tête négatif (11 / 55), quatre composantes, l'en-tête positif (2 / 17), trois composantes."""
    from projet_nutriscore import EXEMPLES_SUJET

    produit = EXEMPLES_SUJET["figure 7"]["produit"]
    lignes = gui.lignesDesPoints(produit, ns.scoreNutriscore(produit))
    assert len(lignes) == 9
    assert "signe negatif" in lignes[0]["composante"] and "Points négatifs N" in lignes[0]["composante"]
    assert lignes[0]["points"] == "11 / 55"
    assert "signe positif" in lignes[5]["composante"] and lignes[5]["points"] == "2 / 17"
    assert lignes[5]["_classe"] == "groupe total"
    assert all("jauge negatif" in ligne["points"] for ligne in lignes[1:5])
    assert all("jauge positif" in ligne["points"] for ligne in lignes[6:])
    assert lignes[6]["_classe"] == "ecarte"          # 11 points négatifs : les protéines ne comptent pas


@baseConstruite
def test_barres_de_concordance_de_la_poelee_fermiere():
    """À 7 critères et λ = 0,6, la Poêlée Fermière franchit b3 (6 cases noires) mais pas b4 (5 cases noires)."""
    plat = [p for p in projet_base.lireBase() if p["code"] == "3257982125116"][0]
    modele = [m for m in gui.resultatsDuProjet()["mrsort"]["modeles"] if m["nom"] == "sept" and m["lam"] == 0.6][0]
    regle = {"criteres": modele["criteres"], "poids": modele["poids"], "profils": modele["profils"], "lam": 0.6}
    barres = gui.barresDeConcordanceHtml(gui.affecter(plat, regle), regle, plat)
    lignes = barres.split("<div class='ligne-concordance'")[1:]          # b5, b4, b3, b2
    assert [ligne.count("case pleine") for ligne in lignes] == [5, 5, 6, 6]
    assert "0,479 &lt; 0,6" in lignes[1] and "0,919 ≥ 0,6, franchi" in lignes[2]


@baseConstruite
def test_la_demonstration_de_la_soutenance():
    """
    Avec les modèles du 30/10 (appris sur 125 plats) : on part de la Poêlée Fermière, sa fiche
    s'affiche ; avec 1,4 g de graisses saturées, elle passe en B′.
    """
    at = AppTest.from_file("../projet_gui.py", default_timeout=20)
    at.session_state["apprisSur"] = "125"
    at.session_state["apprentissage"] = "poids"
    at.run()
    choix = [option for option in at.selectbox(key="exemple").options if "Poêlée Fermière" in option][0]
    at.selectbox(key="exemple").select(choix).run()
    assert not at.exception
    assert at.session_state["platChoisi"]["code"] == "3257982125116"
    assert not at.session_state["valeursModifiees"]
    assert at.session_state["mrsort_sept"]["classe"] == 2                 # C′
    at.number_input(key="saisie_sa").set_value(1.4).run()
    assert at.session_state["valeursModifiees"]
    assert at.session_state["nutriscore"]["label"] == "B"
    assert at.session_state["mrsort_sept"]["classe"] == 3                 # B′


# --- Chercher un produit : code-barres, lien Open Food Facts ou nom (sans réseau : le cache seul) ---

POELEE, LASAGNES, AMANDES = "3257982125116", "20163723", "0634113230049"
cacheDisponible = pytest.mark.skipif(not (projet_base.DOSSIER_BRUT / "produits" / f"{POELEE}.json").exists(),
                                     reason="le cache d'Open Food Facts n'est pas là")


def lancerHorsLigne(monkeypatch):
    """Lance l'interface sans réseau : la recherche ne lit que les fiches gardées dans le cache."""
    monkeypatch.setenv("PROJET_HORS_LIGNE", "1")
    return lancer()


def chercher(at, texte):
    """Saisit un texte dans la recherche et clique sur « Chercher »."""
    at.text_input(key="recherche").set_value(texte)
    return at.button(key="chercher").click().run()


@cacheDisponible
def test_un_code_barres_remplit_la_saisie(monkeypatch):
    """Le code-barres de la Poêlée Fermière : ses valeurs dans les champs, cas général, et le même résultat qu'OFF."""
    at = chercher(lancerHorsLigne(monkeypatch), POELEE)
    assert not at.exception
    assert at.session_state["produitCherche"]["code"] == POELEE
    assert at.number_input(key="saisie_sa").value == 1.6
    assert at.session_state["categorie"] == "general"
    assert at.session_state["nutriscore"]["label"] == "B"
    assert at.session_state["accordOff"] and not at.session_state["horsDomaine"]


@cacheDisponible
def test_un_lien_off_propose_le_type_d_off(monkeypatch):
    """Un lien vers des lasagnes qu'OFF marque viande rouge : le type est proposé, hors du domaine de MR-Sort."""
    at = chercher(lancerHorsLigne(monkeypatch), f"https://fr.openfoodfacts.org/produit/{LASAGNES}/lasagnes")
    assert not at.exception
    assert at.session_state["categorie"] == "viandeRouge"
    assert at.session_state["accordOff"] and at.session_state["horsDomaine"]


@cacheDisponible
def test_un_nom_donne_une_liste_puis_un_choix(monkeypatch):
    """« poêlée fermière » donne une liste ; choisir la Poêlée Fermière remplit les champs."""
    at = chercher(lancerHorsLigne(monkeypatch), "poêlée fermière")
    assert not at.exception
    choix = [option for option in at.selectbox(key="choixRecherche").options if "Poêlée Fermière" in option][0]
    at.selectbox(key="choixRecherche").select(choix).run()
    assert not at.exception
    assert at.session_state["produitCherche"]["code"] == POELEE
    assert at.number_input(key="saisie_so").value == 0.55


@cacheDisponible
def test_une_recherche_sans_resultat_donne_un_message(monkeypatch):
    """Rien dans le cache, et pas de réseau : un message, sans exception ni produit."""
    at = chercher(lancerHorsLigne(monkeypatch), "zzz introuvable")
    assert not at.exception
    assert "Aucun produit" in at.session_state["messageRecherche"]
    assert at.session_state["produitCherche"] is None


@cacheDisponible
def test_partir_d_un_plat_efface_le_produit_cherche(monkeypatch):
    """Après une recherche, choisir un exemple du sujet revient au cas général, sans fiche OFF."""
    at = chercher(lancerHorsLigne(monkeypatch), LASAGNES)
    choix = [option for option in at.selectbox(key="exemple").options if "figure 7" in option][0]
    at.selectbox(key="exemple").select(choix).run()
    assert not at.exception
    assert at.session_state["produitCherche"] is None and at.session_state["categorie"] == "general"


def test_le_type_boisson_change_le_calcul():
    """Choisir « Boisson » : les barèmes des boissons, la ligne des édulcorants, et l'avertissement de MR-Sort."""
    at = lancer()
    at.selectbox(key="categorie").select("boisson").run()
    assert not at.exception
    resultat = at.session_state["nutriscore"]
    assert resultat["categorie"] == "boisson" and "edulcorants" in resultat["points"]
    assert at.session_state["horsDomaine"]


@pytest.mark.skipif(not (projet_base.DOSSIER_BRUT / "produits" / f"{AMANDES}.json").exists(),
                    reason="les échantillons de vérification ne sont pas encore téléchargés")
def test_des_amandes_passent_en_matieres_grasses(monkeypatch):
    """Des amandes : type matières grasses, le champ des lipides, et le même résultat qu'OFF (−10, A)."""
    at = chercher(lancerHorsLigne(monkeypatch), AMANDES)
    assert not at.exception
    assert at.session_state["categorie"] == "matieresGrasses"
    assert at.number_input(key="saisie_lipides").value == 52.5
    assert (at.session_state["nutriscore"]["score"], at.session_state["nutriscore"]["label"]) == (-10, "A")


@pytest.mark.skipif(not projet_base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")
def test_appris_sur_choisit_la_base_des_modeles():
    """« Appris sur » : les 375 plats par défaut, ou les 125 du 30/10 ; les panneaux MR-Sort suivent."""
    at = lancer()
    assert not at.exception
    assert at.segmented_control(key="apprisSur").options == ["375 plats", "125 plats (30/10)"]
    assert at.session_state["mrsort_sept"]["base"] == "375"
    at.segmented_control(key="apprisSur").set_value("125").run()
    assert not at.exception
    assert at.session_state["mrsort_sept"]["base"] == "125" and at.session_state["mrsort_trois"]["base"] == "125"


@cacheDisponible
def test_une_nouvelle_recherche_efface_le_choix_precedent(monkeypatch):
    """Après un choix dans les résultats, une nouvelle recherche par nom repart d'une liste sans choix."""
    at = chercher(lancerHorsLigne(monkeypatch), "poêlée fermière")
    choix = [option for option in at.selectbox(key="choixRecherche").options if "Poêlée Fermière" in option][0]
    at.selectbox(key="choixRecherche").select(choix).run()
    at = chercher(at, "lasagnes bolognaise")
    assert not at.exception
    assert at.selectbox(key="choixRecherche").value is None
    assert all("Lasagne" in option for option in at.selectbox(key="choixRecherche").options)


@baseConstruite
def test_un_plat_sans_marque_n_affiche_pas_none():
    """Deux plats de la base n'ont pas de marque : leur nom s'affiche seul, sans « (None) »."""
    at = lancer()
    options = at.selectbox(key="exemple").options
    assert any("The finest salad" in option for option in options)
    assert not [option for option in options if "None" in option]


@pytest.mark.skipif(not projet_base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")
def test_l_onglet_base_montre_la_base_etendue():
    """
    L'onglet Base montre d'abord la base étendue, et sa vérification porte sur tout le vivier ; puis la base du 30/10.
    Ses choix nomment une base, et non un modèle.
    """
    at = lancer()
    assert not at.exception
    assert at.segmented_control(key="baseAffichee").options == ["375 plats", "125 plats (30/10)"]
    resultats = gui.resultatsDuProjet()
    assert at.session_state["verificationAffichee"] == resultats["nutriscore"]["vivierEtendu"]
    at.segmented_control(key="baseAffichee").set_value("125").run()
    assert not at.exception
    assert at.session_state["verificationAffichee"]["total"] == 125


def profilsAppris():
    """Vrai si les modèles aux profils appris sont dans resultats_projet.json."""
    import json
    if not projet_base.FICHIER_RESULTATS.exists():
        return False
    return "mrsortProfils" in json.loads(projet_base.FICHIER_RESULTATS.read_text(encoding="utf-8"))


@pytest.mark.skipif(not profilsAppris(), reason="les modèles aux profils appris ne sont pas encore calculés")
def test_on_choisit_les_modeles_aux_profils_appris():
    """
    Sur les 125 plats, « Apprentissage » propose les poids appris, les profils appris (poids des
    points maximaux) et le modèle complet. AppTest donne les libellés affichés ; on choisit par la valeur.
    """
    at = lancer()
    at.segmented_control(key="apprisSur").set_value("125").run()
    assert at.segmented_control(key="apprentissage").options == ["Poids appris", "Profils appris", "Tout appris"]
    for apprentissage in ("profils", "complet"):
        at.segmented_control(key="apprentissage").set_value(apprentissage).run()
        assert not at.exception
        assert (at.session_state["mrsort_sept"]["base"], at.session_state["mrsort_sept"]["apprentissage"]) == ("125", apprentissage)


@pytest.mark.skipif(not projet_base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")
def test_l_onglet_modeles_compare_tous_les_modeles():
    """
    L'onglet Modèles montre une ligne par modèle appris sur la base, comme le JSON de la généralisation ;
    ses en-têtes disent sur quels plats se mesure chaque colonne.
    """
    at = lancer()
    assert not at.exception
    lignes = gui.resultatsDuProjet()["generalisation"]["modeles"]
    assert at.session_state["lignesModeles"] == len(lignes)
    assert blocsHtml(at, "Exactitude, plats ajoutés")


@baseConstruite
def test_l_onglet_pas_a_pas_explique_le_classement():
    """
    Le pas à pas reprend le plat et le modèle du calculateur : ses quatre étapes (une par profil)
    mènent à la même classe que le panneau MR-Sort, à 7 critères puis à 3.
    """
    at = lancer()
    assert not at.exception
    pasAPas = at.session_state["pasAPas"]
    assert (pasAPas["nom"], pasAPas["classe"], pasAPas["etapes"]) == ("sept", at.session_state["mrsort_sept"]["classe"], 4)
    at.segmented_control(key="pasAPasModele").set_value("trois").run()
    assert not at.exception
    assert at.session_state["pasAPas"]["classe"] == at.session_state["mrsort_trois"]["classe"]


@baseConstruite
def test_les_formules_du_pas_a_pas_sont_du_latex_propre():
    """Les formules du pas à pas n'ont aucun caractère de contrôle, et gardent leurs commandes (\\begin, \\text, \\\\)."""
    at = lancer()
    formules = [element.value for element in at.latex]
    assert len(formules) == 3
    # Streamlit entoure chaque formule de « $$ » et de retours à la ligne ; aucun autre caractère de contrôle
    assert all(ord(caractere) >= 32 or caractere == "\n" for formule in formules for caractere in formule), formules
    assert "\\begin{cases}" in formules[0] and "\\text{si }" in formules[0] and "\\\\" in formules[0]
    assert "\\text{pour le meilleur profil }" in formules[2]


# --- Vérification de l'interface (08/11) : téléphone, saisies incohérentes, domaine des modèles ---

def test_la_largeur_minimale_des_colonnes_ne_vaut_que_sur_un_grand_ecran():
    """Sur un téléphone, les colonnes s'empilent sur toute la largeur : leur largeur minimale ne s'applique qu'à partir de 640 px."""
    regle = '.st-key-calculateur [data-testid="stColumn"] { min-width: 24rem; }'
    assert regle in gui.STYLE
    assert gui.STYLE.index("@media (min-width: 640px)") < gui.STYLE.index(regle)


def test_un_tableau_large_defile_dans_son_cadre():
    """Un tableau Verso est dans un cadre qui défile en largeur : sur un écran étroit, il n'est pas coupé."""
    tableau = gui.tableHtml([("A", "a", "texte")], [{"a": "1"}])
    assert tableau.startswith("<div class='tableau'>") and ".tableau { overflow-x: auto; }" in gui.STYLE


@cacheDisponible
def test_un_code_trop_court_le_dit(monkeypatch):
    """« 12345 » n'est pas un nom : c'est un code-barres trop court, et le message le dit."""
    at = chercher(lancerHorsLigne(monkeypatch), "123 45")
    assert not at.exception
    assert "8 à 14 chiffres" in at.session_state["messageRecherche"] and "5" in at.session_state["messageRecherche"]


def test_des_ags_au_dela_des_lipides_sont_signales():
    """Matière grasse : 10 g d'acides gras saturés pour 5 g de lipides est impossible, et la saisie le signale."""
    at = lancer()
    at.selectbox(key="categorie").select("matieresGrasses").run()
    at.number_input(key="saisie_lipides").set_value(5.0)
    at.number_input(key="saisie_sa").set_value(10.0).run()
    assert not at.exception
    assert "lipides" in (at.session_state["avertissementSaisie"] or "")
    at.number_input(key="saisie_lipides").set_value(50.0).run()
    assert at.session_state["avertissementSaisie"] is None


def test_un_exemple_du_sujet_sort_du_domaine_de_mr_sort():
    """Les exemples du sujet sont des céréales, pas des plats préparés : les panneaux MR-Sort le disent."""
    at = lancer()
    choix = [option for option in at.selectbox(key="exemple").options if "figure 7" in option][0]
    at.selectbox(key="exemple").select(choix).run()
    assert not at.exception and at.session_state["horsDomaine"]


@baseConstruite
def test_le_premier_ecran_montre_la_poelee_fermiere():
    """Au premier affichage, la Poêlée Fermière, le plat de la démonstration : sa fiche, B, et un plat du domaine de MR-Sort."""
    at = lancer()
    assert at.session_state["platChoisi"]["code"] == "3257982125116"
    assert (at.session_state["nutriscore"]["score"], at.session_state["nutriscore"]["label"]) == (1, "B")
    assert not at.session_state["horsDomaine"]


def test_sans_la_base_le_premier_ecran_part_de_la_figure_6():
    """Sans la base, le premier plat est l'exemple de la fig. 6, choisi dans la liste (il est donc signalé hors du domaine)."""
    exemples = {libelle: plat for libelle, plat in gui.exemplesDisponibles().items() if libelle.startswith("Exemple du sujet")}
    depart = gui.platDeDepart(exemples)
    assert "figure 6" in depart and exemples[depart] == gui.EXEMPLES_SUJET["figure 6"]["produit"]


@baseConstruite
def test_avec_la_base_le_premier_plat_est_la_poelee_fermiere():
    """Avec la base, platDeDepart choisit la Poêlée Fermière."""
    exemples = gui.exemplesDisponibles()
    assert exemples[gui.platDeDepart(exemples)]["code"] == "3257982125116"


def blocDeLaRequete(requete):
    """Le texte d'un bloc @media du style, de son en-tête à son accolade fermante (en début de ligne)."""
    debut = gui.STYLE.index(f"@media {requete}")
    return gui.STYLE[debut:gui.STYLE.index("\n}", debut)]


def test_sur_un_telephone_une_longue_jauge_passe_a_la_ligne():
    """Sous 640 px, une jauge de plus de dix cases (sucres, sel) passe à la ligne toutes les dix cases."""
    assert ".jauge:has(> i:nth-child(11)) { flex-wrap: wrap;" in blocDeLaRequete("(max-width: 639px)")


def test_un_groupe_de_boutons_trop_large_passe_a_la_ligne_a_toutes_les_largeurs():
    """Un groupe de boutons plus large que sa colonne passe à la ligne au lieu de fuir à droite. La règle vaut partout."""
    regle = ".stButtonGroup div:has(> button) { flex-wrap: wrap;"
    assert regle in gui.STYLE
    for requete in ("(max-width: 639px)", "(min-width: 640px)"):
        assert regle not in blocDeLaRequete(requete)


# --- Ergonomie de l'interface (08/11) : revenir au produit, classes rappelées, vocabulaire, profils nommés ---

def boutonRevenirAuProduit(at):
    """Le bouton « Revenir aux valeurs du produit », ou None s'il n'est pas affiché."""
    boutons = [bouton for bouton in at.button if bouton.key == "revenirAuProduit"]
    return boutons[0] if boutons else None


@baseConstruite
def test_revenir_aux_valeurs_du_plat():
    """La Poêlée Fermière avec 1,4 g d'AGS (la démonstration) : le bouton rend 1,6 g, puis disparaît."""
    at = lancer()
    assert boutonRevenirAuProduit(at) is None
    at.number_input(key="saisie_sa").set_value(1.4).run()
    assert at.session_state["valeursModifiees"] and boutonRevenirAuProduit(at) is not None
    boutonRevenirAuProduit(at).click().run()
    assert not at.exception
    assert at.number_input(key="saisie_sa").value == 1.6
    assert not at.session_state["valeursModifiees"] and boutonRevenirAuProduit(at) is None


@cacheDisponible
def test_revenir_aux_valeurs_d_un_produit_cherche(monkeypatch):
    """Un produit cherché, ses sucres et son type changés à la main : le bouton rend ses valeurs, son type et l'accord avec OFF."""
    at = chercher(lancerHorsLigne(monkeypatch), POELEE)
    sucres = at.number_input(key="saisie_su").value
    at.number_input(key="saisie_su").set_value(9.0)
    at.selectbox(key="categorie").select("fromage").run()
    assert at.session_state["accordOff"] is None and boutonRevenirAuProduit(at) is not None
    boutonRevenirAuProduit(at).click().run()
    assert not at.exception
    assert at.number_input(key="saisie_su").value == sucres
    assert at.session_state["categorie"] == "general" and at.session_state["accordOff"]


@pytest.mark.skipif(not (projet_base.DOSSIER_BRUT / "produits" / f"{AMANDES}.json").exists(),
                    reason="les échantillons de vérification ne sont pas encore téléchargés")
def test_des_lipides_modifies_comptent_comme_une_modification(monkeypatch):
    """Des amandes, leurs lipides changés à la main : la fiche ne compare plus au résultat d'OFF, et le bouton de retour apparaît."""
    at = chercher(lancerHorsLigne(monkeypatch), AMANDES)
    assert at.session_state["accordOff"]
    at.number_input(key="saisie_lipides").set_value(40.0).run()
    assert not at.exception
    assert at.session_state["accordOff"] is None and boutonRevenirAuProduit(at) is not None


def test_la_ligne_de_l_editeur_donne_la_classe():
    """La ligne de titre d'un éditeur rappelle la classe du plat dans un petit cadre ; sans profils ordonnés, elle le dit."""
    ligne = gui.ligneDeLEditeur("MR-Sort à 7 critères", 0.6, "375 plats, tout appris", 3)
    assert "λ = 0,6, 375 plats, tout appris" in ligne and "classe-petite" in ligne and "<span class='lettre'>B′</span>" in ligne
    sansClasse = gui.ligneDeLEditeur("MR-Sort à 7 critères", 0.6, "375 plats, tout appris", None)
    assert "classe-petite" not in sansClasse and "pas de classe" in sansClasse


def blocsHtml(at, motif):
    """Les blocs st.html affichés qui contiennent un motif (AppTest les donne comme éléments inconnus)."""
    return [bloc.proto.body for bloc in at.get("html") if motif in bloc.proto.body]


@baseConstruite
def test_les_poids_possibles_ne_sont_annonces_qu_avec_leur_colonne():
    """
    Seuls les modèles aux poids appris ont des poids possibles (des intervalles). Pour les profils
    appris, aux poids fixés, le panneau des paramètres n'en parle pas, et l'éditeur n'a pas leur colonne.
    """
    at = lancer()
    at.segmented_control(key="apprentissage").set_value("profils").run()
    assert not blocsHtml(at, "Les poids possibles")
    at.segmented_control(key="apprentissage").set_value("poids").run()
    assert blocsHtml(at, "Les poids possibles")


@baseConstruite
def test_la_classe_est_rappelee_au_dessus_des_editeurs():
    """Au-dessus de chaque éditeur des paramètres, la classe du plat est celle de son panneau : MR-Sort, puis SuperNutri-score."""
    at = lancer()
    lignes = blocsHtml(at, "class='sous-titre-editeur'")              # et non le bloc du style, qui nomme la classe CSS
    assert len(lignes) == 3
    for ligne, nom in zip(lignes, ("sept", "trois")):
        assert f"<span class='lettre'>{gui.nomDeClasse(at.session_state[f'mrsort_{nom}']['classe'])}</span>" in ligne
    assert f"<span class='lettre'>{at.session_state['superNutri']['lettre']}</span>" in lignes[2]


@baseConstruite
def test_le_pas_a_pas_nomme_le_plat():
    """Le pas à pas nomme le plat du calculateur, et dit quand ses valeurs ont été modifiées."""
    at = lancer()
    assert at.session_state["pasAPas"]["plat"] == "Poêlée Fermière (Cora)"
    at.number_input(key="saisie_sa").set_value(1.4).run()
    assert at.session_state["pasAPas"]["plat"] == "Poêlée Fermière (Cora), valeurs modifiées"


def test_le_pas_a_pas_ne_dit_modifie_que_si_c_est_vrai():
    """Les paramètres ne sont dits « modifiés à la main » que s'ils s'écartent de ceux du modèle appris."""
    appris = {"criteres": ["en", "so"], "poids": {"en": 0.5, "so": 0.5}, "lam": 0.6,
              "profils": [{"en": 2000.0, "so": 2.0}, {"en": 1500.0, "so": 1.5}, {"en": 1000.0, "so": 1.0}, {"en": 500.0, "so": 0.5}]}
    assert gui.memesParametres(dict(appris), appris)
    assert not gui.memesParametres(dict(appris, poids={"en": 0.6, "so": 0.4}), appris)
    sousTitre = gui.sousTitreDuPasAPas("Poêlée Fermière (Cora)", "375 plats, poids appris", 0.6, False)
    assert sousTitre.startswith("Poêlée Fermière (Cora). Modèle « 375 plats, poids appris »") and "λ = 0,6" in sousTitre and "à la main" not in sousTitre
    assert "paramètres modifiés à la main" in gui.sousTitreDuPasAPas("Poêlée Fermière (Cora)", "375 plats, poids appris", 0.6, True)


def test_les_onglets_restent_en_haut_de_l_ecran():
    """La barre des onglets reste collée sous l'en-tête de Streamlit (3,75rem) : on change d'onglet sans remonter la page."""
    assert '.stTabs [role="tablist"] { position: sticky; top: 3.75rem;' in gui.STYLE


@pytest.mark.skipif(not projet_base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")
def test_les_modeles_portent_le_meme_nom_dans_les_deux_onglets():
    """
    Chaque choix d'« Apprentissage » s'écrit « base, apprentissage », avec l'un des noms du tableau
    de l'onglet Modèles ; ce tableau dit pourquoi le modèle sur 375 plats n'y est pas.
    """
    noms = {libelle.lower() for libelle in gui.LIBELLES_APPRENTISSAGES.values()}
    for base, apprentissage in gui.MODELES_APPRIS:
        nombre, nom = gui.libelleDuModele(base, apprentissage).split(", ")
        assert nombre == f"{base} plats" and nom in noms
    at = lancer()
    assert at.segmented_control(key="apprisSur").label == "Appris sur"
    assert at.segmented_control(key="apprentissage").label == "Apprentissage"
    assert blocsHtml(at, "ont appris les plats ajoutés")


def modeleDEssai():
    """Un petit modèle valide : énergie et sel à minimiser, fruits à maximiser, profils de b2 (le moins bon) à b5."""
    return {"criteres": ["en", "so", "fr"], "poids": {"en": 0.4, "so": 0.3, "fr": 0.3}, "lam": 0.6,
            "profils": [{"en": 2000.0, "so": 2.0, "fr": 0.0}, {"en": 1500.0, "so": 1.5, "fr": 10.0},
                        {"en": 1000.0, "so": 1.0, "fr": 30.0}, {"en": 500.0, "so": 0.5, "fr": 50.0}]}


def test_la_phrase_nomme_le_seuil_de_la_classe():
    """La raison d'une classe nomme le profil franchi par la classe qu'il ouvre (b3, le seuil de C′), puis le suivant."""
    detail = {"classe": 2, "concordances": [1.0, 0.919, 0.479, 0.3], "franchis": [True, True, False, False]}
    assert gui.phraseDeFranchissement(detail, 0.6) == ("Franchit le seuil de C′ (b3, concordance 0,919 ≥ λ = 0,6), "
                                                      "pas celui de B′ (b4, 0,479 < 0,6).")
    detail = {"classe": 4, "concordances": [1.0, 1.0, 0.9, 0.705], "franchis": [True] * 4}
    assert gui.phraseDeFranchissement(detail, 0.6) == "Franchit le seuil de A′ (b5, concordance 0,705 ≥ λ = 0,6)."
    detail = {"classe": 0, "concordances": [0.412, 0.3, 0.2, 0.1], "franchis": [False] * 4}
    assert gui.phraseDeFranchissement(detail, 0.6) == "Ne franchit pas le seuil de D′ (b2, 0,412 < 0,6)."


def test_les_profils_portent_leur_classe():
    """Chaque profil porte la classe qu'il ouvre, de b2 (D′) à b5 (A′) : dans l'éditeur, aller et retour, et dans les barres."""
    modele = modeleDEssai()
    tableau = gui.tableauDesParametres(modele)
    assert list(tableau.columns)[-4:] == ["b2 (D′)", "b3 (C′)", "b4 (B′)", "b5 (A′)"]
    relu, messages, valide = gui.modeleDuTableau(tableau, modele)
    assert valide and relu["profils"] == modele["profils"]
    tableau.loc[0, "b5 (A′)"] = 3000.0                       # l'énergie de b5 devient pire que celle de b4
    relu, messages, valide = gui.modeleDuTableau(tableau, modele)
    assert not valide and any("b5 (A′) doit être au moins aussi bon que b4 (B′)" in message for message in messages)
    plat = {"en": 800.0, "so": 0.8, "fr": 40.0}
    barres = gui.barresDeConcordanceHtml(gui.affecter(plat, modele), modele, plat)
    assert "<span class='profil'>b5 (A′)</span>" in barres and "b2, le seuil de D′ :" in barres


@baseConstruite
def test_le_pas_a_pas_nomme_les_seuils():
    """Le pas à pas dit quelle classe ouvre chaque profil, et ses tableaux nomment les profils de la même façon."""
    at = lancer()
    assert blocsHtml(at, "<span class='insecable'>b2 (D′)</span>, <span class='insecable'>b3 (C′)</span>")   # sans coupure
    assert blocsHtml(at, "<th class='nombre'>b5 (A′)</th>")
    assert ".insecable { white-space: nowrap; }" in gui.STYLE


def test_sur_un_telephone_chaque_choix_d_apprentissage_a_sa_ligne():
    """Sous 640 px, les trois choix d'« Apprentissage » ne tiennent pas sur une ligne : chacun prend toute la largeur."""
    assert ".st-key-apprentissage div:has(> button) > button { flex-basis: 100%; }" in blocDeLaRequete("(max-width: 639px)")
    assert ".st-key-apprisSur" not in gui.STYLE                      # les deux choix d'« Appris sur » tiennent sur une ligne


# --- Le domaine des modèles (09/11) : une classe indicative, et la raison précise ---

def test_la_raison_hors_domaine_depend_du_produit():
    """Une raison par cas (eau, boisson, règle à part, produit non préparé, exemple du sujet), aucune pour un plat préparé."""
    assert "pas de classe" in gui.raisonHorsDomaine("eau")
    assert "yaourts à boire" in gui.raisonHorsDomaine("boisson")
    assert "fromages" in gui.raisonHorsDomaine("fromage")
    assert "pas un plat préparé" in gui.raisonHorsDomaine("general", {"platPrepare": False})
    assert "céréales" in gui.raisonHorsDomaine("general", None, exempleDuSujet=True)
    assert gui.raisonHorsDomaine("general", {"platPrepare": True}) is None and gui.raisonHorsDomaine("general") is None


@baseConstruite
def test_une_boisson_a_une_classe_indicative():
    """Le type « Boisson », celui du Yop : l'encadré hors domaine, la classe en pointillés, « à titre indicatif », sans comparaison."""
    at = lancer()
    at.selectbox(key="categorie").select("boisson").run()
    assert not at.exception
    assert blocsHtml(at, "class='hors-domaine'") and "yaourts à boire" in at.session_state["raisonHorsDomaine"]
    verdicts = blocsHtml(at, "class='verdict-modele'")             # MR-Sort, le SuperNutri-score, et l'étape 4 du pas à pas
    assert len(verdicts) == 4
    assert all("titre indicatif" in verdict and "classe-modele indicatif" in verdict for verdict in verdicts)
    assert not any("Nutri-Score dit" in verdict or "classe du Nutri-Score" in verdict for verdict in verdicts)


@baseConstruite
def test_une_eau_n_a_pas_de_classe_mrsort():
    """Une eau : aucune classe MR-Sort, ni dans les panneaux ni au-dessus des éditeurs, et une phrase le dit."""
    at = lancer()
    at.selectbox(key="categorie").select("eau").run()
    assert not at.exception
    assert not blocsHtml(at, "class='verdict-modele'") and blocsHtml(at, "Pas de classe MR-Sort pour une eau")
    assert all("classe-petite" not in ligne for ligne in blocsHtml(at, "class='sous-titre-editeur'"))


@baseConstruite
def test_un_plat_prepare_n_a_rien_d_indicatif():
    """La Poêlée Fermière, un plat préparé du cas général : ni encadré hors domaine, ni classe en pointillés."""
    at = lancer()
    assert at.session_state["raisonHorsDomaine"] is None
    assert not blocsHtml(at, "class='hors-domaine'") and not blocsHtml(at, "classe-modele indicatif")


def test_le_pas_a_pas_dit_quand_la_classe_est_indicative():
    """Hors du domaine des modèles, le sous-titre du pas à pas le dit ; pour un plat préparé, non."""
    assert "classe indicative" in gui.sousTitreDuPasAPas("Yop (Yoplait)", "375 plats, poids appris", 0.6, False, horsDomaine=True)
    assert "indicative" not in gui.sousTitreDuPasAPas("Poêlée Fermière (Cora)", "375 plats, poids appris", 0.6, False)


# --- Les trois apprentissages sur les 375 plats (09/11) : deux choix, et la validation croisée ---

@pytest.mark.skipif(not projet_base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")
def test_l_apprentissage_par_defaut_est_le_meilleur_en_validation_croisee():
    """
    Au premier affichage : 375 plats, avec l'apprentissage qui range le mieux des plats jamais
    vus (validation croisée, 7 critères, λ = 0,6), parmi ceux qui sont calculés ; sans elle, les poids.
    """
    lignes = [ligne for ligne in gui.resultatsDuProjet().get("validationCroisee", {}).get("modeles", [])
              if ligne["nom"] == "sept" and ligne["lam"] == 0.6 and ("375", ligne["mode"]) in gui.modelesDisponibles()]
    attendu = max(lignes, key=lambda ligne: ligne["exactitudeMoyenne"])["mode"] if lignes else "poids"
    assert gui.apprentissageParDefaut() == attendu
    at = lancer()
    assert (at.session_state["apprisSur"], at.session_state["apprentissage"]) == ("375", attendu)


def test_le_tableau_de_la_validation_croisee_met_en_gras_le_meilleur():
    """Le tableau de la validation croisée : l'exactitude moyenne en pourcentage, l'écart entre les parts en points, le meilleur en gras."""
    def ligne(mode, moyenne, aUneClassePres):
        return {"nom": "sept", "mode": mode, "lam": 0.6, "exactitudeMoyenne": moyenne, "ecartType": 0.031,
                "comparaison": {"aUneClassePres": aUneClassePres}}

    lignes = gui.lignesDeLaValidationCroisee([ligne("poids", 0.62, 0.95), ligne("complet", 0.71, 0.93)])
    assert lignes[1]["moyenne"] == "<strong>71,0 %</strong>" and lignes[0]["classe"] == "<strong>95,0 %</strong>"
    assert lignes[0]["ecart"] == "3,1 points" and "<strong>" not in lignes[0]["moyenne"] + lignes[1]["classe"]


def test_les_champs_des_fruits_et_des_fibres_ont_une_aide():
    """Les fruits et légumes se lisent dans la liste des ingrédients, et les fibres manquent souvent : leur champ le dit."""
    at = lancer()
    assert "liste des ingrédients" in at.number_input(key="saisie_fr").help
    assert "comptent 0" in at.number_input(key="saisie_fi").help


@cacheDisponible
def test_partir_d_un_plat_vide_la_recherche(monkeypatch):
    """Après une recherche par nom et un choix, partir d'un plat de la liste vide le champ et les produits trouvés."""
    at = chercher(lancerHorsLigne(monkeypatch), "poêlée fermière")
    choix = [option for option in at.selectbox(key="choixRecherche").options if "Poêlée Fermière" in option][0]
    at.selectbox(key="choixRecherche").select(choix).run()
    choix = [option for option in at.selectbox(key="exemple").options if "figure 7" in option][0]
    at.selectbox(key="exemple").select(choix).run()
    assert not at.exception
    assert at.text_input(key="recherche").value == ""
    assert not [liste for liste in at.selectbox if liste.key == "choixRecherche"]


def test_le_tableau_des_modeles_met_en_gras_les_meilleurs():
    """Dans le tableau des modèles, le meilleur résultat de chaque colonne est en gras, et lui seul."""
    def ligne(nom, mode, base, ajout, aUneClassePres):
        return {"nom": nom, "mode": mode, "lam": 0.6, "base": {"bienRanges": base, "total": 125},
                "ajout": {"bienRanges": ajout, "total": 250, "exactitude": ajout / 250, "aUneClassePres": aUneClassePres}}
    lignes = gui.lignesDuTableauDesModeles([ligne("sept", "poids", 90, 137, 0.904), ligne("sept", "complet", 122, 173, 0.94),
                                            ligne("trois", "profils", 92, 134, 0.984)])
    assert lignes[1]["base"] == "<strong>122/125</strong>" and lignes[1]["ajout"] == "<strong>173/250</strong>"
    assert lignes[1]["pourcentage"].startswith("<strong>69,2") and lignes[2]["classe"].startswith("<strong>98,4")
    assert "<strong>" not in lignes[0]["base"] + lignes[0]["pourcentage"] + lignes[1]["classe"]


@baseConstruite
def test_la_note_des_barres_n_apparait_qu_une_fois():
    """La note qui explique les barres de concordance n'est écrite qu'une fois, sous le premier modèle."""
    at = lancer()
    assert len(blocsHtml(at, "Une case par critère")) == 1


def test_les_nombres_des_editeurs_suivent_la_langue_du_navigateur():
    """Poids et profils des éditeurs s'écrivent au format du navigateur (virgule en français), comme le reste de l'interface."""
    configuration = gui.configurationDeLEditeur()
    for colonne in ["Poids"] + [gui.nomDuProfil(numero) for numero in range(len(gui.PROFILS))]:
        assert configuration[colonne]["type_config"]["format"] == "localized", colonne


# --- λ au curseur (20/11) ---

def curseurLambda(at, rang=0):
    """Le curseur de λ du rang-ième éditeur des paramètres (0 : MR-Sort à 7 critères, 1 : à 3 critères)."""
    return [curseur for curseur in at.select_slider if curseur.label == "Seuil majoritaire λ"][rang]


def lancerAvecLesProfilsAppris():
    """L'interface avec les profils appris sur 375 plats, λ = 0,6 : la Poêlée Fermière y est B′ à 7 critères."""
    at = AppTest.from_file("../projet_gui.py", default_timeout=20)
    at.session_state["apprisSur"] = "375"
    at.session_state["apprentissage"] = "profils"
    return at.run()


def test_lambda_s_ecrit_sans_zero_inutile():
    assert (gui.nombreLambda(0.6), gui.nombreLambda(0.65), gui.nombreLambda(1.0)) == ("0,6", "0,65", "1")


@baseConstruite
def test_l_en_tete_choisit_le_modele_appris():
    """Le choix 0,6 / 0,7 de l'en-tête choisit le modèle appris ; λ lui-même se règle au curseur, dans les paramètres."""
    at = lancer()
    assert at.segmented_control(key="lam_sept").label == "Appris pour λ"
    assert curseurLambda(at).value == 0.6


@pytest.mark.skipif(not projet_base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")
def test_lambda_se_regle_au_curseur():
    """Mêmes poids et mêmes profils, λ = 0,70 : la concordance face à B′ (0,694) ne suffit plus, la Poêlée passe en C′."""
    at = lancerAvecLesProfilsAppris()
    assert gui.nomDeClasse(at.session_state["mrsort_sept"]["classe"]) == "B′"
    curseurLambda(at).set_value(0.7).run()
    assert at.session_state["mrsort_sept"]["lam"] == 0.7
    assert gui.nomDeClasse(at.session_state["mrsort_sept"]["classe"]) == "C′"


@pytest.mark.skipif(not projet_base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")
def test_revenir_aux_parametres_appris_remet_lambda():
    at = lancerAvecLesProfilsAppris()
    curseurLambda(at).set_value(0.7).run()
    at.button(key="revenir_sept").click().run()
    assert curseurLambda(at).value == 0.6
    assert at.session_state["mrsort_sept"]["lam"] == 0.6


@pytest.mark.skipif(not projet_base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")
def test_le_pas_a_pas_suit_lambda_du_curseur():
    """Le pas à pas reprend le λ du curseur, et dit que les paramètres sont modifiés à la main."""
    at = lancerAvecLesProfilsAppris()
    curseurLambda(at).set_value(0.7).run()
    assert blocsHtml(at, "λ = 0,7, paramètres modifiés à la main")


# --- Le SuperNutri-score au calculateur (§3.5) ---

@baseConstruite
def test_les_champs_du_super_nutri_score_suivent_le_plat():
    """La Poêlée Fermière : NOVA 4, 3 additifs (E14XX, E412, E415), aucun à risque, pas bio."""
    at = lancer()
    valeurs = [at.session_state[f"saisie_{cle}"] for cle in ("nova", "additifs", "aRisque", "bio")]
    assert valeurs == [4, 3, 0, False]


@baseConstruite
def test_le_super_nutri_score_range_le_plat_du_calculateur():
    """B au Nutri-Score, C′ au SuperNutri-score : face à B′, elle rate les protéines, les fibres, NOVA, les additifs et le bio."""
    at = lancer()
    assert not at.exception
    assert at.session_state["superNutri"]["lettre"] == "C′"
    assert blocsHtml(at, "Classe C′</strong> : plats moyens ; le Nutri-Score dit B")


@baseConstruite
def test_moins_transformee_la_poelee_passerait_en_b_prime():
    """Transformée (NOVA 3) plutôt qu'ultra-transformée, avec un seul additif : face à B′, elle ne rate plus que 0,26."""
    at = lancer()
    at.session_state["saisie_nova"] = 3
    at.session_state["saisie_additifs"] = 1
    at.run()
    assert at.session_state["superNutri"]["lettre"] == "B′"
    assert at.session_state["valeursModifiees"]


@baseConstruite
def test_lambda_du_super_nutri_score_se_regle_aussi():
    """Le troisième curseur règle λ du SuperNutri-score : à 0,9, la Poêlée ne franchit plus rien (0,876 face à D′), E′."""
    at = lancer()
    assert curseurLambda(at, 2).value == 0.7
    curseurLambda(at, 2).set_value(0.9).run()
    assert at.session_state["superNutri"]["lettre"] == "E′"


@baseConstruite
def test_une_eau_n_a_pas_de_super_nutri_score():
    at = AppTest.from_file("../projet_gui.py", default_timeout=20)
    at.session_state["categorie"] = "eau"
    at.run()
    assert blocsHtml(at, "Pas de classe SuperNutri-score pour une eau")
