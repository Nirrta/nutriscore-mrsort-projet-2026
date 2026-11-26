"""Le texte de l'oral de la soutenance finale cite les chiffres du code, et tient en 15 minutes."""

import json

import pytest

import projet_base
import projet_soutenance as soutenance
import projet_supernutri as sn
from projet_mrsort import affecter, nomDeClasse

PLAT_EXEMPLE = "3257982125116"     # Poêlée Fermière (Cora)


def virgule(valeur, decimales):
    """Un nombre à la française, comme dans le texte : 0,876 ; 14,1."""
    return f"{valeur:,.{decimales}f}".replace(",", " ").replace(".", ",")


def pourcentageOral(part):
    """Une part en pourcentage, comme on la dit : 34,7 % ; 47 % plutôt que 47,0 %."""
    texte = f"{virgule(100 * part, 1)} %"
    return texte.replace(",0 %", " %")


def enPrime(lettre):
    """« B′ » se dit « B prime »."""
    return f"{lettre[0]} prime"


@pytest.fixture(scope="module")
def donnees():
    """Le SuperNutri-score du JSON (sur 375 plats), la Poêlée Fermière et le texte de l'oral, en une chaîne."""
    if not projet_base.FICHIER_RESULTATS.exists() or not projet_base.FICHIER_BASE_ETENDUE.exists():
        pytest.skip("les bases et les résultats ne sont pas encore construits")
    resultats = json.loads(projet_base.FICHIER_RESULTATS.read_text(encoding="utf-8"))
    if "supernutri" not in resultats:
        pytest.skip("le SuperNutri-score n'est pas encore calculé")
    oral = " ".join(" ".join(slide["texte"]) for slide in soutenance.slidesDuTexte(soutenance.TEXTES_ORAUX[2]))
    plat = [p for p in projet_base.lireBase() if p["code"] == PLAT_EXEMPLE][0]
    return {"resultats": resultats, "super": resultats["supernutri"], "plat": plat, "oral": oral}


def test_le_texte_de_l_oral_final_tient_en_15_minutes():
    """Quatorze slides, chacune avec son orateur et son texte, et une durée totale d'au plus 15 minutes."""
    slides = soutenance.slidesDuTexte(soutenance.TEXTES_ORAUX[2])
    assert [slide["numero"] for slide in slides] == list(range(1, 15))
    assert sum(slide["duree"] for slide in slides) <= 15 * 60
    assert all(slide["orateur"] in ("Daniel", "Anis", "Biyao") and slide["texte"] for slide in slides)


def phrases(texte):
    """Les phrases d'un texte, coupées après un point, un point d'interrogation ou un point d'exclamation."""
    import re
    return [phrase for phrase in re.split(r"(?<=[.?!])\s+", texte) if phrase.strip()]


def test_l_oral_parle_en_phrases_courtes():
    """Des phrases courtes, faciles à dire et à suivre : au plus 22 mots chacune."""
    for slide in soutenance.slidesDuTexte(soutenance.TEXTES_ORAUX[2]):
        for paragraphe in slide["texte"]:
            for phrase in phrases(paragraphe):
                assert len(phrase.split()) <= 22, (slide["numero"], phrase)


def test_l_oral_garde_un_debit_tenable():
    """Au plus 125 mots par minute sur chaque slide : le temps de montrer ce que l'on dit."""
    for slide in soutenance.slidesDuTexte(soutenance.TEXTES_ORAUX[2]):
        mots = sum(len(paragraphe.split()) for paragraphe in slide["texte"])
        assert mots / (slide["duree"] / 60) <= 125, (slide["numero"], mots)


def test_chaque_slide_a_ses_explications_pour_le_groupe():
    """Un bloc « Pour comprendre » par slide, pour le groupe : il ne se dit pas, donc il n'entre ni dans le texte dit ni dans les notes."""
    for slide in soutenance.slidesDuTexte(soutenance.TEXTES_ORAUX[2]):
        assert slide["comprendre"], slide["numero"]
        assert not set(slide["comprendre"]) & set(slide["texte"]), slide["numero"]
        assert all(not ligne.startswith("- ") for ligne in slide["comprendre"])


