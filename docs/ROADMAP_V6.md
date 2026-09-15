# Roadmap JARVIS V6.2 → V6.9

Point de départ : V6.1, écran/webcam sur demande, réponses Kokoro, une image
en mémoire vive pendant deux minutes pour les questions de suivi. Le moteur
de vision choisi est Groq. Le premier lot V6.2 est intégré et testé ; une
surveillance vocale réelle reste à valider sur la machine. Les versions
suivantes sont prévues. Un premier ajout de captures locales prépare la V6.3 :
images écran/fenêtre/zone et vidéos sélectionnées, commandes d'arrêt et de
statut, fichiers conservés avec des noms uniques. Voir [Captures](CAPTURES.md).
L'analyse et la surveillance de fenêtres/zones restent à intégrer.

| Version | Résultat attendu | Exemple vocal | Critère de validation |
|---|---|---|---|
| **6.2 — Surveillance visuelle bornée** | Surveiller l'écran sur demande, reconnaître une fin de compilation/téléchargement ou une erreur, puis annoncer une fois. Arrêt, statut, limite de durée et de requêtes. | « Surveille cette compilation pendant cinq minutes. » | Deux observations concordantes avant alerte ; silence, dialogue, rappels et arrêt restent fonctionnels ; aucun redémarrage automatique de surveillance. |
| **6.3 — Fenêtre et zone ciblées** | Choisir un moniteur, une fenêtre ou une région ; réduire les captures inutiles et les données envoyées. Détection des changements de pixels avec seuils mesurés. | « Surveille seulement ce terminal. » | Zone vérifiée sous KDE/Wayland, erreurs explicites si inaccessible ; changements utiles détectés malgré curseur et horloge. Dépend du support réel du bureau. |
| **6.4 — Lecture et preuves visuelles** | Extraire le texte et les éléments visibles avec positions, qualité de lecture et distinction observation/hypothèse. Jeux d'images de référence. | « Lis précisément le message d'erreur. » | Mesurer erreurs de transcription et hallucinations ; signaler texte illisible ; relier chaque conclusion à un élément effectivement visible. |
| **6.5 — Diagnostic de développement** | Croiser l'erreur visible avec les journaux ou fichiers explicitement désignés ; proposer une correction contextualisée. | « Explique pourquoi cette compilation échoue. » | Diagnostic reproductible sur projets de test ; sources distinguées ; pas de lecture étendue de fichiers sans lien avec la demande. |
| **6.6 — Actions guidées par la vision** | Convertir une observation en proposition d'action PC connue, avec validation par la politique existante, contrôle du résultat et arrêt possible. | « Prépare la correction et montre-moi ce que tu ferais. » | Pas de commande shell arbitraire issue d'une image ; confirmations existantes respectées ; action vérifiée et échec décrit sans succès fictif. |
| **6.7 — Routines proactives contextuelles** | Combiner état PC, tâches, horaire et surveillance explicitement activée ; gérer priorité, silence, report et répétitions. | « Quand je code, préviens-moi des erreurs de compilation. » | Règles consultables et désactivables ; aucun suivi continu implicite ; limites de fréquence et de coût ; reprise de règles documentée. |
| **6.8 — Fournisseurs et performances** | Ajouter une interface de fournisseurs, un mode local si le matériel le permet, diagnostics de latence et quotas. | « Utilise la vision locale pour cette session. » | Mesures réelles sur la GeForce 930MX ; aucune promesse de rapidité sans mesure ; aucun basculement local → cloud silencieux. Choix explicite si la configuration locale est insuffisante. |
| **6.9 — Stabilisation de la V6** | Consolider installation, diagnostic, migration, tests et documentation ; établir les limites avant V7. | « Vérifie l'état de tes capacités. » | Parcours vocaux réels écran/webcam/surveillance, déconnexions, refus d'accès, quotas, arrêt/redémarrage ; rapport de qualité et de latence ; régressions V5/V6 contrôlées. |

## Premier lot : V6.2

- Écran entier seulement ; la webcam reste ponctuelle en V6.2.
- Commandes explicites pour démarrer, arrêter et consulter la surveillance.
- Cibles initiales : compilation, téléchargement, apparition d'une erreur.
- Cinq minutes par défaut, de une à quinze minutes sur demande ; au moins
  trente secondes entre observations terminées, dix analyses distantes maximum.
- Images strictement identiques ignorées, sauf seconde vérification d'un
  événement candidat. Les petits changements ne sont pas encore filtrés.
- Réponse Groq structurée et validée : attente, fin, erreur ou inconnu, avec
  indice visible. Deux résultats concordants sont nécessaires pour alerter.
- Les notifications passent par le runtime existant : report pendant le
  dialogue, respect du mode silencieux, une annonce à la fois.
- Arrêt immédiat de la planification ; un appel déjà commencé peut se
  terminer, mais son résultat tardif ne doit ni alerter ni relancer la tâche.
- Captures temporaires supprimées ; pas de conservation des images de
  surveillance dans le contexte conversationnel. Les annonces textuelles
  suivent le stockage habituel des notifications.
- Pas de reprise automatique après fermeture ou redémarrage de Jarvis.

## Ordre de travail et passage de version

Le premier lot V6.2 passe la suite générale (690 tests), puis les 46 tests
de surveillance après le dernier ajustement. Les classifications Groq ont
été essayées sur deux images artificielles. Le [guide V6](V6_VISION.md)
décrit les commandes, les limites et les validations.

Les captures locales écran/fenêtre/zone et l'enregistrement vidéo sont
maintenant branchés dans `main.py` ; les captures réelles écran/fenêtre et
une vidéo avec arrêt automatique ont été vérifiées. La prochaine étape
est de valider la surveillance réelle, puis de réutiliser le ciblage dans
l'analyse et la surveillance de la V6.3. Les observations
visuelles restent probabilistes : une image ne prouve pas l'état interne
d'un processus. La lecture native de l'état d'une tâche Jarvis est préférable
quand cet état est déjà disponible.

Pour chaque version : code et documentation cohérents, tests ciblés puis
contrôle des intégrations touchées, essai matériel lorsque nécessaire, bilan
séparant ce qui a été réellement observé de ce qui reste à vérifier. Les
versions 6.3 à 6.9 évolueront selon ces résultats et les essais sur la machine.
