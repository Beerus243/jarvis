# Captures locales : images et vidéos

Lancement habituel : `.venv-kokoro-cuda/bin/python main.py`.
Après « Hey Jarvis » et le signal, prononcer une commande ci-dessous.
Ces commandes passent par le même parseur, la politique d'actions et
l'exécuteur PC que les autres commandes de `main.py`.

| Commande | Résultat |
|---|---|
| « Fais une capture » / « Fais une capture d'écran » | Image PNG du bureau complet. |
| « Capture la fenêtre active » | Image PNG de la fenêtre actuellement au premier plan. |
| « Capture une zone de l'écran » | Sélection rectangulaire dans Spectacle, puis image PNG. |
| « Enregistre mon écran pendant trente secondes » | Vidéo WebM de l'écran choisi dans Spectacle. |
| « Enregistre la fenêtre pendant deux minutes » | Vidéo de la fenêtre à sélectionner dans Spectacle. |
| « Enregistre une zone pendant quinze secondes » | Vidéo d'une zone à sélectionner. |
| « Arrête la vidéo » | Termine et vérifie la vidéo avant d'annoncer sa sauvegarde. |
| « Statut de l'enregistrement » | État de la session et temps restant, ou résultat de la dernière session. |

Les images sont conservées dans `~/Pictures/Jarvis`, les vidéos dans
`~/Videos/Jarvis`. Chaque nom contient la cible, la date, l'heure et un
identifiant : une nouvelle capture ne remplace plus la précédente. Le chemin
exact apparaît dans le terminal ; l'annonce vocale donne le dossier.

Les captures enregistrées restent locales. Elles ne sont pas envoyées à Groq.
« Regarde mon écran » conserve son fonctionnement distinct : capture
éphémère et analyse distante. Les cibles fenêtre/zone de ce lot concernent
les fichiers enregistrés ; l'analyse Groq et la surveillance ciblées restent
à intégrer dans la suite V6.3.

## Sélection et arrêt

Pour une image de zone, dessiner le rectangle puis valider dans Spectacle.
Échap annule la sélection ; celle-ci est limitée à 60 secondes.
La fenêtre active est capturée directement, sans sélection.

Pour une vidéo, choisir l'écran, la fenêtre ou la zone dans l'interface
native de Spectacle. Jarvis annonce l'ouverture de la session ; cela ne
prouve pas encore qu'une image vidéo a été enregistrée. La durée inclut
la sélection : 60 secondes par défaut, entre 5 secondes et 15 minutes.
Le traitement vocal reste disponible après l'ouverture de cette session.

L'arrêt automatique, « arrête la vidéo » ou la fermeture normale de Jarvis
finalisent l'enregistrement. Le fichier est vérifié avec `ffprobe` avant
l'annonce de réussite. Une annulation, un fichier absent ou illisible, ou un
arrêt forcé donnent un échec explicite. Un fichier partiel éventuel reste
sur disque pour diagnostic, sans être présenté comme une vidéo réussie.
« Arrête la vidéo » rend immédiatement la main pendant la sauvegarde. Le
statut indique cette étape et la confirmation arrive une fois le fichier
validé. L'encodage logiciel VP9 dispose de 120 secondes pour terminer après
l'arrêt de la capture, contre 20 auparavant. Un dépassement reste un échec
explicite ; la fermeture de Jarvis attend la finalisation en cours.
Sans runtime (`--no-proactive`), les commandes et l'arrêt automatique
fonctionnent aussi ; l'annonce automatique de fin apparaît seulement dans
le terminal. Avec le runtime, elle rejoint les notifications vocales.

## Bureau et dépendances

La vidéo de ce lot utilise **Spectacle sous KDE Wayland**, avec `gdbus` et
`ffprobe` (FFmpeg). Aucun paquet Python ni moteur vocal supplémentaire.
Une seule session vidéo Jarvis peut être active. Si Spectacle est déjà
ouvert, Jarvis demande de fermer cette session avant de commencer.
Les captures PNG utilisent une instance séparée pour ne pas arrêter la vidéo.

L'arrêt D-Bus cible uniquement la connexion du processus Spectacle lancé
par Jarvis, après vérification de son PID. Il utilise le comportement
`activate()` de Spectacle : finaliser la vidéo active ; sinon rester inactif
avec `--dbus`. Jarvis ne lance pas de capture audio séparée : les possibilités
et réglages audio du Spectacle installé s'appliquent.

Références de l'implémentation KDE :
[interface D-Bus](https://github.com/KDE/spectacle/blob/master/dbus/org.kde.Spectacle.xml),
[activation et finalisation](https://github.com/KDE/spectacle/blob/master/src/SpectacleCore.cpp).

## Validation

La suite complète s'exécute avec `.venv-kokoro-cuda/bin/python -m scripts.test_v5`.
Deux avertissements existants subsistent : extraction TAR et initialisation
NVML dans l'environnement de test.

Les tests couvrent le routage texte et vocal de `main.py`, les cibles,
les fichiers uniques, les délais et annulations, la propriété du processus,
l'arrêt explicite et automatique, et les échecs de finalisation.
Sur cette machine, les captures réelles écran (1366 × 768) et fenêtre
active (1366 × 722) ont été vérifiées avec FFmpeg ; les fichiers de test
ont été supprimés. La sélection rectangulaire reste à essayer à la souris.
Un second essai vidéo réel a validé un WebM après sélection de l'écran et
arrêt automatique, avec suppression du fichier temporaire. Le premier essai
n'avait pas produit de vidéo validable ; Jarvis avait correctement signalé
l'échec. L'arrêt à la voix passe les tests de routage et de finalisation ;
le parcours complet avec le microphone reste à essayer.

Le journal du 15 septembre a exposé un WebM incomplet lors d'un arrêt vocal.
Une copie de 12,167 secondes a été récupérée et décodée sans erreur ; l'original
reste conservé. Les tests ciblés couvrent maintenant la sauvegarde asynchrone,
le statut pendant un encodage lent et les appels d'arrêt d'une ancienne session.
Un nouvel enregistrement réel reste à valider avec ce délai étendu.