def test_le_texte_explique_les_mots_et_prepare_les_questions():
    """Avant les slides, les mots à connaître ; après, les questions probables du jury et leurs réponses."""
    texte = soutenance.TEXTES_ORAUX[2].read_text(encoding="utf-8")
    assert "\n# Les mots à connaître\n" in texte and "\n# Les questions probables du jury\n" in texte
    for mot in ("MR-Sort", "Profil", "Concordance", "λ", "Veto", "NOVA", "Matrice", "Écart moyen"):
        assert f"**{mot}" in texte, mot


def test_les_explications_citent_les_chiffres_du_code(donnees):
    """Les calculs détaillés pour le groupe : la Poêlée face à b4 et son « et si », le muesli, leur seuil en points, nos additifs."""
    comprendre = " ".join(" ".join(slide["comprendre"]) for slide in soutenance.slidesDuTexte(soutenance.TEXTES_ORAUX[2]))
    poids = sn.MODELE_SUPER["poids"]
    rates = poids["pr"] + poids["fi"] + poids["nova"] + poids["additifs"] + poids["bio"]
    assert f"= {virgule(rates, 3)}" in comprendre and f"donc {virgule(1 - rates, 3)}" in comprendre
    assert virgule(1 - (poids["pr"] + poids["fi"] + poids["bio"]), 3) in comprendre      # NOVA 3 et un seul additif
    assert f"font {virgule(poids['en'] + poids['su'] + poids['pr'], 3)}" in comprendre  # le muesli face à D′
    transformation = donnees["super"]["etendue"]["transformation"]
    assert f"{transformation['sansAdditif']} sans additif" in comprendre
    assert f"{transformation['avecARisque']} avec au moins un additif à risque" in comprendre
    assert f"{virgule(15 * donnees['super']['autreGroupe']['modele']['lam'], 2)} points" in comprendre


def test_l_oral_cite_les_poids(donnees):
    poids = sn.MODELE_SUPER["poids"]
    oral = donnees["oral"]
    assert f"Le groupe NOVA pèse {virgule(poids['nova'], 2)}" in oral
    assert f"Les additifs pèsent {virgule(poids['additifs'] + poids['aRisque'], 2)} en tout" in oral
    assert f"le bio, {virgule(poids['bio'], 2)}" in oral and poids["bio"] == min(poids.values())
    assert f"Le seuil majoritaire vaut {virgule(sn.MODELE_SUPER['lam'], 1)}" in oral


def test_l_oral_justifie_les_poids_des_piliers(donnees):
    """À limiter pèse le plus, comme les points négatifs du Nutri-Score ; la transformation pèse 1 − λ."""
    from projet_nutriscore import NEGATIFS, POINTS_MAX, POSITIFS
    negatifs, positifs = sum(POINTS_MAX[c] for c in NEGATIFS), sum(POINTS_MAX[c] for c in POSITIFS)
    assert (f"À limiter pèse le plus, comme au Nutri-Score : ses points négatifs vont jusqu'à {negatifs}, les positifs "
            f"jusqu'à {positifs}") in donnees["oral"]
    assert sn.PILIERS["transformation et production"][0] == pytest.approx(1 - sn.MODELE_SUPER["lam"])
    assert "pèse justement 0,30 : à lui seul, il ne fait jamais perdre une classe" in donnees["oral"]


def test_l_oral_explique_la_transformation(donnees):
    """Le groupe NOVA de nos plats, la source qui le justifie, et les deux exemples d'additifs."""
    transformation, oral = donnees["super"]["etendue"]["transformation"], donnees["oral"]
    nova = transformation["nova"]
    assert nova["1"] == nova["2"] == 0
    assert f"Nos plats sont tous NOVA 3 ou 4. Et {nova['4']} sur {transformation['total']} sont ultra-transformés" in oral
    assert "NutriNet-Santé associe l'ultra-transformé à plus de cancers et de maladies cardiovasculaires" in oral
    poelee, regina = transformation["exemples"]
    assert poelee["aRisque"] == 0 and 250 in sn.numerosDesAdditifs(regina["listeAdditifs"])
    assert (f"La Poêlée Fermière a {poelee['additifs']} additifs, aucun à risque. La pizza Regina en a {regina['aRisque']} "
            "à risque, dont le nitrite du jambon") in oral


