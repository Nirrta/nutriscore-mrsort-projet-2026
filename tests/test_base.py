"""Tests de la constitution de la base (question 3.1)."""

import copy

import pytest

import projet_base as base
import projet_design as design
import projet_nutriscore as ns


def reponseOff():
    """Fabrique une réponse de l'API produit d'OFF pour un plat préparé ordinaire, retenu par tous les filtres."""
    composantes = {
        "negative": [{"id": "energy", "value": 502}, {"id": "sugars", "value": 2},
                     {"id": "saturated_fat", "value": 1.5}, {"id": "salt", "value": 0.9}],
        "positive": [{"id": "proteins", "value": 6}, {"id": "fiber", "value": 2.5},
                     {"id": "fruits_vegetables_legumes", "value": 45}],
    }
    fiche = {
        "code": "1234567890123",
        "product_name_fr": "Plat de test",
        "brands": "Marque, Autre marque",
        "quantity": "300 g",
        "categories_tags": ["en:meals"],
        "countries_tags": ["en:france"],
        "labels_tags": [],
        "nova_group": 4,
        "additives_n": 2,
        "additives_tags": ["en:e330", "en:e415"],
        "environmental_score_score": 60,
        "environmental_score_grade": "b",
        "last_modified_t": 1760000000,
        "nutriments": {"fiber_100g": 2.5, "proteins_100g": 6, "fat_100g": 5, "carbohydrates_100g": 12,
                       "energy-kcal_100g": 120},
        "nutriscore": {"2023": {"nutriscore_computed": 1, "grade": "b", "score": 1, "data": {
            "is_beverage": 0, "is_water": 0, "is_cheese": 0, "is_fat_oil_nuts_seeds": 0,
            "is_red_meat_product": 0, "components": composantes}}},
    }
    return {"status": 1, "code": fiche["code"], "product": fiche}


def platFictif(code, label, nom=None, marque="M"):
    """Fabrique une ligne de base minimale."""
    return {"code": code, "nom": nom or f"plat {code}", "marque": marque, "label": label, "score": 0,
            "en": 500, "sa": 1, "su": 2, "so": 0.5, "pr": 5, "fi": 2, "fr": 10}


# --- Lecture d'une fiche et filtres ---

def test_un_plat_ordinaire_est_retenu():
    """Un plat complet, du cas général, passe tous les filtres ; sa ligne reprend les valeurs d'OFF."""
    produit, echec = base.extraireProduit(reponseOff())
    assert echec is None
    assert (produit["en"], produit["sa"], produit["su"], produit["so"]) == (502, 1.5, 2, 0.9)
    assert (produit["pr"], produit["fi"], produit["fr"]) == (6, 2.5, 45)
    assert (produit["score"], produit["label"]) == (1, "B")
    assert produit["sodium"] == pytest.approx(360)          # 0,9 g de sel = 360 mg de sodium
    assert produit["marque"] == "Marque"
    assert produit["listeAdditifs"] == "E330, E415"
    assert (produit["nova"], produit["additifs"], produit["labelGreen"], produit["bio"]) == (4, 2, "B", "non")


@pytest.mark.parametrize("modification, etape", [
    (lambda r: r.update(status=0), "fiche disponible"),
    (lambda r: r["product"].update(categories_tags=["en:soups"]), "plat préparé vendu en France"),
    (lambda r: r["product"]["nutriscore"]["2023"].update(nutriscore_computed=0), "Nutri-Score 2023 calculé"),
    (lambda r: r["product"]["nutriscore"]["2023"]["data"].update(is_red_meat_product=1), "cas général du Nutri-Score"),
    (lambda r: r["product"]["nutriscore"]["2023"]["data"].update(is_cheese=1), "cas général du Nutri-Score"),
    (lambda r: r["product"]["nutriments"].pop("fiber_100g"), "sept composantes connues"),
    (lambda r: r["product"].update(nova_group=None), "NOVA et additifs connus"),
    (lambda r: r["product"]["nutriscore"]["2023"]["data"]["components"]["negative"][3].update(value=12),
     "valeurs plausibles"),
])
def test_chaque_filtre_ecarte_le_plat_a_la_bonne_etape(modification, etape):
    """Chaque défaut écarte le plat à l'étape correspondante de l'entonnoir."""
    reponse = reponseOff()
    modification(reponse)
    assert base.extraireProduit(reponse) == (None, etape)


