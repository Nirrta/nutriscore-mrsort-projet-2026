"""Les textes de la soutenance citent les chiffres du code, et le texte de l'oral tient en 15 minutes."""

import json

import pytest

import projet_base
import projet_mrsort as mr
import projet_nutriscore as ns
import projet_soutenance as soutenance

PLAT_EXEMPLE = "3257982125116"     # Poêlée Fermière (Cora)
PUREE, COLIN = "3270160875528", "3254560437647"
SOUPE = "3760346870602"


def virgule(valeur, decimales):
    """Un nombre à la française, comme dans les textes : 0,919 ; 2 373."""
    return f"{valeur:,.{decimales}f}".replace(",", " ").replace(".", ",")


@pytest.fixture(scope="module")
def donnees():
    """Le JSON des résultats, les plats de la base par code-barres, et les deux textes."""
    if not projet_base.FICHIER_RESULTATS.exists() or not projet_base.FICHIER_BASE.exists():
        pytest.skip("la base et les résultats ne sont pas encore construits")
    resultats = json.loads(projet_base.FICHIER_RESULTATS.read_text(encoding="utf-8"))
    if "mrsort" not in resultats:
        pytest.skip("les modèles MR-Sort ne sont pas encore calculés")
    plats = {plat["code"]: plat for plat in projet_base.lireBase()}
    return {"resultats": resultats, "plats": plats,
            "oral": soutenance.TEXTE_ORAL.read_text(encoding="utf-8"),
            "dossier": soutenance.DOSSIER_DEMARCHE.read_text(encoding="utf-8")}


def modeleDuJson(resultats, nom, lam):
    """Un modèle MR-Sort appris, tel qu'il est rangé dans le JSON."""
    for modele in resultats["mrsort"]["modeles"]:
        if modele["nom"] == nom and modele["lam"] == lam and modele["mode"] == "poids":
            return modele
    raise KeyError((nom, lam))


def test_le_texte_de_l_oral_tient_en_15_minutes():
    """Dix slides, chacune avec son orateur, son texte et une durée totale d'au plus 15 minutes."""
    slides = soutenance.slidesDuTexte()
    assert [slide["numero"] for slide in slides] == list(range(1, 11))
    assert sum(slide["duree"] for slide in slides) <= 15 * 60
    assert all(slide["orateur"] in ("Daniel", "Anis", "Biyao") and slide["texte"] for slide in slides)


def test_l_oral_s_en_tient_aux_resultats():
    """Ce qu'on dit ne parle ni de la règle des 25 %, ni de la soupe, ni de la déclaration d'IA, ni des questions."""
    dit = " ".join(" ".join(slide["texte"]) for slide in soutenance.slidesDuTexte())
    assert not [mot for mot in ("25 %", "soupe", "figure 4", "déclaration", "vos questions") if mot in dit]
    assert "points négatifs, en rouge" in dit and "points positifs, en vert" in dit


def test_les_textes_citent_la_base(donnees):
    """L'entonnoir, le vivier et le tirage."""
    base = donnees["resultats"]["base"]
    entonnoir = base["entonnoir"]
    for etape, nombre in entonnoir.items():
        assert f"| {etape[0].upper() + etape[1:]} | {nombre} |" in donnees["dossier"], etape
    assert f"Nous avons repéré {entonnoir['candidats repérés']} candidats" in donnees["oral"]
    assert f"de {entonnoir['cas général du Nutri-Score']} à {entonnoir['sept composantes connues']} plats" in donnees["oral"]
    assert f"Il reste {entonnoir['sans doublon']} plats" in donnees["oral"]
    vivier = ", ".join(f"{base['vivierParClasse'][lettre]} {lettre}" for lettre in "ABCDE")
    assert f"({vivier})" in donnees["dossier"]
    assert f"graine {base['graine']}" in donnees["dossier"]


def test_les_textes_citent_le_nutriscore(donnees):
    """La vérification sur la base, et la valeur exacte du sel de la soupe."""
    verification = donnees["resultats"]["nutriscore"]
    assert f"{verification['reproduits']} plats sur {verification['total']}" in donnees["oral"]
    assert f"{verification['reproduits']} plats sur {verification['total']}" in donnees["dossier"]
    sel = virgule(donnees["plats"][SOUPE]["so"], 4)
    assert sel in donnees["oral"] and sel in donnees["dossier"]


