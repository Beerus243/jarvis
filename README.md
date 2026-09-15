# JARVIS

Assistant personnel Python V7.7, vocal par défaut avec « Hey Jarvis » et Kokoro :
actions PC, mémoire corrigible, tâches persistantes, rappels proactifs et
vision ponctuelle de l'écran ou de la webcam après configuration.

Le [bilan V5](docs/V5_IMPLEMENTATION.md) décrit les ajouts, les validations et les limites avant la vision.
La [vision V6](docs/V6_VISION.md) décrit les nouvelles commandes et le choix du
fournisseur d'analyse des images.
Les lots 6.3 à 6.9 ajoutent ciblage, lecture structurée, diagnostic de fichiers,
propositions d’action, routines et choix du fournisseur. Le [guide V6.9](docs/V6_9.md)
donne les commandes, les essais réalisés et les limites. La [roadmap](docs/ROADMAP_V6.md)
récapitule leur état.

Les lots [V7.0 à V7.7](docs/V7_7.md) ajoutent les sessions de projet, les
préférences de pause corrigibles, les questions, les propositions contextualisées,
les points de reprise et le démarrage automatique à la connexion au bureau.
La [roadmap V7](docs/ROADMAP_V7.md) distingue cette intégration de l’évaluation
quotidienne à venir ; les [résultats de validation](docs/VALIDATION_V7_7.md)
détaillent les tests et leurs limites.

## Installation

```bash
source .venv-kokoro-cuda/bin/activate
python -m pip install -r requirements-voice-cuda.txt
```

Pour Groq, définir `GROQ_API_KEY` dans `.env`. Le modèle par défaut est
`openai/gpt-oss-120b` et peut être changé avec `MODEL`.

La vision réutilise cette clé avec son propre modèle, `qwen/qwen3.6-27b`.
« Regarde mon écran » ou « regarde avec ma webcam » envoie une image à Groq,
puis lit l'analyse avec Kokoro. Les fichiers temporaires sont supprimés après
l'analyse ; une seule image reste en mémoire vive pendant deux minutes pour
« explique cette erreur » ou « lis ce texte ». « Regarde à nouveau » reprend
une capture, « oublie ce que tu as vu » efface ce contexte temporaire.
Les options sont détaillées dans le [guide V6](docs/V6_VISION.md).

« Surveille cette compilation pendant cinq minutes » active une surveillance
d'écran limitée : au moins 30 secondes entre observations, 10 analyses Groq
maximum, deux résultats concordants avant une alerte. « Que surveilles-tu »
donne son état ; « arrête la surveillance » l'arrête. Le runtime doit être
actif (lancement habituel sans `--no-proactive`).

« Capture la fenêtre active », « capture une zone de l'écran » et
« enregistre mon écran pendant trente secondes » enregistrent des fichiers
locaux. « Arrête la vidéo » termine l'enregistrement. Les images vont dans
`~/Pictures/Jarvis`, les vidéos dans `~/Videos/Jarvis`, avec des noms uniques.
La sélection vidéo et de zone utilise Spectacle sous KDE Wayland.
Voir les [commandes de capture et leurs limites](docs/CAPTURES.md).

Nouveautés vocales : « regarde la fenêtre active », « définis la zone 0 0 800 600 »,
« lis précisément la cible », « diagnostique cette erreur avec le fichier … »,
« prépare la correction », « quand je code, préviens-moi des erreurs de compilation ».
« Vérifie l'état de tes capacités » donne le diagnostic. Le mode local optionnel
nécessite un modèle visuel Ollama installé ; aucun repli cloud n'est automatique.

Le profil `requirements-voice-cuda.txt` conserve Torch 2.6.0 + CUDA 11.8,
Kokoro 0.9.4 et Transformers 5.15.1. `requirements.txt` est le profil CPU
historique ; ne pas l’installer dans cet environnement CUDA.

## Lancement

Depuis la racine du projet :

```bash
.venv-kokoro-cuda/bin/python main.py
```

Sans option, `main.py` démarre maintenant le mode vocal, précharge Kokoro et
annonce « Bonjour Fabrice. Je suis prêt. ». Aucune saisie clavier n’est requise.
Le chargement initial peut prendre plusieurs dizaines de secondes.

Options disponibles :