def test_les_proteines_viennent_du_tableau_quand_off_ne_les_compte_pas():
    """À partir de 11 points négatifs, OFF retire les protéines de son calcul : on les lit dans le tableau."""
    reponse = reponseOff()
    positives = reponse["product"]["nutriscore"]["2023"]["data"]["components"]["positive"]
    positives.pop(0)
    reponse["product"]["nutriments"]["proteins_100g"] = 7.5
    produit, echec = base.extraireProduit(reponse)
    assert echec is None and produit["pr"] == 7.5


def test_la_valeur_exacte_remplace_la_valeur_arrondie():
    """
    Cas de la « Soupe pdt/courgette » : OFF affiche 0,4 g de sel mais compte 2 points, car la
    valeur exacte est 0,4043 g. On reprend la valeur exacte ; une valeur trop différente ne
    remplace pas celle du calcul.
    """
    reponse = reponseOff()
    reponse["product"]["nutriscore"]["2023"]["data"]["components"]["negative"][3]["value"] = 0.4
    reponse["product"]["nutriments"]["salt_100g"] = 0.4043
    reponse["product"]["nutriments"]["sugars_100g"] = 9.0          # trop loin des 2 g du calcul : ignoré
    valeurs = base.valeursDuCalculOff(reponse["product"])
    assert valeurs["so"] == 0.4043 and valeurs["su"] == 2


def test_valeurs_plausibles():
    """Les contrôles écartent un sel de 12 g, des graisses saturées supérieures aux graisses, une somme de 110 g."""
    plat = {"en": 500, "sa": 1, "su": 2, "so": 0.5, "pr": 5, "fi": 2, "fr": 10}
    assert base.valeursPlausibles(plat, graisses=5, glucides=10)
    assert not base.valeursPlausibles(dict(plat, so=12), None, None)
    assert not base.valeursPlausibles(dict(plat, sa=6), graisses=5, glucides=10)
    assert not base.valeursPlausibles(plat, graisses=50, glucides=60)


def test_sans_doublon_garde_le_plus_petit_code():
    """Deux fiches au même nom et à la même marque n'en font qu'une : la plus petite par code-barres."""
    plats = [platFictif("3", "A", nom="Taboulé", marque="Ma"), platFictif("1", "A", nom="taboulé", marque="MA"),
             platFictif("2", "B", nom="Couscous")]
    assert [p["code"] for p in base.sansDoublon(plats)] == ["1", "2"]


# --- Tirage ---

def vivierFictif(parClasse=30):
    """Un vivier de parClasse plats par classe."""
    return [platFictif(f"{classe}{numero:03d}", classe) for classe in "ABCDE" for numero in range(parClasse)]


def test_le_tirage_est_reproductible():
    """La même graine redonne le même échantillon, 25 plats par classe ; une autre graine en donne un autre."""
    premier = base.tirerEchantillon(vivierFictif(), 25, graine=2026)
    second = base.tirerEchantillon(list(reversed(vivierFictif())), 25, graine=2026)
    assert [p["code"] for p in premier] == [p["code"] for p in second]
    assert base.vivierParClasse(premier) == {classe: 25 for classe in "ABCDE"}
    autre = base.tirerEchantillon(vivierFictif(), 25, graine=1)
    assert [p["code"] for p in autre] != [p["code"] for p in premier]


def test_le_tirage_refuse_une_classe_trop_petite():
    """Avec 10 plats E seulement, on ne peut pas en tirer 25."""
    vivier = [p for p in vivierFictif() if p["label"] != "E"] + [platFictif(f"E{n}", "E") for n in range(10)]
    with pytest.raises(ValueError):
        base.tirerEchantillon(vivier, 25)


# --- Contrôles du sujet ---

