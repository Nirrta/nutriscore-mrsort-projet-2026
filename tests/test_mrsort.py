"""Tests du modèle MR-Sort (question 3.3)."""

import projet_mrsort as mr


def modeleAnnexe(poids, profils, lam):
    """Un modèle à trois critères g1, g2, g3, tous à maximiser, comme dans les annexes du sujet."""
    criteres = ["g1", "g2", "g3"]
    return {"criteres": criteres, "poids": dict(zip(criteres, poids)),
            "profils": [dict(zip(criteres, profil)) for profil in profils],
            "lam": lam, "sens": {critere: "max" for critere in criteres}}


def plat(g1, g2, g3):
    """Un produit des annexes, évalué sur g1, g2 et g3."""
    return {"g1": g1, "g2": g2, "g3": g3}


def test_concordance_partielle_compte_l_egalite():
    """Une égalité avec le profil compte comme « au moins aussi bon », dans les deux sens."""
    assert mr.concordancePartielle(5, 5, "max") == 1 and mr.concordancePartielle(4.9, 5, "max") == 0
    assert mr.concordancePartielle(5, 5, "min") == 1 and mr.concordancePartielle(5.1, 5, "min") == 0


def test_exemple_de_l_annexe_B():
    """Annexe B : b = (5, 5, 5), w = (0,45 ; 0,25 ; 0,30), λ = 0,6 : a et c en C2, b en C1."""
    modele = modeleAnnexe([0.45, 0.25, 0.30], [[5, 5, 5]], 0.6)
    assert mr.affecter(plat(6, 6, 3), modele)["classe"] == 1
    assert mr.affecter(plat(3, 6, 6), modele)["classe"] == 0
    assert mr.affecter(plat(6, 3, 6), modele)["classe"] == 1
    assert mr.affecter(plat(6, 6, 3), modele)["concordances"][0] == 0.45 + 0.25


def test_exemple_de_l_annexe_C():
    """Annexe C : w = (0,7 ; 0,2 ; 0,1), λ = 0,6, b2 = (4, 4, 5), b3 = (7, 4, 5) : a, b, c en C1, C2, C3."""
    modele = modeleAnnexe([0.7, 0.2, 0.1], [[4, 4, 5], [7, 4, 5]], 0.6)
    assert [mr.affecter(p, modele)["classe"] for p in (plat(2, 4, 5), plat(5, 4, 5), plat(8, 4, 5))] == [0, 1, 2]


def test_le_meilleur_profil_franchi_l_emporte():
    """Un plat qui franchit b3 mais pas b4 est en C3, même s'il franchit aussi b2."""
    modele = modeleAnnexe([0.5, 0.3, 0.2], [[1, 1, 1], [2, 2, 2], [3, 3, 3], [4, 4, 4]], 0.7)
    resultat = mr.affecter(plat(3.5, 3, 1), modele)
    assert resultat["franchis"] == [True, True, True, False]
    assert resultat["classe"] == 3


def test_le_seuil_est_atteint_malgre_les_arrondis():
    """0,1 + 0,7 vaut 0,7999999999999999 en machine : le plat doit tout de même franchir λ = 0,8."""
    modele = modeleAnnexe([0.1, 0.7, 0.2], [[5, 5, 5]], 0.8)
    assert 0.1 + 0.7 < 0.8
    assert mr.affecter(plat(6, 6, 0), modele)["classe"] == 1


def test_criteres_a_minimiser_de_la_base():
    """Sur les critères du Nutri-Score, le sens vient de CRITERES : moins de sel, c'est mieux."""
    modele = {"criteres": ["so", "fr"], "poids": {"so": 0.6, "fr": 0.4}, "lam": 0.6,
              "profils": [{"so": 1.0, "fr": 40}]}
    assert mr.affecter({"so": 0.8, "fr": 0}, modele)["classe"] == 1     # peu de sel : le profil est franchi
    assert mr.affecter({"so": 1.2, "fr": 90}, modele)["classe"] == 0    # trop de sel : 0,4 < 0,6


