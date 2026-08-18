from memory import find_semantic_memory


QUESTIONS = [

    "Quelle technologie gère mon serveur ?",

    "Quelle technologie utilise mon interface ?",

    "Quelle est ma couleur préférée ?",

    "Qu'est-ce que j'aime regarder ?",

    "Avec quel langage ai-je développé le projet ?",

    "Où sont stockées les données ?"

]


print("=" * 60)
print("TEST MÉMOIRE JARVIS V1.9")
print("=" * 60)


for question in QUESTIONS:

    print()
    print("-" * 60)

    print(
        f"Question : {question}"
    )

    print("-" * 60)


    souvenir = find_semantic_memory(
        question,
        debug=True
    )


    if souvenir:

        print()

        print(
            "✓ SOUVENIR RETENU"
        )

        print()

        print(
            f"ID         : "
            f"{souvenir.get('id')}"
        )

        print(
            f"Catégorie  : "
            f"{souvenir.get('categorie')}"
        )

        print(
            f"Contenu    : "
            f"{souvenir.get('contenu')}"
        )

        print(
            f"Importance : "
            f"{souvenir.get('importance')}"
        )

    else:

        print()

        print(
            "✗ Aucun souvenir suffisamment pertinent"
        )


print()
print("=" * 60)# Mission

Tu travailles directement sur mon projet JARVIS Python dans VS Code.

Ton objectif est de reprendre le projet existant, de l'auditer, de le restructurer proprement et de corriger les problèmes d'architecture sans détruire le travail déjà réalisé.

IMPORTANT :

- Ne recommence PAS le projet depuis zéro.
- Ne remplace PAS mon architecture par une architecture totalement différente sans raison.
- Préserve le comportement actuel de JARVIS.
- Préserve les fonctionnalités déjà fonctionnelles.
- Préserve les données existantes dans `user.json`.
- Préserve le système de mémoire sémantique déjà développé.
- Préserve les embeddings existants lorsqu'ils sont valides.
- Ne supprime aucune fonctionnalité fonctionnelle simplement pour simplifier.
- Avant toute modification importante, inspecte les fichiers existants.
- Ne suppose jamais qu'un fichier contient quelque chose : lis-le.
- Après chaque groupe de modifications, lance les tests.
- Corrige les imports cassés après déplacement des fichiers.
- Le projet doit continuer à être exécutable avec le même environnement virtuel `.venv`.

## ÉTAT ACTUEL DU PROJET

JARVIS est actuellement un assistant Python en terminal.

Le projet possède notamment :

- `main.py`
- `memory.py`
- `semantic_memory.py`
- `user.json`
- plusieurs fichiers de tests, notamment :
  - `test_semantic_threshold.py`
  - `test_memory_v18.py`
- probablement d'autres fichiers Python liés aux outils, à la personnalité, aux réponses ou à la configuration.

Le système de mémoire a déjà évolué jusqu'à environ JARVIS V1.9.

Il utilise notamment :

- mémoire structurée
- catégories
- importance
- embeddings
- recherche sémantique
- similarité
- recherche lexicale
- score hybride
- détection de catégorie
- score de spécificité
- tests de mémoire

Le projet utilise notamment `sentence-transformers` et PyTorch pour la partie embeddings.

Le système doit continuer à fonctionner sur CPU.

---

# OBJECTIF FINAL DE CETTE MISSION

À la fin de ta mission, je veux avoir une base propre ressemblant à une vraie application Python organisée.

Proposition d'architecture cible :

```text
jarvis/
│
├── main.py
│
├── config/
│   ├── __init__.py
│   └── settings.py
│
├── core/
│   ├── __init__.py
│   ├── assistant.py
│   ├── router.py
│   └── response.py
│
├── memory/
│   ├── __init__.py
│   ├── memory.py
│   ├── semantic_memory.py
│   ├── memory_cleaner.py
│   └── memory_utils.py
│
├── ai/
│   ├── __init__.py
│   └── ...
│
├── tools/
│   ├── __init__.py
│   ├── browser.py
│   ├── system.py
│   ├── music.py
│   └── ...
│
├── personality/
│   ├── __init__.py
│   └── personality.py
│
├── data/
│   └── user.json
│
├── tests/
│   ├── __init__.py
│   ├── test_memory.py
│   ├── test_semantic_memory.py
│   ├── test_threshold.py
│   ├── test_memory_v18.py
│   └── ...
│
├── scripts/
│   ├── clean_memory.py
│   └── ...
│
├── requirements.txt
├── README.md
└── .gitignore
```

