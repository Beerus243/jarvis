# Audit des commandes et première intégration vocale

## Trajet depuis main.py

Le terminal et `LocalWakeVoicePipeline.from_defaults()` utilisent tous deux
`core.command_session.process_command` :

```text
main.py (texte ou --voice)
  → core.command_session.process_command
  → core.brain.think
  → core.orchestrator.process
  → intelligence.analyze → response_planner → response_executor
      → action_executor → dispatcher → outil / exécuteur PC
      → environment.command_handler
      → mémoire / contexte / tâche / réponse IA
```

Les commandes ne doivent donc pas être importées individuellement dans
`main.py`. Les anciens imports inutilisés et la lecture anticipée de la
mémoire ont été retirés du point d'entrée.

## Corrections de branchement

| Cas vérifié | Problème corrigé |
|---|---|
| Terminal, projets et commandes françaises | Les alias `open`, `play`, `browser` produits par la normalisation ne correspondaient pas à plusieurs règles françaises. |
| `mets en pause` | La commande pouvait être interprétée comme une recherche musicale « en pause ». |
| `cherche Python sur internet` | Le mot « internet » pouvait déclencher une ouverture simple du navigateur avant le traitement de la recherche. |
| `ouvre https://example.com/Path?q=Test` | L'URL brute est transmise avec sa casse et ses paramètres, avant normalisation. |
| Commandes composées | Les cibles des applications sont conservées ; les règles déterministes précèdent la classification approximative qui pouvait perdre les paramètres. |
| Dossier avec chemin explicite | `OPEN_FOLDER` atteint maintenant l'exécuteur de dossiers. |
| État/réglage/réactivation du volume et état média | Les routes spécifiques ne sont plus masquées par la branche générique `VOLUME_*` / `MEDIA_*`. |
| Installation des outils Android | La formulation du catalogue atteint `ANDROID_TOOLS_INSTALL`. |
| Annulation d'environnement | La ponctuation de `Stop !` est tolérée ; un plan en attente reçoit l'annulation au lieu de fermer le terminal. |

`tests/test_main_commands.py` vérifie les commandes représentatives des familles
du catalogue à travers le vrai cerveau, le planificateur et la politique, avec
les actions finales simulées. `tests/test_command_dispatch_routes.py` vérifie
les branches PC corrigées avec les appels système simulés. Ces tests valident
le branchement logiciel, pas la disponibilité réelle de Spotify, KWin, des
applications ou des outils système sur une machine donnée.

## Activation vocale

- Microphone système par défaut ; choix possible avec `--mic-device` et liste
  via `--list-microphones`.
- Fréquence de capture identique pour le microphone et le détecteur.
- Réveil local, signal, capture d'une commande, transcription Google `fr-FR`,
  cerveau commun, réponse et retour en veille.
- Aucune transcription avant le réveil. Le microphone est fermé pendant le
  signal et le traitement de la réponse pour éviter l'accumulation d'audio.
- Arrêt reconnu avant l'appel au cerveau ; nettoyage des ressources sur erreur
  et sur interruption. Les erreurs de transcription permettent un nouveau réveil.
- Délai réseau du transcripteur limité à 10 secondes ; historique technique en
  mémoire limité aux 100 derniers cycles.

Les tests `test_main_voice.py`, `test_local_wake_pipeline.py` et
`test_wake_word_engine.py` utilisent un microphone, un transcripteur et un
modèle simulés. Le wrapper réinitialise les scores du modèle et son tampon
audio au début de chaque cycle ; l'API utilisée est celle
d'[openWakeWord 0.4.0](https://github.com/dscripka/openWakeWord/blob/v0.4.0/openwakeword/model.py).

## Limites constatées

- La première version attend une pause après « Hey Jarvis » et capture une
  durée fixe. La détection automatique de fin de phrase et la commande en une
  seule phrase restent à intégrer.
- Au moment de cet audit, `.venv/bin/python` est absent et le Python système
  n'a ni `speech_recognition` ni `openwakeword`. Aucun essai de reconnaissance
  au microphone réel n'est donc validé.
- Les actions `FILE_COPY` et `FILE_MOVE` existent dans l'exécuteur mais n'ont
  pas encore de grammaire naturelle complète dans le parseur.
- La suppression et la fermeture d'application restent soumises à la politique
  de confirmation ; leur dialogue de confirmation PC n'est pas complet. Elles
  ne sont pas annoncées comme exécutables de bout en bout.
- Le contrôle avancé des fenêtres et la luminosité peuvent retourner
  `NOT_SUPPORTED`. Les réglages audio dédiés ne disposent pas encore de leur
  propre route (l'ancienne formulation utilise les paramètres Wi-Fi).
- Les commandes d'environnement atteignent leur gestionnaire ; l'installation
  reste conditionnée par un plan, un artefact officiel validé et la confirmation.
  Le catalogue ne garantit pas une installation réelle à partir d'une phrase.

## Vérification ciblée

```bash
python -m pytest tests/test_main_commands.py tests/test_main_voice.py \
  tests/test_command_dispatch_routes.py tests/test_local_wake_pipeline.py \
  tests/test_wake_word_engine.py tests/test_intent.py -q
```

Ces fichiers sont inclus dans la sélection de tests de `pytest.ini`.

Validation du 14 septembre 2026 : `python3 -m pytest -q` termine avec **481
tests réussis** dans une copie temporaire du projet contenant les mêmes fichiers
d'implémentation et de tests. La compilation Python des fichiers modifiés et
`git diff --check` passent également. Le lancement `python3 main.py --voice`
signale correctement l'absence de `speech_recognition` dans l'environnement
disponible ; le microphone réel reste à valider après réparation des dépendances.
