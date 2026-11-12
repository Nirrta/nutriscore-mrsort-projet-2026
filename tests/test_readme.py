"""Les chiffres cités dans le README sont ceux de resultats/resultats_projet.json."""

import json
from pathlib import Path

import pytest

import projet_base


README = Path(__file__).parent.parent / "README.md"


def pourcentage(part):
    """Une part en pourcentage à une décimale, à la française : 0,72 donne « 72,0 % »."""
    return f"{100 * part:.1f} %".replace(".", ",")


@pytest.fixture(scope="module")
def resultats():
    """Le JSON des résultats, s'il contient la base, le Nutri-Score et MR-Sort."""
    if not projet_base.FICHIER_RESULTATS.exists():
        pytest.skip("les résultats ne sont pas encore calculés")
    donnees = json.loads(projet_base.FICHIER_RESULTATS.read_text(encoding="utf-8"))
    if not all(cle in donnees for cle in ("base", "nutriscore", "mrsort")):
        pytest.skip("les résultats ne sont pas complets")
    return donnees


def test_le_readme_cite_la_base(resultats):
    """L'entonnoir, le vivier par classe, la graine et la date d'extraction."""
    texte = README.read_text(encoding="utf-8")
    base = resultats["base"]
    assert f"{base['entonnoir']['candidats repérés']} candidats repérés" in texte
    assert f"{base['entonnoir']['sans doublon']} plats retenus" in texte
    assert f"{base['nombrePlats']} plats tirés, {base['parClasse']} par classe (graine {base['graine']})" in texte
    assert base["dateExtraction"] in texte
    ligne = " | ".join(str(base["vivierParClasse"][lettre]) for lettre in "ABCDE")
    assert f"| {ligne} |" in texte


def test_le_readme_cite_la_verification_du_nutriscore(resultats):
    """Le nombre de plats reproduits."""
    verification = resultats["nutriscore"]
    assert f"{verification['reproduits']}/{verification['total']} plats" in README.read_text(encoding="utf-8")


def test_le_readme_cite_les_modeles(resultats):
    """Chaque ligne du tableau des modèles, et les paires inversées."""
    texte = README.read_text(encoding="utf-8")
    for modele in resultats["mrsort"]["modeles"]:
        ligne = (f"| {len(modele['criteres'])} critères | {str(modele['lam']).replace('.', ',')} | "
                 f"{modele['bienRanges']}/{modele['total']} | {pourcentage(modele['exactitude'])} | "
                 f"{pourcentage(modele['aUneClassePres'])} |")
        assert ligne in texte, ligne
    inversions = resultats["mrsort"]["inversions"]
    assert f"Il y en a {inversions['sept']['nombre']} à 7 critères et {inversions['trois']['nombre']} à 3 critères" in texte


def test_le_readme_cite_la_base_etendue(resultats):
    """L'entonnoir de la base étendue, ses pages ajoutées, sa taille et le vivier hors de la base."""
    if "baseEtendue" not in resultats:
        pytest.skip("la base étendue n'est pas construite")
    texte = README.read_text(encoding="utf-8")
    etendue = resultats["baseEtendue"]
    pages = sum(len(liste) for liste in etendue["pagesAjoutees"].values())
    assert (f"{etendue['entonnoir']['candidats repérés']} candidats repérés (les pages de la base, plus {pages} "
            f"pages tirées dans le même ordre), {etendue['entonnoir']['sans doublon']} plats retenus") in texte
    assert (f"{etendue['nombrePlats']} plats, {etendue['parClasse']} par classe (graine {etendue['graine']}, "
            f"ajout extrait le {etendue['dateExtraction']})") in texte
    ligne = " | ".join(str(etendue["vivierHorsBase"][lettre]) for lettre in "ABCDE")
    assert f"| {ligne} |" in texte


def test_le_readme_cite_les_cas_particuliers(resultats):
    """Les fiches reproduites de chaque cas particulier, le vivier étendu, et la lecture des seuils par OFF."""
    from projet_nutriscore import CATEGORIES

    verification = resultats["nutriscore"]
    if "casParticuliers" not in verification:
        pytest.skip("les cas particuliers ne sont pas encore vérifiés")
    texte = README.read_text(encoding="utf-8")
    for categorie, bilan in verification["casParticuliers"].items():
        assert f"| {CATEGORIES[categorie]} | {bilan['reproduits']}/{bilan['total']} |" in texte
    vivier = verification["vivierEtendu"]
    assert f"{vivier['reproduits']}/{vivier['total']} plats du vivier étendu" in texte
    sel = verification["seuilsPile"]["salt"]
    assert f"OFF lit « > » {sel['strict']} fois sur {sel['strict'] + sel['inclusif']} pour le sel" in texte


