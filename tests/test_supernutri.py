"""Tests du SuperNutri-score (question 3.4) : ses critères, ses poids, ses profils et le classement de la base."""

import openpyxl
import pytest

import projet_base
import projet_supernutri as sn
from projet_mrsort import affecter, nomDeClasse


baseConstruite = pytest.mark.skipif(not projet_base.FICHIER_BASE.exists(), reason="la base n'est pas encore construite")

LIMITER = ["en", "sa", "su", "so"]
FAVORISER = ["pr", "fi", "fr"]
TRANSFORMATION = ["nova", "additifs", "aRisque", "bio"]


def platAuNiveauDeAPrime():
    """Un plat qui vaut le profil de A′ (b5) sur les onze critères : il le franchit avec une concordance de 1."""
    return {"en": 300, "sa": 1.0, "su": 2.0, "so": 0.2, "pr": 15.0, "fi": 7.0, "fr": 80.0,
            "nova": 3, "additifs": 0, "listeAdditifs": None, "bio": "oui"}


# --- Les poids ---

def test_les_onze_criteres_dans_l_ordre():
    """Les sept composantes du Nutri-Score, puis la transformation et la production."""
    assert sn.CRITERES_SUPER == LIMITER + FAVORISER + TRANSFORMATION


def test_les_poids_suivent_les_trois_piliers():
    """À limiter 0,40, à favoriser 0,30, transformation et production 0,30 ; la somme fait 1."""
    poids = sn.MODELE_SUPER["poids"]
    assert sum(poids.values()) == pytest.approx(1)
    assert sum(poids[c] for c in LIMITER) == pytest.approx(0.40)
    assert sum(poids[c] for c in FAVORISER) == pytest.approx(0.30)
    assert sum(poids[c] for c in TRANSFORMATION) == pytest.approx(0.30)


def test_dans_un_pilier_nutritionnel_les_poids_suivent_les_points_maximaux():
    """Le sel (20 points au plus) pèse deux fois l'énergie (10 points) ; les protéines (7) pèsent 7/5 des fibres (5)."""
    poids = sn.MODELE_SUPER["poids"]
    assert poids["so"] == pytest.approx(2 * poids["en"])
    assert poids["pr"] == pytest.approx(7 / 5 * poids["fi"])


def test_les_poids_de_la_transformation_et_de_la_production():
    """NOVA 0,10 ; nombre d'additifs et additifs à risque 0,075 chacun ; bio 0,05, le plus faible."""
    poids = sn.MODELE_SUPER["poids"]
    assert (poids["nova"], poids["additifs"], poids["aRisque"], poids["bio"]) == pytest.approx((0.10, 0.075, 0.075, 0.05))
    assert poids["bio"] == min(poids.values())


# --- Les profils ---

def test_les_profils_sont_ordonnes():
    """De b2 (D′) à b5 (A′), chaque profil est au moins aussi exigeant que le précédent, dans le sens du critère."""
    profils = sn.MODELE_SUPER["profils"]
    for critere in sn.CRITERES_SUPER:
        valeurs = [profil[critere] for profil in profils]
        if sn.MODELE_SUPER["sens"][critere] == "min":
            assert valeurs == sorted(valeurs, reverse=True), critere
        else:
            assert valeurs == sorted(valeurs), critere


def test_les_seuils_de_a_prime_viennent_des_allegations():
    """Règlement CE 1924/2006 : « faible teneur » en AGS (1,5 g), en sucres (5 g) et en sel (0,3 g) ; « riche en fibres » (6 g)."""
    a, b = sn.MODELE_SUPER["profils"][3], sn.MODELE_SUPER["profils"][2]
    assert (a["sa"], a["su"], a["so"], a["fi"]) == (1.5, 5, 0.3, 6)
    assert b["fi"] == 3                                        # « source de fibres » pour B′


def test_lambda_vaut_0_7():
    assert sn.MODELE_SUPER["lam"] == 0.7


# --- Les additifs à risque et les valeurs d'un plat ---

def test_les_additifs_a_risque():
    """Nitrites et nitrates (E249 à E252), phosphates, carraghénanes ; l'acide citrique (E330) n'en est pas un."""
    assert sn.additifsARisque("E250, E330, E451, E407a") == 3
    assert sn.additifsARisque("E14XX, E330, E415") == 0
    assert sn.additifsARisque(None) == 0
    assert sn.additifsARisque("e252") == 1


def test_les_valeurs_d_un_plat():
    """Le bio vaut 1 ou 0, et les additifs à risque se comptent dans la liste des additifs."""
    valeurs = sn.valeursDuPlat(dict(platAuNiveauDeAPrime(), listeAdditifs="E250, E330", bio="non"))
    assert (valeurs["bio"], valeurs["aRisque"], valeurs["additifs"]) == (0, 1, 0)
    assert sn.valeursDuPlat(platAuNiveauDeAPrime())["bio"] == 1


def test_une_valeur_absente_ne_vote_pas_pour_le_plat():
    """Sans groupe NOVA, le plat perd la voix de NOVA (0,10) face à chaque profil, mais garde les autres."""
    detail = affecter(sn.valeursDuPlat(dict(platAuNiveauDeAPrime(), nova=None)), sn.MODELE_SUPER)
    assert detail["concordances"][3] == pytest.approx(0.90)
    assert nomDeClasse(detail["classe"]) == "A′"


