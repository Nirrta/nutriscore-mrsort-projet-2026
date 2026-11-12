"""Tests de l'apprentissage des paramètres de MR-Sort (question 3.3)."""

import json
import time
from types import SimpleNamespace

import pytest

import projet_apprentissage as ap
import projet_base
import projet_mrsort as mr


CRITERES = ["g1", "g2", "g3"]
SENS = {critere: "max" for critere in CRITERES}


def plat(g1, g2, g3):
    """Un produit des annexes, évalué sur g1, g2 et g3."""
    return {"g1": g1, "g2": g2, "g3": g3}


def test_poids_de_l_annexe_B():
    """
    Annexe B : avec b = (5, 5, 5) et λ = 0,6, il faut w1 + w2 ≥ 0,6, w2 + w3 < 0,6 et
    w1 + w3 ≥ 0,6. Le programme trouve des poids qui rangent bien les trois produits.
    """
    produits = [plat(6, 6, 3), plat(3, 6, 6), plat(6, 3, 6)]
    classes = [1, 0, 1]
    modele = {"criteres": CRITERES, "profils": [plat(5, 5, 5)], "lam": 0.6, "sens": SENS, "poids": {}}
    resultat = ap.apprendrePoids(produits, classes, modele)
    w = resultat["modele"]["poids"]
    assert resultat["bienRanges"] == resultat["optimum"] == 3
    assert abs(sum(w.values()) - 1) < 1e-9
    assert w["g1"] + w["g2"] >= 0.6 - 1e-9
    assert w["g2"] + w["g3"] <= 0.6 - mr.EPSILON + 1e-9
    assert w["g1"] + w["g3"] >= 0.6 - 1e-9


def test_poids_quand_aucun_modele_exact_n_existe():
    """
    Deux produits identiques rangés dans deux classes différentes : un seul peut être bien
    rangé, et le programme le dit.
    """
    produits = [plat(6, 6, 6), plat(6, 6, 6), plat(1, 1, 1)]
    modele = {"criteres": CRITERES, "profils": [plat(5, 5, 5)], "lam": 0.6, "sens": SENS, "poids": {}}
    resultat = ap.apprendrePoids(produits, [1, 0, 0], modele)
    assert resultat["optimum"] == resultat["bienRanges"] == 2


def test_les_poids_sont_arrondis_au_millieme():
    """Les poids appris ont au plus trois décimales et font exactement 1."""
    produits = [plat(6, 6, 3), plat(3, 6, 6), plat(6, 3, 6)]
    modele = {"criteres": CRITERES, "profils": [plat(5, 5, 5)], "lam": 0.6, "sens": SENS, "poids": {}}
    poids = ap.apprendrePoids(produits, [1, 0, 1], modele)["modele"]["poids"]
    assert all(round(valeur, 3) == valeur for valeur in poids.values())
    assert round(sum(poids.values()), 9) == 1


def test_profils_par_medianes():
    """
    Deux classes : sur g1, médianes 2 et 8, donc profil 5. Le profil suivant ne peut pas
    être moins bon que le précédent : l'ordre est imposé même si les médianes reculent.
    """
    produits = [plat(1, 1, 1), plat(3, 3, 3), plat(7, 9, 2), plat(9, 9, 2), plat(9, 1, 9)]
    classes = [0, 0, 1, 1, 2]
    profils = ap.profilsParMedianes(produits, classes, CRITERES, SENS)
    assert profils[0] == {"g1": 5, "g2": 5.5, "g3": 2}
    assert profils[1]["g1"] == (8 + 9) / 2
    assert profils[1]["g3"] == (2 + 9) / 2
    assert profils[1]["g2"] == 5.5          # (9 + 1) / 2 = 5 reculerait : on garde la valeur de b2
    for critere in CRITERES:
        assert profils[1][critere] >= profils[0][critere]


# --- Les poids possibles, et le départage par la plus grande marge ---