def virgule(valeur, decimales):
    """Un nombre à la française : 0,334."""
    return f"{valeur:.{decimales}f}".replace(".", ",")


def test_le_readme_cite_les_intervalles_des_poids(resultats):
    """L'intervalle du poids des acides gras saturés, à 7 critères, pour λ = 0,6 et 0,7."""
    texte = README.read_text(encoding="utf-8")
    for modele in resultats["mrsort"]["modeles"]:
        if modele["nom"] == "sept" and "intervalles" in modele:
            bas, haut = modele["intervalles"]["sa"]
            assert f"de {virgule(bas, 3)} à {virgule(haut, 3)} à λ = {virgule(modele['lam'], 1)}" in texte


def test_le_readme_cite_la_generalisation(resultats):
    """Les modèles du 30/10 sur la base et sur les 250 plats ajoutés, ligne par ligne."""
    if "generalisation" not in resultats:
        pytest.skip("la généralisation n'est pas encore calculée")
    texte = README.read_text(encoding="utf-8")
    from projet_mrsort import APPRENTISSAGES

    for ligne in resultats["generalisation"]["modeles"]:
        nombre = 7 if ligne["nom"] == "sept" else 3
        attendu = (f"| {nombre} critères | {APPRENTISSAGES[ligne['mode']]} | {virgule(ligne['lam'], 1)} | "
                   f"{ligne['base']['bienRanges']}/{ligne['base']['total']} | "
                   f"{ligne['ajout']['bienRanges']}/{ligne['ajout']['total']} | {pourcentage(ligne['ajout']['exactitude'])} |")
        assert attendu in texte, attendu
    sept = [ligne for ligne in resultats["generalisation"]["modeles"] if ligne["nom"] == "sept" and ligne["lam"] == 0.6][0]
    perte = round(100 * (sept["base"]["exactitude"] - sept["ajout"]["exactitude"]))
    assert f"Le modèle à 7 critères perd {perte} points sur des plats nouveaux" in texte


def test_le_readme_cite_la_courbe(resultats):
    """Le premier et le dernier point de la courbe d'apprentissage, à 7 et à 3 critères."""
    if "courbeApprentissage" not in resultats:
        pytest.skip("la courbe d'apprentissage n'est pas encore calculée")
    texte = README.read_text(encoding="utf-8")
    courbe = resultats["courbeApprentissage"]
    for nom, nombre in (("sept", 7), ("trois", 3)):
        premier, dernier = courbe[nom][0], courbe[nom][-1]
        attendu = (f"À {nombre} critères, l'exactitude sur des plats jamais vus passe de "
                   f"{pourcentage(premier['tenusAPart'])} ({premier['taille']} plats appris) à "
                   f"{pourcentage(dernier['tenusAPart'])} ({dernier['taille']} plats appris)")
        assert attendu in texte, attendu


def test_le_readme_cite_les_modeles_sur_375_plats(resultats):
    """Chaque ligne du tableau des modèles appris sur les 375 plats, et leurs paires inversées."""
    if "mrsortEtendu" not in resultats:
        pytest.skip("les modèles sur 375 plats ne sont pas encore appris")
    texte = README.read_text(encoding="utf-8")
    for modele in resultats["mrsortEtendu"]["modeles"]:
        ligne = (f"| {len(modele['criteres'])} critères | {virgule(modele['lam'], 1)} | "
                 f"{modele['bienRanges']}/{modele['total']} | {pourcentage(modele['exactitude'])} | "
                 f"{pourcentage(modele['aUneClassePres'])} |")
        assert ligne in texte, ligne
    inversions = resultats["mrsortEtendu"]["inversions"]
    assert (f"Sur les 375 plats, il y a {inversions['sept']['nombre']} paires inversées à 7 critères "
            f"et {inversions['trois']['nombre']} à 3 critères") in texte
    sept = [m for m in resultats["mrsortEtendu"]["modeles"] if m["nom"] == "sept" and m["lam"] == 0.6][0]
    poids = ", ".join(virgule(sept["poids"][critere], 3) for critere in ("en", "sa", "so"))
    assert f"l'énergie, les acides gras saturés et le sel portent l'essentiel ({poids.rsplit(', ', 1)[0]} et {poids.rsplit(', ', 1)[1]})" in texte
    assert all(sept["intervalles"][critere][0] >= 0.2 for critere in ("en", "sa", "so"))