Cette architecture est une BASE.

Tu dois l'adapter aux fichiers réellement présents dans mon projet.

Ne crée pas artificiellement 30 fichiers inutiles.

---

# PHASE 1 — AUDIT

Commence par examiner tout le projet.

Analyse :

- tous les `.py`
- `main.py`
- `memory.py`
- `semantic_memory.py`
- `user.json`
- tous les fichiers de tests
- les imports
- les dépendances
- les fonctions utilisées
- les appels entre modules
- les fichiers inutilisés
- les doublons
- les fonctions mortes
- les imports inutilisés
- les chemins codés en dur
- les éventuelles dépendances circulaires

Ne modifie rien immédiatement.

Commence par produire une analyse interne de l'architecture actuelle.

Identifie précisément :

1. le point d'entrée ;
2. le système mémoire ;
3. le système sémantique ;
4. les outils ;
5. la personnalité ;
6. les tests ;
7. les données ;
8. la configuration ;
9. les dépendances externes.

---

# PHASE 2 — STRUCTURATION

Crée les sous-dossiers nécessaires.

La racine doit devenir beaucoup plus propre.

`main.py` doit rester dans la racine.

Les tests doivent sortir de la racine et aller dans :

```text
tests/
```

Les scripts utilitaires comme `clean_memory.py` doivent aller dans :

```text
scripts/
```

La mémoire doit être regroupée dans :

```text
memory/
```

Les outils dans :

```text
tools/
```

La personnalité dans :

```text
personality/
```

Les données utilisateur dans :

```text
data/
```

La configuration dans :

```text
config/
```

Le cœur de JARVIS dans :

```text
core/
```

N'utilise pas un dossier si aucun fichier réel ne le justifie.

---

# PHASE 3 — IMPORTS

Après avoir déplacé les fichiers :

- corrige tous les imports ;
- utilise des imports Python propres ;
- ajoute les `__init__.py` nécessaires ;
- évite les imports relatifs excessivement complexes ;
- évite les imports circulaires.

Exemple :

```python
from memory.memory import remember
```

plutôt qu'un import dépendant du répertoire courant.

Le lancement depuis la racine doit fonctionner :

```bash
python main.py
```

et avec mon environnement :

```bash
/home/malangafabrice/dev/jarvis/.venv/bin/python main.py
```

---

# PHASE 4 — CHEMINS

Ne laisse pas les chemins dépendre du dossier depuis lequel la commande est lancée.

Par exemple, `user.json` doit être correctement trouvé même si un module est appelé depuis un autre dossier.

Centralise le chemin de données dans la configuration.

