# JARVIS V5.18 — intégration avant la vision

## Mise à jour : voix Kokoro par défaut

`main.py` sans option écoute désormais « Hey Jarvis » ; `--text` conserve le
clavier pour le diagnostic. Le moteur existant est préchargé puis annonce
oralement sa disponibilité : français `f`, voix `ff_siwis`, 24 kHz et sélection
CUDA/CPU inchangés. Les rappels et commandes passent par ce même moteur.

Environnement à utiliser : `.venv-kokoro-cuda` (Python 3.12, Torch
2.6.0+cu118, Kokoro 0.9.4). Le profil `requirements-voice-cuda.txt` préserve
ces versions. Les constats sur eSpeak et Python 3.14 ci-dessous concernent
uniquement l’ancienne validation dans `.venv`, pas cette configuration Kokoro.

Les dépendances absentes de cet environnement — adaptateur OpenAI pour Groq,
Sentence Transformers et RapidFuzz — ont été installées. Le correcteur des
formulations fautives retrouve ainsi son moteur de comparaison.

139 tests ciblés réussissent dans l’environnement Kokoro CUDA, dont les
40 commandes du catalogue envoyées via le pipeline vocal de `main.py`, sans
saisie clavier. Les tests simulent le son et les actions PC pour préserver
les applications et données personnelles.

La suite élargie a ensuite produit 568 réussites et un échec dû à un plan
d’environnement laissé par un autre test. Après isolation de cet état,
les 24 tests concernés (plans, tâches, voix et confirmations) passent.
`pip check`, la compilation Python et le contrôle du diff passent aussi.

Les premiers essais matériels avaient dépassé leurs limites de 120 et
90 secondes pendant le chargement. Le nouvel essai du 15 septembre 2026,
avec un délai plus long, atteint bien l'écoute du micro : Kokoro chargé sur
la GeForce 930MX (CUDA 11.8), voix `ff_siwis`, annonce de 2,40 secondes
générée en 11,91 secondes puis lue. Le lancement sans option rencontre une
session proactive déjà active ; l'essai vocal utilise donc `--no-proactive`.

