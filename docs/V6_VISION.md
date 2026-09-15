# JARVIS V6.9 — vision, suivi et surveillance bornée

Les ajouts 6.3 à 6.9 et leurs commandes sont décrits dans le [guide V6.9](V6_9.md).
La [roadmap](ROADMAP_V6.md) indique le code livré et les validations restantes.

La V6 ajoute l'analyse d'une image de l'écran ou de la webcam au dialogue
vocal existant. Une première demande déclenche une capture, une description puis une
réponse avec Kokoro `ff_siwis`. Le moteur vocal et le réglage du micro restent
ceux de la V5.

## Commandes

Après « Hey Jarvis » et le signal :

- « Regarde mon écran. »
- « Analyse mon écran et explique cette erreur. »
- « Lis le texte à l'écran. »
- « Explique cette erreur sur mon écran. »
- « Regarde avec ma webcam. »
- « Décris ce qui est devant ma webcam. »
- « Que vois-tu devant la webcam ? »

Après une analyse réussie, pendant deux minutes :

- « Explique cette erreur. »
- « Lis ce texte. » ou « Traduis ce passage en français. »
- « Décris cet objet. »
- « Regarde à nouveau. » : nouvelle capture de la même source.
- « Oublie ce que tu as vu. » : efface le contexte visuel temporaire.

Les questions de suivi utilisent l'image précédente et le dernier échange
visuel. Elles n'ouvrent pas à nouveau la webcam ni la capture d'écran.
Pour observer un changement survenu depuis, demander une nouvelle capture.
Les formulations courtes sans image en contexte demandent une nouvelle
capture. Les commandes ordinaires (heure, ouverture d'application,
confirmation) conservent leur routage habituel.

La commande existante « fais une capture d'écran » garde son comportement :
elle enregistre une capture sans demander d'analyse.

## Surveillance V6.2

Depuis le lancement habituel de `main.py`, après « Hey Jarvis » :

- « Surveille cette compilation pendant cinq minutes. »
- « Surveille ce téléchargement. »
- « Préviens-moi si une erreur apparaît à l'écran. »
- « Que surveilles-tu ? »
- « Arrête la surveillance. »

Une seule surveillance d'écran peut être active. La durée est de cinq minutes
par défaut, configurable dans la commande de une à quinze minutes. Une
observation démarre au moins trente secondes après la fin de la précédente,
avec dix analyses Groq au maximum. Il n'y a aucune capture de surveillance
avant la commande de démarrage. La webcam reste réservée aux prises ponctuelles.

La cible choisie est capturée (écran entier par défaut). Les images identiques
et les changements sous le seuil de pixels ne sont pas renvoyés, sauf pour
confirmer un événement candidat. Le ciblage et le filtre sont décrits dans
le [guide V6.9](V6_9.md). Une réponse structurée indique attente, fin, erreur
ou inconnu, avec un indice visible. Deux observations concordantes sont
nécessaires pour annoncer un événement, puis la surveillance s'arrête.
Trois échecs consécutifs, la limite d'analyses ou la durée maximale l'arrêtent
aussi, avec une annonce expliquant la raison.

Le traitement est séparé de l'horloge des rappels. Il ne commence pas une
capture pendant que le runtime est occupé par une commande. Les annonces
respectent le dialogue et le mode silencieux ; le mode silencieux retarde
les annonces, mais n'arrête pas les captures. « Arrête la surveillance »
annule les futures observations et les annonces encore en attente de cette
surveillance. « Oublie ce que tu as vu » l'arrête également et efface le
contexte visuel temporaire. Un appel déjà lancé peut terminer, mais son
résultat tardif est ignoré. À la fermeture du programme, cet appel borné finit
son nettoyage ; la sortie peut donc attendre jusqu'au délai de l'opération.

Le runtime est obligatoire : le mode `--no-proactive` refuse le démarrage
de surveillance. Aucune surveillance ne reprend après un redémarrage. Les
images de surveillance sont supprimées et ne remplacent pas l'image de
conversation V6.1 ; les annonces textuelles sont conservées comme les autres
notifications. Pour examiner une alerte, demander « regarde mon écran ».

Il s'agit d'un indice visuel, pas d'une lecture native du processus : une
fenêtre masquée ou un message ambigu peut empêcher la détection. Un événement
très bref entre deux observations peut être manqué, et deux réponses du
modèle ne garantissent pas l'absence de faux positifs. Garder la fenêtre cible
active pour le suivi par identifiant KWin ; une perte de focus est refusée,
sans analyser une autre fenêtre. Une nouvelle surveillance annule les annonces
encore en attente de la précédente.

