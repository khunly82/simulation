# Simulateur d'entretien technique (style Coderbyte)

Deux versions, mêmes règles et même banque de questions :

- **Web (`web/`)** : recommandée, fonctionne sur Mac, Windows et Linux (voir ci-dessous).
- **Bureau (`coderbyte_sim/`)** : Tkinter, non fonctionnelle sur certains Python de macOS.

## Version web (Mac / Windows / Linux)

Prérequis : [Node.js](https://nodejs.org) 18+ (sur Mac : `brew install node`) et une connexion
internet au premier chargement (le Python du candidat tourne dans le navigateur via Pyodide,
téléchargé depuis un CDN) — aucun Python à installer.

```sh
cd web
node server.js        # ou : npm start
```

Ouvrir <http://localhost:3000>. Options dans l'URL : `?minutes=5` (durée réduite),
`?seed=42` (tirage reproductible). Les rapports sont écrits dans `results/` ; sans le
serveur Node (`python3 -m http.server -d web/public`), un bouton permet de les télécharger.
Recharger la page ne remet pas le chrono à zéro (session conservée dans le navigateur).
Tests de la logique : `cd web && npm test`.

---

## Version bureau (Tkinter)

Application de bureau (Python 3.10+, Tkinter, **aucune dépendance**) qui simule un test
d'entretien : 5 questions tirées de la banque, 50 minutes au total, pas de retour en arrière.
Les candidats codent **en Python uniquement**.

## Lancer

```powershell
python -m coderbyte_sim
```

Options : `--minutes 10` (durée réduite pour essayer), `--seed 42` (tirage reproductible).

## Règles du test

- 5 questions : 2 faciles, 2 moyennes, 1 difficile (tirage aléatoire), présentées dans cet ordre.
- Un seul chrono de 50 min. À l'expiration, le test s'arrête et le code en cours est conservé ;
  les questions non atteintes comptent 0.
- « Valider et question suivante » est définitif (confirmation demandée) : pas de retour.
- Bouton **Exécuter les tests d'exemple** (illimité) : n'exécute que les cas visibles de l'énoncé.
- À la fin, correction sur **tous** les cas (exemples + cachés). Score = moyenne des ratios
  de cas réussis par question. Détail et code sauvegardés dans `results/*.json`.
- Les sorties sont comparées en texte (`str(valeur)`), comme sur Coderbyte : renvoyer `"true"`
  et non `True` quand l'énoncé parle de la chaîne `true`.
- Chaque test a 3 s maximum (boucle infinie = échec du test) ; le code tourne dans un
  sous-processus séparé.

## Banque de questions

36 questions (12 faciles, 12 moyennes, 12 difficiles) dont les énoncés viennent de
[gutty333/Easy-Programming-Challenges](https://github.com/gutty333/Easy-Programming-Challenges)
(dépôt de solutions C++ : seuls les énoncés sont repris, les tests et solutions Python
sont propres à ce projet). Ajouter une question :

1. écrire la solution de référence dans `tools/references.py` (même nom que la fonction demandée) ;
2. ajouter l'énoncé dans `tools/statements.json` et une entrée dans la liste `Q` de
   `tools/build_bank.py` (cas d'exemple visibles + entrées cachées) ;
3. `python tools/build_bank.py` régénère `coderbyte_sim/bank.json` et `web/public/bank.json` (les sorties attendues des cas
   cachés sont calculées par la référence) ;
4. `python -m unittest discover -s tests` vérifie que chaque référence passe tous ses tests.

Les énoncés ambigus ont été précisés par un champ « Note » affiché au candidat
(ex. horloge circulaire pour `TimeDifference`).

## Structure

```
coderbyte_sim/   app.py (interface) · engine.py (session, correction) · runner.py (sandbox) · bank.json
tools/           références + générateur de la banque (non nécessaires pour passer le test)
tests/           tests unitaires du moteur et de la banque
results/         rapports générés (ignorés par git)
```

Limites connues : en version bureau le sous-processus n'est pas un vrai bac à sable (pas
d'isolation réseau/fichiers) ; en version web le code reste dans le navigateur, mais
`bank.json` (cas cachés et résultats attendus) est lisible via les outils de développement.
À utiliser en entretien de confiance, pas comme plateforme publique.
Les références sont dans `tools/` : ne pas les distribuer aux candidats.