def test_verifier_base_sur_une_base_trop_petite():
    """50 plats, 10 par classe : les conditions de taille ne sont pas remplies."""
    conditions = {libelle: respectee for libelle, respectee, detail in base.verifierBase(vivierFictif(10))}
    assert not conditions["au moins 100 aliments"]
    assert not conditions["au moins 20 aliments de label A"]
    assert conditions["pas de code-barres en double"]


def test_intersection_rapportee_a_la_plus_petite_base():
    """5 plats communs entre une base de 20 et une base de 40 : 25 % de la plus petite."""
    baseA = [platFictif(str(n), "A") for n in range(20)]
    baseB = [platFictif(str(n), "A") for n in range(15, 55)]
    assert base.intersectionAvecAutreBase(baseA, baseB) == (5, 25.0)


def test_lettres_et_couleurs_des_classes():
    """Les classes de nos modèles (A′) prennent la couleur de la classe officielle correspondante."""
    assert design.lettreDeClasse("A′") == "A" and design.lettreDeClasse("e") == "E"
    assert design.couleurClasse("C′") == design.COULEURS_CLASSES["C"]
    assert design.couleurLettre("A") == "#FFFFFF" and design.couleurLettre("C") == "#000000"


# --- La base livrée ---

baseConstruite = pytest.mark.skipif(not base.FICHIER_BASE.exists(), reason="la base n'est pas encore construite")


@baseConstruite
def test_la_base_livree_respecte_le_sujet():
    """La base livrée remplit toutes les conditions du sujet (§3.1)."""
    for libelle, respectee, detail in base.verifierBase(base.FICHIER_BASE):
        assert respectee, f"{libelle} : {detail}"


@baseConstruite
def test_la_base_a_toutes_ses_colonnes():
    """Chaque plat a les colonnes de COLONNES, et 25 plats par classe."""
    plats = base.lireBase()
    assert len(plats) == 125
    assert set(plats[0]) == {cle for cle, entete in base.COLONNES}
    assert base.vivierParClasse(plats) == {classe: 25 for classe in "ABCDE"}


@baseConstruite
def test_la_base_se_reconstruit_depuis_le_cache():
    """Sans réseau, depuis donnees/brut/, on retrouve exactement les mêmes plats."""
    reconstruite, entonnoir, infos = base.construireBase(depuisCache=True, afficher=False)
    assert [p["code"] for p in reconstruite] == [p["code"] for p in base.lireBase()]


# --- Un produit d'Open Food Facts à la demande (code-barres, lien ou nom, pour l'interface) ---

POELEE, LASAGNES, SANS_FIBRES = "3257982125116", "20163723", "0077544332409"
cacheDisponible = pytest.mark.skipif(not (base.DOSSIER_BRUT / "produits" / f"{POELEE}.json").exists(),
                                     reason="le cache d'Open Food Facts n'est pas là")


@pytest.mark.parametrize("texte, code", [
    ("3257982125116", "3257982125116"),
    (" 3257 9821 25116 ", "3257982125116"),
    ("https://fr.openfoodfacts.org/produit/3257982125116/poelee-fermiere-cora", "3257982125116"),
    ("https://world.openfoodfacts.org/product/3257982125116", "3257982125116"),
    ("es.openfoodfacts.org/producto/20163723/lasagnes", "20163723"),
    ("poêlée fermière", None),
    ("123", None),
    ("https://fr.openfoodfacts.org/", None),
])
def test_code_depuis_saisie(texte, code):
    """Un code de 8 à 14 chiffres, espaces permis, ou un lien vers une fiche d'OFF ; sinon, rien."""
    assert base.codeDepuisSaisie(texte) == code


@cacheDisponible
def test_la_recherche_par_nom_trouve_dans_le_cache_sans_reseau():
    """Sans réseau, la recherche lit les fiches du cache, sans tenir compte des accents ni des majuscules."""
    resultats, erreur = base.rechercherParNom("poelee FERMIERE", reseau=False)
    assert erreur is None and POELEE in [resultat["code"] for resultat in resultats]
    assert all(resultat["source"] == "cache" for resultat in resultats)
    assert base.rechercherParNom("zzz introuvable", reseau=False) == ([], None)