# --- Classes, comparaison au Nutri-Score, paires inversées ---

def platBase(label, **valeurs):
    """Un plat de base fictif : sept composantes moyennes, modifiées par valeurs."""
    plat = {"code": label, "nom": f"plat {label}", "label": label,
            "en": 500, "sa": 1, "su": 2, "so": 0.5, "pr": 5, "fi": 2, "fr": 10}
    plat.update(valeurs)
    return plat


def test_classes_et_labels():
    """E correspond à C1 (numéro 0, E′), A à C5 (numéro 4, A′)."""
    assert [mr.classeDuLabel(lettre) for lettre in "EDCBA"] == [0, 1, 2, 3, 4]
    assert mr.classeDuLabel("A′") == 4 and mr.nomDeClasse(0) == "E′"


def test_comparaison_au_nutriscore():
    """3 plats bien rangés sur 4, le quatrième à une classe près ; la matrice met A en haut à gauche."""
    comparaison = mr.comparerAuNutriscore([4, 3, 0, 0], [4, 3, 0, 1])
    assert (comparaison["bienRanges"], comparaison["exactitude"], comparaison["aUneClassePres"]) == (3, 0.75, 1.0)
    assert comparaison["matrice"][0][0] == 1        # A rangé en A′
    assert comparaison["matrice"][4][4] == 1        # E rangé en E′
    assert comparaison["matrice"][4][3] == 1        # E rangé en D′


def test_paires_de_dominance_inversees():
    """Un plat meilleur partout mais moins bien classé forme une paire inversée ; l'inverse non."""
    meilleurMaisE = platBase("E", en=300, so=0.1, fr=80)
    moinsBonMaisA = platBase("A", en=900, so=1.5, fr=0)
    paires = mr.paresDeDominanceInversees([meilleurMaisE, moinsBonMaisA], mr.CRITERES_TROIS)
    assert paires == [(meilleurMaisE, moinsBonMaisA)]
    assert mr.paresDeDominanceInversees([platBase("A", en=300), platBase("E", en=900)], mr.CRITERES_TROIS) == []


def test_approximation_avec_des_parametres_donnes_a_la_main(tmp_path):
    """Un modèle donné à la main range les plats, et l'Excel des affectations a ses trois feuilles."""
    from openpyxl import load_workbook

    produits = [platBase("A", so=0.1, fr=90), platBase("C", so=0.9, fr=30), platBase("E", so=2.5, fr=0)]
    modele = {"poids": {"en": 0.2, "so": 0.5, "fr": 0.3}, "lam": 0.6,
              "profils": [{"en": 1000, "so": 2.0, "fr": 5}, {"en": 800, "so": 1.5, "fr": 20},
                          {"en": 600, "so": 1.0, "fr": 40}, {"en": 400, "so": 0.3, "fr": 60}]}
    resultat = mr.approximerNutriscore(produits, mr.CRITERES_TROIS, apprentissage=modele)
    # A franchit b5 (sel 0,5 + fruits 0,3 = 0,8) ; C franchit b4 (énergie 0,2 + sel 0,5 = 0,7) ;
    # E ne franchit aucun profil (énergie seule, 0,2)
    assert [mr.nomDeClasse(k) for k in resultat["obtenues"]] == ["A′", "B′", "E′"]
    assert resultat["comparaison"]["bienRanges"] == 2
    chemin = tmp_path / "affectations.xlsx"
    mr.ecrireAffectations(produits, resultat, chemin)
    assert load_workbook(chemin).sheetnames == ["affectations", "paramètres", "synthèse"]


def test_poids_appris_sur_des_plats_fictifs():
    """Des plats dont les trois critères suivent exactement la classe sont tous bien rangés."""
    produits = [platBase(lettre, en=300 + 150 * k, so=0.2 + 0.4 * k, fr=80 - 18 * k)
                for k, lettre in enumerate("ABCDE") for _ in range(3)]
    resultat = mr.approximerNutriscore(produits, mr.CRITERES_TROIS, lam=0.6, apprentissage="poids")
    assert abs(sum(resultat["modele"]["poids"].values()) - 1) < 1e-9
    assert resultat["comparaison"]["bienRanges"] == len(produits)


