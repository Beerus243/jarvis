# Validation V7.7 — 15 septembre 2026

Environnement utilisé : `.venv-kokoro-cuda/bin/python`, Python 3.12. Les tests
s’exécutent via `scripts.test_v5` dans une copie temporaire du projet, sans `.env`
et avec une base SQLite distincte par test. Aucun rappel réel n’est consommé,
aucune voix n’est diffusée et aucune préférence personnelle n’est inventée.

## Résultats

La régression complète finale passe **916 tests**, sans échec, en **146,73 secondes**.
Quatre avertissements déjà présents subsistent (dépréciations Python et NVML
indisponible dans le bac à sable). Commande exécutée :

```bash
.venv-kokoro-cuda/bin/python -m scripts.test_v5
```

Les validations ciblées ont également passé :

- 79 tests des commandes personnelles, du cycle de vie, de l’entrée vocale et
  des notifications vocales après les corrections d’intégration.
- 10 tests du cycle de vie et du rappel pendant une analyse visuelle lente,
  dont arrêt SIGTERM d’un vrai sous-processus `main.py` utilisant une entrée
  vocale simulée, puis vérification de la libération du verrou.
- 10 tests du cycle de vie incluant la migration du service historique.
- 12 tests vocaux, dont interruption d’une notification avec retour Kokoro
  annulé (`False`) : l’écoute de commande doit être active dès le retour de
  l’annonce.
- Compilation des fichiers modifiés et contrôle `git diff --check`.

La première suite complète a passé 908 tests et révélé un test de rappel qui
ne déclarait pas de présence active. Ce test utilise désormais un capteur simulé,
comme le scénario l’exige. La suivante a passé 913 tests et révélé une lecture
bufferisée incorrecte du signal de disponibilité dans le nouveau banc d’essai
SIGTERM ; le lecteur du test a été corrigé et son scénario isolé passe.

## Scénarios couverts

- Temps actif, verrouillage, absence, contexte ambigu, changement de projet,
  suspension et saut d’horloge ; aucune récupération fictive du temps arrêté.
- Sommeil persistant, exception explicite pour les rappels, concentration,
  capteur trop ancien et interaction explicite sur bureau déverrouillé.
- Hypothèses après trois jours distincts, absence de confirmation implicite,
  expiration d’une hypothèse, réponse numérique contextualisée, correction et oubli.
- Question unique, budgets, absence de réponse, refus et report lié au projet.
- Point de reprise créé une seule fois, changement de chemin, résultat partiel
  d’une action PC et arrêt pendant une action lente.
- Routage réel de `MEDIA_PAUSE` vers l’exécuteur PC ; aucune commande shell
  produite par le modèle personnel.
- Verrou de lancement, reprise d’un micro simulé déconnecté, préchargement vocal
  sans salutation et arrêt système propre.
- Protocole Wayland avec trames fragmentées ; aucun abonnement clavier/pointeur.

## Vérifications natives silencieuses

La connexion au protocole Wayland a réussi (`protocol_ready=True`). Le capteur
KDE a retourné `locked`, cohérent avec le bureau verrouillé pendant le contrôle.
Le thread de présence s’est arrêté proprement. Le retour `NotSupported` de
`ScreenSaver.GetSessionIdleTime` a été vérifié auparavant ; le runtime utilise
le protocole Wayland à sa place.

Le service a été accepté par `systemd-analyze --user verify`. L’ancien lanceur
activé sur `default.target` a été sauvegardé sous :

```
~/.config/systemd/user/jarvis.service.pre-v7-20260915-095912-419534
```

Le nouveau service est installé dans `~/.config/systemd/user/jarvis.service`.
Le lien `default.target.wants/jarvis.service` a été remplacé par celui de
`graphical-session.target.wants`. État vérifié après installation :

```
UnitFileState=enabled
ActiveState=inactive
SubState=dead
```

Il démarrera à la prochaine connexion graphique. Il n’a pas été lancé pendant
les essais nocturnes. L’installation a conservé les réglages utiles de l’ancien
lanceur (`PYTHONUNBUFFERED=1`) et utilise toujours le venv Kokoro.

## Limites de la validation

Aucun essai réel de reconnaissance « Hey Jarvis », de conversation avec Fabrice,
de pause musicale ou d’ouverture d’éditeur n’a été lancé cette nuit. Les actions
PC sont simulées dans les tests pour ne pas perturber le bureau. L’ouverture
réelle d’une nouvelle session graphique et son arrêt restent à observer lors
de la prochaine connexion. Les habitudes et la pertinence des interventions
nécessitent plusieurs journées d’usage : elles ne sont pas validées par ces tests.