def test_intervalles_des_poids_de_l_annexe_B():
    """
    Annexe B : parmi les poids qui rangent bien les trois produits (w1 + w2 ≥ 0,6,
    w2 + w3 ≤ 0,6 − ε, w1 + w3 ≥ 0,6), w1 va de 0,401 à 1, et w2 comme w3 de 0 à 0,4.
    """
    produits = [plat(6, 6, 3), plat(3, 6, 6), plat(6, 3, 6)]
    modele = {"criteres": CRITERES, "profils": [plat(5, 5, 5)], "lam": 0.6, "sens": SENS, "poids": {}}
    intervalles = ap.intervallesDesPoids(produits, [1, 0, 1], modele, optimum=3)
    for critere, (bas, haut) in {"g1": (0.401, 1), "g2": (0, 0.4), "g3": (0, 0.4)}.items():
        assert intervalles[critere][0] == pytest.approx(bas, abs=1e-6)
        assert intervalles[critere][1] == pytest.approx(haut, abs=1e-6)


def test_le_departage_par_la_marge_garde_l_optimum():
    """
    Annexe B : le départage par la plus grande marge range toujours bien les trois produits, avec
    une marge au moins égale à celle du solveur. Ici, g1 décide seul : sa marge vaut 0,4.
    """
    produits = [plat(6, 6, 3), plat(3, 6, 6), plat(6, 3, 6)]
    classes = [1, 0, 1]
    modele = {"criteres": CRITERES, "profils": [plat(5, 5, 5)], "lam": 0.6, "sens": SENS, "poids": {}}
    solveur = ap.apprendrePoids(produits, classes, modele)
    marge = ap.apprendrePoids(produits, classes, modele, departage="marge")
    assert marge["bienRanges"] == solveur["bienRanges"] == 3
    assert marge["marge"] >= solveur["marge"]
    assert marge["marge"] == pytest.approx(0.4) == ap.margeDuModele(produits, classes, marge["modele"])
    assert marge["modele"]["poids"] == {"g1": 1, "g2": 0, "g3": 0}


@pytest.mark.skipif(not projet_base.FICHIER_RESULTATS.exists() or not projet_base.FICHIER_BASE.exists(),
                    reason="la base et les résultats ne sont pas encore construits")
def test_le_poids_des_ags_n_est_indispensable_qu_a_0_7():
    """
    Sur la base, à 7 critères : parmi les modèles qui rangent bien 90 plats, le plus petit poids
    des AGS dépasse 1 − λ à λ = 0,7 (aucun profil n'est franchi sans eux), mais pas à λ = 0,6.
    L'intervalle des AGS du JSON est celui que l'on recalcule, et les intervalles du JSON
    contiennent les poids du solveur.
    """
    plats = projet_base.lireBase()
    classes = [mr.classeDuLabel(p["label"]) for p in plats]
    resultats = json.loads(projet_base.FICHIER_RESULTATS.read_text(encoding="utf-8"))
    sept = [m for m in resultats["mrsort"]["modeles"] if m["nom"] == "sept" and m["mode"] == "poids"]
    assert sorted(m["lam"] for m in sept) == [0.6, 0.7]
    for modele in sept:
        regle = {"criteres": modele["criteres"], "profils": modele["profils"], "lam": modele["lam"], "poids": {}}
        bas, haut = ap.intervallesDesPoids(plats, classes, regle, modele["bienRanges"], criteres=["sa"])["sa"]
        assert (bas > 1 - modele["lam"]) == (modele["lam"] == 0.7)
        assert modele["intervalles"]["sa"] == [round(bas, 3), round(haut, 3)]
        for critere in modele["criteres"]:
            minimum, maximum = modele["intervalles"][critere]
            assert minimum - 1e-3 <= modele["poids"][critere] <= maximum + 1e-3


def test_l_arrondi_ne_laisse_pas_de_zero_negatif():
    """Un poids que le solveur rend à −0,000000001 s'arrondit à 0, et non à −0 (qui s'afficherait « −0,0000 »)."""
    import math

    produits = [plat(6, 6, 3), plat(3, 6, 6), plat(6, 3, 6)]
    modele = {"criteres": CRITERES, "profils": [plat(5, 5, 5)], "lam": 0.6, "sens": SENS,
              "poids": {"g1": 0.45, "g2": 0.25, "g3": 0.30}}
    modele["poids"] = {"g1": 0.70000000001, "g2": -1e-12, "g3": 0.3}
    arrondi = ap.arrondirPoids(modele, produits, [1, 0, 1])
    assert all(math.copysign(1, valeur) > 0 for valeur in arrondi["poids"].values()), arrondi["poids"]


