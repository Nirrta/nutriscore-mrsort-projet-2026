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


def formes(diapo, debut):
    """Les formes d'une slide dont le nom commence par `debut`, dans l'ordre où elles sont dessinées."""
    return [forme for forme in diapo.shapes if forme.name.startswith(debut)]


def teinte(forme):
    """La couleur de fond d'une forme, au format « #RRGGBB »."""
    return "#" + str(forme.fill.fore_color.rgb).upper()


# --- Les graphiques : la grammaire commune ---

def test_le_gris_de_la_matrice_fonce_avec_la_part():
    """Blanc pour une case vide, gris très foncé pour la plus pleine : 1 − 0,85 × part, comme la figure du 30/10."""
    assert slides_projet.grisDeMatrice(0) == "#FFFFFF"
    assert slides_projet.grisDeMatrice(1) == "#262626"
    niveaux = [int(slides_projet.grisDeMatrice(part / 10)[1:3], 16) for part in range(11)]
    assert niveaux == sorted(niveaux, reverse=True) and len(set(niveaux)) == 11


def test_l_encre_est_blanche_sur_un_gris_fonce():
    """Le nombre d'une case se lit toujours : blanc sur un gris foncé, noir sur un gris clair."""
    assert slides_projet.encreSurGris("#262626") == "#FFFFFF"
    assert slides_projet.encreSurGris("#E0E0E0") == "#000000"
    assert slides_projet.encreSurGris(slides_projet.grisDeMatrice(0)) == "#000000"


def test_un_nom_de_case_retrecit_jusqu_a_tenir():
    """Dans une case étroite, la police rétrécit jusqu'à ce que chaque mot tienne ; dans une case large, elle reste."""
    taille = slides_projet.tailleQuiTient(["Sodium", "1 point"], 0.6, 13)
    assert taille < 13 and slides_projet.largeurTexte("Sodium", slides_projet.DEMI_GRAS, taille) <= 0.6
    assert slides_projet.tailleQuiTient(["Sucres", "5 points"], 3.0, 13) == 13


def test_les_tableaux_a_barres_tiennent_leur_colonne(slides):
    """Le filet d'en-tête d'un tableau à barres a la largeur de sa colonne, comme celui d'un tableau."""
    from pptx.util import Inches

    largeur = slides_projet.LARGEUR - 2 * slides_projet.MARGE
    decalages, = formes(slides.slides[8], "Décalages filet d'en-tête")
    assert decalages.width == pytest.approx(Inches(largeur), abs=Inches(0.02))
    raisons, = formes(slides.slides[6], "Raisons filet d'en-tête")
    assert raisons.width == pytest.approx(Inches(slides_projet.LARGEUR - slides_projet.MARGE - 7.2), abs=Inches(0.02))


def test_quatorze_slides_sans_debordement(slides):
    """Quatorze slides ; la génération se serait arrêtée si un titre ou un texte débordait."""
    assert len(slides.slides) == 14


def test_la_slide_2_dit_la_regle_des_proteines(slides):
    assert "ne votent que si le Nutri-Score les compte" in texteDeLaSlide(slides.slides[1])


def test_la_slide_2_justifie_les_poids_des_piliers(slides):
    """À limiter pèse le plus, comme les points négatifs du Nutri-Score ; la transformation pèse 1 − λ."""
    from projet_nutriscore import NEGATIFS, POINTS_MAX, POSITIFS
    texte = texteDeLaSlide(slides.slides[1])
    negatifs, positifs = sum(POINTS_MAX[c] for c in NEGATIFS), sum(POINTS_MAX[c] for c in POSITIFS)
    assert (negatifs, positifs) == (55, 17)
    assert f"les points négatifs ({negatifs} au plus) dépassent les positifs ({positifs})" in texte
    assert "soit 1 − λ" in texte and "elle ne fait jamais perdre une classe" in texte