Par exemple :

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MEMORY_FILE = DATA_DIR / "user.json"
```

Adapte cela à l'architecture finale.

---

# PHASE 5 — MÉMOIRE

Refactorise proprement le système mémoire actuel.

Préserve les fonctions existantes importantes :

- `load_memory()`
- `save_memory()`
- `remember()`
- `analyze_memory()`
- `recall_memory()`
- `find_best_memory()`
- `find_semantic_memory()`
- `search_memory()`
- `update_missing_embeddings()`

Si certaines fonctions doivent être renommées ou séparées, fais-le proprement et mets à jour tous les appels.

Ne casse pas l'API interne inutilement.

---

# PHASE 6 — DONNÉES

Déplace :

```text
user.json
```

dans :

```text
data/user.json
```

mais conserve exactement les souvenirs existants.

Ne recrée pas artificiellement les souvenirs.

Ne perds aucune donnée.

Ne modifie pas le contenu des souvenirs sauf si cela est nécessaire pour réparer un format réellement invalide.

Conserve :

- id
- contenu
- catégorie
- date
- importance
- embedding

lorsqu'ils existent.

---

# PHASE 7 — NETTOYAGE DES DOUBLONS

Conserve le principe du nettoyage mémoire déjà développé.

Le nettoyage doit pouvoir :

- détecter les doublons exacts ;
- éviter de supprimer des souvenirs réellement différents ;
- préserver le souvenir le plus pertinent ;
- conserver les embeddings ;
- conserver les IDs valides ;
- ne pas casser `user.json`.

Le script doit rester exécutable séparément.

Par exemple :

```bash
python scripts/clean_memory.py
```

---

# PHASE 8 — MÉMOIRE SÉMANTIQUE

Conserve le système basé sur les embeddings.

Le système doit continuer à :

1. transformer la question en embedding ;
2. comparer avec les souvenirs ;
3. calculer la similarité ;
4. récupérer plusieurs candidats ;
5. classer les candidats ;
6. sélectionner le meilleur souvenir.

Ne remplace pas `sentence-transformers` par une autre technologie.

Ne télécharge pas un nouveau modèle inutilement.

Utilise le modèle déjà présent dans le projet.

---

# PHASE 9 — SCORING HYBRIDE

Le projet possède maintenant plusieurs dimensions de scoring.

Conserve l'idée :

```text
semantic score
+
lexical score
+
category score
+
specificity score
```

Le score final doit être calculé de manière cohérente.

Les pondérations doivent être centralisées et facilement modifiables.

Par exemple :

```python
SEMANTIC_WEIGHT = ...
LEXICAL_WEIGHT = ...
CATEGORY_WEIGHT = ...
SPECIFICITY_WEIGHT = ...
```

Ne choisis pas arbitrairement de nouvelles valeurs sans analyser les résultats actuels.

Documente brièvement pourquoi les valeurs retenues fonctionnent.

---

# PHASE 10 — PROBLÈME IMPORTANT À CORRIGER

Les tests précédents ont montré un problème :

Pour :

```text
Quelle technologie gère mon serveur ?
```

JARVIS peut parfois sélectionner :

```text
Le frontend de JARVIS utilise React.
```

au lieu de :

```text
Le backend du projet JARVIS utilise FastAPI.
```

Et pour :

```text
Qu'est-ce que j'aime regarder ?
```

JARVIS peut sélectionner :

```text
La couleur préférée de Fabrice est le jaune.
```

C'est incorrect.

Corrige le système de ranking.

Le système doit favoriser :

- la correspondance du sujet ;
- la correspondance de la catégorie ;
- la correspondance des termes importants ;
- la spécificité du souvenir ;
- la similarité sémantique.

Mais attention :

Une catégorie correcte ne doit PAS suffire à faire gagner un souvenir sémantiquement incorrect.

Exemple :

```text
Question : Qu'est-ce que j'aime regarder ?
Catégorie : preference
```

Le souvenir :

```text
La couleur préférée de Fabrice est le jaune.
```

est dans la bonne catégorie mais ne répond pas à la question.

Il doit donc être rejeté.

---

# PHASE 11 — DÉTECTION DE SPÉCIFICITÉ

Améliore le système de spécificité.

Exemples de concepts importants :

```text
serveur → backend
interface → frontend
langage → Python
données → PostgreSQL
regarder → films / animés
couleur → couleur
```

Mais ne crée pas un système gigantesque de synonymes codés en dur.

L'objectif est de fournir un mécanisme léger qui aide le ranking.

---

# PHASE 12 — SEUIL DE CONFIANCE

Le système doit distinguer :

```text
réponse fiable
```

de :

```text
candidat faible
```

Par exemple :

```text
score >= seuil
→ souvenir accepté
```

sinon :

```text
→ aucun souvenir suffisamment pertinent
```

Le seuil doit être configurable.

Il doit être testé avec plusieurs questions.

---

# PHASE 13 — CAS AMBIGUS

Ajoute des tests pour vérifier que JARVIS ne répond pas n'importe quoi.

Exemples :

```text
Quelle technologie gère mon serveur ?
```

attendu :

```text
FastAPI
```

```text
Quelle technologie utilise mon interface ?
```

attendu :

```text
React
```

```text
Quelle est ma couleur préférée ?
```

attendu :

```text
jaune
```

```text
Avec quel langage ai-je développé le projet ?
```

attendu :

```text
Python
```

```text
Où sont stockées les données ?
```

attendu :

```text
PostgreSQL
```

Et surtout :

```text
Qu'est-ce que j'aime regarder ?
```

Si aucun souvenir correspondant n'existe réellement dans `user.json`, JARVIS doit dire qu'il ne sait pas.

Il ne doit surtout PAS répondre :

```text
ta couleur préférée est le jaune
```

---

# PHASE 14 — TESTS

Regroupe tous les tests dans :

```text
tests/
```

Nettoie les noms.

Crée si nécessaire :

```text
tests/test_memory.py
tests/test_semantic_memory.py
tests/test_memory_ranking.py
tests/test_memory_threshold.py
tests/test_memory_v18.py
```

Évite les tests redondants.

Les tests doivent vérifier :

- chargement mémoire ;
- sauvegarde ;
- ajout ;
- catégories ;
- embeddings ;
- recherche sémantique ;
- ranking ;
- seuil ;
- rejet ;
- doublons.

---

# PHASE 15 — TEST DE NON-RÉGRESSION

Après les modifications, exécute les tests.

Puis lance :

```bash
python main.py
```

Teste au minimum :

```text
bonjour
qui suis-je
quel est mon objectif
quelle est ma couleur préférée
quelle technologie utilise mon interface
quelle technologie gère mon serveur
avec quel langage ai-je développé le projet
où sont stockées les données
quitter
```

Si une fonctionnalité qui fonctionnait avant ne fonctionne plus, corrige-la.

---

# PHASE 16 — GESTION DES ERREURS

Améliore la robustesse sans rendre le code inutilement compliqué.

Gère notamment :

- `user.json` absent ;
- `user.json` corrompu ;
- embedding absent ;
- embedding invalide ;
- souvenir sans catégorie ;
- souvenir sans importance ;
- modèle indisponible ;
- fichier manquant.

Les erreurs doivent être compréhensibles.

Ne masque pas silencieusement toutes les exceptions avec :

```python
except Exception:
    pass