# --- La généralisation : des plats que le modèle n'a pas vus ---

def test_exactitude_equilibree():
    """Chaque classe compte autant : trois A bien rangés et un E mal rangé font 75 %, mais 50 % à classes égales."""
    comparaison = mr.comparerAuNutriscore([4, 4, 4, 0], [4, 4, 4, 1])
    assert comparaison["exactitude"] == 0.75 and comparaison["exactitudeEquilibree"] == 0.5


def test_appliquer_un_modele_n_apprend_rien():
    """Un modèle déjà appris range de nouveaux plats tel quel : ses classes sont celles d'affecter."""
    produits = [platBase("A", so=0.1, fr=90), platBase("C", so=0.9, fr=30), platBase("E", so=2.5, fr=0)]
    modele = {"criteres": mr.CRITERES_TROIS, "poids": {"en": 0.2, "so": 0.5, "fr": 0.3}, "lam": 0.6,
              "profils": [{"en": 1000, "so": 2.0, "fr": 5}, {"en": 800, "so": 1.5, "fr": 20},
                          {"en": 600, "so": 1.0, "fr": 40}, {"en": 400, "so": 0.3, "fr": 60}]}
    resultat = mr.appliquerModele(produits, modele)
    assert resultat["obtenues"] == [mr.affecter(p, modele)["classe"] for p in produits]
    assert resultat["attendues"] == [4, 2, 0] and resultat["comparaison"]["bienRanges"] == 2


def platsFictifs():
    """Six plats par classe, dont les trois critères suivent la classe, avec un léger désordre."""
    return [platBase(lettre, code=f"{lettre}{i}", en=300 + 150 * k + 7 * i, so=0.2 + 0.4 * k + 0.03 * i, fr=80 - 18 * k - i)
            for k, lettre in enumerate("ABCDE") for i in range(6)]


def test_courbe_d_apprentissage_sur_des_plats_fictifs():
    """
    La courbe tient à part des plats de chaque classe, apprend sur des tailles croissantes, et
    se refait à l'identique : chaque tirage a sa propre graine, et un point se recalcule seul.
    """
    courbe = mr.courbeDApprentissage(platsFictifs(), mr.CRITERES_TROIS, tailles=(10, 20), tirages=2, tenusAPart=2)
    assert [point["taille"] for point in courbe] == [10, 20]
    for point in courbe:
        assert 0 <= point["tenusAPart"] <= 1 and 0 <= point["appris"] <= 1 and len(point["tirages"]) == 2
    assert courbe == mr.courbeDApprentissage(platsFictifs(), mr.CRITERES_TROIS, tailles=(10, 20), tirages=2, tenusAPart=2)
    seul = mr.pointDeLaCourbe(platsFictifs(), mr.CRITERES_TROIS, 0.6, taille=20, tirage=1, tenusAPart=2)
    assert seul == courbe[1]["tirages"][1]


def test_les_parts_de_la_validation_croisee_sont_stratifiees():
    """Trois parts de 10 plats, deux de chaque classe, disjointes, qui couvrent tous les plats et se refont à l'identique."""
    produits = platsFictifs()
    parts = mr.plisStratifies(produits, plis=3)
    assert len(parts) == 3 and all(len(part) == 10 for part in parts)
    assert all(sum(1 for plat in part if plat["label"] == lettre) == 2 for part in parts for lettre in "ABCDE")
    assert sorted(plat["code"] for part in parts for plat in part) == sorted(plat["code"] for plat in produits)
    assert parts == mr.plisStratifies(produits, plis=3)