# --- Phase 2 : les poids fixés par les points maximaux, les profils appris (annexe C) ---

def test_poids_des_points_max():
    """Les poids fixés sont les points maximaux du Nutri-Score, ramenés à une somme de 1."""
    sept = ap.poidsDesPointsMax(mr.CRITERES_SEPT)
    assert sept == {"en": 10 / 72, "sa": 10 / 72, "su": 15 / 72, "so": 20 / 72, "pr": 7 / 72, "fi": 5 / 72, "fr": 5 / 72}
    assert ap.poidsDesPointsMax(mr.CRITERES_TROIS) == {"en": 10 / 35, "so": 20 / 35, "fr": 5 / 35}


def test_seuils_candidats():
    """Un peu sous la plus petite valeur, le milieu de deux valeurs voisines, un peu au-dessus de la plus grande."""
    assert ap.seuilsCandidats([5, 2, 8, 5]) == [1, 3.5, 6.5, 9]
    assert ap.seuilsCandidats([4, 4]) == [3, 5]


def test_profils_de_l_annexe_C():
    """
    Annexe C : w = (0,7 ; 0,2 ; 0,1), λ = 0,6, a = (2, 4, 5) en C1, b = (5, 4, 5) en C2,
    c = (8, 4, 5) en C3. Il faut 2 < g1(b2) ≤ 5 et 5 < g1(b3) ≤ 8 : le programme prend le
    milieu entre les plats voisins, 3,5 et 6,5, et range bien les trois produits.
    """
    produits = [plat(2, 4, 5), plat(5, 4, 5), plat(8, 4, 5)]
    modele = {"criteres": CRITERES, "poids": {"g1": 0.7, "g2": 0.2, "g3": 0.1}, "lam": 0.6, "sens": SENS}
    resultat = ap.apprendreProfils(produits, [0, 1, 2], modele)
    profils = resultat["modele"]["profils"]
    assert resultat["bienRanges"] == resultat["optimum"] == 3 and resultat["optimal"]
    assert [profil["g1"] for profil in profils] == [3.5, 6.5]
    assert [mr.affecter(p, resultat["modele"])["classe"] for p in produits] == [0, 1, 2]


def test_les_profils_appris_restent_ordonnes():
    """Sur des plats fictifs, chaque profil appris est au moins aussi bon que le précédent, sur chaque critère."""
    produits = [plat(1 + k + i, 9 - k - i, 3 + k) for k in range(4) for i in range(2)]
    classes = [k for k in range(4) for i in range(2)]
    modele = {"criteres": CRITERES, "poids": {"g1": 0.5, "g2": 0.3, "g3": 0.2}, "lam": 0.6,
              "sens": {"g1": "max", "g2": "min", "g3": "max"}}
    resultat = ap.apprendreProfils(produits, classes, modele)
    profils = resultat["modele"]["profils"]
    for bas, haut in zip(profils, profils[1:]):
        assert haut["g1"] >= bas["g1"] and haut["g2"] <= bas["g2"] and haut["g3"] >= bas["g3"]
    assert resultat["bienRanges"] == resultat["optimum"]


# --- Phase 2 : le modèle complet (poids, profils et λ appris) ---

def test_le_modele_complet_trouve_un_modele_exact_quand_il_existe():
    """
    Annexe B, poids, profil et λ inconnus : un modèle range exactement les trois produits ;
    le programme le trouve, et dit qu'un modèle exact existe.
    """
    produits = [plat(6, 6, 3), plat(3, 6, 6), plat(6, 3, 6)]
    resultat = ap.apprendreModeleComplet(produits, [1, 0, 1], CRITERES, sens=SENS, exact=True)
    assert resultat["existe"] is True and resultat["bienRanges"] == 3
    assert 0.5 < resultat["modele"]["lam"] <= 1 and abs(sum(resultat["modele"]["poids"].values()) - 1) < 1e-9