def test_la_slide_2_dessine_la_barre_des_poids(slides):
    """
    Les onze critères en une barre : une case par critère, large comme son poids, dans l'ordre des piliers ; le
    repère de λ tombe à 0,7 de la barre, au début du pilier de la transformation.
    """
    modele = resultatsDuSuperNutri()["supernutri"]["modele"]
    diapo = slides.slides[1]
    cases = formes(diapo, "Poids case ")
    assert [forme.name.removeprefix("Poids case ") for forme in cases] == modele["criteres"]
    largeur = sum(forme.width for forme in cases)
    for forme, critere in zip(cases, modele["criteres"]):
        assert forme.width / largeur == pytest.approx(modele["poids"][critere], abs=0.002)
    repere, = formes(diapo, "Poids repère λ")
    assert (repere.left + repere.width / 2 - cases[0].left) / largeur == pytest.approx(modele["lam"], abs=0.003)
    texte = texteDeLaSlide(diapo)
    assert "il faut 0,7 du poids pour franchir un profil" in texte and "tout ce pilier" in texte
    for pilier in ("À limiter", "À favoriser", "Transformation"):
        assert pilier in texte


def test_la_slide_3_explique_nova_et_les_additifs_a_risque(slides):
    """Les quatre groupes NOVA et nos plats dans chacun ; les trois familles d'additifs à risque ; les deux exemples."""
    transformation = resultatsDuSuperNutri()["supernutri"]["etendue"]["transformation"]
    texte = texteDeLaSlide(slides.slides[2])
    assert "le groupe NOVA et les additifs à risque" in texte
    for groupe in ("brut ou peu transformé", "ingrédient culinaire", "transformé", "ultra-transformé"):
        assert groupe in texte
    assert transformation["nova"] == {"1": 0, "2": 0, "3": 118, "4": 257}
    for famille, nombre in transformation["familles"].items():
        assert famille.capitalize() in texte and str(nombre) in texte
    assert "ANSES 2022" in texte and "EFSA 2019" in texte and "EFSA 2018" in texte
    poelee, regina = transformation["exemples"]
    assert slides_projet.typographie("aucun à risque : amidon modifié (E14XX), gomme guar (E412) et gomme xanthane (E415)") in texte
    assert slides_projet.typographie(f"{regina['additifs']} additifs, dont {regina['aRisque']} à risque : nitrite de "
                                     "sodium (E250) et polyphosphates (E452)") in texte
    assert "E450\u00a0à\u00a0E452" in texte


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
    texte = texteDeLaSlide(slides.slides[5])
    assert slides_projet.typographie("Poêlée Fermière : B au Nutri-Score, C′ au SuperNutri-score") in texte
    assert "B′" in texte


def test_la_slide_de_la_poelee_nomme_la_classe_de_chaque_profil(slides):
    """« b5 (A′) » plutôt que « b5 » : chaque profil dit la classe qu'il ouvre."""
    texte = texteDeLaSlide(slides.slides[5])
    assert all(profil in texte for profil in ("b5 (A′)", "b4 (B′)", "b3 (C′)", "b2 (D′)"))


def test_la_slide_de_la_poelee_rappelle_les_piliers(slides):
    """Au-dessus des barres, les trois piliers de la slide 2, dans le même ordre et à la largeur de leur poids."""
    diapo = slides.slides[5]
    noms = formes(diapo, "Concordance pilier ")
    assert [forme.text_frame.text for forme in noms] == ["À limiter", "À favoriser", "Transformation"]
    filets = formes(diapo, "Concordance filet du pilier ")
    cadre, = formes(diapo, "Concordance b5 cadre")
    assert [round(forme.width / cadre.width, 1) for forme in filets] == [0.4, 0.3, 0.3]


def test_la_slide_6_compte_les_plats_qui_montent_et_descendent(slides):
    """Plus sévère que le Nutri-Score ; ceux qui montent sont chargés en points négatifs, et MR-Sort n'a pas de veto."""
    ecarts = resultatsDuSuperNutri()["supernutri"]["etendue"]["ecarts"]
    texte = texteDeLaSlide(slides.slides[6])
    assert slides_projet.typographie(f"Plus sévère que le Nutri-Score : {ecarts['descendent']} plats descendent, "
                                     f"{ecarts['montent']} montent") in texte
    assert f"{ecarts['montees']['chargees']} ont au moins 11 points négatifs" in texte and "sans veto" in texte