def test_le_readme_cite_les_trois_apprentissages_sur_375_plats(resultats):
    """Le tableau des profils appris et du modèle complet sur les 375 plats, et les étapes du modèle complet à 7 critères."""
    if "mrsortEtenduProfils" not in resultats or "modeleCompletEtendu" not in resultats:
        pytest.skip("les apprentissages sur 375 plats ne sont pas encore calculés")
    texte = README.read_text(encoding="utf-8")
    for cle, nom in (("mrsortEtenduProfils", "profils appris"), ("modeleCompletEtendu", "tout appris")):
        for modele in resultats[cle]["modeles"]:
            garanti = "—" if modele.get("borne") is None else f"{modele['borne']}{' (prouvé)' if modele['optimal'] else ''}"
            ligne = (f"| {len(modele['criteres'])} critères | {nom} | {virgule(modele['lam'], 1)} | "
                     f"{modele['bienRanges']}/{modele['total']} | {garanti} | {pourcentage(modele['aUneClassePres'])} |")
            assert ligne in texte, ligne
    sept = [m for m in resultats["modeleCompletEtendu"]["modeles"] if m["nom"] == "sept" and m["lam"] == 0.6][0]
    assert f"tout appris : {' → '.join(map(str, sept['historique'][:-1]))})" in texte
    # Le premier tour du modèle complet refait l'apprentissage des profils, arrêté par la même limite de temps
    profils = [m for m in resultats["mrsortEtenduProfils"]["modeles"] if m["nom"] == "sept" and m["lam"] == 0.6][0]
    assert f"trouve {sept['historique'][0]} plats au lieu de {profils['bienRanges']}" in texte


def test_le_readme_cite_la_validation_croisee(resultats):
    """
    Le tableau de la validation croisée : une ligne par apprentissage, avec l'exactitude moyenne
    des parts, leur écart-type, les plats bien rangés sur les 375 et les parts où l'optimum est prouvé.
    """
    if "validationCroisee" not in resultats:
        pytest.skip("la validation croisée n'est pas encore calculée")
    texte = README.read_text(encoding="utf-8")
    noms = {"poids": "poids appris", "profils": "profils appris", "complet": "tout appris"}
    for ligne in resultats["validationCroisee"]["modeles"]:
        parts, comparaison = ligne["parts"], ligne["comparaison"]
        prouvees = "—" if parts[0]["optimal"] is None else f"{sum(1 for part in parts if part['optimal'])}/{len(parts)}"
        attendue = (f"| {len(ligne['criteres'])} critères | {noms[ligne['mode']]} | {virgule(ligne['lam'], 1)} | "
                    f"{pourcentage(ligne['exactitudeMoyenne'])} | {virgule(100 * ligne['ecartType'], 1)} points | "
                    f"{comparaison['bienRanges']}/{comparaison['total']} | {pourcentage(comparaison['aUneClassePres'])} | "
                    f"{prouvees} |")
        assert attendue in texte, attendue


def test_le_readme_commente_la_validation_croisee(resultats):
    """
    Le commentaire de la validation croisée : ce que les profils appris gagnent sur les poids appris
    (en moyenne et part par part), ce que donne le modèle complet, le cas des 3 critères, et combien
    l'exactitude varie d'une part à l'autre.
    """
    if "validationCroisee" not in resultats or "modeleCompletEtendu" not in resultats:
        pytest.skip("la validation croisée n'est pas encore calculée")
    texte = README.read_text(encoding="utf-8")
    lignes = {(ligne["nom"], ligne["mode"], ligne["lam"]): ligne for ligne in resultats["validationCroisee"]["modeles"]}

    def parts(nom, mode, lam):
        """Les plats bien rangés de chaque part, pour un apprentissage."""
        return [part["bienRanges"] for part in lignes[(nom, mode, lam)]["parts"]]

    def moyenne(nom, mode, lam):
        """L'exactitude moyenne d'un apprentissage, en pourcentage."""
        return pourcentage(lignes[(nom, mode, lam)]["exactitudeMoyenne"])

    # À 7 critères et λ = 0,6 : les profils appris font mieux que les poids appris, sauf dans une part, à égalité
    profils, poids = parts("sept", "profils", 0.6), parts("sept", "poids", 0.6)
    meilleures = sum(1 for a, b in zip(profils, poids) if a > b)
    assert all(a >= b for a, b in zip(profils, poids))
    assert (f"{moyenne('sept', 'profils', 0.6)} contre {moyenne('sept', 'poids', 0.6)} à λ = 0,6, "
            f"mieux dans {meilleures} parts sur {len(profils)}") in texte
    # À λ = 0,7 : mieux dans toutes les parts
    assert all(a > b for a, b in zip(parts("sept", "profils", 0.7), parts("sept", "poids", 0.7)))
    assert f"mieux dans les 5 parts ({moyenne('sept', 'profils', 0.7)} contre {moyenne('sept', 'poids', 0.7)})" in texte
    # Le modèle complet : sur des plats nouveaux, puis sur les 375 plats qu'il a appris
    assert (f"{moyenne('sept', 'complet', 0.6)} à λ = 0,6 et {moyenne('sept', 'complet', 0.7)} à λ = 0,7, "
            f"contre {moyenne('sept', 'profils', 0.6)} et {moyenne('sept', 'profils', 0.7)} pour les profils appris") in texte
    complets = {m["lam"]: m["bienRanges"] for m in resultats["modeleCompletEtendu"]["modeles"] if m["nom"] == "sept"}
    assert f"({complets[0.6]} et {complets[0.7]})" in texte
    # À 3 critères : la meilleure moyenne est aux poids appris, mais pas dans toutes les parts
    trois = [ligne["exactitudeMoyenne"] for (nom, _, _), ligne in lignes.items() if nom == "trois"]
    assert lignes[("trois", "poids", 0.6)]["exactitudeMoyenne"] == max(trois)
    assert (f"({moyenne('trois', 'poids', 0.6)}, contre {moyenne('trois', 'profils', 0.6)} et "
            f"{moyenne('trois', 'profils', 0.7)} pour les profils appris)") in texte
    for lam in (0.6, 0.7):
        devant = sum(1 for a, b in zip(parts("trois", "profils", lam), parts("trois", "poids", lam)) if a > b)
        assert f"dans {devant} parts sur 5" in texte
    profils375 = [m for m in resultats["mrsortEtenduProfils"]["modeles"] if m["nom"] == "trois" and m["lam"] == 0.6][0]
    poids375 = [m for m in resultats["mrsortEtendu"]["modeles"] if m["nom"] == "trois" and m["lam"] == 0.6][0]
    assert f"({profils375['bienRanges']} contre {poids375['bienRanges']})" in texte
    # L'écart-type entre les parts, du plus petit au plus grand
    ecarts = [ligne["ecartType"] for ligne in lignes.values()]
    assert f"de {virgule(100 * min(ecarts), 1)} à {virgule(100 * max(ecarts), 1)} points" in texte