def test_la_validation_croisee_range_chaque_plat_une_fois():
    """Chaque plat est rangé une fois, par un modèle appris sans lui ; l'exactitude moyenne est celle des parts."""
    resultat = mr.validationCroisee(platsFictifs(), mr.CRITERES_TROIS, 0.6, "poids", plis=3)
    assert resultat["comparaison"]["total"] == 30 and [part["total"] for part in resultat["parts"]] == [10, 10, 10]
    moyenne = sum(part["exactitude"] for part in resultat["parts"]) / 3
    assert abs(resultat["exactitudeMoyenne"] - moyenne) < 1e-9 and resultat["ecartType"] >= 0


def test_la_limite_de_temps_va_jusqu_au_solveur(monkeypatch):
    """approximerNutriscore transmet sa limite de temps à l'apprentissage des profils (les longs calculs sur 375 plats la règlent)."""
    import projet_apprentissage

    vraie, vues = projet_apprentissage.apprendreProfils, []

    def apprendreEnNotantLaLimite(produits, classes, modele, limiteSecondes=300, **options):
        """Note la limite reçue, puis apprend vraiment."""
        vues.append(limiteSecondes)
        return vraie(produits, classes, modele, limiteSecondes, **options)

    monkeypatch.setattr(projet_apprentissage, "apprendreProfils", apprendreEnNotantLaLimite)
    mr.approximerNutriscore(platsFictifs(), mr.CRITERES_TROIS, 0.6, "profils", limiteSecondes=7)
    assert vues == [7]


def test_l_excel_de_la_validation_croisee(tmp_path):
    """L'Excel de la validation croisée : une ligne par apprentissage, son exactitude moyenne, et ses parts à l'optimum prouvé."""
    from openpyxl import load_workbook

    ligne = mr.validationCroisee(platsFictifs(), mr.CRITERES_TROIS, 0.6, "poids", plis=3)
    ligne.update(nom="trois", mode="poids", secondes=1)
    chemin = tmp_path / "validation_croisee.xlsx"
    mr.ecrireValidationCroisee({"plis": 3, "modeles": [ligne]}, chemin)
    lignes = list(load_workbook(chemin)["validation croisée"].values)
    assert len(lignes) == 2 and lignes[0][3] == "Exactitude moyenne"
    assert lignes[1][3] == ligne["exactitudeMoyenne"] and lignes[1][7] == "3 sur 3"


# --- La généralisation sur la base étendue (chiffres du JSON) ---

import json

import pytest

import projet_base


def resultatsDuJson(cle):
    """Une clé de resultats_projet.json, ou un saut du test si elle n'y est pas encore."""
    if not projet_base.FICHIER_RESULTATS.exists() or not projet_base.FICHIER_BASE_ETENDUE.exists():
        pytest.skip("la base étendue n'est pas construite")
    resultats = json.loads(projet_base.FICHIER_RESULTATS.read_text(encoding="utf-8"))
    if cle not in resultats:
        pytest.skip(f"{cle} n'est pas encore calculé")
    return resultats[cle]


def test_les_modeles_du_30_10_sur_les_plats_ajoutes():
    """Les quatre modèles du 30/10, appliqués aux 250 plats ajoutés : les chiffres du JSON sont ceux que l'on recalcule."""
    generalisation = resultatsDuJson("generalisation")
    assert generalisation["modeles"] == mr.evaluerGeneralisation()
    assert all(ligne["ajout"]["total"] == 250 for ligne in generalisation["modeles"])


def test_la_courbe_d_apprentissage_du_json():
    """
    Un tirage de la courbe se recalcule à l'identique, et, à 7 critères, les plats jamais vus
    sont mieux rangés quand le modèle apprend sur 300 plats que sur 25.
    """
    courbe = resultatsDuJson("courbeApprentissage")
    plats = projet_base.lireBase(projet_base.FICHIER_BASE_ETENDUE)
    premier = courbe["sept"][0]
    assert mr.pointDeLaCourbe(plats, mr.CRITERES_SEPT, courbe["lam"], premier["taille"], 0, courbe["tenusAPart"]) \
        == premier["tirages"][0]
    assert courbe["sept"][-1]["tenusAPart"] > courbe["sept"][0]["tenusAPart"]