def test_l_oral_cite_la_regle_des_proteines(donnees):
    from projet_nutriscore import SEUIL_PROTEINES
    assert f"pas pour un produit qui a {SEUIL_PROTEINES} points négatifs ou plus" in donnees["oral"]


def test_l_oral_cite_la_repartition(donnees):
    repartition = donnees["super"]["etendue"]["repartition"]
    total = sum(repartition.values())
    assert 0.4 <= repartition["C′"] / total < 0.5                           # « près de la moitié »
    assert (f"{repartition['A′']} sont en A prime et {repartition['B′']} en B prime. Près de la moitié, "
            f"{repartition['C′']}, sont en C prime") in donnees["oral"]


def test_l_oral_suit_la_poelee_fermiere(donnees):
    """Ses deux concordances décisives, ce qu'elle rate face à B′, et ce qui la ferait monter."""
    plat, oral = donnees["plat"], donnees["oral"]
    detail = sn.classerPlat(plat)
    assert detail["lettre"] == "C′"
    # les concordances vont de b2 à b5 : b3 (le seuil de C′) est la deuxième, b4 (celui de B′) la troisième
    assert f"{virgule(detail['concordances'][1], 3)}, au-dessus de 0,7" in oral
    assert f"Il ne reste que {virgule(detail['concordances'][2], 3)} du poids" in oral
    assert sn.ecartsAuNutriscore([plat])["plats"][0]["rates"] == ["pr", "fi", "nova", "additifs", "bio"]
    moinsTransforme = sn.classerPlat(dict(plat, nova=3, additifs=1))["lettre"]
    assert f"Avec NOVA 3 et un seul additif, elle passerait en {enPrime(moinsTransforme)}" in oral


def test_l_oral_cite_la_comparaison_au_nutriscore(donnees):
    """Plus sévère que le Nutri-Score, surtout en haut ; ceux qui montent sont chargés en points négatifs."""
    etendue = donnees["super"]["etendue"]
    ecarts, oral = etendue["ecarts"], donnees["oral"]
    sens, matrice = etendue["comparaison"]["sens"], etendue["comparaison"]["matrice"]
    assert sens["ecartMoyen"] > 0 and "Notre modèle est plus sévère que le Nutri-Score" in oral
    assert f"{ecarts['egaux']} gardent sa classe, {ecarts['descendent']} descendent et {ecarts['montent']} montent" in oral
    assert f"un plat perd {virgule(sens['ecartMoyen'], 2)} classe" in oral
    parLabel = ecarts["descentesParLabel"]
    assert (f"{parLabel['A']['plats']} des {sum(matrice[0])} plats A descendent, et {parLabel['B']['plats']} des "
            f"{sum(matrice[1])} plats B") in oral
    montees = ecarts["montees"]
    assert f"{montees['chargees']} des {ecarts['montent']} ont au moins 11 points négatifs" in oral
    raisons = sorted(ecarts["raisonsDesDescentes"].items(), key=lambda paire: -paire[1])[:5]
    assert [critere for critere, _ in raisons] == ["fi", "pr", "bio", "so", "nova"]
    r = dict(raisons)
    assert (f"les fibres, pour {r['fi']} plats. Puis les protéines, pour {r['pr']}. Le label bio, pour {r['bio']}. Le sel, "
            f"pour {r['so']}. Et le groupe NOVA, pour {r['nova']}") in oral


def test_l_oral_cite_la_sensibilite_aux_poids(donnees):
    sensibilite, oral = donnees["super"]["sensibilite"]["etendue"], donnees["oral"]
    plusSensible = max(sensibilite["poids"]["unParUn"], key=lambda ligne: ligne["plats"])
    assert plusSensible["critere"] == "pr" and plusSensible["delta"] > 0
    assert f"quand il gagne 0,05, {plusSensible['plats']} plats changent de classe" in oral
    parts = {point["amplitude"]: f"{virgule(100 * point['partMoyenne'], 1)} %" for point in sensibilite["courbe"]}
    assert (f"À plus ou moins 0,01, {parts[0.01]} des plats changent en moyenne. À plus ou moins 0,02, {parts[0.02]}. "
            f"À plus ou moins 0,05, {parts[0.05]}") in oral
    favoriser = set(sn.PILIERS["à favoriser"][1])
    assert all(set(plat["rates"]) == favoriser for plat in sensibilite["auBord"])
    assert f"{len(sensibilite['auBord'])} plats sont au bord de leur classe : ils ratent tout le pilier à favoriser" in oral