# --- Le seuil majoritaire ---

def test_rater_toute_la_transformation_laisse_a_prime_possible():
    """Ultra-transformé, plein d'additifs, non bio, mais au niveau de A′ sur les sept composantes : 0,70, soit λ."""
    plat = dict(platAuNiveauDeAPrime(), nova=4, additifs=8, listeAdditifs="E250, E451", bio="non")
    detail = affecter(sn.valeursDuPlat(plat), sn.MODELE_SUPER)
    assert detail["concordances"][3] == pytest.approx(0.70)
    assert nomDeClasse(detail["classe"]) == "A′"


def test_rater_aussi_un_critere_nutritionnel_fait_perdre_a_prime():
    """Le même plat, avec 3 g de fibres au lieu de 7 : il perd la voix des fibres et tombe sous λ face à A′."""
    plat = dict(platAuNiveauDeAPrime(), nova=4, additifs=8, listeAdditifs="E250, E451", bio="non", fi=3.0)
    detail = affecter(sn.valeursDuPlat(plat), sn.MODELE_SUPER)
    assert detail["concordances"][3] < 0.7
    assert nomDeClasse(detail["classe"]) != "A′"


# --- La base ---

@baseConstruite
def test_la_poelee_fermiere_est_c_prime():
    """
    La Poêlée Fermière (B au Nutri-Score) : 1,6 g de protéines, sous le seuil de D′ (2,4 g) ; NOVA 4 et 3 additifs
    lui ferment B′. Face à C′, elle ne rate que les protéines : 1 − 0,124 ≥ 0,7.
    """
    plat = [p for p in projet_base.lireBase() if p["code"] == "3257982125116"][0]
    assert sn.classerPlat(plat)["lettre"] == "C′"


@baseConstruite
def test_le_super_nutri_score_range_toute_la_base_et_ecrit_l_excel(tmp_path):
    """Chaque plat reçoit une classe ; l'Excel a une ligne par plat, avec sa classe et son Nutri-Score."""
    sortie = tmp_path / "supernutri.xlsx"
    resultat = sn.superNutriScore(projet_base.FICHIER_BASE, sortie=sortie, afficher=False)
    assert len(resultat["plats"]) == 125
    assert sum(resultat["repartition"].values()) == 125
    feuille = openpyxl.load_workbook(sortie).worksheets[0]
    entetes = [cellule.value for cellule in feuille[1]]
    assert "SuperNutri-score" in entetes and "Nutri-Score" in entetes
    assert feuille.max_row == 126


# --- Les analyses de sensibilité ---

def platAuBordDeAPrime(**changements):
    """Le plat qui rate toute la transformation : sa concordance face à A′ vaut 0,70, juste λ. Le moindre souffle le fait tomber."""
    return dict(platAuNiveauDeAPrime(), nova=4, additifs=8, listeAdditifs="E250, E451", bio="non", **changements)


def test_le_calcul_rapide_donne_la_classe_d_affecter():
    """Les critères satisfaits ne dépendent pas des poids : la classe qu'on en tire est celle d'affecter."""
    for plat in (platAuNiveauDeAPrime(), platAuBordDeAPrime(), platAuBordDeAPrime(fi=2.5, so=0.9)):
        valeurs = sn.valeursDuPlat(plat)
        satisfaits = sn.criteresSatisfaits(valeurs, sn.MODELE_SUPER)
        assert sn.classeDepuisSatisfaits(satisfaits, sn.MODELE_SUPER["poids"], 0.7) == affecter(valeurs, sn.MODELE_SUPER)["classe"]


def test_un_poids_modifie_garde_une_somme_de_1():
    """Le sel perd 0,05 ; les autres poids sont ramenés pour que la somme fasse 1, et aucun ne devient négatif."""
    poids = sn.poidsModifies(sn.MODELE_SUPER["poids"], "so", -0.05)
    assert poids["so"] == pytest.approx(sn.MODELE_SUPER["poids"]["so"] - 0.05)
    assert sum(poids.values()) == pytest.approx(1)
    assert sn.poidsModifies(sn.MODELE_SUPER["poids"], "bio", -0.08)["bio"] == 0


def test_des_poids_tires_au_hasard_restent_valides():
    import random
    poids = sn.poidsTires(sn.MODELE_SUPER["poids"], 0.05, random.Random(1))
    assert sum(poids.values()) == pytest.approx(1)
    assert min(poids.values()) >= 0


def test_sans_amplitude_aucun_plat_ne_change():
    resultat = sn.sensibilitePoids([platAuBordDeAPrime(), platAuNiveauDeAPrime()], amplitude=0, tirages=5)
    assert all(ligne["plats"] == 0 for ligne in resultat["unParUn"])
    assert resultat["partMoyenne"] == 0


def test_un_plat_au_bord_change_quand_un_de_ses_criteres_pese_moins():
    """Le sel, que le plat satisfait, perd 0,05 : la concordance face à A′ passe sous λ, et le plat change de classe."""
    resultat = sn.sensibilitePoids([platAuBordDeAPrime()], tirages=0)
    ligne = [l for l in resultat["unParUn"] if l["critere"] == "so" and l["delta"] < 0][0]
    assert ligne["plats"] == 1