def test_le_modele_complet_prouve_qu_aucun_modele_exact_n_existe():
    """
    Un plat meilleur qu'un autre sur tous les critères, mais rangé plus bas : MR-Sort est
    monotone, aucun modèle ne peut ranger les deux. Le solveur le prouve.
    """
    produits = [plat(6, 6, 6), plat(1, 1, 1)]
    resultat = ap.apprendreModeleComplet(produits, [0, 1], CRITERES, sens=SENS, exact=True)
    assert resultat["existe"] is False and resultat["modele"] is None


def test_le_modele_complet_range_au_moins_aussi_bien():
    """Sans exiger l'exactitude, le modèle complet range au moins autant de plats qu'un modèle à poids fixés."""
    produits = [plat(1 + k + i, 9 - k - i, 3 + (k + i) % 3) for k in range(3) for i in range(3)]
    classes = [k for k in range(3) for i in range(3)]
    sens = {"g1": "max", "g2": "min", "g3": "max"}
    fixes = ap.apprendreProfils(produits, classes, {"criteres": CRITERES, "poids": {"g1": 0.4, "g2": 0.4, "g3": 0.2},
                                                    "lam": 0.6, "sens": sens})
    complet = ap.apprendreModeleComplet(produits, classes, CRITERES, sens=sens)
    assert complet["bienRanges"] >= fixes["bienRanges"] and complet["optimal"]


def test_l_alternance_garde_le_meilleur_modele():
    """
    Le modèle complet par alternance : profils appris à poids fixés, puis poids appris sur
    ces profils, et ainsi de suite tant que ça progresse. Il garde le meilleur modèle de
    l'historique, et range au moins autant de plats que les profils appris seuls.
    """
    produits = [plat(1 + k + (i % 2), 8 - k - i, 3 + (k * i) % 4) for k in range(3) for i in range(4)]
    classes = [k for k in range(3) for i in range(4)]
    sens = {"g1": "max", "g2": "min", "g3": "max"}
    poids = {"g1": 0.2, "g2": 0.2, "g3": 0.6}
    resultat = ap.apprendreParAlternance(produits, classes, CRITERES, 0.6, poids=poids, sens=sens)
    seuls = ap.apprendreProfils(produits, classes, {"criteres": CRITERES, "poids": poids, "lam": 0.6, "sens": sens})
    assert resultat["bienRanges"] == max(resultat["historique"]) >= seuls["bienRanges"]
    assert resultat["bienRanges"] == ap.nombreBienRanges(produits, classes, resultat["modele"])
    assert resultat["historique"][0] == seuls["bienRanges"]


# --- La mise en veille pendant un calcul ---


def solveurSimule(statuts, appels, dureeDeCalcul=0.0):
    """
    Remplace milp : à chaque appel, calcule dureeDeCalcul secondes, puis renvoie une solution
    du statut suivant de `statuts` (1 : arrêt sur la limite de temps, 0 : optimum trouvé).
    `appels` reçoit la limite de temps de chaque appel.
    """
    def solveur(c, constraints, integrality, bounds, options):
        appels.append(options["time_limit"])
        time.sleep(dureeDeCalcul)
        return SimpleNamespace(status=statuts[len(appels) - 1], x=None)
    return solveur


def test_un_calcul_coupe_par_la_veille_est_recommence(monkeypatch):
    """
    L'horloge de HiGHS compte la veille : Mac fermé, le solveur atteint sa limite sans avoir
    calculé. time.perf_counter, qui ne compte pas la veille, le montre : on recommence.
    """
    appels = []
    monkeypatch.setattr(ap, "milp", solveurSimule([1, 0], appels))
    solution = ap.resoudreCreux([1.0], [{0: 1.0}], [0.0], [1.0], [1], ([0.0], [1.0]), 60)
    assert appels == [60, 60]
    assert solution.status == 0


def test_un_calcul_arrete_sur_sa_limite_n_est_pas_recommence(monkeypatch):
    """Si le solveur a vraiment calculé jusqu'à sa limite, on garde sa solution."""
    appels = []
    monkeypatch.setattr(ap, "milp", solveurSimule([1, 0], appels, dureeDeCalcul=0.05))
    solution = ap.resoudreCreux([1.0], [{0: 1.0}], [0.0], [1.0], [1], ([0.0], [1.0]), 0.05)
    assert appels == [0.05]
    assert solution.status == 1