def test_l_oral_cite_la_sensibilite_aux_profils(donnees):
    profils, oral = donnees["super"]["sensibilite"]["etendue"]["profils"], donnees["oral"]
    assert (f"Au total, {len(profils['plats'])} plats changent au moins une fois : {profils['platsComposantes']} par les "
            f"seuils nutritionnels, {profils['platsEntiers']} par NOVA et les additifs") in oral
    plusActif = max(profils["scenarios"], key=lambda scenario: scenario["plats"])
    assert (plusActif["profil"], plusActif["critere"], plusActif["ancienne"], plusActif["nouvelle"]) == ("b3", "nova", 4, 3)
    assert f"Exiger NOVA 3 dès C prime ferait changer {plusActif['plats']} plats" in oral
    # les plats nommés sont ceux de la slide, et ils passent tous de C′ à D′
    import slides_projet
    noms = slides_projet.platsDuDecalage(profils, plusActif)
    assert all(nom in oral for nom in noms)
    for plat in profils["plats"]:
        if plat["nom"] in noms:
            assert "b3 groupe NOVA 4 → 3 : C′ → D′" in plat["decalages"]
    assert "qui passeraient de C prime à D prime" in oral


def test_l_oral_compare_les_deux_modeles_sur_les_deux_bases(donnees):
    """Leurs 300 classes redonnées, chaque modèle face au Nutri-Score sur chaque base, et l'accord des deux modèles."""
    autre, oral = donnees["super"]["autreGroupe"], donnees["oral"]
    assert f"leur modèle redonne leurs {autre['reproduits']} classes" in oral and autre["reproduits"] == autre["total"]
    assert autre["recoupement"][0] == 0 and "Aucun produit n'est commun aux deux bases" in oral
    leurs, nos = autre["leurs"], autre["nos"]
    # chaque modèle colle mieux au Nutri-Score sur sa propre base, et chacun est plus sévère que lui partout
    assert leurs["leurFaceAuNutriscore"]["exactitude"] > leurs["notreFaceAuNutriscore"]["exactitude"]
    assert nos["notreFaceAuNutriscore"]["exactitude"] > nos["leurFaceAuNutriscore"]["exactitude"]
    ecart = {(base, modele): autre[base][f"{modele}FaceAuNutriscore"]["sens"]["ecartMoyen"]
             for base in ("leurs", "nos") for modele in ("notre", "leur")}
    assert all(valeur > 0 for valeur in ecart.values())
    assert (f"de {virgule(ecart['nos', 'notre'], 2)} classe en moyenne pour le nôtre, {virgule(ecart['leurs', 'leur'], 2)} "
            "pour le leur") in oral
    assert f"{virgule(ecart['leurs', 'notre'], 2)} classe pour le nôtre, {virgule(ecart['nos', 'leur'], 2)} pour le leur" in oral
    assert f"la même classe qu'à {pourcentageOral(leurs['notreFaceALeur']['exactitude'])} de leurs céréales" in oral


def test_l_oral_presente_leur_modele(donnees):
    """Leurs cinq critères et leurs points, leur règle des 10 points sur 15, et ce qui manque à leur modèle."""
    autre, oral = donnees["super"]["autreGroupe"], donnees["oral"]
    modele = autre["modele"]
    assert [round(15 * modele["poids"][c]) for c in modele["criteres"]] == [5, 4, 3, 2, 1]
    assert ("les sucres pèsent le plus, 5 points sur 15. Puis les fibres, 4, le groupe NOVA, 3, les graisses saturées, 2, "
            "et le sodium, 1") in oral
    assert round(15 * modele["lam"], 2) == 9.45 and "Un produit franchit un profil avec 10 points sur 15" in oral
    assert "ils n'ont ni énergie, ni protéines, ni additifs, ni bio" in oral


