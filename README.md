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

Les données persistantes sont dans `data/`. Les chemins sont centralisés dans
`config/settings.py`, donc le lancement ne dépend pas du dossier courant.

## Architecture

```text
main.py                 point d'entrée terminal
config/                 chemins et paramètres
core/                   orchestration, conversation et routage
memory/                 mémoire structurée, sémantique et ranking hybride
ai/                     adaptateur Groq compatible OpenAI
tools/                  outils système
personality/            réponses déterministes
voice/                  modules vocaux existants, sans nouvelle intégration
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

