# JARVIS

Assistant personnel Python en terminal, avec mémoire structurée et recherche sémantique CPU.

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
python main.py
```

Pour l'activation vocale en deux temps :

```bash
python main.py --list-microphones
python main.py --voice
# Facultatif : choisir un microphone et adapter la capture
python main.py --voice --mic-device 3 --sample-rate 44100 --wake-threshold 0.4 --command-seconds 5
```

Dites **« Hey Jarvis »**, attendez le signal et l'affichage **« J'écoute votre
commande »**, puis parlez. La commande est enregistrée pendant 5 secondes par
défaut. Jarvis utilise le même cerveau que le terminal, répond puis revient en
veille. Dites « Hey Jarvis », puis « quitter » après le signal, ou utilisez
`Ctrl+C` pour arrêter.

La détection du mot-clé est locale (`openwakeword`, modèle `hey_jarvis`). La
transcription de la commande utilise Google en français via `SpeechRecognition`
et nécessite Internet. `PyAudio` doit pouvoir accéder au microphone ; le
périphérique système est sélectionné par défaut. Le microphone est fermé
pendant le signal, la transcription et la réponse. La synthèse vocale conserve
le moteur Kokoro existant.

Les dépendances figurent dans `requirements.txt`. Si `.venv/bin/python` est
absent ou si un module vocal manque, réparez l'environnement Python avant
l'essai au microphone. `--help` et le terminal ne chargent pas les modèles de
détection vocale. Le mode « Hey Jarvis, commande » sans pause n'est pas encore
pris en charge.

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
pytest
```

Le scénario mémoire ciblé peut être lancé ainsi :

```bash
python -m tests.test_memory_v19
```
