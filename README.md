# JARVIS

Assistant personnel Python V5.18, utilisable au clavier ou avec « Hey Jarvis » :
actions PC, mémoire corrigible, tâches persistantes et rappels proactifs.

Le [bilan V5](docs/V5_IMPLEMENTATION.md) décrit les ajouts, les validations et les limites avant la vision.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Pour Groq, définir `GROQ_API_KEY` dans `.env`. Le modèle par défaut est
`openai/gpt-oss-120b` et peut être changé avec `MODEL`.

## Lancement

Depuis la racine du projet :

```bash
.venv/bin/python main.py
```

Pour l'activation vocale en deux temps :

```bash
.venv/bin/python main.py --list-microphones
.venv/bin/python main.py --voice
# Facultatif : choisir un microphone et adapter la capture
.venv/bin/python main.py --voice --sample-rate 44100 --wake-threshold 0.4 --command-seconds 12
```

Dites **« Hey Jarvis »**, attendez le signal et l'affichage **« J'écoute votre
commande »**, puis parlez. Une pause de 0,8 seconde termine la phrase ; la capture
est plafonnée à 5 secondes par défaut (`--command-seconds` permet de l'allonger).
Après la réponse, vous disposez de 8 secondes pour répondre sans répéter le
mot-clé, notamment pour dire « confirme » ou « annule ». « Merci Jarvis » ou
« retour en veille » termine cet échange. Pendant une réponse vocale, répétez
« Hey Jarvis » pour interrompre la lecture puis donnez votre nouvelle commande.
« Quitter » ou `Ctrl+C` arrête le programme.

La détection du mot-clé est locale (`openwakeword`, modèle `hey_jarvis`). La
transcription de la commande utilise Google en français via `SpeechRecognition`
et nécessite Internet. `PyAudio` doit pouvoir accéder au microphone ; le
périphérique système est sélectionné par défaut. Le microphone est fermé
pendant le signal et la transcription ; il est rouvert pendant la réponse pour
détecter une interruption. `--no-barge-in` désactive ce comportement.
Kokoro est utilisé s'il est disponible ; sinon eSpeak NG produit la voix française
localement. Sur le `.venv` Python 3.14 réparé, eSpeak NG sert actuellement de secours.

Les dépendances figurent dans `requirements.txt`. Si `.venv/bin/python` est
absent ou si un module vocal manque, réparez l'environnement Python avant
l'essai au microphone. `--help` et le terminal ne chargent pas les modèles de
détection vocale. Le mode « Hey Jarvis, commande » sans pause n'est pas encore
pris en charge.

Diagnostic local du micro (250 ms oubliées aussitôt), du modèle et de la synthèse :

```bash
.venv/bin/python -m scripts.check_voice
```

## Proactivité et tâches

L'horloge fonctionne tant que `main.py` reste ouvert, même sans saisie. En terminal,
les notifications sont affichées ; en mode vocal, elles sont aussi prononcées
entre les échanges. `--no-proactive` désactive l'horloge et l'exécution en arrière-plan.

- `rappelle-moi dans 10 minutes de faire une pause`
- `rappelle-moi demain à 9h de reprendre Jarvis`
- `liste mes rappels`, `annule le rappel <identifiant>`
- `mode silencieux`, `reprends les notifications`, `rappelle-moi plus tard`
- `ouvre Firefox puis ouvre GitHub` : tâche en plusieurs étapes.
- `mes tâches`, `annule la tâche`, `pause la tâche`, `reprends la tâche <identifiant>`
- `configure ma routine de travail : ouvre Firefox puis ouvre GitHub`, puis `au boulot`.
- `mission vérifie l'état du PC et donne-moi l'heure` : planification Groq limitée à 8 étapes.

Les tâches, rappels et préférences persistent dans `data/runtime.sqlite3`.
Un rappel échu pendant l'arrêt sera présenté au prochain lancement. Les tâches
interrompues nécessitent une reprise explicite ; une étape au résultat inconnu
n'est pas rejouée automatiquement. La mission utilise un catalogue fixe d'outils
et s'arrête sur un échec, une répétition ou sa limite d'étapes.

## Souvenirs corrigibles

`retiens éditeur : VS Code`, `corrige éditeur : Vim`, `oublie éditeur` et
`liste mes souvenirs` gèrent les faits explicites. Ils sont datés et transmis au
modèle avec le profil et les souvenirs pertinents. Les écritures JSON sont
verrouillées et atomiques ; l'historique récent conserve jusqu'à 100 messages.

L'[audit du branchement des commandes](docs/VOICE_ACTIVATION_AUDIT.md) détaille
les corrections, les tests et les fonctionnalités encore partielles.

Les données persistantes sont dans `data/`. Les chemins sont centralisés dans
`config/settings.py`, donc le lancement ne dépend pas du dossier courant.

## Architecture

```text
main.py                 point d'entrée terminal et --voice
config/                 chemins et paramètres
core/                   orchestration, conversation et routage
memory/                 mémoire structurée, sémantique et ranking hybride
ai/                     adaptateur Groq compatible OpenAI
tools/                  outils système
personality/            réponses déterministes
voice/                  détection locale, capture, transcription et réponse vocale
data/                   user.json, historique et conversation
scripts/                utilitaires exécutables
tests/                  tests et scénarios de non-régression
```

## Mémoire

`data/user.json` conserve les souvenirs, leurs catégories, dates, importances,
IDs et embeddings. La recherche combine similarité sémantique, mots informatifs,
catégorie et correspondance du sujet précis. Les pondérations et le seuil sont
dans `config/settings.py`.

Pour compléter les embeddings absents :

```bash
python -m scripts.update_memory
```

Pour nettoyer les doublons :

```bash
python -m scripts.clean_memory
```

## Tests

```bash
.venv/bin/python -m scripts.test_v5
```

Ce lanceur utilise une copie temporaire pour préserver les données personnelles.
`pytest.ini` sélectionne la suite automatisée ; plusieurs autres fichiers
`test_*.py` historiques sont des scripts interactifs et ne font pas partie de cette suite.

Le scénario mémoire ciblé peut être lancé ainsi :

```bash
python -m tests.test_memory_v19
```