@cacheDisponible
def test_la_recherche_par_nom_ignore_la_ponctuation_et_le_pluriel():
    """Les guillemets et les deux-points ne gênent pas, et « lasagnes » trouve aussi « Lasagne »."""
    assert POELEE in [r["code"] for r in base.rechercherParNom('poêlée "fermière": cora', reseau=False)[0]]
    assert base.motsDeLaRecherche("Lasagnes, BOLOGNAISE !") == ["lasagne", "bolognaise"]
    assert base.correspond(["lasagne", "bolognaise"], "Lasagne bolognaise gratinée")
    assert not base.correspond(["poelee", "cora"], "Pain Cora")


@cacheDisponible
def test_une_fiche_absente_du_cache_hors_ligne_donne_un_message(monkeypatch):
    """Hors ligne (PROJET_HORS_LIGNE=1), un code absent du cache donne un message, sans appel au réseau."""
    monkeypatch.setenv("PROJET_HORS_LIGNE", "1")
    reponse, erreur = base.ficheEnDirect("0000000000000")
    assert reponse is None and "hors ligne" in erreur
    reponse, erreur = base.ficheEnDirect(POELEE)
    assert erreur is None and reponse["product"]["code"] == POELEE


def test_open_food_facts_injoignable_donne_un_message(monkeypatch):
    """Un serveur qui ne répond pas donne un message clair, et non une exception."""
    monkeypatch.setattr(base, "URL_PRODUIT", "http://127.0.0.1:9/api/v2/product/{code}")
    reponse, erreur = base.ficheEnDirect("0000000000000", reseau=True)
    assert reponse is None and "injoignable" in erreur


@cacheDisponible
def test_produit_depuis_la_fiche_de_la_poelee_fermiere():
    """La Poêlée Fermière : cas général, plat préparé, rien ne manque, et les valeurs de la base."""
    produit = base.produitDepuisFiche(base.ficheEnDirect(POELEE, reseau=False)[0])
    assert produit["categorie"] == "general" and produit["platPrepare"] and produit["manquantes"] == []
    assert produit["nutriscoreOff"] == {"score": 1, "label": "B"}
    plat = [p for p in base.lireBase() if p["code"] == POELEE][0]
    assert all(produit[cle] == plat[cle] for cle in ("en", "sa", "su", "so", "pr", "fi", "fr"))


@cacheDisponible
def test_produit_depuis_la_fiche_de_lasagnes_marquees_viande_rouge():
    """
    OFF marque ces lasagnes « viande rouge », alors que la FAQ exclut les plats composés : on
    propose son type, avec la raison, et notre calcul de ce type retrouve celui d'OFF.
    """
    produit = base.produitDepuisFiche(base.ficheEnDirect(LASAGNES, reseau=False)[0])
    assert produit["categorie"] == "viandeRouge" and produit["platPrepare"]
    assert "viande rouge" in produit["raisonCategorie"]
    calcul = ns.scoreNutriscore(produit, categorie=produit["categorie"])
    assert {"score": calcul["score"], "label": calcul["label"]} == produit["nutriscoreOff"]


@cacheDisponible
def test_une_valeur_manquante_vaut_0_et_c_est_dit():
    """Fibres non déclarées : elles valent 0, comme chez OFF, et la fiche le signale."""
    produit = base.produitDepuisFiche(base.ficheEnDirect(SANS_FIBRES, reseau=False)[0])
    assert produit["manquantes"] == ["fi"] and produit["fi"] == 0
    calcul = ns.scoreNutriscore(produit, categorie=produit["categorie"])
    assert {"score": calcul["score"], "label": calcul["label"]} == produit["nutriscoreOff"]


AMANDES, CERNEAUX = "0634113230049", "3257980532602"


@pytest.mark.skipif(not (base.DOSSIER_BRUT / "produits" / f"{CERNEAUX}.json").exists(),
                    reason="les échantillons de vérification ne sont pas encore téléchargés")