def test_la_slide_7_grise_la_matrice_et_encadre_la_diagonale(slides):
    """
    La matrice face au Nutri-Score : 25 cases d'autant plus foncées qu'elles comptent de plats, la diagonale
    encadrée, les nombres écrits sauf les zéros, et les deux zones nommées dans leurs coins vides.
    """
    matrice = resultatsDuSuperNutri()["supernutri"]["etendue"]["comparaison"]["matrice"]
    diapo = slides.slides[6]
    cases = {forme.name: forme for forme in formes(diapo, "Matrice case ")}
    assert len(cases) == 25
    plusGrande = max(max(ligne) for ligne in matrice)
    for i, ligne in enumerate(matrice):
        for j, valeur in enumerate(ligne):
            assert teinte(cases[f"Matrice case {i} {j}"]) == slides_projet.grisDeMatrice(valeur / plusGrande)
    assert len(formes(diapo, "Matrice diagonale ")) == 5
    nombres = [forme.text_frame.text for forme in formes(diapo, "Matrice nombre ")]
    assert sorted(nombres) == sorted(str(valeur) for ligne in matrice for valeur in ligne if valeur)
    texte = texteDeLaSlide(diapo)
    assert "plus sévère" in texte and "plus permissif" in texte
    # chaque zone se lit sur un fond blanc, qui cache les filets gris des cases qu'elle couvre
    fonds = formes(diapo, "Matrice fond de la zone ")
    assert len(fonds) == 2 and all(teinte(fond) == "#FFFFFF" for fond in fonds)
    assert "En ligne le Nutri-Score, en colonne le SuperNutri-score" in texte


def test_la_slide_7_montre_les_raisons_en_barres(slides):
    """Les cinq critères les plus ratés par les plats qui descendent : des barres noires sur la trame de ces plats."""
    ecarts = resultatsDuSuperNutri()["supernutri"]["etendue"]["ecarts"]
    diapo = slides.slides[6]
    raisons = sorted(ecarts["raisonsDesDescentes"].items(), key=lambda paire: -paire[1])[:5]
    barres, trames = formes(diapo, "Raisons barre "), formes(diapo, "Raisons trame ")
    assert len(barres) == len(trames) == 5
    for barre, trame, (_, compte) in zip(barres, trames, raisons):
        assert barre.width / trame.width == pytest.approx(compte / ecarts["descendent"], abs=0.01)
    valeurs = [forme.text_frame.text for forme in formes(diapo, "Raisons valeur ")]
    assert valeurs == [str(compte) for _, compte in raisons]


def test_la_slide_8_dessine_les_tirages_en_barres(slides):
    """
    Pour chaque amplitude, la moyenne en noir sur la trame du maximum, sur une même échelle ; puis les cinq
    variations d'un seul poids qui changent le plus de plats, en barres.
    """
    sensibilite = resultatsDuSuperNutri()["supernutri"]["sensibilite"]["etendue"]
    diapo = slides.slides[7]
    moyennes, maximums = formes(diapo, "Tirages barre "), formes(diapo, "Tirages trame ")
    assert len(moyennes) == len(maximums) == len(sensibilite["courbe"])
    plusGrand = max(point["partMax"] for point in sensibilite["courbe"])
    for moyenne, maximum, point in zip(moyennes, maximums, sensibilite["courbe"]):
        assert moyenne.width / maximum.width == pytest.approx(point["partMoyenne"] / point["partMax"], abs=0.01)
        assert maximum.width / maximums[-1].width == pytest.approx(point["partMax"] / plusGrand, abs=0.01)
    variations = sorted(sensibilite["poids"]["unParUn"], key=lambda ligne: -ligne["plats"])[:5]
    barres = formes(diapo, "Un par un barre ")
    assert len(barres) == 5
    for barre, variation in zip(barres, variations):
        assert barre.width / barres[0].width == pytest.approx(variation["plats"] / variations[0]["plats"], abs=0.01)


def test_la_slide_9_dessine_les_decalages_en_barres(slides):
    """La colonne des plats qui changent devient une barre : NOVA domine les seuils nutritionnels."""
    profils = resultatsDuSuperNutri()["supernutri"]["sensibilite"]["etendue"]["profils"]
    scenarios = sorted(profils["scenarios"], key=lambda scenario: -scenario["plats"])[:6]
    barres = formes(slides.slides[8], "Décalages barre ")
    assert len(barres) == 6
    for barre, scenario in zip(barres, scenarios):
        assert barre.width / barres[0].width == pytest.approx(scenario["plats"] / scenarios[0]["plats"], abs=0.01)