```bash
.venv-kokoro-cuda/bin/python main.py --list-microphones
.venv-kokoro-cuda/bin/python main.py --text  # clavier uniquement sur demande
# Facultatif : choisir un microphone et adapter la capture
.venv-kokoro-cuda/bin/python main.py --voice --sample-rate 44100 --wake-threshold 0.4 --command-seconds 12
```

Dites **« Hey Jarvis »**, attendez le signal et l'affichage **« J'écoute votre
commande »**, puis parlez. Une pause de 1,5 seconde termine la phrase ; la capture
est plafonnée à 20 secondes par défaut (`--command-seconds` permet de l'allonger).
`--silence-seconds 2` autorise des pauses plus longues. Le seuil de début de
parole est de 120 (`--speech-threshold`), avec un seuil plus bas pendant la
phrase pour conserver les mots prononcés doucement. Une commande atteignant
la durée maximale est signalée et n'est pas exécutée partiellement.
Après la réponse, vous disposez de 8 secondes pour répondre sans répéter le
mot-clé, notamment pour dire « confirme » ou « annule ». « Merci Jarvis » ou
« retour en veille » termine cet échange. Pendant une réponse vocale, répétez
« Hey Jarvis » pour interrompre la lecture puis donnez votre nouvelle commande.
L'interruption annule les morceaux de réponse restants ; une inférence CUDA
déjà commencée peut finir en arrière-plan, mais son audio ne sera pas joué.
Attendez le signal et « J'écoute votre commande » pour donner la suite.
Si la transcription ne comprend pas une commande après le réveil, Jarvis
propose une nouvelle tentative après le signal. Pendant le suivi, un audio
incompréhensible ramène discrètement en veille. « Hey Jarvis » seul, même
transcrit « est Jarvis », relance l'écoute sans solliciter le modèle de dialogue.
« Quitter » ou `Ctrl+C` arrête le programme.

La détection du mot-clé est locale (`openwakeword`, modèle `hey_jarvis`). La
transcription de la commande utilise Google en français via `SpeechRecognition`
et nécessite Internet. `PyAudio` doit pouvoir accéder au microphone ; le
périphérique système est sélectionné par défaut. Le microphone est fermé
pendant le signal et la transcription ; il est rouvert pendant la réponse pour
détecter une interruption. `--no-barge-in` désactive ce comportement.
Le mode vocal utilise le moteur Kokoro existant : français `f`, voix `ff_siwis`,
sortie 24 kHz et CUDA si disponible, sinon CPU. Les réponses, confirmations et
rappels sont prononcés par ce même moteur. Si sa préparation échoue, le
programme signale l’erreur sans basculer au clavier ni remplacer la voix.
Le secours eSpeak reste limité aux anciens chemins de diagnostic.

Au retour en veille, « micro prêt » est affiché après préparation du détecteur
et ouverture du flux : vous pouvez alors dire « Hey Jarvis ». Le moteur ne
charge que ce mot-clé et restaure un état silencieux déjà préparé pour éviter
les premières trames ignorées après une réinitialisation. Les notifications
sont consultées une fois par seconde pendant l'écoute. Si plus d'une
demi-seconde d'audio s'accumule, les anciennes trames sont abandonnées pour
revenir au son récent. Le gain du micro et le seuil de « Hey Jarvis » sont conservés.

Les dépendances vocales CUDA figurent dans `requirements-voice-cuda.txt`. Si `.venv-kokoro-cuda/bin/python` est
absent ou si un module vocal manque, réparez l'environnement Python avant
l'essai au microphone. `--help` et le terminal ne chargent pas les modèles de
détection vocale. Le mode « Hey Jarvis, commande » sans pause n'est pas encore
pris en charge.

Diagnostic local du micro (250 ms oubliées aussitôt), du modèle et de la synthèse :

```bash
.venv-kokoro-cuda/bin/python -m scripts.check_voice
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
.venv-kokoro-cuda/bin/python -m scripts.test_v5
```

Ce lanceur utilise une copie temporaire pour préserver les données personnelles.
`pytest.ini` sélectionne la suite automatisée ; plusieurs autres fichiers
`test_*.py` historiques sont des scripts interactifs et ne font pas partie de cette suite.

Le scénario mémoire ciblé peut être lancé ainsi :

```bash
python -m tests.test_memory_v19
```