Le micro système (`default`, index 12 lors de l'essai, mono 44 100 Hz) était
saturé à 100 % de volume, avec capture et amplification interne à +30 dB
chacune. Mesures de cinq secondes, sans conservation de l'audio :

| Volume d'entrée PipeWire | RMS médian | Pic absolu | Échantillons écrêtés |
|---|---:|---:|---:|
| 100 % | 21 419 | 32 768 | 13,91 % |
| 25 % | 1 130 | 5 380 | 0 % |
| 12 % | 182 | 4 470 | 0 % |

Le volume système a été réglé à 12 % (amplification interne 0 dB, capture
+4,5 dB). Ces mesures successives ne garantissent pas un environnement sonore
identique. Le seuil de capture reste 300 RMS et le seuil Hey Jarvis 0,40 ;
ce réglage a ensuite permis de reconnaître la parole de l'utilisateur.
Le démarrage n'effectue pas encore de calibration automatique du bruit.
Les 27 tests ciblés (`test_wake_word_engine`, `test_audio_capture`,
`test_main_voice`) passent dans `.venv-kokoro-cuda` ; ils utilisent des
doubles de test et ne prouvent pas la reconnaissance d'une voix réelle.

L'essai réel a ensuite détecté « Hey Jarvis » dans `main.py` à 0,664,
0,454 et 0,477. Les deux premiers essais n'ont pas fourni de commande
exploitable (capture vide, puis `UnknownValueError` du STT). Au troisième,
après le signal, la transcription est « quelle heure il est » et la réponse
« Il est actuellement 00:10:11 ». Kokoro a généré les 2,85 secondes de
réponse en 2,33 secondes. La chaîne micro → réveil → commande → réponse
vocale est donc validée sur un échange réel, sans établir un taux de
fiabilité général. L'écoute de suivi a encore produit un `UnknownValueError`
avant l'arrêt volontaire du test ; la distinction bruit/parole reste à
améliorer pour éviter ces relances inutiles. Le diagnostic local séparé a aussi détecté le réveil
à 0,408 ; le niveau RMS maximal par bloc était de 4 159.

Pour refaire ce réglage système (il concerne toutes les applications),
sur cette machine :

```bash
pactl set-source-volume alsa_input.pci-0000_00_1f.3.analog-stereo 12%
```

Le volume précédent était 100 %. Ne pas le réappliquer sans vérifier la
saturation. Après fermeture de l'autre session Jarvis, le lancement habituel
sans `--no-proactive` réactive aussi les rappels et la surveillance.

```bash
.venv-kokoro-cuda/bin/python main.py
```

La boucle proactive et l'état durable utilisent le même point d'entrée que les
commandes au clavier et au microphone. Le fichier `voice/wake_word_engine.py`
et son modèle `hey_jarvis` sont réutilisés.

## Intégration

| Domaine | Comportement livré |
|---|---|
| Routage | `main.py → command_session → brain → orchestrator` pour le texte et la voix ; contrôles de session avant la classification générale. |
| Résultats | Refus et échecs conservés ; retour sémantique texte/dictionnaire corrigé. La personnalité préserve les réponses opérationnelles. |
| Confirmations | Action PC exacte, identifiée, valable 10 minutes et consommée une fois. Reprise des séquences après confirmation. |
| Tâches | SQLite : étapes, progression, résultats, pause, annulation, reprise. Les étapes réussies ne sont pas rejouées. |
| Missions | Groq choisit un outil à la fois dans un catalogue fixe ; paramètres validés, résultats réinjectés, 8 étapes maximum, arrêt sur erreur ou répétition. |
| Proactivité | Horloge indépendante de la saisie ; rappels relatifs/datés, alertes batterie/activité, mode silencieux, report de 10 minutes. |
| Attention | Annonces différées pendant un échange ; une alerte par épisode d'activité/décharge et une notification délivrée à la fois. |
| Mémoire | Faits datés, correction, oubli, contexte pertinent transmis au modèle. JSON verrouillés et atomiques ; historique borné à 100 messages. |
| Voix | Fin de phrase après 0,8 s de silence, suivi pendant 8 s sans nouveau réveil, retour en veille, interruption de lecture par Hey Jarvis. |
| Environnement | Plans Flutter stable, JDK 17 et outils CLI Android depuis les métadonnées officielles ; archive, destination, empreinte et étapes affichées avant confirmation. Archive vérifiée avant extraction ; destination non vide refusée. |
| Contexte PC | Réseau observé via NetworkManager, serveur audio testé, RAM mesurée, données indisponibles signalées comme inconnues. |

Une réparation générique propose un composant manquant à la fois. Une demande
explicite conserve le produit demandé. Node/Next et les versions spécifiques
non prises en charge sont refusés plutôt que remplacés par Flutter. L'audit
Flutter Android examine aussi les composants Android et les licences ; il ne
déclare pas le réseau indisponible sans observation.

## Démarrage et commandes

```bash
.venv-kokoro-cuda/bin/python main.py --command-seconds 12
```

Dire « Hey Jarvis », attendre le signal, puis donner la commande. Après la
réponse, dire directement « confirme », « annule » ou une autre commande dans
les 8 secondes. « Merci Jarvis » rend la main au détecteur. « Hey Jarvis »
pendant la lecture coupe la réponse ; « stop » peut ensuite annuler une tâche
active. Sans tâche ni confirmation, « stop » quitte le programme.

- `rappelle-moi dans deux minutes de faire une pause`
- `mode silencieux`, puis `reprends les notifications`
- `ouvre Firefox puis ouvre GitHub`
- `mes tâches`, `pause la tâche`, `reprends la tâche`, `annule la tâche`
- `configure ma routine de travail : ouvre Firefox puis ouvre GitHub`, puis `au boulot`
- `retiens éditeur : VS Code`, `corrige éditeur : Vim`, `oublie éditeur`
- `mission vérifie l'état du PC et donne-moi l'heure`
- `installe les outils Android`, `montre-moi ce que tu ferais`, puis `confirme` ou `annule`

L'état V5 est dans `data/runtime.sqlite3`. Le profil et les fichiers mémoire
existants sont conservés. `JARVIS_STATE_DB` permet de choisir une base séparée.
Une seule session proactive peut utiliser la même base simultanément.

## Python et validation

Le `.venv` existant a été réparé sans effacer ses paquets : Python 3.14.7,
PyAudio système, SpeechRecognition, openwakeword 0.4.0 et pyttsx3. `pip check`
ne trouve aucune dépendance cassée. Kokoro ne s'installe pas avec ses dépendances
de langue sur Python 3.14 ; eSpeak NG assure la synthèse locale française.
`requirements.txt` rend Kokoro optionnel sur 3.14.

```bash
.venv-kokoro-cuda/bin/python -m scripts.test_v5
.venv-kokoro-cuda/bin/python -m scripts.check_voice
.venv-kokoro-cuda/bin/python main.py --list-microphones
```

Le lanceur de tests utilise une copie temporaire des données. `pytest.ini`
sélectionne la suite automatisée ; certains anciens fichiers `test_*.py` sont
encore des scripts interactifs. Les nouvelles régressions couvrent notamment
les écritures simultanées, rappels après redémarrage, annulation et reprise,
confirmation unique, correction mémoire, limites du modèle et dialogue vocal.
Les actions PC et installations des tests sont simulées ou limitées à des
archives temporaires. Le véritable thread de travail et son horloge sont
également testés sans saisie utilisateur.

Résultats du 14 septembre 2026 : **522 tests de la suite réussis**, puis
**15 tests ciblés réussis** après l'ajustement du choix de produit à
installer, et **86 tests de routage réussis** après correction de la commande
des paramètres audio qui ouvrait les paramètres Wi-Fi. Ces groupes se
recouvrent. Le lanceur isolé a également été essayé sur 6 tests. Compilation
Python et vérification des espaces du diff réussies.

Vérifications matérielles réussies : capture du micro par défaut pendant
250 ms, modèle Hey Jarvis chargé et silence traité, WAV français généré.
Les données audio du diagnostic sont oubliées et le WAV supprimé. Les
métadonnées Android et Adoptium ont été téléchargées et converties en artefacts
validés, sans installer de SDK. L'URL Flutter est construite conformément au
[manifeste officiel](https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json).
La sélection d'outils utilise l'[API Groq](https://console.groq.com/docs/tool-use/overview).

## Limites et prochaines étapes

- Un échange complet avec ta voix reste à essayer : réveil réel, STT Google,
  réponse audible et interruption dans le bruit. Les tests simulés et la capture
  matérielle ne mesurent pas les faux réveils ni la compréhension.
- STT Google et missions Groq exigent Internet. Les missions ont été validées
  avec des réponses de modèle simulées, sans exécution distante réelle.
- Jarvis doit rester ouvert pour annoncer les rappels. Les rappels échus
  pendant un arrêt reviennent au lancement ; aucun service automatique n'est
  installé. Une coupure entre l'annonce et son enregistrement peut la faire
  réapparaître au redémarrage.
- L'interruption écoute « Hey Jarvis », sans annulation d'écho acoustique.
  `--no-barge-in` la désactive. « Hey Jarvis, commande » sans pause n'est pas
  encore capturé comme un seul énoncé.
- L'annulation arrête les prochaines étapes ; elle ne défait pas un effet déjà
  commencé. Une étape au résultat inconnu après arrêt exige une vérification
  humaine. Les installations d'environnement restent synchrones.
- Les outils CLI Android ne constituent pas un SDK complet : plateformes,
  build-tools et licences restent à configurer. Les installations complètes
  n'ont pas été exécutées sur ta machine pendant cette validation.
- Une ouverture d'application atteste la demande de lancement, sans prouver que
  la fenêtre est prête. Le contrôle avancé KWin reste dépendant d'un fournisseur
  compatible. La vision reste à intégrer.

Avant la vision : essayer une dizaine d'échanges vocaux, régler les seuils dans
ton environnement sonore, puis améliorer le STT local et la qualité de voix.
La perception visuelle pourra ensuite utiliser les mêmes tâches, résultats et
confirmations.