def test_la_slide_7_cite_les_tirages(slides):
    """La part moyenne de plats qui changent, pour chaque amplitude des tirages, et les plats au bord."""
    sensibilite = resultatsDuSuperNutri()["supernutri"]["sensibilite"]["etendue"]
    texte = texteDeLaSlide(slides.slides[7])
    for point in sensibilite["courbe"]:
        assert slides_projet.pourcentage(point["partMoyenne"], 1) in texte
    assert f"{len(sensibilite['auBord'])} plats" in texte


def test_la_slide_8_cite_les_decalages_les_plus_actifs(slides):
    profils = resultatsDuSuperNutri()["supernutri"]["sensibilite"]["etendue"]["profils"]
    plusActif = max(profils["scenarios"], key=lambda scenario: scenario["plats"])
    assert str(plusActif["plats"]) in texteDeLaSlide(slides.slides[8])


def test_la_slide_8_nomme_des_plats_qui_changent(slides):
    """Le sujet demande d'identifier les produits qui changent : la slide en nomme trois, sous le décalage le plus actif."""
    profils = resultatsDuSuperNutri()["supernutri"]["sensibilite"]["etendue"]["profils"]
    plusActif = max(profils["scenarios"], key=lambda scenario: scenario["plats"])
    noms = [plat["nom"] for plat in profils["plats"] if plat["code"] in plusActif["codes"]]
    texte = texteDeLaSlide(slides.slides[8])
    assert sum(1 for nom in noms if nom in texte) == 3


def autreGroupe():
    """La comparaison avec l'autre groupe, dans le JSON."""
    autre = resultatsDuSuperNutri()["supernutri"].get("autreGroupe")
    if autre is None:
        pytest.skip("la base de l'autre groupe n'est pas encore comparée")
    return autre


def test_la_slide_10_presente_leur_modele(slides):
    """Leur base, leurs cinq critères en points sur 15 et leurs seuils, leur λ, le sens de leurs classes, et ce qui manque."""
    autre = autreGroupe()
    modele = autre["modele"]
    texte = texteDeLaSlide(slides.slides[9])
    assert [round(15 * modele["poids"][c]) for c in modele["criteres"]] == [5, 4, 3, 2, 1]
    assert "λ = 0,63" in texte and f"{autre['total']} céréales" in texte
    assert f"leur modèle redonne leurs {autre['reproduits']} classes" in texte
    for critere in modele["criteres"]:
        for profil in modele["profils"]:
            assert slides_projet.seuilEcrit(critere, profil[critere], modele["sens"][critere]) in texte
    assert "très bon choix" in texte and "à limiter" in texte
    assert "65 A, 64 B, 64 C, 64 D et 43 E" in texte
    assert "l'énergie, les protéines" in texte.replace("’", "'")


def test_la_slide_10_dessine_les_deux_barres_des_poids(slides):
    """
    Leur modèle en une barre, comme le nôtre à la slide 2 : cinq cases larges comme leurs points sur 15, et leur
    repère λ ; au-dessus, le rappel de notre barre à onze cases.
    """
    modele = autreGroupe()["modele"]
    diapo = slides.slides[9]
    cases = formes(diapo, "Leur barre case ")
    assert [forme.name.removeprefix("Leur barre case ") for forme in cases] == modele["criteres"]
    largeur = sum(forme.width for forme in cases)
    assert [round(15 * forme.width / largeur) for forme in cases] == [5, 4, 3, 2, 1]
    repere, = formes(diapo, "Leur barre repère λ")
    assert (repere.left + repere.width / 2 - cases[0].left) / largeur == pytest.approx(modele["lam"], abs=0.003)
    assert len(formes(diapo, "Notre barre case ")) == 11
    assert "10 points sur 15" in texteDeLaSlide(diapo)