```

---

# PHASE 17 — CONFIGURATION

Centralise les paramètres importants.

Par exemple :

```text
model name
memory file
semantic threshold
ranking weights
maximum results
```

dans :

```text
config/settings.py
```

Ne mets pas les paramètres critiques dispersés dans plusieurs fichiers.

---

# PHASE 18 — PERSONNALITÉ

Si `personality.py` existe, place-le dans :

```text
personality/personality.py
```

Préserve son comportement.

Ne transforme pas encore la personnalité en LLM.

Ne crée pas encore un système conversationnel complexe.

---

# PHASE 19 — OUTILS

Si les fonctions suivantes existent :

```text
open_browser
get_time
open_musique
```

ou équivalentes, organise-les dans :

```text
tools/
```

par domaine.

Par exemple :

```text
tools/browser.py
tools/system.py
tools/music.py
```

Ne change pas leur comportement fonctionnel.

---

# PHASE 20 — CORE

Si nécessaire, crée une couche `core/`.

Son rôle sera progressivement de gérer :

```text
entrée utilisateur
      ↓
analyse
      ↓
mémoire
      ↓
intention
      ↓
outil
      ↓
réponse
```

Mais ne construis pas encore le système vocal.

---

# PHASE 21 — PRÉPARATION POUR LE FUTUR LLM

Prépare l'architecture pour qu'un LLM puisse être ajouté plus tard.

Mais :

NE PAS intégrer de LLM maintenant.

Ne pas ajouter OpenAI.

Ne pas ajouter Groq.

Ne pas ajouter Ollama.

Ne pas ajouter une API externe simplement pour faire joli.

La mémoire et le routage doivent rester indépendants du futur LLM.

---

# PHASE 22 — PRÉPARATION VOCALE

IMPORTANT :

Cette mission s'arrête JUSTE AVANT l'intégration des commandes vocales.

Tu peux préparer une architecture permettant plus tard :

```text
voice/
    speech_to_text.py
    text_to_speech.py
    voice_controller.py