def test_un_tirage_se_refait_a_l_identique():
    plats = [platAuBordDeAPrime(), platAuBordDeAPrime(fi=2.5), platAuNiveauDeAPrime()]
    assert sn.sensibilitePoids(plats, tirages=50, graine=7) == sn.sensibilitePoids(plats, tirages=50, graine=7)


def test_sans_decalage_aucun_profil_ne_bouge():
    resultat = sn.sensibiliteProfils([platAuBordDeAPrime()], decalage=0, pasEntier=0)
    assert resultat["scenarios"] == [] and resultat["plats"] == []


def test_un_plat_au_seuil_change_quand_le_seuil_bouge():
    """Le plat a pile 0,3 g de sel, le seuil de A′ : à 0,285 g (− 5 %), il ne le satisfait plus et quitte A′."""
    resultat = sn.sensibiliteProfils([platAuBordDeAPrime(so=0.3)])
    assert len(resultat["plats"]) == 1
    scenarios = [s for s in resultat["scenarios"] if s["profil"] == "b5" and s["critere"] == "so" and s["plats"] == 1]
    assert [s["nouvelle"] for s in scenarios] == [0.285]


def test_un_decalage_qui_casserait_l_ordre_est_ecarte():
    """NOVA vaut 3 pour B′ et pour A′ : passer celui de B′ à 2 le rendrait plus exigeant que celui de A′."""
    resultat = sn.sensibiliteProfils([platAuNiveauDeAPrime()])
    assert not [s for s in resultat["scenarios"] if s["profil"] == "b4" and s["critere"] == "nova" and s["nouvelle"] == 2]
    assert not [s for s in resultat["scenarios"] if s["critere"] == "bio"]


def test_les_plats_qui_changent_se_comptent_par_famille_de_decalages():
    """Les composantes (± 5 %) et les entiers (± 1 : NOVA, additifs) se comptent à part : leurs pas ne sont pas comparables."""
    resultat = sn.sensibiliteProfils([platAuBordDeAPrime(so=0.3)])
    assert (resultat["platsComposantes"], resultat["platsEntiers"]) == (1, 0)


def test_l_excel_de_la_sensibilite(tmp_path):
    """Quatre feuilles : les poids un par un (22 variations), les tirages par amplitude, les profils, les plats qui changent."""
    plats = [platAuBordDeAPrime(so=0.3, code="1", nom="Au bord"), dict(platAuNiveauDeAPrime(), code="2", nom="Loin du bord")]
    sensibilites = {"base": sn.sensibilites(plats, tirages=20), "etendue": sn.sensibilites(plats, tirages=20)}
    chemin = tmp_path / "sensibilite.xlsx"
    sn.ecrireSensibilite(sensibilites, chemin)
    classeur = openpyxl.load_workbook(chemin)
    assert classeur.sheetnames == ["poids un par un", "tirages", "profils", "plats qui changent"]
    assert classeur["poids un par un"].max_row == 1 + 2 * len(sn.CRITERES_SUPER)
    assert classeur["tirages"].max_row == 1 + len(sn.AMPLITUDES)
    assert [c.value for c in classeur["plats qui changent"][2]][:3] == ["125 plats", "1", "Au bord"]


def test_les_plats_au_bord_de_leur_classe():
    """Un plat dont la classe tient à une concordance de λ pile est au bord : on dit lesquels, et ce qu'ils ratent."""
    resultat = sn.platsAuBord([platAuBordDeAPrime(code="1"), dict(platAuNiveauDeAPrime(), code="2")])
    assert [plat["code"] for plat in resultat] == ["1"]
    assert resultat[0]["rates"] == ["nova", "additifs", "aRisque", "bio"]


# --- La comparaison au Nutri-Score ---

def test_un_plat_qui_monte_et_un_plat_qui_descend():
    """
    Au niveau de A′ partout, mais C au Nutri-Score : il monte de deux classes. Ultra-transformé, à 3 g de fibres, mais A au
    Nutri-Score : il descend en B′ ; face au profil de A′, il rate les fibres et tout le pilier de la transformation.
    """
    monte = dict(platAuNiveauDeAPrime(), code="1", nom="Monte", label="C")
    descend = platAuBordDeAPrime(fi=3.0, code="2", nom="Descend", label="A")
    resultat = sn.ecartsAuNutriscore([monte, descend])
    assert (resultat["montent"], resultat["descendent"], resultat["egaux"]) == (1, 1, 0)
    lignes = {ligne["code"]: ligne for ligne in resultat["plats"]}
    assert (lignes["1"]["ecart"], lignes["1"]["rates"]) == (2, [])
    assert (lignes["2"]["ecart"], lignes["2"]["lettre"]) == (-1, "B′")
    assert lignes["2"]["rates"] == ["fi", "nova", "additifs", "aRisque", "bio"]
    assert resultat["raisonsDesDescentes"]["nova"] == 1 and resultat["raisonsDesDescentes"]["en"] == 0