def test_la_slide_11_aligne_quatre_matrices(slides):
    """
    Chacun sur sa base, puis chacun sur la base de l'autre : quatre matrices grisées ligne par ligne (où va chaque
    classe du Nutri-Score), sans nombres ; sous chacune, l'écart moyen et la part de même classe ; en bas, l'accord
    entre les deux modèles sur chaque base.
    """
    autre = autreGroupe()
    diapo = slides.slides[10]
    texte = texteDeLaSlide(diapo)
    ordre = (("nos", "notreFaceAuNutriscore"), ("leurs", "leurFaceAuNutriscore"),
             ("leurs", "notreFaceAuNutriscore"), ("nos", "leurFaceAuNutriscore"))
    for rang, (base, cle) in enumerate(ordre, start=1):
        comparaison = autre[base][cle]
        cases = {forme.name: forme for forme in formes(diapo, f"Matrice {rang} case ")}
        assert len(cases) == 25, (base, cle)
        for i, ligne in enumerate(comparaison["matrice"]):
            for j, valeur in enumerate(ligne):
                part = valeur / sum(ligne) if sum(ligne) else 0
                assert teinte(cases[f"Matrice {rang} case {i} {j}"]) == slides_projet.grisDeMatrice(part), (base, cle, i, j)
        assert not formes(diapo, f"Matrice {rang} nombre ")
        assert slides_projet.ecartSigne(comparaison["sens"]["ecartMoyen"]) in texte, (base, cle)
        assert slides_projet.pourcentage(comparaison["sens"]["pareil"], 1) in texte, (base, cle)
        assert comparaison["sens"]["pareil"] == pytest.approx(comparaison["exactitude"])
    for base in ("leurs", "nos"):
        assert slides_projet.pourcentage(autre[base]["notreFaceALeur"]["exactitude"], 1) in texte, base
    assert "Chacun sur sa base" in texte and slides_projet.typographie("Chacun sur la base de l'autre") in texte
    assert "Aucun produit en commun" in texte and "complétées par Open Food Facts" in texte
    assert "Même référence des deux côtés" in texte


def test_la_slide_12_dessine_les_bloquants_en_barres(slides):
    """La part des produits qui ratent chaque critère : des barres noires sur la trame de 100 %."""
    autre = autreGroupe()
    diapo = slides.slides[11]
    for base, modele in (("leurs", "notre"), ("nos", "leur")):
        parts = sorted(autre[base]["bloquants"][modele].items(), key=lambda paire: -paire[1])[:3]
        barres, trames = formes(diapo, f"Bloquants {base} barre "), formes(diapo, f"Bloquants {base} trame ")
        assert len(barres) == len(trames) == 3
        for barre, trame, (_, part) in zip(barres, trames, parts):
            assert barre.width / trame.width == pytest.approx(part, abs=0.01)


def test_la_slide_12_montre_ce_qui_bloque_chaque_modele(slides):
    """Ce que chaque modèle rate le plus souvent sur la base de l'autre, au seuil de B′, et un produit de chaque base."""
    autre = autreGroupe()
    texte = texteDeLaSlide(slides.slides[11])
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
    texte = texteDeLaSlide(slides.slides[13])
    ecarts = resultats["etendue"]["ecarts"]
    assert f"{ecarts['descendent']} descendent, surtout en haut, et {ecarts['montent']} montent" in texte
    assert "sans veto" in texte.lower()
    assert f"{len(resultats['etendue']['secsEnAPrime'])} de nos {resultats['etendue']['repartition']['A′']} plats A′" in texte


def test_le_pdf_des_slides_suit_les_slides(slides):
    """Le PDF de secours a autant de pages que les slides, et porte l'empreinte de leur texte et de leurs notes."""
    from pypdf import PdfReader

    import projet_soutenance

    pdf = slides_projet.SORTIES[2].with_suffix(".pdf")
    if not pdf.exists():
        pytest.skip("le PDF des slides n'est pas encore exporté")
    assert len(PdfReader(pdf).pages) == len(slides.slides)
    assert projet_soutenance.empreinteDuPdf(pdf) == slides_projet.empreinteDesSlides(slides), \
        "le PDF des slides est en retard : relancer python3 slides_projet.py --soutenance 2 (PowerPoint l'exporte)"
