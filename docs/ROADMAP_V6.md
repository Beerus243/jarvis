# Roadmap JARVIS V6.2 → V6.9

État au 15 septembre 2026 : les lots V6.3 à V6.9 sont intégrés au routeur
vocal et à `main.py`. Le [guide V6.9](V6_9.md) décrit le périmètre livré,
les commandes et les mesures. Les critères ci-dessous restent des critères
de validation ; les essais matériels et les limites ne sont pas effacés par
le passage du numéro de version.

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

## État des lots 6.3 à 6.9

| Lot | Livré | Validation ou limite restante |
|---|---|---|
| 6.3 | Zones fixes, moniteur, fenêtre active et identifiant KWin ; comparaison de pixels locale. | Captures réelles et nettoyage vérifiés. Fenêtre doit rester active ; moniteur à 100 %, sans rotation. |
| 6.4 | JSON de lecture validé, texte/qualité/positions/hypothèses ; benchmark reproductible. | Transcription exacte sur une fixture, aucun texte inventé sur une image blanche ; positions approximatives, précision générale non certifiée. |
| 6.5 | Diagnostic image + fichier désigné, lecture bornée, provenance et correction proposée. | Tests de sources, masquage, fichier absent/non régulier et oubli ; qualité des diagnostics réels à évaluer. |
| 6.6 | Proposition d'ouverture du fichier dans VS Code ou vérification Wi-Fi ; confirmation consommée une fois et politique existante. | Exécution/résultat natif distingués ; aucune édition automatique ni clic par coordonnées. |
| 6.7 | Routine développement opt-in, contexte PC/tâche/horaire, 15 minutes, une surveillance, priorité/report/silence. | Pas de reprise après redémarrage ; essai vocal réel jusqu'à l'alerte restant. |
| 6.8 | Groq/local interchangeables explicitement, budget partagé et latences de session. | Ollama/modèle local absents ; matériel mesuré mais aucune inférence locale revendiquée. |
| 6.9 | Rapport de capacités, migration additive, commandes documentées et tests de régression. | Micro, vidéo et parcours de bout en bout à valider avec l'utilisateur avant de déclarer la V6 stabilisée sur tous les usages. |

Les détails de mesure figurent dans le [bilan V6.9](V6_9.md). Le numéro V6.9
désigne le code livré, pas une promesse de vision parfaite. La V7 pourra
construire les missions de projet sur ces capacités après validation des
parcours quotidiens de Fabrice.

La suite souhaitée par Fabrice est détaillée dans la [roadmap V7](ROADMAP_V7.md) :
modèle personnel, contexte de travail, questions, anticipation et présence permanente.