@baseConstruite
def test_la_poelee_fermiere_descend_d_une_classe():
    """B au Nutri-Score, C′ au SuperNutri-score : face à B′, elle rate les protéines, les fibres, NOVA, les additifs et le bio."""
    plat = [p for p in projet_base.lireBase() if p["code"] == "3257982125116"][0]
    ligne = sn.ecartsAuNutriscore([plat])["plats"][0]
    assert ligne["ecart"] == -1
    assert ligne["rates"] == ["pr", "fi", "nova", "additifs", "bio"]


@baseConstruite
def test_l_excel_dit_l_ecart_au_nutriscore(tmp_path):
    """Chaque plat a son écart au Nutri-Score et ce qui l'explique ; une feuille croise les deux classements."""
    sortie = tmp_path / "supernutri.xlsx"
    sn.superNutriScore(projet_base.FICHIER_BASE, sortie=sortie, afficher=False)
    classeur = openpyxl.load_workbook(sortie)
    entetes = [cellule.value for cellule in classeur.worksheets[0][1]]
    assert "Écart au Nutri-Score" in entetes and "Critères ratés" in entetes
    assert "comparaison" in classeur.sheetnames


# --- La base d'un autre groupe ---

CORRESPONDANCE = {"code": "EAN", "nom": "Produit", "en": "Energie (kJ)", "sa": "AGS", "su": "Sucres", "so": "Sel",
                  "pr": "Proteines", "fi": "Fibres", "fr": "Fruits et legumes (%)", "label": "Nutri-Score",
                  "leurClasse": "SuperNutri"}
ENTETES = ["EAN", "Produit", "Energie (kJ)", "AGS", "Sucres", "Sel", "Proteines", "Fibres", "Fruits et legumes (%)",
           "Nutri-Score", "SuperNutri"]
POELEE = ["3257982125116", "Poêlée Fermière", "287", "1,6", "1,6", "0,55", "1,6", "2,6", "65", "B", "C"]
INCONNU = ["0000000000017", "Inconnu", "500", "2", "3", "1", "5", "2", "10", "C", "D"]
fichePoelee = pytest.mark.skipif(not (projet_base.DOSSIER_BRUT / "produits" / "3257982125116.json").exists(),
                                 reason="la fiche de la Poêlée Fermière n'est pas dans le cache")


@fichePoelee
def test_importer_une_base_aux_colonnes_differentes(tmp_path, monkeypatch):
    """
    Leurs colonnes portent d'autres noms, leurs nombres ont des virgules, et NOVA, les additifs et le bio manquent :
    on les lit dans la fiche d'OFF gardée dans le cache. Un code absent du cache, hors ligne, est signalé.
    """
    monkeypatch.setenv("PROJET_HORS_LIGNE", "1")
    classeur = openpyxl.Workbook()
    classeur.active.append(ENTETES)
    classeur.active.append(POELEE)
    classeur.active.append(INCONNU)
    chemin = tmp_path / "autre.xlsx"
    classeur.save(chemin)
    plats, manques = sn.importerBaseAutreGroupe(chemin, CORRESPONDANCE)
    poelee, inconnu = plats
    assert (poelee["en"], poelee["sa"], poelee["so"], poelee["label"], poelee["leurClasse"]) == (287, 1.6, 0.55, "B", "C")
    assert (poelee["nova"], poelee["additifs"], poelee["bio"]) == (4, 3, "non")
    assert inconnu["nova"] is None
    assert list(manques) == ["0000000000017"]


def test_importer_un_csv_a_point_virgule(tmp_path):
    """Un CSV séparé par des points-virgules, sans compléter par OFF."""
    chemin = tmp_path / "autre.csv"
    chemin.write_text("\n".join(";".join(ligne) for ligne in (ENTETES, INCONNU)), encoding="utf-8")
    plats, manques = sn.importerBaseAutreGroupe(chemin, CORRESPONDANCE, completer=False)
    assert (plats[0]["code"], plats[0]["so"], plats[0]["leurClasse"]) == ("0000000000017", 1.0, "D")
    assert manques == {}