def test_les_textes_expliquent_la_version_de_mars_2025(donnees):
    """La « version de mars 2025 » du sujet : l'algorithme actualisé en 2023, avec les maximums du code."""
    negatifs = sum(ns.POINTS_MAX[composante] for composante in ns.NEGATIFS)
    positifs = sum(ns.POINTS_MAX[composante] for composante in ns.POSITIFS)
    assert f"de 0 à {negatifs} et de 0 à {positifs} points" in donnees["oral"]
    assert f"{negatifs} points négatifs et {positifs} positifs" in donnees["dossier"]
    for texte in (donnees["oral"], donnees["dossier"]):
        assert "16 mars 2025" in texte and "17 mars 2025" in texte
        assert "FAQ officielle de 2023" not in texte and "de 2023, page 29" not in texte


def test_les_textes_citent_les_modeles(donnees):
    """Le tableau des modèles, l'exactitude, les erreurs de plus d'une classe et les paires inversées."""
    resultats = donnees["resultats"]
    for modele in resultats["mrsort"]["modeles"]:
        ligne = (f"| {len(modele['criteres'])} critères | {virgule(modele['lam'], 1)} | "
                 f"{modele['bienRanges']}/{modele['total']} | {virgule(100 * modele['exactitude'], 1)} % | "
                 f"{virgule(100 * modele['aUneClassePres'], 1)} % |")
        assert ligne in donnees["dossier"], ligne
    sept, trois = modeleDuJson(resultats, "sept", 0.6), modeleDuJson(resultats, "trois", 0.6)
    assert f"{sept['bienRanges']} plats sur {sept['total']} sont rangés comme le Nutri-Score" in donnees["oral"]
    assert f"{virgule(100 * sept['aUneClassePres'], 1)} % des plats sont à une classe près" in donnees["oral"]
    assert f"{trois['bienRanges']} plats, {virgule(100 * trois['exactitude'], 1)} %" in donnees["oral"]
    loin = sum(sept["matrice"][i][j] for i in range(5) for j in range(5) if abs(i - j) > 1)
    assert f"seuls {loin} plats sont à plus d'une classe" in donnees["oral"]
    assert f"seuls {loin} plats sont à plus d'une classe" in donnees["dossier"]
    paires = resultats["mrsort"]["inversions"]
    assert paires["sept"]["nombre"] == 0
    assert f"{paires['trois']['nombre']} paires" in donnees["oral"]
    assert f"{paires['trois']['nombre']} paires" in donnees["dossier"]
    assert f"{virgule(sept['poids']['sa'], 4)} pour les graisses saturées" in donnees["dossier"]
    assert f"{virgule(sept['poids']['sa'], 2)} pour les graisses saturées" in donnees["oral"]


def test_les_textes_citent_le_plat_d_exemple(donnees):
    """La Poêlée Fermière : 3 − 2 = 1, B ; C′ à 7 critères ; B′ avec 1,4 g de graisses saturées."""
    plat = donnees["plats"][PLAT_EXEMPLE]
    calcul = ns.scoreNutriscore(plat)
    assert (calcul["N"], calcul["P"], calcul["score"], calcul["label"]) == (3, 2, 1, "B")
    assert calcul["points"]["so"] == 2 and calcul["points"]["fr"] == 2
    modele = modeleDuJson(donnees["resultats"], "sept", 0.6)
    regle = {"criteres": modele["criteres"], "poids": modele["poids"], "profils": modele["profils"], "lam": 0.6}
    detail = mr.affecter(plat, regle)
    assert mr.nomDeClasse(detail["classe"]) == "C′"
    assert f"franchit b3 avec {virgule(detail['concordances'][1], 3)}" in donnees["oral"]
    assert f"il ne reste que {virgule(detail['concordances'][2], 3)}" in donnees["oral"]
    moinsGras = dict(plat, sa=1.4)
    assert ns.scoreNutriscore(moinsGras)["label"] == "B"
    assert mr.nomDeClasse(mr.affecter(moinsGras, regle)["classe"]) == "B′"
    assert f"de {virgule(plat['sa'], 1)} à 1,4 g" in donnees["oral"]