def test_l_oral_explique_ce_qui_bloque_chaque_modele(donnees):
    """Notre seuil d'énergie ne vote pour aucune céréale au seuil de B′ ; leurs fibres bloquent nos plats ; les deux exemples."""
    autre, oral = donnees["super"]["autreGroupe"], donnees["oral"]
    assert autre["leurs"]["bloquants"]["notre"]["en"] == 1
    assert f"{pourcentageOral(round(autre['nos']['bloquants']['leur']['fi'], 2))} de nos plats ratent leur seuil de fibres" in oral
    muesli, poelee = autre["exemples"]
    assert (muesli["label"], muesli["leur"], muesli["notre"]) == ("C", "B′", "E′") and not muesli["proteinesComptees"]
    assert muesli["notreAuDessus"]["rates"] == ["en", "su", "pr"]
    assert f"{virgule(muesli['notreAuDessus']['poids'], 2)} du poids, plus que les 0,30 permis" in oral
    assert (poelee["leur"], poelee["leurAuDessus"]["rates"]) == ("E′", ["fi", "nova"])
    lam = autre["modele"]["lam"]
    assert (f"elle rate {virgule(poelee['leurAuDessus']['poids'], 2)} du poids, quand leur seuil n'en permet que "
            f"{virgule(1 - lam, 2)}") in oral


def test_l_oral_cite_la_demonstration(donnees):
    """Le geste du curseur de λ : la classe de la Poêlée à 0,6 et à 0,7, avec les profils appris sur 375 plats."""
    modele = [m for m in donnees["resultats"]["mrsortEtenduProfils"]["modeles"] if m["nom"] == "sept" and m["lam"] == 0.6][0]
    regle = {"criteres": modele["criteres"], "poids": modele["poids"], "profils": modele["profils"]}
    classes = [enPrime(nomDeClasse(affecter(donnees["plat"], dict(regle, lam=lam))["classe"])) for lam in (0.6, 0.7)]
    assert f"range la Poêlée en {classes[0]} à 0,6 ; à 0,7, elle passe en {classes[1]}" in donnees["oral"]


def test_la_conclusion_reprend_les_chiffres(donnees):
    etendue, sensibilite = donnees["super"]["etendue"], donnees["super"]["sensibilite"]["etendue"]
    autre, oral = donnees["super"]["autreGroupe"], donnees["oral"]
    ecarts, cereales = etendue["ecarts"], autre["leurs"]["notreFaceAuNutriscore"]
    assert cereales["sens"]["plusPermissif"] == 0
    descentes = round(cereales["sens"]["plusSevere"] * cereales["total"])
    assert (f"Sur nos {sum(etendue['repartition'].values())} plats, {ecarts['descendent']} descendent et {ecarts['montent']} "
            f"montent ; sur leurs céréales, {descentes} descendent et aucune ne monte") in oral
    secs = etendue["secsEnAPrime"]
    assert f"{len(secs)} de nos {etendue['repartition']['A′']} plats en A prime sont des produits secs" in oral
    assert sum(1 for nom in secs if nom.startswith("Couscous")) == len(secs) - 1 and "Velouté de pois cassés" in secs
    assert "Sans veto, un plat très salé ne perd que la case du sel" in oral
    assert f"Et {len(sensibilite['auBord'])} plats sont au bord de leur classe" in oral


def test_le_pdf_de_l_oral_suit_son_texte():
    """Le PDF de l'oral porte l'empreinte du texte dont il vient : il est recompilé après chaque changement du texte."""
    source = soutenance.TEXTES_ORAUX[2]
    pdf = source.with_suffix(".pdf")
    if not pdf.exists():
        pytest.skip("le PDF de l'oral n'est pas encore compilé")
    assert soutenance.empreinteDuPdf(pdf) == soutenance.empreinte(source.read_text(encoding="utf-8")), \
        "le PDF de l'oral est en retard : relancer python3 projet_soutenance.py --soutenance 2"
