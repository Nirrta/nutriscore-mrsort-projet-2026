"""Tests des figures (diagramme des profils, matrice de confusion, entonnoir)."""

import projet_figures as fg


MODELE = {
    "criteres": ["en", "so", "fr"], "poids": {"en": 0.3, "so": 0.5, "fr": 0.2}, "lam": 0.6,
    "profils": [{"en": 1100, "so": 1.6, "fr": 5}, {"en": 900, "so": 1.2, "fr": 15},
                {"en": 700, "so": 0.9, "fr": 30}, {"en": 500, "so": 0.6, "fr": 50}],
}


def test_le_mieux_est_toujours_en_haut():
    """Sur un critère à minimiser (le sel), moins de sel place le plat plus haut ; sur les fruits, c'est l'inverse."""
    etendues = {"so": (0, 2), "fr": (0, 100)}
    assert fg.positionSurLAxe(0.2, "so", etendues, MODELE) > fg.positionSurLAxe(1.8, "so", etendues, MODELE)
    assert fg.positionSurLAxe(80, "fr", etendues, MODELE) > fg.positionSurLAxe(10, "fr", etendues, MODELE)
    assert fg.positionSurLAxe(5, "so", etendues, MODELE) == 0          # hors de l'axe : posé sur le bord


def test_etendues_de_la_base():
    """Les axes vont du 5e au 95e centile : un plat extrême ne tasse pas l'échelle."""
    plats = [{"so": valeur} for valeur in [0.1 * k for k in range(21)] + [9.0]]
    bas, haut = fg.etenduesDeLaBase(plats, ["so"])["so"]
    assert bas == 0.1 and haut < 9.0


def test_les_figures_s_ecrivent(tmp_path):
    """Les trois figures s'écrivent en PNG."""
    fg.figureProfils(MODELE, {"en": 650, "so": 1.0, "fr": 45}, tmp_path / "profils.png", nomDuPlat="Taboulé")
    fg.figureMatriceConfusion([[5, 1, 0, 0, 0], [1, 4, 1, 0, 0], [0, 1, 4, 1, 0], [0, 0, 1, 4, 1], [0, 0, 0, 1, 5]],
                              tmp_path / "matrice.png", titre="Essai, λ = 0,6")
    fg.figureEntonnoir({"candidats repérés": 100, "sans doublon": 40}, tmp_path / "entonnoir.png")
    for nom in ("profils.png", "matrice.png", "entonnoir.png"):
        assert (tmp_path / nom).stat().st_size > 10_000


def test_la_courbe_d_apprentissage_s_ecrit(tmp_path):
    """La courbe d'apprentissage, à 7 et à 3 critères, s'écrit en PNG."""
    courbe = {nom: [{"taille": taille, "appris": 0.9 - taille / 1000, "tenusAPart": 0.5 + taille / 1000, "ecartType": 0.05}
                    for taille in (25, 125, 300)] for nom in ("sept", "trois")}
    fg.figureCourbe(courbe, tmp_path / "courbe.png", titre="Essai")
    assert (tmp_path / "courbe.png").stat().st_size > 10_000


def test_les_figures_ne_cherchent_pas_une_graisse_absente(tmp_path, caplog):
    """Archivo Condensed n'existe qu'en graisse 800 : les figures la demandent ainsi, sans avertissement de matplotlib."""
    import logging

    with caplog.at_level(logging.WARNING):
        fg.figureProfils(MODELE, {"en": 650, "so": 1.0, "fr": 45}, tmp_path / "profils.png")
        courbe = {nom: [{"taille": t, "appris": 0.8, "tenusAPart": 0.6, "ecartType": 0.05} for t in (25, 300)]
                  for nom in ("sept", "trois")}
        fg.figureCourbe(courbe, tmp_path / "courbe.png", titre="Essai")
    assert not [r.getMessage() for r in caplog.records if "findfont" in r.getMessage()]