def coalition(plat, profil, modele):
    """Les critères qui votent pour le plat face au profil : il y vaut au moins le profil."""
    return [critere for critere in modele["criteres"]
            if mr.concordancePartielle(plat[critere], profil[critere], mr.sensDuCritere(critere, modele)) == 1]


def test_les_reponses_du_jury_sur_l_apprentissage(donnees):
    """
    Le programme linéaire (ε, 90 plats au plus aux deux seuils), les plats que les profils
    empêchent de bien ranger (dont la Poêlée Fermière), et le rôle à part des graisses saturées.
    """
    resultats, oral = donnees["resultats"], donnees["oral"]
    sept, septHaut = modeleDuJson(resultats, "sept", 0.6), modeleDuJson(resultats, "sept", 0.7)
    assert f"ε = {virgule(mr.EPSILON, 3)}" in oral
    assert septHaut["bienRanges"] == sept["bienRanges"]
    assert f"avec ces profils, {sept['bienRanges']} est le maximum" in oral

    # même coalition face aux deux profils qui bornent sa classe : le plat ne peut pas être bien rangé
    profils = sept["profils"]
    assert septHaut["profils"] == profils
    bloques = [code for code, plat in donnees["plats"].items() if 1 <= mr.classeDuLabel(plat["label"]) <= 3
               and coalition(plat, profils[mr.classeDuLabel(plat["label"]) - 1], sept)
               == coalition(plat, profils[mr.classeDuLabel(plat["label"])], sept)]
    assert PLAT_EXEMPLE in bloques
    erreurs = sept["total"] - sept["bienRanges"]
    assert f"{len(bloques)} plats de la base sont dans ce cas" in oral
    assert (f"Sur nos {erreurs} erreurs à 7 critères, {len(bloques)} viennent donc des profils eux-mêmes, "
            f"et {erreurs - len(bloques)} des conflits entre plats") in oral

    # sans les graisses saturées, les six autres critères n'atteignent λ à aucun des deux seuils
    for modele in (sept, septHaut):
        assert 1 - modele["poids"]["sa"] < modele["lam"]
    assert f"ne font ensemble que {virgule(1 - sept['poids']['sa'], 2)}, moins que λ" in oral


def test_les_textes_citent_la_paire_puree_colin(donnees):
    """La paire inversée de l'exposé est bien une paire inversée, avec les valeurs citées."""
    puree, colin = donnees["plats"][PUREE], donnees["plats"][COLIN]
    assert (puree["label"], colin["label"]) == ("D", "A")
    assert mr.auMoinsAussiBon(puree, colin, mr.CRITERES_TROIS)
    for texte in (donnees["oral"], donnees["dossier"]):
        assert f"741 contre 774 kJ" in texte and f"{puree['en']:g} contre {colin['en']:g}" == "741 contre 774"
        assert f"{virgule(puree['so'], 2)} contre {virgule(colin['so'], 2)} g" in texte
        assert f"{virgule(puree['sa'], 1)} g de graisses saturées contre {virgule(colin['sa'], 1)}" in texte
        assert f"{virgule(puree['pr'], 1)} g de protéines contre {colin['pr']:g}" in texte


def test_le_texte_cite_l_etendue_des_criteres(donnees):
    """Slide 4 : l'énergie, le sel, et les fruits et légumes, du minimum au maximum de la base."""
    plats = list(donnees["plats"].values())
    energie = [plat["en"] for plat in plats]
    sel = [plat["so"] for plat in plats]
    fruits = [plat["fr"] for plat in plats]
    assert f"l'énergie va de {virgule(min(energie), 0)} à {virgule(max(energie), 0)} kJ" in donnees["oral"]
    assert f"le sel de {virgule(min(sel), 0)} à {virgule(max(sel), 2)} g" in donnees["oral"]
    assert f"les fruits et légumes de {virgule(min(fruits), 0)} à {virgule(max(fruits), 0)} %" in donnees["oral"]