@pytest.mark.skipif(not projet_base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")
def test_l_import_rend_les_classes_de_nos_250_plats_ajoutes(tmp_path, monkeypatch):
    """
    Nos 250 plats ajoutés, déguisés en base d'un autre groupe (autres noms de colonnes, sans NOVA, additifs ni bio) :
    l'import complète tout depuis le cache, hors ligne, et chaque plat retrouve sa classe.
    """
    monkeypatch.setenv("PROJET_HORS_LIGNE", "1")
    ajoutes = [plat for plat in projet_base.lireBase(projet_base.FICHIER_BASE_ETENDUE) if plat["lot"] != projet_base.LOT_BASE]
    classeur = openpyxl.Workbook()
    classeur.active.append(ENTETES)
    for plat in ajoutes:
        classeur.active.append([plat["code"], plat["nom"]] + [plat[c] for c in ("en", "sa", "su", "so", "pr", "fi", "fr")]
                               + [plat["label"], None])
    chemin = tmp_path / "autre.xlsx"
    classeur.save(chemin)
    plats, manques = sn.importerBaseAutreGroupe(chemin, CORRESPONDANCE)
    assert len(plats) == 250 and manques == {}
    for importe, plat in zip(plats, ajoutes):
        assert sn.classerPlat(importe)["lettre"] == sn.classerPlat(plat)["lettre"], plat["nom"]


@pytest.mark.skipif(not (projet_base.DOSSIER_BRUT / "produits" / "0635646.json").exists(), reason="fiche absente du cache")
def test_un_code_se_retrouve_meme_ecrit_avec_d_autres_zeros(monkeypatch):
    """Le cache garde la fiche sous « 0635646 » ; la base écrit « 00635646 », et une autre base pourrait écrire « 635646 »."""
    monkeypatch.setenv("PROJET_HORS_LIGNE", "1")
    for code in ("00635646", "635646"):
        reponse, message = sn.ficheDuCode(code)
        assert reponse is not None, message


def test_un_nombre_d_additifs_a_risque_saisi_prime_sur_la_liste():
    """L'interface saisit directement le nombre d'additifs à risque ; vide, il ne vote pas."""
    assert sn.valeursDuPlat(dict(platAuNiveauDeAPrime(), aRisque=2))["aRisque"] == 2
    assert sn.valeursDuPlat(dict(platAuNiveauDeAPrime(), aRisque=None))["aRisque"] == float("inf")


def test_un_libelle_en_minuscule_garde_ses_sigles():
    """Dans une phrase, « Groupe NOVA » devient « groupe NOVA », et non « groupe nova »."""
    assert (sn.libelleEnMinuscule("nova"), sn.libelleEnMinuscule("so")) == ("groupe NOVA", "sel")


# --- La base de l'autre groupe : le téléchargement des fiches (25/11) ---

def test_le_telechargement_ne_redemande_pas_une_fiche_gardee(tmp_path, monkeypatch):
    """Seules les fiches absentes du cache sont demandées à OFF ; un produit inconnu d'OFF est compté à part."""
    demandes = []

    def ficheProduitSimulee(code, depuisCache):
        demandes.append(code)
        return {"status": 0} if code == "0000000000017" else {"status": 1, "product": {}}

    monkeypatch.setattr(sn, "ficheProduit", ficheProduitSimulee)
    classeur = openpyxl.Workbook()
    classeur.active.append(["code", "nom"])
    for code in ("3257982125116", "0000000000017", "0000000000024"):        # le premier est déjà gardé
        classeur.active.append([code, "un produit"])
    chemin = tmp_path / "autre.xlsx"
    classeur.save(chemin)
    lues, introuvables = sn.telechargerFichesAutreGroupe(chemin, {"code": "code"})
    assert demandes == ["0000000000017", "0000000000024"]
    assert (lues, introuvables) == (2, ["0000000000017"])


# --- Les protéines que le Nutri-Score retient, selon le type de produit (25/11) ---

def platChargeEnNegatifs(**changements):
    """Énergie, AGS, sucres et sel élevés (bien plus de 11 points négatifs), et 15 g de protéines."""
    return dict(platAuNiveauDeAPrime(), en=2100, sa=8.0, su=20.0, so=2.0, pr=15.0, **changements)


def test_les_proteines_ne_votent_plus_a_partir_de_11_points_negatifs():
    """Comme le Nutri-Score de 2023 : au-delà de 11 points négatifs, il ne compte plus les protéines."""
    assert sn.valeursDuPlat(platChargeEnNegatifs())["pr"] == float("-inf")
    assert sn.valeursDuPlat(platAuNiveauDeAPrime())["pr"] == 15.0


def test_les_proteines_d_un_fromage_votent_toujours():
    assert sn.valeursDuPlat(platChargeEnNegatifs(), "fromage")["pr"] == 15.0


def test_les_proteines_d_une_viande_rouge_comptent_au_plus_comme_deux_points():
    """Au plus 2 points de protéines : elles votent comme 4,8 g, le seuil de C′, et plus celui de B′ (7,2 g)."""
    valeurs = sn.valeursDuPlat(platAuNiveauDeAPrime(), "viandeRouge")
    assert valeurs["pr"] == 4.8
    satisfaits = sn.criteresSatisfaits(valeurs, sn.MODELE_SUPER)
    assert "pr" in satisfaits[1] and "pr" not in satisfaits[2]


def test_les_proteines_d_une_matiere_grasse_ne_votent_plus_a_partir_de_7_points():
    """Une matière grasse : le seuil est de 7 points négatifs, et non 11 (son énergie et ses AGS se notent autrement)."""
    plat = dict(platAuNiveauDeAPrime(), en=900, sa=4.5, su=1.0, so=0.4, pr=15.0, lipides=10.0)   # 8 points négatifs
    from projet_nutriscore import scoreNutriscore
    assert 7 <= scoreNutriscore(plat, categorie="matieresGrasses")["N"] < 11
    assert sn.valeursDuPlat(plat, "matieresGrasses")["pr"] == float("-inf")


def test_le_type_vient_du_produit_s_il_n_est_pas_donne():
    """Un produit de l'autre base porte son type (lu sur OFF) : sans type donné, c'est le sien qui compte."""
    assert sn.valeursDuPlat(platChargeEnNegatifs(categorie="fromage"))["pr"] == 15.0


# --- Le modèle de l'autre groupe, dans notre moteur (25/11) ---

baseAutreGroupe = pytest.mark.skipif(not sn.FICHIER_AUTRE_GROUPE.exists(), reason="la base de l'autre groupe n'est pas là")


@baseAutreGroupe
def test_leur_modele_se_lit_dans_leur_feuille():
    """Cinq critères dans nos clés (leur « tr » est NOVA, leur « so » le sodium en mg), des poids de somme 1, λ = 0,63."""
    modele = sn.modeleDeLAutreGroupe()
    assert modele["criteres"] == ["su", "fi", "nova", "sa", "sodium"]
    assert sum(modele["poids"].values()) == pytest.approx(1)
    assert modele["poids"]["su"] == pytest.approx(5 / 15, abs=1e-3)
    assert modele["lam"] == 0.63
    assert [profil["nova"] for profil in modele["profils"]] == [3, 3, 3, 1]


@baseAutreGroupe
def test_leur_modele_recode_redonne_leurs_300_classes():
    """Recodé depuis leur seule feuille, leur modèle redonne la classe de chacun de leurs produits."""
    plats, manques = sn.importerBaseAutreGroupe(sn.FICHIER_AUTRE_GROUPE, sn.CORRESPONDANCE_AUTRE_GROUPE, completer=False)
    modele = sn.modeleDeLAutreGroupe()
    differents = [plat["nom"] for plat in plats if sn.classerAvecUnModele(plat, modele)["lettre"][0] != plat["leurClasse"]]
    assert len(plats) == 300 and differents == []


# --- Les deux bases étendues et la comparaison des deux modèles (25/11) ---

@fichePoelee
def test_l_import_lit_aussi_le_type_au_nutriscore(tmp_path, monkeypatch):
    """La fiche d'OFF donne aussi le type du produit au Nutri-Score : la Poêlée Fermière est du cas général."""
    monkeypatch.setenv("PROJET_HORS_LIGNE", "1")
    classeur = openpyxl.Workbook()
    classeur.active.append(ENTETES)
    classeur.active.append(POELEE)
    chemin = tmp_path / "autre.xlsx"
    classeur.save(chemin)
    plats, manques = sn.importerBaseAutreGroupe(chemin, CORRESPONDANCE)
    assert plats[0]["categorie"] == "general" and plats[0]["ficheLue"]


def test_la_base_completee_garde_leurs_colonnes_et_ajoute_les_notres(tmp_path):
    """Leurs colonnes d'abord, puis ce qu'OFF ajoute ; une feuille « lisez-moi » dit d'où vient chaque chose."""
    source = tmp_path / "leur.xlsx"
    classeur = openpyxl.Workbook()
    classeur.active.append(["code", "nom"])
    classeur.active.append(["0000000000017", "Muesli"])
    classeur.save(source)
    plat = {"code": "0000000000017", "nom": "Muesli", "nova": 3, "additifs": 2, "listeAdditifs": "E250, E330", "bio": "oui",
            "categorie": "general", "ficheLue": "2026-11-26"}
    chemin = tmp_path / "completee.xlsx"
    sn.ecrireBaseCompletee([plat], source, chemin)
    lu = openpyxl.load_workbook(chemin)
    entetes = [cellule.value for cellule in lu.worksheets[0][1]]
    assert entetes[:2] == ["code", "nom"]
    assert "Additifs à risque (OFF)" in entetes and "Bio (OFF)" in entetes and "Type au Nutri-Score (OFF)" in entetes
    ligne = dict(zip(entetes, [cellule.value for cellule in lu.worksheets[0][2]]))
    assert (ligne["Additifs à risque (OFF)"], ligne["Bio (OFF)"]) == (1, "oui")
    assert "lisez-moi" in lu.sheetnames


@baseConstruite
def test_notre_base_enrichie_explique_chaque_classe(tmp_path):
    """Chaque plat : les protéines que retient le Nutri-Score, et profil par profil, les critères qui votent contre lui."""
    sortie = tmp_path / "supernutri.xlsx"
    sn.superNutriScore(projet_base.FICHIER_BASE, sortie=sortie, afficher=False)
    feuille = openpyxl.load_workbook(sortie).worksheets[0]
    entetes = [cellule.value for cellule in feuille[1]]
    assert "Protéines retenues par le Nutri-Score" in entetes and "Explication" in entetes
    lignes = [dict(zip(entetes, [cellule.value for cellule in ligne])) for ligne in feuille.iter_rows(min_row=2)]
    poelee = [ligne for ligne in lignes if ligne["Code-barres"] == "3257982125116"][0]
    assert poelee["Explication"].startswith("A′ : rate ") and "C′ : franchi" in poelee["Explication"]


def test_deux_modeles_comparés_sur_une_base():
    """Chaque modèle face au Nutri-Score, puis l'un face à l'autre, et ce qui bloque chacun au seuil de B′."""
    leur = {"criteres": ["su", "fi"], "poids": {"su": 0.5, "fi": 0.5}, "lam": 0.6, "sens": {"su": "min", "fi": "max"},
            "profils": [{"su": 20, "fi": 1}, {"su": 15, "fi": 2}, {"su": 10, "fi": 3}, {"su": 5, "fi": 6}]}
    plats = [dict(platAuNiveauDeAPrime(), code="1", nom="Bon", label="A", leurClasse="A"),
             dict(platAuBordDeAPrime(fi=0.5), code="2", nom="Sans fibres", label="C", leurClasse="E")]
    resultat = sn.comparerDeuxModeles(plats, leur)
    assert resultat["total"] == 2
    assert resultat["notreFaceAuNutriscore"]["total"] == resultat["leurFaceAuNutriscore"]["total"] == 2
    assert resultat["leurReproduit"] == 2                       # leur modèle redonne leur colonne
    assert resultat["bloquants"]["leur"]["fi"] == 0.5           # le plat sans fibres rate leur seuil de B′


def leurModeleJouet():
    """Un modèle à deux critères, à la manière du leur : les sucres et le sodium (en mg)."""
    return {"criteres": ["su", "sodium"], "poids": {"su": 0.5, "sodium": 0.5}, "lam": 0.6,
            "sens": {"su": "min", "sodium": "min"},
            "profils": [{"su": 20, "sodium": 800}, {"su": 15, "sodium": 600}, {"su": 10, "sodium": 400}, {"su": 5, "sodium": 200}]}


def test_leur_modele_lit_le_sodium_de_nos_plats_dans_le_sel():
    """Nos plats donnent le sel, en g ; leur modèle lit le sodium, en mg : 1 g de sel, c'est 400 mg de sodium."""
    plat = dict(platAuNiveauDeAPrime(), so=0.4)
    assert sn.avecLeSodium(plat)["sodium"] == pytest.approx(160)
    assert sn.avecLeSodium(dict(plat, sodium=90))["sodium"] == 90            # un sodium donné est gardé


def test_l_analyse_de_l_autre_groupe_compare_les_deux_bases():
    """Leurs produits et nos plats, chacun rangé par les deux modèles ; le recoupement des deux bases, et un exemple par base."""
    leurs = [dict(platAuNiveauDeAPrime(), code="1", nom="Muesli", label="A", leurClasse="A", sodium=80, categorie="general"),
             dict(platAuNiveauDeAPrime(), code="2", nom="Pétales", label="C", leurClasse="D", su=18, sodium=700)]
    nos = [dict(platAuNiveauDeAPrime(), code="3", nom="Poêlée", label="B"),
           dict(platAuNiveauDeAPrime(), code="2", nom="Même code", label="A")]
    analyse = sn.analyseAutreGroupe(leurs, {"9": "absent"}, leurModeleJouet(), nos, exemples=("1", "3"))
    assert analyse["reproduits"] == 2 and analyse["total"] == 2 and analyse["manques"] == ["9"]
    assert analyse["recoupement"] == [1, 50.0]
    assert analyse["leurs"]["total"] == 2 and analyse["nos"]["total"] == 2
    assert analyse["types"] == {"general": 1, "inconnu": 1}
    assert [(e["code"], e["base"]) for e in analyse["exemples"]] == [("1", "leurs"), ("3", "nos")]
    assert analyse["exemples"][0]["leur"] == "A′" and analyse["exemples"][0]["notre"] == "A′"
    assert analyse["exemples"][0]["proteinesComptees"]                # 15 g de protéines, peu de points négatifs


def test_l_excel_de_l_autre_groupe_a_trois_feuilles(tmp_path):
    """Leurs produits rangés par les deux modèles, nos plats rangés par leur modèle, et la comparaison."""
    leurs = [dict(platAuNiveauDeAPrime(), code="1", nom="Muesli", label="A", leurClasse="A", sodium=80)]
    nos = [dict(platAuNiveauDeAPrime(), code="3", nom="Poêlée", label="B")]
    analyse = sn.analyseAutreGroupe(leurs, {}, leurModeleJouet(), nos, exemples=("1", "3"))
    chemin = tmp_path / "autre.xlsx"
    sn.ecrireAutreGroupe(leurs, nos, analyse, leurModeleJouet(), chemin)
    classeur = openpyxl.load_workbook(chemin)
    assert classeur.sheetnames == ["leurs produits", "nos plats", "comparaison"]
    entetes = [cellule.value for cellule in classeur["leurs produits"][1]]
    assert {"Nutri-Score", "Leur SuperNutri-score", "Notre SuperNutri-score", "Additifs à risque"} <= set(entetes)
    assert classeur["nos plats"].max_row == 2


def test_ce_qui_empeche_un_produit_de_monter():
    """Le plat qui rate toute la transformation, avec 400 kJ (au-dessus des 335 kJ de A′) : B′, car face à A′ il rate cinq critères."""
    plat = dict(platAuBordDeAPrime(), en=400)
    detail = sn.rateAuDessus(sn.valeursDuPlat(plat), sn.MODELE_SUPER)
    assert detail["rates"] == ["en", "nova", "additifs", "aRisque", "bio"]
    assert detail["poids"] == pytest.approx(sn.MODELE_SUPER["poids"]["en"] + 0.30)
    assert sn.rateAuDessus(sn.valeursDuPlat(platAuNiveauDeAPrime()), sn.MODELE_SUPER) is None


def test_les_produits_secs_en_a_prime():
    """Un couscous sec (1 500 kJ pour 100 g) peut rester en A′ : la liste des produits secs en A′ le nomme, pas la purée."""
    sec = dict(platAuNiveauDeAPrime(), en=1500, code="1", nom="Couscous", label="A")
    frais = dict(platAuNiveauDeAPrime(), code="2", nom="Purée", label="A")
    assert sn.produitsSecsEnAPrime([sec, frais]) == ["Couscous"]


# --- Plus sévère ou plus permissif que la référence (26/11) ---

def test_le_sens_des_ecarts_d_une_matrice():
    """Lignes : la référence (A à E) ; colonnes : le modèle (A′ à E′). À droite de la diagonale, le modèle range plus bas."""
    matrice = [[2, 1, 0, 0, 0],          # deux A restent en A′, un A descend en B′
               [1, 0, 0, 0, 1],          # un B monte en A′, un B descend de trois classes, en E′
               [0] * 5, [0] * 5, [0] * 5]
    assert sn.sensDesEcarts(matrice) == {"plusSevere": 0.4, "pareil": 0.4, "plusPermissif": 0.2,
                                         "ecartMoyen": pytest.approx(3 / 5)}


def test_pourquoi_un_plat_descend_et_pourquoi_un_autre_monte():
    """
    Un plat A au Nutri-Score, sans fibres, salé et ultra-transformé, descend en C′. Un plat très salé (5 g de sel, 20 points)
    que le Nutri-Score classe E monte : MR-Sort, sans veto, ne lui retire que la case du sel.
    """
    descend = dict(platAuNiveauDeAPrime(), code="1", nom="Descend", label="A", fi=1.0, so=1.0, nova=4, bio="non")
    monte = dict(platAuNiveauDeAPrime(), code="2", nom="Monte", label="E", so=5.0)
    ecarts = sn.ecartsAuNutriscore([descend, monte])
    assert (ecarts["descendent"], ecarts["montent"]) == (1, 1)
    assert ecarts["descentesParLabel"]["A"]["plats"] == 1
    assert set(ecarts["descentesParLabel"]["A"]["raisons"]) == {"so", "fi", "nova", "bio"}
    assert ecarts["montees"]["chargees"] == 1 and ecarts["montees"]["raisons"]["so"] == 1


def test_chaque_comparaison_dit_son_sens():
    """Les deux modèles face au Nutri-Score, et le nôtre face au leur : chacun avec ses parts plus sévère et plus permissive."""
    leur = {"criteres": ["su", "fi"], "poids": {"su": 0.5, "fi": 0.5}, "lam": 0.6, "sens": {"su": "min", "fi": "max"},
            "profils": [{"su": 20, "fi": 1}, {"su": 15, "fi": 2}, {"su": 10, "fi": 3}, {"su": 5, "fi": 6}]}
    plats = [dict(platAuNiveauDeAPrime(), code="1", nom="Bon", label="B", leurClasse="A")]
    resultat = sn.comparerDeuxModeles(plats, leur)
    assert resultat["notreFaceAuNutriscore"]["sens"]["plusPermissif"] == 1          # A′ pour un plat B
    assert resultat["notreFaceALeur"]["sens"]["pareil"] == 1


# --- La transformation des plats : NOVA et additifs à risque (26/11) ---

def test_la_transformation_des_plats():
    """Les plats de chaque groupe NOVA, les plats bio, sans additif, et ceux qui ont un additif à risque, famille par famille."""
    plats = [dict(platAuNiveauDeAPrime(), code="1", nova=3, additifs=0, listeAdditifs=None, bio="oui"),
             dict(platAuNiveauDeAPrime(), code="2", nova=4, additifs=2, listeAdditifs="E250, E452", bio="non"),
             dict(platAuNiveauDeAPrime(), code="3", nova=4, additifs=1, listeAdditifs="E407", bio="non")]
    transformation = sn.transformationDesPlats(plats, exemples=("2",))
    assert transformation["nova"] == {"1": 0, "2": 0, "3": 1, "4": 2}
    assert (transformation["bio"], transformation["sansAdditif"], transformation["avecARisque"]) == (1, 1, 2)
    assert transformation["familles"] == {"nitrites et nitrates": 1, "phosphates": 1, "carraghénanes": 1}
    assert [(e["code"], e["aRisque"], e["listeAdditifs"]) for e in transformation["exemples"]] == [("2", 2, "E250, E452")]


def test_chaque_famille_d_additifs_a_risque_a_sa_raison():
    assert set(sn.RAISONS_DES_ADDITIFS_A_RISQUE) == set(sn.ADDITIFS_A_RISQUE)
    assert sorted(sn.GROUPES_NOVA) == [1, 2, 3, 4]


@pytest.mark.skipif(not projet_base.FICHIER_BASE_ETENDUE.exists(), reason="la base étendue n'est pas construite")
def test_les_deux_exemples_de_la_transformation_sont_dans_la_base():
    """La Poêlée Fermière : NOVA 4, trois additifs, aucun à risque. La pizza Regina : le nitrite (E250) et un polyphosphate (E452)."""
    transformation = sn.transformationDesPlats(projet_base.lireBase(projet_base.FICHIER_BASE_ETENDUE))
    poelee, regina = transformation["exemples"]
    assert (poelee["nom"], poelee["nova"], poelee["additifs"], poelee["aRisque"]) == ("Poêlée Fermière", 4, 3, 0)
    assert (regina["nom"], regina["marque"], regina["aRisque"]) == ("Regina", "Buitoni", 2)
    assert {250, 452} <= sn.numerosDesAdditifs(regina["listeAdditifs"])
