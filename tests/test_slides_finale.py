"""Tests des slides de la soutenance finale (27/11) : le SuperNutri-score, ses analyses et l'interface."""

import json

import pytest

import projet_base
import slides_projet


def resultatsDuSuperNutri():
    """Le JSON des résultats, s'il contient le SuperNutri-score ; sinon None."""
    if not projet_base.FICHIER_RESULTATS.exists():
        return None
    resultats = json.loads(projet_base.FICHIER_RESULTATS.read_text(encoding="utf-8"))
    return resultats if "supernutri" in resultats else None


@pytest.fixture(scope="module")
def slides(tmp_path_factory):
    """Les slides de la soutenance finale, écrites une seule fois pour les tests qui suivent."""
    if resultatsDuSuperNutri() is None or not projet_base.FICHIER_BASE.exists():
        pytest.skip("le SuperNutri-score n'est pas encore calculé")
    from pptx import Presentation

    chemin = tmp_path_factory.mktemp("finale") / "soutenance_finale.pptx"
    slides_projet.slidesSoutenance2(chemin)
    return Presentation(chemin)


def texteDeLaSlide(diapo):
    """Tous les textes d'une slide, mis bout à bout."""
    return " ".join(forme.text_frame.text for forme in diapo.shapes if forme.has_text_frame and forme.text_frame.text)


def test_onze_slides_sans_debordement(slides):
    """Onze slides ; la génération se serait arrêtée si un titre ou un texte débordait."""
    assert len(slides.slides) == 11


def test_le_pied_de_page_dit_la_soutenance_finale(slides):
    assert "Projet MR-Sort, soutenance finale" in texteDeLaSlide(slides.slides[1])


def test_les_notes_reprennent_le_texte_de_l_oral_final(slides):
    """Les notes de chaque slide : l'orateur et la durée, puis tout le texte à dire, tirés de texte_soutenance_2.md."""
    from projet_soutenance import TEXTES_ORAUX, slidesDuTexte

    oral = slidesDuTexte(TEXTES_ORAUX[2])
    assert len(oral) == len(slides.slides)
    for diapo, slide in zip(slides.slides, oral):
        notes = diapo.notes_slide.notes_text_frame.text
        assert notes.startswith(f"{slide['orateur']}, {slide['duree'] // 60} min")
        assert all(paragraphe in notes for paragraphe in slide["texte"])


def test_la_slide_5_suit_la_poelee_fermiere(slides):
    """B au Nutri-Score, C′ au SuperNutri-score ; NOVA 3 et un seul additif la feraient monter en B′."""
    texte = texteDeLaSlide(slides.slides[4])
    assert "Poêlée Fermière : B au Nutri-Score, C′ au SuperNutri-score" in texte
    assert "B′" in texte


def test_la_slide_6_compte_les_plats_qui_montent_et_descendent(slides):
    ecarts = resultatsDuSuperNutri()["supernutri"]["etendue"]["ecarts"]
    assert f"{ecarts['descendent']} plats descendent, {ecarts['montent']} montent" in texteDeLaSlide(slides.slides[5])


def test_la_slide_7_cite_les_tirages(slides):
    """La part moyenne de plats qui changent, pour chaque amplitude des tirages, et les plats au bord."""
    sensibilite = resultatsDuSuperNutri()["supernutri"]["sensibilite"]["etendue"]
    texte = texteDeLaSlide(slides.slides[6])
    for point in sensibilite["courbe"]:
        assert slides_projet.pourcentage(point["partMoyenne"], 1) in texte
    assert f"{len(sensibilite['auBord'])} plats" in texte


def test_la_slide_8_cite_les_decalages_les_plus_actifs(slides):
    profils = resultatsDuSuperNutri()["supernutri"]["sensibilite"]["etendue"]["profils"]
    plusActif = max(profils["scenarios"], key=lambda scenario: scenario["plats"])
    assert str(plusActif["plats"]) in texteDeLaSlide(slides.slides[7])