def test_les_modeles_sur_375_plats():
    """Le modèle final à 7 critères, λ = 0,6 : appris sur les 375 plats, départagé par la plus grande marge."""
    modeles = resultatsDuJson("mrsortEtendu")["modeles"]
    sept = [m for m in modeles if m["nom"] == "sept" and m["lam"] == 0.6][0]
    assert sept["total"] == 375 and "plus grande marge" in sept["methode"] and sept["intervalles"]
    plats = projet_base.lireBase(projet_base.FICHIER_BASE_ETENDUE)
    recalcule = mr.approximerNutriscore(plats, mr.CRITERES_SEPT, 0.6, "poids", departage="marge")
    assert recalcule["modele"]["poids"] == sept["poids"]
    assert recalcule["comparaison"]["bienRanges"] == sept["bienRanges"]


def test_apprentissage_des_profils_par_mrsort():
    """
    Le second apprentissage du sujet : poids fixés par les points maximaux du Nutri-Score,
    profils appris. Sur des plats dont les critères suivent la classe, tous sont bien rangés,
    et le solveur le prouve.
    """
    resultat = mr.approximerNutriscore(platsFictifs(), mr.CRITERES_TROIS, lam=0.6, apprentissage="profils")
    assert resultat["modele"]["poids"] == {"en": 10 / 35, "so": 20 / 35, "fr": 5 / 35}
    assert "profils appris" in resultat["methode"] and resultat["optimal"]
    assert resultat["comparaison"]["bienRanges"] == resultat["optimum"] == len(platsFictifs())


def test_chercher_un_modele_exact():
    """
    Une paire inversée suffit à prouver qu'aucun modèle exact n'existe (MR-Sort est monotone) ;
    sans paire inversée, le programme du modèle complet cherche, et ici trouve, un modèle exact.
    """
    inverses = [platBase("E", code="e", en=300, so=0.1, fr=80), platBase("A", code="a", en=900, so=1.5, fr=0)]
    reponse = mr.chercherUnModeleExact(inverses, mr.CRITERES_TROIS, limiteSecondes=30)
    assert reponse["existe"] is False and reponse["preuve"] == "paires inversées"
    ordonnes = [platBase(lettre, code=lettre, en=300 + 150 * k, so=0.2 + 0.4 * k, fr=80 - 18 * k)
                for k, lettre in enumerate("ABCDE")]
    reponse = mr.chercherUnModeleExact(ordonnes, mr.CRITERES_TROIS, limiteSecondes=30)
    assert reponse["existe"] is True and reponse["preuve"] == "programme linéaire" and reponse["modele"]


def test_les_modeles_aux_profils_appris():
    """
    Les 4 modèles aux profils appris sur la base : les poids des points maximaux, des profils
    ordonnés, le nombre de plats bien rangés que l'on retrouve, jamais au-dessus du maximum
    prouvé par le solveur (« borne »).
    """
    import projet_apprentissage as ap

    modeles = resultatsDuJson("mrsortProfils")["modeles"]
    plats = projet_base.lireBase()
    assert sorted((m["nom"], m["lam"]) for m in modeles) == [("sept", 0.6), ("sept", 0.7), ("trois", 0.6), ("trois", 0.7)]
    for modele in modeles:
        assert modele["poids"] == pytest.approx(ap.poidsDesPointsMax(modele["criteres"]))
        regle = {"criteres": modele["criteres"], "poids": modele["poids"], "profils": modele["profils"], "lam": modele["lam"]}
        assert mr.appliquerModele(plats, regle)["comparaison"]["bienRanges"] == modele["bienRanges"] <= modele["borne"]
        for bas, haut in zip(modele["profils"], modele["profils"][1:]):
            for critere in modele["criteres"]:
                if mr.sensDuCritere(critere, regle) == "max":
                    assert haut[critere] >= bas[critere]
                else:
                    assert haut[critere] <= bas[critere]