def test_le_readme_cite_les_profils_appris(resultats):
    """Le tableau des modèles aux profils appris (avec le maximum prouvé), et ce qu'ils gagnent sur des plats jamais vus."""
    if "mrsortProfils" not in resultats or "generalisation" not in resultats:
        pytest.skip("les modèles aux profils appris ne sont pas encore calculés")
    texte = README.read_text(encoding="utf-8")
    for modele in resultats["mrsortProfils"]["modeles"]:
        ligne = (f"| {len(modele['criteres'])} critères | {virgule(modele['lam'], 1)} | "
                 f"{modele['bienRanges']}/{modele['total']} | {modele['borne']}{' (prouvé)' if modele['optimal'] else ''} | "
                 f"{pourcentage(modele['aUneClassePres'])} |")
        assert ligne in texte, ligne
    lignes = {(l["nom"], l["mode"], l["lam"]): l for l in resultats["generalisation"]["modeles"]}
    profils, poids = lignes[("sept", "profils", 0.6)], lignes[("sept", "poids", 0.6)]
    assert (f"sur les plats ajoutés, jamais vus, {pourcentage(profils['ajout']['exactitude'])} au lieu de "
            f"{pourcentage(poids['ajout']['exactitude'])}") in texte


def test_le_readme_cite_le_modele_complet(resultats):
    """Le modèle complet (ses étapes, sa note sur les plats jamais vus) et la réponse à la question 1 du sujet."""
    if "modeleComplet" not in resultats:
        pytest.skip("le modèle complet n'est pas encore appris")
    texte = README.read_text(encoding="utf-8")
    complet = resultats["modeleComplet"]
    sept = [m for m in complet["modeles"] if m["nom"] == "sept" and m["lam"] == 0.6][0]
    assert f"{' → '.join(map(str, sept['historique'][:-1]))} plats bien rangés" in texte
    ligne = [l for l in resultats["generalisation"]["modeles"] if l["nom"] == "sept" and l["mode"] == "complet" and l["lam"] == 0.6][0]
    assert f"le meilleur sur les plats jamais vus ({pourcentage(ligne['ajout']['exactitude'])})" in texte
    exact = complet["exact"]
    assert exact["trois"]["existe"] is False and f"{exact['trois']['paires']} paires inversées" in texte
    if exact["sept"]["existe"] is None:
        meilleur = max(m["bienRanges"] for m in complet["modeles"] if m["nom"] == "sept")
        assert (f"range {meilleur} plats sur 125, et le solveur, en {exact['sept']['limiteSecondes'] // 60} minutes, n'a ni "
                f"trouvé de modèle exact ni prouvé qu'il n'en existe pas") in texte
