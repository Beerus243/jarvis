# JARVIS — MASTER TECHNICAL MAP

## CURRENT VERSION

État de référence : V5.17 (dernier commit `3b9b7d2`). Aucun fichier de version unique n’a été trouvé ; la version est déduite des commits et de la documentation.

## PROJECT STRUCTURE

- `main.py` : bootstrap texte/voix.
- `core/` : cerveau, 
intelligence, routage, actions, contexte PC et environnement.
- `core/actions/` : `PCAction`, `ActionResult`, executor PC et capture d’écran.
- `core/environment/` : audit, résolution, plans, confirmation, installation et vérification Flutter/Android/JDK.
- `memory/` : mémoire personnelle, état, historique, mémoire sémantique et projet.
- `personality/` : réponses contextuelles et suivi conversationnel.
- `tools/` : applications, navigateur, Spotify, projets et utilitaires système.
- `voice/` : capture, VAD, wake word, STT et sortie Kokoro.
- `tests/` : tests unitaires par domaine.
- `docs/` : commandes et rapports.
- `data/` : `user.json` et `conversation.json` runtime, non destinés au commit.

## CORE FILES

`brain.py` appelle l’orchestrateur et la personnalité. `orchestrator.py` construit la décision, planifie et exécute. `intelligence.py` classe les requêtes. `intent.py` et `action_parser.py` normalisent les commandes. `dispatcher.py` relie les intentions aux outils. `action_policy.py` classe les risques. `core/action_executor.py` journalise et applique policy/confirmation. `core/actions/` exécute les actions typées.

## MAIN.PY

Le mode texte lit une ligne puis appelle `brain.think`. Le mode vocal instancie `LocalWakeVoicePipeline`. Le code vocal utilise PyAudio, wake word, capture de commande, Google Speech Recognition puis le même brain ; la réponse est envoyée à `voice_manager`/Kokoro.

## TEXT PIPELINE

`main.py → brain → orchestrator → intelligence → response_planner → response_executor → dispatcher/action executor → ActionResult → réponse`.

Les requêtes mémoire et environnement sont traitées par leurs handlers locaux avant les fallbacks sémantiques/LLM.

## VOICE PIPELINE

Microphone → wake word/VAD → STT Google (`fr-FR`) → texte → brain → actions/réponse → Kokoro (`ff_siwis`) → audio. Le pipeline actuel utilise 44,1 kHz et le device vocal configuré dans `voice_pipeline.py`; `pause_threshold` SpeechRecognition vaut 1 s.

## INTELLIGENCE

Détection locale des actions, mémoire personnelle/projet, état utilisateur, environnement, tâches et questions PC. Les demandes générales peuvent utiliser la mémoire sémantique puis Groq.

## MEMORY

`data/user.json` stocke profil, état personnel et journal d’actions. `data/conversation.json` conserve l’historique conversationnel. `memory/` fournit état, habitudes, historique, mémoire structurée et sémantique.

## PERSONALITY

`PersonalityEngine` maintient un historique court, références, suivis (`pending_intent`) et adapte les réponses au contexte fourni par le brain.

## CONTEXT

`get_personal_context()` fournit activité, localisation, disponibilité et historique personnel. `get_pc_context()` fournit OS, batterie, audio, applications connues, fenêtres KWin et informations système.

## PC ACTION ARCHITECTURE

`Intent → Dispatcher → PCAction → ActionPolicy → ActionExecutor → ActionResult`.

## ALL PC ACTIONS

Applications : `OPEN_APPLICATION`, `CLOSE_APPLICATION`, `LIST_APPLICATIONS`.

Fichiers/dossiers : `FILE_CREATE`, `FILE_OPEN`, `FILE_COPY`, `FILE_MOVE`, `FILE_DELETE`, `OPEN_FOLDER`.

Web/capture : `OPEN_URL`, `SCREENSHOT`.

Audio/média : `VOLUME_STATUS`, `VOLUME_SET`, `VOLUME_UP`, `VOLUME_DOWN`, `VOLUME_MUTE`, `VOLUME_UNMUTE`, `MEDIA_PLAY`, `MEDIA_PAUSE`, `MEDIA_NEXT`, `MEDIA_PREVIOUS`, `MEDIA_STATUS`.

Réseau : `WIFI_STATUS/ENABLE/DISABLE`, `BLUETOOTH_STATUS/ENABLE/DISABLE`.

Système : `PC_STATUS`, `CPU_STATUS`, `RAM_STATUS`, `GPU_STATUS`.

Fenêtres : lecture via KWin si fournisseur disponible ; contrôle avancé actuellement `NOT_SUPPORTED`.

## APPLICATION DISCOVERY

`core/pc_discovery.py` lit les fichiers `.desktop` dans `/usr/share/applications` et `~/.local/share/applications`. La découverte est en lecture seule et séparée de l’allowlist d’exécution. Flatpak est supporté par l’allowlist d’applications existante mais n’est pas énuméré séparément par le resolver.

## FILE SYSTEM ACTIONS

Les chemins sont résolus canoniquement et limités à `Path.home()`. Les suppressions nécessitent une confirmation ; aucun dossier n’est créé par `OPEN_FOLDER`.

## AUDIO CONTROL

`wpctl` est utilisé avec des arguments fixes pour le volume ; `playerctl` pour les médias. Une dépendance absente produit `NOT_SUPPORTED`/échec contrôlé.

