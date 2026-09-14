# JARVIS V5.18 — intégration avant la vision

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
.venv/bin/python main.py --voice --command-seconds 12
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
.venv/bin/python -m scripts.test_v5
.venv/bin/python -m scripts.check_voice
.venv/bin/python main.py --list-microphones
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