```

MAIS :

- ne développe pas le Speech-to-Text ;
- ne développe pas le Text-to-Speech ;
- ne configure pas le microphone ;
- ne configure pas le wake word ;
- ne configure pas PyAudio ;
- ne configure pas Whisper ;
- ne configure pas une voix TTS ;
- ne lance aucune conversation vocale.

Tu peux seulement laisser l'architecture prête à recevoir cette fonctionnalité.

La prochaine étape après cette mission sera une leçon dédiée :

# INTÉGRATION DES COMMANDES VOCALES

Tu dois t'arrêter avant cette leçon.

---

# PHASE 23 — README

Mets à jour `README.md`.

Documente :

- installation ;
- environnement virtuel ;
- lancement ;
- architecture ;
- mémoire ;
- tests ;
- nettoyage mémoire.

Exemple :

```bash
source .venv/bin/activate
python main.py
```

Tests :

```bash
pytest
```

ou les commandes réellement adaptées au projet.

---

# PHASE 24 — REQUIREMENTS

Analyse les imports réellement utilisés.

Crée ou mets à jour :

```text
requirements.txt
```

avec uniquement les dépendances réellement nécessaires.

Ne supprime pas une dépendance utilisée.

Ne rajoute pas de dépendances inutiles.

---

# PHASE 25 — GITIGNORE

Vérifie `.gitignore`.

Il doit notamment éviter de versionner :

```text
.venv/
__pycache__/
*.pyc
```

et éventuellement les fichiers sensibles.

ATTENTION :

Ne supprime pas `user.json` du projet si JARVIS en dépend actuellement, sauf si tu mets en place une solution équivalente sans perte de données.

---

# PHASE 26 — QUALITÉ DU CODE

Après la restructuration :

- supprimer les imports inutilisés ;
- supprimer les fonctions réellement mortes ;
- éviter les duplications ;
- améliorer les noms ;
- ajouter des docstrings aux fonctions importantes ;
- conserver des fonctions relativement courtes ;
- éviter les fichiers gigantesques lorsque leur séparation est naturelle.

Ne fais PAS une réécriture totale juste pour modifier le style.

---

# PHASE 27 — TEST FINAL OBLIGATOIRE

Avant de considérer la mission terminée :

1. vérifier que tous les imports fonctionnent ;
2. vérifier que `user.json` est toujours lisible ;
3. vérifier que les embeddings sont toujours utilisables ;
4. lancer les tests ;
5. lancer `main.py` ;
6. tester les commandes principales ;
7. vérifier la recherche mémoire ;
8. vérifier le nettoyage des doublons ;
9. vérifier qu'aucune donnée n'a été perdue.

---

# RÈGLE ABSOLUE

Ne considère PAS la mission terminée simplement parce que le code semble propre.

Le critère de réussite est :

```text
JARVIS fonctionne après la restructuration.
```

---

# RAPPORT FINAL

À la fin, donne-moi un rapport clair avec :

## 1. Architecture finale

Afficher l'arborescence réelle du projet.

## 2. Fichiers déplacés

Lister les anciens chemins et les nouveaux chemins.

## 3. Fichiers créés

Lister uniquement les fichiers réellement créés.

## 4. Fichiers modifiés

Lister les fichiers modifiés.

## 5. Corrections mémoire

Expliquer les problèmes corrigés dans :

- recherche sémantique ;
- ranking ;
- catégorie ;
- spécificité ;
- seuil ;
- doublons.

## 6. Tests

Indiquer exactement quelles commandes ont été exécutées et leurs résultats.

## 7. Fonctionnalités conservées

Confirmer que les fonctionnalités existantes fonctionnent toujours.

## 8. Problèmes restants

Lister uniquement les vrais problèmes encore présents.

## 9. Prochaine étape

Indiquer explicitement :

```text
PROCHAINE LEÇON :
INTÉGRATION DES COMMANDES VOCALES
```

Ne commence PAS cette leçon.

---

# CONSIGNE FINALE

Travaille directement sur les fichiers du projet.

Ne me donne pas seulement des conseils.

Inspecte → modifie → teste → corrige → reteste.

Ne détruis aucune fonctionnalité existante.

Ne perds aucune mémoire.

Ne commence pas l'intégration vocale.

Arrête-toi exactement juste avant cette étape.
print("FIN DU TEST")
print("=" * 60)