## NETWORK CONTROL

Wi‑Fi via `nmcli`, Bluetooth via `bluetoothctl`, paramètres via modules KDE allowlistés et `kcmshell6`.

## HARDWARE MONITORING

`hardware_monitor.py` mesure CPU sur deux snapshots `/proc/stat`, RAM via `/proc/meminfo`, GPU via `nvidia-smi` si disponible. Les métriques absentes valent `None`.

## WINDOW / KWIN

`kwin_context.py` lit un fournisseur `jarvis-kwin-context` optionnel sous Wayland. Sans fournisseur : `active_window.available=False`, fenêtres vides. Aucun contrôle KWin fiable n’est actuellement disponible.

## SCREENSHOT

Capture via Spectacle avec timeout et résultat structuré, chemin sous `~/Pictures/Jarvis`.

## ENVIRONMENT ENGINE

`core/environment/` contient détecteurs, profils, résolveurs d’artefacts, providers officiels, cache, plans, confirmation, lock, installation et vérification. Le flux réel est : audit → readiness/gaps → résolution locale/cache/provider → plan → confirmation → exécution contrôlée → vérification.

## ENVIRONMENT COMMANDS

Audits Flutter, Android, JDK, gaps, readiness, préparation et réparation confirmée sont présents dans `core/environment/intent.py`, `command_registry.py` et `command_handler.py`.

## PENDING PLAN / CONFIRMATION

`pending_plan.py` conserve un plan temporaire avec expiration et identifiant. Les confirmations sont validées avant revalidation et exécution ; les annulations nettoient le plan.

## SECURITY MODEL

Allowlist d’actions, confirmation des actions sensibles, chemins user-space, validation d’artefacts/checksum dans l’Environment Engine, absence de `shell=True`, `os.system`, `eval`, `exec` et `sudo` dans les nouvelles actions PC.

## DOCUMENTATION

`docs/COMMANDS.md` documente les commandes PC, environnement et limites. Certaines actions KWin avancées restent documentées comme non garanties.

## TEST ARCHITECTURE

123 fichiers de tests sont présents, couvrant mémoire, voix, intelligence, actions PC, environnement et sécurité. Résultat actuel : **370 passed**.

## CURRENT USER COMMANDS

Applications (`ouvre Firefox`, `ouvre Spotify`, `liste mes applications`), fichiers/dossiers (`crée un fichier`, `ouvre le fichier`, `ouvre le dossier`), web (`ouvre YouTube`), audio/média, Wi‑Fi/Bluetooth, état PC/CPU/RAM/GPU, capture écran et audits d’environnement.

## CURRENT CAPABILITIES

Terminal : READY · Texte : READY · Voix : PARTIAL (dépend matériel/Google/Kokoro) · Applications : READY pour allowlist · Fichiers : READY user-space · Screenshot : READY au niveau code · Audio : PARTIAL selon PipeWire · Wi‑Fi/Bluetooth : PARTIAL selon outils/session · CPU/RAM : READY localement · GPU : PARTIAL · Windows/KWin : UNAVAILABLE sans bridge · Environment Engine : READY au niveau testé · Vision : NOT IMPLEMENTED.

## REMAINING GAPS

Contrôle KWin réel, métriques GPU lorsque `nvidia-smi` est indisponible, température CPU, intégration MIME/default apps complète, tests matériels GUI et vision.

## DO NOT BREAK

Ne pas modifier inutilement `main.py`, `LocalWakeVoicePipeline`, STT, VAD, wake word, Kokoro, brain, intelligence, dispatcher, policy/executor, Environment Engine ou les mémoires runtime.

## ARCHITECTURE DIAGRAMS

```text
USER → main.py → brain → intelligence → planner → executor → dispatcher/actions → result → response
MIC → VAD/wake word → STT → brain → action/response → Kokoro → speaker
Intent → Dispatcher → PCAction → ActionPolicy → ActionExecutor → ActionResult
Audit → Readiness → Discovery/Cache/Provider → Plan → Confirmation → Lock → Install → Verify
```

## TEST RESULTS

`pytest -q` : **370 passed in 8.40s**. `git diff --check` : OK.

## GIT STATUS

Branche `main`, dernier commit `3b9b7d2`. Modifications runtime non commitées : `data/user.json`, `data/conversation.json`, `pytest.ini`; fichiers non suivis `ben10` et `code`. Aucun commit ni push effectué pour cette cartographie.

## ROADMAP

V2 voix · V3 intelligence · V4 mémoire/état · V5 actions PC · V6 fondation PC/monitoring · V6 Vision non implémentée · V7 proactivité avancée non implémentée.

## VERIFIED FACTS

- 370 tests passent.
- Le dépôt est sur `main`.
- Aucun pipeline vocal n’a été modifié pour cette cartographie.
- KWin retourne un contexte indisponible sans fournisseur.
- Les métriques GPU peuvent être absentes sans échec simulé.

## NEXT DEVELOPMENT RECOMMENDATION

1. Valider le statut volume dans la session PipeWire réelle.
2. Installer/valider le fournisseur KWin persistant avant tout contrôle de fenêtre.
3. Ajouter des tests de parsing pour les suivis PC (`et mon GPU ?`, `et la RAM ?`).
4. Compléter la résolution des applications Flatpak/default MIME.
5. Reporter la vision après stabilisation des capacités PC.
