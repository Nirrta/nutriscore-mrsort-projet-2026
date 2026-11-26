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


def test_douze_slides_sans_debordement(slides):
    """Douze slides ; la génération se serait arrêtée si un titre ou un texte débordait."""
    assert len(slides.slides) == 12


def test_la_slide_2_dit_la_regle_des_proteines(slides):
    assert "ne votent que si le Nutri-Score les compte" in texteDeLaSlide(slides.slides[1])


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
    assert slides_projet.typographie("Poêlée Fermière : B au Nutri-Score, C′ au SuperNutri-score") in texte
    assert "B′" in texte


def test_la_slide_6_compte_les_plats_qui_montent_et_descendent(slides):
    """Plus sévère que le Nutri-Score ; ceux qui montent sont chargés en points négatifs, et MR-Sort n'a pas de veto."""
    ecarts = resultatsDuSuperNutri()["supernutri"]["etendue"]["ecarts"]
    texte = texteDeLaSlide(slides.slides[5])
    assert slides_projet.typographie(f"Plus sévère que le Nutri-Score : {ecarts['descendent']} plats descendent, "
                                     f"{ecarts['montent']} montent") in texte
    assert f"{ecarts['montees']['chargees']} ont au moins 11 points négatifs" in texte and "sans veto" in texte


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


def test_la_slide_8_nomme_des_plats_qui_changent(slides):
    """Le sujet demande d'identifier les produits qui changent : la slide en nomme trois, sous le décalage le plus actif."""
    profils = resultatsDuSuperNutri()["supernutri"]["sensibilite"]["etendue"]["profils"]
    plusActif = max(profils["scenarios"], key=lambda scenario: scenario["plats"])
    noms = [plat["nom"] for plat in profils["plats"] if plat["code"] in plusActif["codes"]]
    texte = texteDeLaSlide(slides.slides[7])
    assert sum(1 for nom in noms if nom in texte) == 3


def autreGroupe():
    """La comparaison avec l'autre groupe, dans le JSON."""
    autre = resultatsDuSuperNutri()["supernutri"].get("autreGroupe")
    if autre is None:
        pytest.skip("la base de l'autre groupe n'est pas encore comparée")
    return autre


def test_la_slide_9_croise_les_deux_modeles_et_les_deux_bases(slides):
    """
    Pour chaque base, chaque modèle face au Nutri-Score, puis le nôtre face au leur : la part des produits dans la même
    classe, plus sévère, plus permissive. Puis les écarts moyens, et leurs classes redonnées.
    """
    autre = autreGroupe()
    texte = texteDeLaSlide(slides.slides[8])
    for base in ("leurs", "nos"):
        for cle in ("notreFaceAuNutriscore", "leurFaceAuNutriscore", "notreFaceALeur"):
            for mesure in ("pareil", "plusSevere", "plusPermissif"):
                assert slides_projet.pourcentage(autre[base][cle]["sens"][mesure], 1) in texte, (base, cle, mesure)
            assert autre[base][cle]["sens"]["pareil"] == pytest.approx(autre[base][cle]["exactitude"])
    for base, cle in (("nos", "notreFaceAuNutriscore"), ("leurs", "leurFaceAuNutriscore"),
                      ("leurs", "notreFaceAuNutriscore"), ("nos", "leurFaceAuNutriscore")):
        assert slides_projet.ecartSigne(autre[base][cle]["sens"]["ecartMoyen"]) in texte, (base, cle)
    assert f"redonne leurs {autre['reproduits']} classes" in texte


def test_la_slide_10_montre_ce_qui_bloque_chaque_modele(slides):
    """Ce que chaque modèle rate le plus souvent sur la base de l'autre, au seuil de B′, et un produit de chaque base."""
    autre = autreGroupe()
    texte = texteDeLaSlide(slides.slides[9])
    for base, modele in (("leurs", "notre"), ("nos", "leur")):
        critere, part = max(autre[base]["bloquants"][modele].items(), key=lambda paire: paire[1])
        assert slides_projet.pourcentage(part) in texte, (base, critere)
    for exemple in autre["exemples"]:
        assert exemple["nom"] in texte


def test_aucun_signe_double_ne_commence_une_ligne():
    """Une espace insécable avant « ; », « : », « ? », « ! » et « % », et dans les guillemets ; l'apostrophe typographique."""
    assert slides_projet.typographie("au bord ; à 0,05 : 11,5 % « oui » l'eau ?") == \
        "au bord ; à 0,05 : 11,5 % « oui » l’eau ?"


def test_la_conclusion_dit_la_severite_et_les_limites(slides):
    """Plus sévère que le Nutri-Score sur nos plats et sur leurs céréales ; sans veto ; les produits secs en A′."""
    resultats = resultatsDuSuperNutri()["supernutri"]
    texte = texteDeLaSlide(slides.slides[11])
    ecarts = resultats["etendue"]["ecarts"]
    assert f"{ecarts['descendent']} descendent, surtout en haut, et {ecarts['montent']} montent" in texte
    assert "sans veto" in texte.lower()
    assert f"{len(resultats['etendue']['secsEnAPrime'])} de nos {resultats['etendue']['repartition']['A′']} plats A′" in texte