def test_les_valeurs_estimees_par_off_sont_reprises_et_signalees():
    """
    Amandes : OFF compte 9,9 g de fibres qu'il a estimées (absentes du tableau nutritionnel) ;
    cerneaux de noix : sans tableau nutritionnel, les AGS et les lipides se déduisent de
    l'énergie des AGS et du ratio AGS / lipides du calcul d'OFF. Notre calcul retrouve alors OFF.
    """
    amandes = base.produitDepuisFiche(base.ficheEnDirect(AMANDES, reseau=False)[0])
    assert amandes["fi"] == 9.9 and amandes["estimees"] == ["fi"] and amandes["manquantes"] == []
    cerneaux = base.produitDepuisFiche(base.ficheEnDirect(CERNEAUX, reseau=False)[0])
    assert cerneaux["sa"] == pytest.approx(238.65 / 37) and cerneaux["lipides"] == pytest.approx(100 * 238.65 / 37 / 9.6)
    for produit in (amandes, cerneaux):
        calcul = ns.scoreNutriscore(produit, categorie=produit["categorie"])
        assert {"score": calcul["score"], "label": calcul["label"]} == produit["nutriscoreOff"]


# --- La base étendue : la base, plus 50 plats par classe tirés hors de la base ---

etendueConstruite = pytest.mark.skipif(not base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")


@etendueConstruite
def test_la_base_etendue_contient_la_base_et_75_plats_par_classe():
    """375 plats, 75 par classe : les 125 de la base, inchangés (lot « base du 30/10 »), et 250 autres."""
    etendue = base.lireBase(base.FICHIER_BASE_ETENDUE)
    assert len(etendue) == 375 and base.vivierParClasse(etendue) == {classe: 75 for classe in "ABCDE"}
    lot = [p for p in etendue if p["lot"] == base.LOT_BASE]
    ajout = [p for p in etendue if p["lot"] == base.LOT_AJOUT]
    assert [p["code"] for p in lot] == [p["code"] for p in base.lireBase()] and len(ajout) == 250
    assert len({p["code"] for p in etendue}) == 375
    assert base.horsDeLaBase(ajout, lot) == ajout                     # ni le même code, ni le même nom et la même marque
    assert all(respectee for libelle, respectee, detail in base.verifierBase(etendue))


@etendueConstruite
def test_la_base_etendue_se_reconstruit_depuis_le_cache():
    """Sans réseau, depuis donnees/brut/, on retrouve exactement les mêmes 375 plats, et la base du 30/10."""
    reconstruite, entonnoir, infos = base.construireBaseEtendue(depuisCache=True, afficher=False)
    assert [p["code"] for p in reconstruite] == [p["code"] for p in base.lireBase(base.FICHIER_BASE_ETENDUE)]
    assert infos["vivierHorsBase"] == base.vivierParClasse(base.horsDeLaBase(infos["vivier"], base.lireBase()))


def test_sans_calcul_d_off_les_valeurs_viennent_du_tableau_nutritionnel():
    """Un produit dont OFF ne calcule pas le Nutri-Score : ses valeurs viennent du tableau nutritionnel."""
    reponse = reponseOff()
    fiche = reponse["product"]
    del fiche["nutriscore"]
    fiche["nutriments"].update({"energy-kj_100g": 502, "saturated-fat_100g": 1.5, "sugars_100g": 2, "salt_100g": 0.9,
                                "fruits-vegetables-legumes-estimate-from-ingredients_100g": 45})
    produit = base.produitDepuisFiche(reponse)
    assert produit["manquantes"] == [] and produit["nutriscoreOff"] is None and produit["categorie"] == "general"
    assert (produit["su"], produit["so"], produit["fr"]) == (2, 0.9, 45)


def test_hors_de_la_base_accepte_une_marque_vide():
    """Une marque vide relue dans l'Excel vaut None : le plat reste comparable, par son code et son nom."""
    lot = [platFictif("1", "A", nom="Plat", marque=None)]
    ajout = [platFictif("2", "A", nom="Plat", marque=None), platFictif("3", "A", nom="Autre", marque=None)]
    assert base.horsDeLaBase(ajout, lot) == [ajout[1]]
