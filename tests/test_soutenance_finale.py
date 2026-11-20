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
    """Onze slides, chacune avec son orateur et son texte, et une durée totale d'au plus 15 minutes."""
    slides = soutenance.slidesDuTexte(soutenance.TEXTES_ORAUX[2])
    assert [slide["numero"] for slide in slides] == list(range(1, 12))
    assert sum(slide["duree"] for slide in slides) <= 15 * 60
    assert all(slide["orateur"] in ("Daniel", "Anis", "Biyao") and slide["texte"] for slide in slides)


def test_l_oral_cite_les_poids(donnees):
    poids = sn.MODELE_SUPER["poids"]
    oral = donnees["oral"]
    assert f"Le groupe NOVA pèse {virgule(poids['nova'], 2)}" in oral
    assert f"Les additifs pèsent {virgule(poids['additifs'] + poids['aRisque'], 2)} en tout" in oral
    assert f"le bio, {virgule(poids['bio'], 2)}" in oral and poids["bio"] == min(poids.values())
    assert f"Le seuil majoritaire vaut {virgule(sn.MODELE_SUPER['lam'], 1)}" in oral


def test_l_oral_cite_la_repartition(donnees):
    repartition = donnees["super"]["etendue"]["repartition"]
    total = sum(repartition.values())
    assert 0.45 <= repartition["C′"] / total <= 0.55                       # « la moitié »
    assert (f"{repartition['A′']} sont en A prime, {repartition['B′']} en B prime, et la moitié, {repartition['C′']}, "
            "en C prime") in donnees["oral"]


def test_l_oral_suit_la_poelee_fermiere(donnees):
    """Ses deux concordances décisives, ce qu'elle rate face à B′, et ce qui la ferait monter."""
    plat, oral = donnees["plat"], donnees["oral"]
    detail = sn.classerPlat(plat)
    assert detail["lettre"] == "C′"
    # les concordances vont de b2 à b5 : b3 (le seuil de C′) est la deuxième, b4 (celui de B′) la troisième
    assert f"{virgule(detail['concordances'][1], 3)}, au-dessus de 0,7" in oral
    assert f"{virgule(detail['concordances'][2], 3)} seulement" in oral
    assert sn.ecartsAuNutriscore([plat])["plats"][0]["rates"] == ["pr", "fi", "nova", "additifs", "bio"]
    moinsTransforme = sn.classerPlat(dict(plat, nova=3, additifs=1))["lettre"]
    assert f"Avec NOVA 3 et un seul additif, elle passerait en {enPrime(moinsTransforme)}" in oral


def test_l_oral_cite_la_comparaison_au_nutriscore(donnees):
    etendue = donnees["super"]["etendue"]
    ecarts, oral = etendue["ecarts"], donnees["oral"]
    assert f"{ecarts['egaux']} gardent la classe du Nutri-Score, {ecarts['descendent']} descendent et {ecarts['montent']} montent" in oral
    raisons = sorted(ecarts["raisonsDesDescentes"].items(), key=lambda paire: -paire[1])[:5]
    assert [critere for critere, _ in raisons] == ["fi", "bio", "pr", "so", "nova"]
    r = dict(raisons)
    assert (f"les fibres, pour {r['fi']} plats, le label bio, pour {r['bio']}, les protéines, pour {r['pr']}, le sel, "
            f"pour {r['so']}, et le groupe NOVA, pour {r['nova']}") in oral
    assert f"{etendue['comparaison']['matrice'][3][2]} plats D du Nutri-Score montent ainsi en C prime" in oral


def test_l_oral_cite_la_sensibilite_aux_poids(donnees):
    sensibilite, oral = donnees["super"]["sensibilite"]["etendue"], donnees["oral"]
    plusSensible = max(sensibilite["poids"]["unParUn"], key=lambda ligne: ligne["plats"])
    assert plusSensible["critere"] == "pr" and plusSensible["delta"] > 0
    assert f"quand il gagne 0,05, {plusSensible['plats']} plats changent de classe" in oral
    parts = {point["amplitude"]: f"{virgule(100 * point['partMoyenne'], 1)} %" for point in sensibilite["courbe"]}
    assert (f"à plus ou moins 0,01, {parts[0.01]} des plats changent en moyenne ; à plus ou moins 0,02, {parts[0.02]} ; "
            f"à plus ou moins 0,05, {parts[0.05]}") in oral
    favoriser = set(sn.PILIERS["à favoriser"][1])
    assert all(set(plat["rates"]) == favoriser for plat in sensibilite["auBord"])
    assert f"{len(sensibilite['auBord'])} plats sont au bord de leur classe : ils ratent tout le pilier à favoriser" in oral


def test_l_oral_cite_la_sensibilite_aux_profils(donnees):
    profils, oral = donnees["super"]["sensibilite"]["etendue"]["profils"], donnees["oral"]
    assert f"Au total, {len(profils['plats'])} plats changent au moins une fois" in oral
    assert f"{profils['platsComposantes']} plats changent par eux. NOVA et les additifs, {profils['platsEntiers']}" in oral
    plusActif = max(profils["scenarios"], key=lambda scenario: scenario["plats"])
    assert (plusActif["profil"], plusActif["critere"], plusActif["ancienne"], plusActif["nouvelle"]) == ("b3", "nova", 4, 3)
    assert f"exiger NOVA 3 dès C prime ferait changer {plusActif['plats']} plats" in oral


def test_l_oral_cite_l_import_et_la_demonstration(donnees):
    """Les plats ajoutés qui ont servi à vérifier l'import, et le geste du curseur de λ."""
    ajoutes = sum(1 for plat in projet_base.lireBase(projet_base.FICHIER_BASE_ETENDUE) if plat["lot"] == projet_base.LOT_AJOUT)
    assert f"Nous l'avons vérifié sur nos {ajoutes} plats ajoutés" in donnees["oral"]
    modele = [m for m in donnees["resultats"]["mrsortEtenduProfils"]["modeles"] if m["nom"] == "sept" and m["lam"] == 0.6][0]
    regle = {"criteres": modele["criteres"], "poids": modele["poids"], "profils": modele["profils"]}
    classes = [enPrime(nomDeClasse(affecter(donnees["plat"], dict(regle, lam=lam))["classe"])) for lam in (0.6, 0.7)]
    assert f"range la Poêlée en {classes[0]} à 0,6 ; à 0,7, elle passe en {classes[1]}" in donnees["oral"]


def test_la_conclusion_reprend_les_chiffres(donnees):
    etendue, sensibilite = donnees["super"]["etendue"], donnees["super"]["sensibilite"]["etendue"]
    total = sum(etendue["repartition"].values())
    principal = [point for point in sensibilite["courbe"] if point["amplitude"] == 0.05][0]
    assert f"{etendue['repartition']['A′']} plats en A prime sur {total}" in donnees["oral"]
    assert (f"{len(sensibilite['auBord'])} plats sont au bord, et à plus ou moins 0,05, "
            f"{virgule(100 * principal['partMoyenne'], 1)} % des plats changent") in donnees["oral"]
