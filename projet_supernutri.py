"""
projet_supernutri.py : le SuperNutri-score, notre propre modèle MR-Sort (question 3.4).

Le SuperNutri-score ne cherche plus à reproduire le Nutri-Score. Il range les plats selon
neuf critères : les sept composantes du Nutri-Score, le groupe NOVA (degré de
transformation, à minimiser) et le nombre d'additifs (à minimiser). Une variante « verte »
ajoute le Green-Score (à maximiser), pour mesurer combien de plats changent de classe
quand l'environnement entre dans le vote.

Choix proposés, à arrêter en atelier de groupe (9/11) :
- poids : trois piliers, ce qui est à limiter, ce qui est à favoriser, la transformation ;
- profils : ancrés sur les seuils des allégations nutritionnelles du règlement CE 1924/2006
  (sucres ≤ 5 g, AGS ≤ 1,5 g, sel ≤ 0,3 g, fibres ≥ 3 g et 6 g), sur NOVA ≤ 3 et sur un
  nombre d'additifs de 0, 1, 3 et 5 ;
- seuil majoritaire λ = 0,7 ;
- sens des classes A′ à E′ : des repères de fréquence de consommation, sans conseil médical.

Le sujet demande aussi deux analyses de sensibilité, une comparaison au Nutri-Score et un
test sur la base d'un autre groupe.

État : à écrire en phase 3 (du 9/11 au 27/11).
"""


# --- Question 3.4 : le modèle ---

def superNutriScore(fichier, modele=None, variante="sante", sortie=None, afficher=True):
    """Range les plats avec le SuperNutri-score. variante : "sante" (9 critères) ou "vert" (10 critères)."""
    raise NotImplementedError("phase 3")


# --- Question 3.4 : analyses de sensibilité ---

def sensibilitePoids(produits, modele, amplitude=0.05, tirages=1000, graine=0):
    """Fait varier légèrement les poids (somme toujours égale à 1) et mesure la part des plats qui changent de classe."""
    raise NotImplementedError("phase 3")


def sensibiliteProfils(produits, modele, decalage=0.05):
    """Déplace les valeurs des profils (en gardant leur ordre) et liste les plats dont l'affectation change."""
    raise NotImplementedError("phase 3")


# --- Question 3.4 : comparaisons ---

def comparerAuNutriscore(produits, modele):
    """Compare le SuperNutri-score au Nutri-Score : plats qui montent ou descendent, et pourquoi."""
    raise NotImplementedError("phase 3")


def importerBaseAutreGroupe(fichier, correspondance):
    """
    Lit la base d'un autre groupe, en renommant ses colonnes selon la correspondance donnée.
    Le groupe NOVA et les additifs sont récupérés sur OFF par code-barres s'ils manquent.
    """
    raise NotImplementedError("phase 3")
