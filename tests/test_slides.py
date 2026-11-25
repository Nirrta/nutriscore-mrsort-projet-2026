"""Tests des slides de la soutenance intermédiaire."""

import json

import pytest

import projet_base
import slides_projet


def resultatsComplets():
    """Vrai si la base, la vérification du Nutri-Score et les modèles MR-Sort sont dans le JSON."""
    if not projet_base.FICHIER_RESULTATS.exists():
        return False
    resultats = json.loads(projet_base.FICHIER_RESULTATS.read_text(encoding="utf-8"))
    return all(cle in resultats for cle in ("base", "nutriscore", "mrsort"))


def test_un_titre_trop_long_arrete_la_generation():
    """Un titre qui ne tient pas sur une ligne arrête la génération."""
    with pytest.raises(ValueError):
        slides_projet.verifierUneLigne("Titre", "Un titre beaucoup trop long " * 6, slides_projet.TITRE, 32, 11.9)


def test_nombres_a_la_francaise():
    """Virgule décimale et espace insécable entre les milliers."""
    assert slides_projet.nombre(1913.5, 1) == "1 913,5"
    assert slides_projet.pourcentage(0.875) == "88 %"


@pytest.fixture(scope="module")
def slides(tmp_path_factory):
    """Les slides de la soutenance intermédiaire, écrites une seule fois pour les tests qui suivent."""
    if not resultatsComplets():
        pytest.skip("les résultats ne sont pas encore calculés")
    from pptx import Presentation

    chemin = tmp_path_factory.mktemp("slides") / "soutenance.pptx"
    slides_projet.slidesSoutenance1(chemin)
    return Presentation(chemin)


def test_les_slides_s_ecrivent_sans_debordement(slides):
    """Dix slides ; la génération se serait arrêtée si un titre ou un texte débordait."""
    assert len(slides.slides) == 10


def textesDeLaSlide(diapo):
    """Les textes non vides d'une slide, dans l'ordre de ses formes."""
    return [forme.text_frame.text for forme in diapo.shapes if forme.has_text_frame and forme.text_frame.text]


def test_les_notes_reprennent_le_texte_de_l_oral(slides):
    """Les notes de chaque slide : l'orateur et la durée, puis tout le texte à dire, tirés de texte_soutenance_1.md."""
    from projet_soutenance import slidesDuTexte

    for diapo, slide in zip(slides.slides, slidesDuTexte()):
        notes = diapo.notes_slide.notes_text_frame.text
        assert notes.startswith(f"{slide['orateur']}, {slide['duree'] // 60} min")
        assert all(paragraphe in notes for paragraphe in slide["texte"])


def test_la_slide_5_calcule_les_exemples_du_sujet(slides):
    """Le tableau des contrôles donne N − P = score pour les fig. 6 et 7, calculés par notre Nutri-Score."""
    from projet_nutriscore import EXEMPLES_SUJET, scoreNutriscore

    textes = textesDeLaSlide(slides.slides[4])
    for exemple in EXEMPLES_SUJET.values():
        calcul = scoreNutriscore(exemple["produit"])
        assert f"{calcul['N']} − {calcul['P']} = {calcul['score']}" in textes


def test_la_slide_6_explique_les_deux_profils_decisifs(slides):
    """La Poêlée Fermière franchit b3 (tout vote pour elle sauf les protéines), mais pas b4 (les acides gras saturés)."""
    textes = textesDeLaSlide(slides.slides[5])
    assert "b3, franchi" in textes and "b4, non franchi" in textes
    assert slides_projet.typographie("Tous les critères votent pour le plat, sauf les protéines : 0,919 ≥ 0,6.") in textes
    assert slides_projet.typographie("Les acides gras saturés ne votent plus : 0,479 < 0,6. Le plat reste en\u00a0C′.") in textes


def couleurDeLaForme(diapo, nom):
    """La couleur de fond (« RRGGBB ») de la forme nommée `nom` sur une slide."""
    forme = [forme for forme in diapo.shapes if forme.name == nom][0]
    return str(forme.fill.fore_color.rgb)


def test_la_slide_2_montre_les_points_negatifs_en_rouge_et_les_positifs_en_vert(slides):
    """Comme les fig. 6 et 7 : un en-tête par groupe avec son total, et des cases pleines rouges (E) ou vertes (A)."""
    from projet_design import COULEUR_NEGATIFS, COULEUR_POSITIFS

    diapo = slides.slides[1]
    textes = textesDeLaSlide(diapo)
    assert "Points négatifs N" in textes and "Points positifs P" in textes
    assert "3 / 55" in textes and "2 / 17" in textes
    assert "score = N − P = 3 − 2 = 1" in textes
    assert couleurDeLaForme(diapo, "Points jauge so 1") == COULEUR_NEGATIFS.lstrip("#")
    assert couleurDeLaForme(diapo, "Points jauge fr 1") == COULEUR_POSITIFS.lstrip("#")
    assert couleurDeLaForme(diapo, "Points repère Points négatifs N") == COULEUR_NEGATIFS.lstrip("#")
    assert couleurDeLaForme(diapo, "Points repère Points positifs P") == COULEUR_POSITIFS.lstrip("#")


def test_les_slides_3_5_et_10_restent_aux_resultats(slides):
    """Ni la règle des 25 %, ni la fig. 4, ni la soupe, ni la déclaration d'IA, ni « Place à vos questions »."""
    for numero, absents in [(2, ["25 %"]), (4, ["soupe", "fig. 4", "Un écart"]), (9, ["déclaration", "questions"])]:
        texte = " ".join(textesDeLaSlide(slides.slides[numero]))
        assert not [absent for absent in absents if absent in texte], numero + 1
    assert "N − P = score" in textesDeLaSlide(slides.slides[4])
    assert "Merci." in textesDeLaSlide(slides.slides[9])


def test_la_quantite_perd_le_e_des_quantites_estimees():
    """« 450 g e » (le ℮ des quantités estimées, recopié par Open Food Facts) s'affiche « 450 g »."""
    assert slides_projet.quantite({"quantite": "450 g e"}) == "450 g"
    assert slides_projet.quantite({"quantite": "1 kg"}) == "1 kg"