def test_le_modele_complet_du_json():
    """
    Le modèle complet (alternance) : le nombre de plats bien rangés se retrouve, et c'est le
    meilleur de son historique. À 3 critères, les paires inversées prouvent qu'aucun modèle
    exact n'existe ; à 7 critères, aucune paire n'est inversée.
    """
    complet = resultatsDuJson("modeleComplet")
    plats = projet_base.lireBase()
    for modele in complet["modeles"]:
        regle = {"criteres": modele["criteres"], "poids": modele["poids"], "profils": modele["profils"], "lam": modele["lam"]}
        assert mr.appliquerModele(plats, regle)["comparaison"]["bienRanges"] == modele["bienRanges"] == max(modele["historique"])
    assert complet["exact"]["trois"]["existe"] is False and complet["exact"]["trois"]["preuve"] == "paires inversées"
    assert complet["exact"]["sept"]["paires"] == 0


def test_les_trois_apprentissages_sur_375_plats():
    """
    Les profils appris et le modèle complet sur les 375 plats : quatre modèles chacun, et le
    nombre de plats bien rangés du JSON se retrouve en rangeant la base étendue.
    """
    plats = projet_base.lireBase(projet_base.FICHIER_BASE_ETENDUE)
    for cle in ("mrsortEtenduProfils", "modeleCompletEtendu"):
        modeles = resultatsDuJson(cle)["modeles"]
        assert len(modeles) == 4 and all(modele["total"] == 375 for modele in modeles)
        for modele in modeles:
            regle = {"criteres": modele["criteres"], "poids": modele["poids"], "profils": modele["profils"], "lam": modele["lam"]}
            assert mr.appliquerModele(plats, regle)["comparaison"]["bienRanges"] == modele["bienRanges"]


def test_la_validation_croisee_du_json():
    """
    La validation croisée sur les 375 plats : 5 parts de 75 plats, une moyenne qui est celle des
    parts, et, recalculée ici (quelques secondes), la même exactitude pour les poids appris à 3 critères.
    """
    croisee = resultatsDuJson("validationCroisee")
    assert croisee["plis"] == 5
    for ligne in croisee["modeles"]:
        assert [part["total"] for part in ligne["parts"]] == [75] * 5 and ligne["comparaison"]["total"] == 375
        assert abs(ligne["exactitudeMoyenne"] - sum(part["exactitude"] for part in ligne["parts"]) / 5) < 1e-9
    ligne = [l for l in croisee["modeles"] if (l["nom"], l["mode"], l["lam"]) == ("trois", "poids", 0.6)][0]
    recalcul = mr.validationCroisee(projet_base.lireBase(projet_base.FICHIER_BASE_ETENDUE), mr.CRITERES_TROIS, 0.6, "poids")
    assert recalcul["comparaison"]["bienRanges"] == ligne["comparaison"]["bienRanges"]


# --- Le pas à pas : l'affectation d'un plat, étape par étape ---

def test_etapes_de_l_affectation():
    """
    Annexe B : face à b = (5, 5, 5), le produit a = (6, 6, 3) vaut au moins le profil sur g1 et g2
    (c = 1, 1, 0) ; ces deux critères pèsent 0,45 + 0,25 = 0,70 ≥ 0,6 : b est franchi, a va en C2.
    Les étapes donnent les mêmes concordances et la même classe qu'affecter.
    """
    modele = modeleAnnexe([0.45, 0.25, 0.30], [[5, 5, 5]], 0.6)
    etapes, classe = mr.etapesDeLAffectation(plat(6, 6, 3), modele)
    assert etapes[0]["profil"] == "b2" and etapes[0]["partielles"] == {"g1": 1, "g2": 1, "g3": 0}
    assert etapes[0]["pour"] == ["g1", "g2"] and etapes[0]["franchi"]
    assert etapes[0]["concordance"] == mr.affecter(plat(6, 6, 3), modele)["concordances"][0]
    assert classe == mr.affecter(plat(6, 6, 3), modele)["classe"] == 1