## Configuration

Le fournisseur de vision est distinct du modèle de conversation `MODEL`.
L'adaptateur livré utilise Groq et sa clé `GROQ_API_KEY` existante. Il envoie
l'image et la demande de vision à Groq, sans joindre l'historique personnel.
Groq est activé par défaut, conformément au choix de l'utilisateur.

Options `.env` :

```dotenv
JARVIS_VISION_PROVIDER=groq
JARVIS_VISION_MODEL=qwen/qwen3.6-27b
JARVIS_CAMERA_DEVICE=/dev/video0
```

`JARVIS_VISION_PROVIDER=disabled` désactive toute capture destinée à l'analyse.
Un adaptateur local Ollama est fourni en V6.8 ; il exige un modèle visuel déjà
installé. Aucun repli local vers Groq n'est automatique. Voir [V6.9](V6_9.md).

Le modèle par défaut de l'adaptateur est `qwen/qwen3.6-27b`, documenté pour les
entrées image par [Groq](https://console.groq.com/docs/vision). Sa disponibilité
dépend aussi des droits et quotas du compte. Le modèle textuel
`openai/gpt-oss-120b` n'est pas utilisé pour analyser les images.

Prérequis système : Spectacle pour l'écran, FFmpeg pour préparer les images
et capturer une image V4L2 de la webcam. Ils sont déjà présents sur la machine
testée ; aucune modification de Torch, CUDA ou Kokoro n'est nécessaire.

```bash
.venv-kokoro-cuda/bin/python main.py
```

## Fonctionnement et limites

Le trajet est `main.py → brain → orchestrator → core.vision → réponse Kokoro`.
La reconnaissance des commandes de vision précède le dialogue général. Les
réponses sont descriptives : le contenu de l'image ne déclenche aucune action
PC. Les captures ponctuelles s'effectuent sur une demande reconnue. La seule
surveillance périodique est celle activée explicitement, directement ou par
une routine contextuelle V6.7, et bornée
comme décrit ci-dessus. Une demande qui mentionne explicitement
l'écran ou la webcam, ou « regarde à nouveau », prend une nouvelle image.
Les demandes courtes de suivi s'appuient sur la dernière image disponible.

Une seule image JPEG (au maximum 4 Mio), sa source et le dernier échange
visuel restent en mémoire vive pendant 120 secondes après la première
analyse réussie. Un minuteur les retire même sans nouvelle commande ; les
suivis ne prolongent pas cette durée. Le contexte disparaît aussi à l'oubli
explicite, à la désactivation de la vision lors d'une nouvelle demande ou à
l'arrêt de `main.py`. Une capture nouvelle remplace le contexte ancien même
si elle échoue, pour éviter de répondre sur la mauvaise image.

Un appel Groq déjà en cours peut terminer après un oubli ou une expiration,
mais son résultat est alors écarté. Le contexte n'est pas restauré par une
réponse tardive. L'oubli temporaire ne supprime pas l'historique textuel des
conversations, ni une requête déjà envoyée au fournisseur.

Chaque image utilise un répertoire temporaire privé et unique, supprimé
après l'analyse, y compris lors d'une erreur ou d'un `Ctrl+C`. L'image est
convertie en JPEG, limitée à 1920 pixels par côté et à 4 Mio avant envoi.
Spectacle est limité à 20 secondes pour la vision (60 secondes pour sélectionner une zone), FFmpeg à 12 secondes et le client Groq
réutilise le délai de 20 secondes sans nouvelle tentative automatique.

L'écran entier peut contenir des informations personnelles. Avec Groq,
elles quittent le PC lors de l'analyse. La suppression locale des fichiers
ne garantit pas leur suppression chez le fournisseur. Le texte de la réponse
rejoint l'historique conversationnel habituel de Jarvis. Chaque suivi visuel
renvoie à Groq l'image gardée en mémoire et le dernier échange visuel, sans
joindre l'historique personnel général.

La webcam est ouverte pour une seule image, puis fermée par FFmpeg. Un cache
physique, une autre application qui monopolise la caméra, un périphérique
différent ou une autorisation manquante peuvent empêcher la capture.
Le texte très petit ou les éléments non visibles peuvent rester illisibles.

## Validation reproductible

```bash
.venv-kokoro-cuda/bin/python -m scripts.test_v5 tests/test_v6_vision.py
.venv-kokoro-cuda/bin/python -m scripts.test_v5 tests/test_v6_visual_followup.py
.venv-kokoro-cuda/bin/python -m scripts.test_v5 tests/test_v6_watch.py
```

Le lanceur historique `scripts.test_v5` isole les données dans une copie
temporaire et inclut les tests V6. Les tests vérifient les commandes explicites,
les erreurs de capture/API, la suppression des images et le parcours vocal
de `main.py` avec des doubles de test. Les appels réseau et périphériques
sont simulés dans ces tests.

Validation précédente de la V6.0 : **622 tests réussis** dans `.venv-kokoro-cuda` avec
`python -m scripts.test_v5` (273,81 secondes). Deux avertissements subsistent
dans les tests existants : dépréciation de l'extraction TAR et initialisation
NVML indisponible dans l'environnement de test. La compilation des modules
modifiés et `git diff --check` passent également.

## Essais sur la machine — 15 septembre 2026

- Capture webcam réelle : JPEG de 36 214 octets en 4,32 secondes, puis fichier supprimé.
- Capture écran réelle : JPEG de 252 231 octets en 9,96 secondes, puis fichier supprimé.
  Le premier essai a échoué ; le diagnostic suivant puis la capture complète
  ont réussi. Le délai de Spectacle pour la vision est porté à 20 secondes
  pour laisser davantage de marge au démarrage.
- API Groq réelle avec `qwen/qwen3.6-27b` : une image bleue créée pour le test
  reçoit la réponse « La couleur principale est le bleu. »

Ces essais vérifient séparément la capture matérielle et le modèle distant.
Les images réelles de l'écran et de la webcam n'ont pas été envoyées pendant
ces contrôles. Le parcours vocal est testé avec entrée audio et sortie vocale
simulées ; un échange vocal complet de vision reste à essayer par l'utilisateur.

## Validation du suivi V6.1

La suite générale passe : **645 tests réussis** en 487,45 secondes dans
`.venv-kokoro-cuda`. Les deux avertissements précédents (TAR et NVML) restent
présents. La compilation et `git diff --check` passent également.

Les 61 tests de vision passent après le réglage final du client. Ils couvrent
la réutilisation de l'image après suppression du fichier, l'expiration par
minuteur, l'oubli, le remplacement de source, les erreurs, les réponses
tardives et un dialogue passant par le mode vocal de `main.py` avec le son
simulé. Le routage a été corrigé pour que l'oubli visuel précède la commande
générique d'oubli de la mémoire personnelle.

Un essai réel Groq a posé deux questions sur une image bleue artificielle,
après suppression du fichier local. La première tentative identifiait le
bleu mais ajoutait un détail visuel absent. Après resserrement des consignes
et réglage de `temperature=0`, le nouvel essai a répondu « La couleur
dominante est le bleu. », puis « Bleu. » au suivi sur les mêmes octets JPEG.
Ce contrôle valide la transmission du contexte ; il ne garantit pas
l'exactitude de toutes les descriptions visuelles.

## Validation du premier lot V6.2

La suite générale passe : **690 tests réussis** en 298,12 secondes dans
`.venv-kokoro-cuda`, avec les deux avertissements TAR/NVML déjà connus.
Après le dernier ajustement de remplacement d'une surveillance expirée,
les **46 tests de surveillance** passent en 15,64 secondes. La compilation
et `git diff --check` passent également.

Les tests ciblés vérifient démarrage explicite, statut, arrêt, durée,
quotas, images identiques, double observation, ambiguïtés, erreurs répétées,
résultats tardifs et annulation des annonces. Ils couvrent aussi l'oubli
visuel, le redémarrage et le dialogue vocal de `main.py` avec audio simulé.
Un rappel est délivré pendant qu'une capture de surveillance simulée est
bloquée : l'horloge des rappels reste indépendante de l'analyse visuelle.

Essai réel du fournisseur : sur une image artificielle « BUILD SUCCESSFUL »,
Groq renvoie `state=complete` et un indice décrivant ce texte visible, au
format JSON attendu. Une seconde image artificielle, uniformément bleue,
renvoie `state=unknown` et ne déclencherait pas d'alerte. Le modèle y ajoute
toutefois une zone blanche absente dans son explication : les détails de
ses descriptions peuvent rester inexacts même lorsque l'état est adapté.
Les images personnelles de l'écran n'ont pas été
envoyées pour cette vérification. Une surveillance réelle de bout en bout,
avec annonces Kokoro, reste à valider avec l'utilisateur ; il ne s'agit pas
encore d'un test de fiabilité sur de longues sessions de travail.
