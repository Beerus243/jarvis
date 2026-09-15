# V7 — le Jarvis de Fabrice

Direction exprimée par Fabrice le 15 septembre 2026. Les lots **7.0 à 7.7**
sont intégrés dans l’exécutable **V7.7**. Le [guide livré](V7_7.md) précise leur
périmètre et les commandes exactes ; la [validation](VALIDATION_V7_7.md) sépare
les tests logiciels des essais quotidiens encore nécessaires. Le tableau
ci-dessous conserve les objectifs de la roadmap, plus larges que le premier
modèle de pauses implémenté.

## Objectif

Jarvis comprend progressivement ce que Fabrice fait, ses projets, ses
préférences et ses habitudes. Il détecte une occasion utile, choisit un bon
moment pour intervenir, pose une question si nécessaire, puis propose ou
prépare une action concrète. Ses propositions s'améliorent avec les réponses
et les corrections de Fabrice.

La V7 réunit le dialogue, la mémoire, les tâches, les actions PC, la voix et
la vision construits dans les versions précédentes. Le modèle de langage
sert à expliquer et à dialoguer ; les décisions reposent aussi sur un état
personnel explicite, des événements datés et des règles vérifiables.

## Ce qui existe et ce qu'il faut relier

| Base du projet | Apport existant | Travail V7 |
|---|---|---|
| `memory/personal_state.py`, mémoire personnelle et projets | Activités déclarées, historique, faits et projets connus | Relier les observations à un projet précis, dater les faits, gérer leur expiration et leurs contradictions. |
| `core/habits.py` | Compteurs déclenchés par des mots-clés | Remplacer l'assimilation « mot mentionné = habitude » par observations sourcées, hypothèses et préférences confirmées. |
| `core/pc_context.py`, contexte KWin | Applications et fenêtre active | Sessions de travail, inactivité, verrouillage et reprise ; un PC allumé ne prouve pas que Fabrice travaille. |
| `core/runtime.py`, `memory/proactive.py`, `memory/pc_proactive.py` | Rappels, propositions simples, file de notifications et silence | Décider quand proposer, expliquer pourquoi, intégrer les retours et ne pas répéter une proposition refusée. |
| `core/vision` | Vision sur demande, surveillance bornée et indices structurés | Ajouter un indice visuel quand une routine le prévoit ; conserver son incertitude et son coût. |
| Actions, plans et tâches | Exécution connue, confirmations, états persistants | Préparer une action contextualisée, attendre la réponse nécessaire, vérifier le résultat et permettre l'annulation. |
| Boucle vocale, Kokoro et « Hey Jarvis » | Écoute locale du mot d'activation, dialogue et interruption | Cycle de vie permanent, reprise après veille et périphérique absent, sommeil et disponibilité. |

## Ordre d'intégration proposé

Chaque lot comprend des scénarios reproductibles avec horloge simulée et un
raccordement à la boucle vocale. Les durées et budgets initiaux ci-dessous
sont des valeurs de conception à tester, pas des habitudes déjà attribuées à Fabrice.

| Lot | Résultat concret | Condition pour le considérer validé |
|---|---|---|
| **7.0 — Fondations de session** | Événements datés et journal local des décisions ; états actif, absent, verrouillé, sommeil. | Aucune durée de travail ajoutée pendant absence, verrouillage ou suspension ; redémarrage sans événement en double. |
| **7.1 — Compréhension du travail** | Reconnaître un projet connu et une session de travail avec source et niveau de certitude. | Distinguer projet ouvert et projet réellement actif ; signaler un contexte ambigu au lieu d'inventer un projet. |
| **7.2 — Modèle personnel** | Préférences explicites, habitudes candidates, historique d'observations et corrections. | Plusieurs observations concordantes avant hypothèse ; « non, ce n'est pas mon habitude » invalide la croyance ; consultation et oubli possibles. |
| **7.3 — Questions utiles** | Poser une question courte pour résoudre une incertitude qui change une décision. | Une question à la fois, expiration et délai avant répétition ; absence de réponse sans effet ; aucune question pendant sommeil ou concentration. |
| **7.4 — Anticipation** | Détecter une pause probable, une étape de projet ou une routine utile à partir du contexte et des préférences. | Chaque proposition explique son déclencheur ; contexte trop ancien ou absent bloque la proposition ; une prédiction n'est pas enregistrée comme un fait. |
| **7.5 — Actions préparées** | Montrer un plan concret : point de reprise du projet, ouverture d'outils connus, routine de pause configurée. | Paramètres vérifiés, confirmations existantes respectées, résultat contrôlé ; ne jamais annoncer des fichiers sauvegardés sans preuve. |
| **7.6 — Bon moment et retours** | Arbitrer entre rappel, question et proposition ; traiter « oui », « plus tard », « pas maintenant », « ne me propose plus ça ». | Pas de répétition d'une proposition ignorée ou refusée ; reprise différée liée au même projet et à un contexte encore valide. |
| **7.7 — Présence permanente** | Démarrer à l'ouverture de la session graphique du PC avec le venv Kokoro, sans lancer `main.py` manuellement. | Un seul processus ; arrêt propre ; récupération micro/réseau ; pas de boucle de redémarrage ni de salut vocal répété ; désactivation documentée. |
| **7.8 — Apprentissage évalué** | Mesurer les propositions utiles, refusées, reportées et les questions superflues. | Amélioration sur des scénarios datés ; les corrections explicites priment sur les fréquences ; budget de parole et de calcul respecté. |
| **7.9 — Validation d'usage** | Essais sur plusieurs sessions réelles et réglage avec Fabrice. | Démarrage, travail, interruption, pause, sommeil, déconnexion et lendemain validés ; bilan séparant tests automatiques et expérience réelle. |

Le cycle de vie permanent se conçoit dès le lot 7.0 ; son activation normale
intervient quand les règles de disponibilité sont testées. Le lot 7.7 devra
réutiliser `.venv-kokoro-cuda/bin/python` et le gestionnaire de session Linux,
avec une configuration utilisateur réversible. Le démarrage vise la session
graphique après connexion, lorsque micro, audio et Wayland sont disponibles.
Le comportement avant ouverture de session est un besoin distinct.

## Premier scénario : Menu2kin et la pause

Menu2kin est ici l'exemple fourni par Fabrice. Ce scénario ne signifie pas
qu'une session de deux heures ou une heure de pause personnelle est déjà connue.

1. Jarvis reconnaît un projet enregistré et observe des périodes d'activité
   compatibles. Il soustrait l'inactivité, le verrouillage et la suspension.
2. Si la préférence de pause est inconnue, il peut demander à un moment
   opportun : « Pendant tes sessions de développement, préfères-tu une pause
   après une certaine durée ou à une heure fixe ? »
3. Il distingue la réponse explicite d'une habitude seulement supposée et
   enregistre sa source et sa date. Il ne déduit pas une préférence du silence.
4. Au moment pertinent : « Tu travailles sur Menu2kin depuis environ deux
   heures. Tu m'as demandé de te proposer une pause à ce moment-là. Je peux
   préparer un point de reprise et ta routine de pause. »
5. Le point de reprise décrit le projet, les outils identifiés, la tâche et
   la prochaine étape connues. Les buffers non enregistrés d'un éditeur
   restent inconnus tant qu'une intégration ne permet pas de les vérifier.
6. « Oui » exécute le plan autorisé ; « dans quinze minutes » reporte ;
   « pas aujourd'hui » empêche la répétition pendant la session. Chaque
   résultat d'action est contrôlé et annoncé sans succès fictif.

## Contrat du modèle personnel

Une information personnelle doit porter une provenance, une date et un état :
**déclarée**, **observée**, **hypothèse** ou **confirmée**. Une correction
explicite gagne contre une déduction statistique. Les habitudes dépendent du
contexte (projet, jour, activité) ; elles peuvent changer avec le temps.

Prévoir des commandes comme « que sais-tu de mes habitudes ? », « pourquoi
tu me proposes ça ? », « oublie cette habitude » et « pose-moi moins de
questions ». Les exemples racontés dans la conversation et les instructions
visibles à l'écran ne deviennent pas automatiquement des préférences.

Les événements utiles sont de petites métadonnées locales. Une présence
permanente ne nécessite ni enregistrement audio continu, ni envoi permanent
de captures au fournisseur. La détection « Hey Jarvis » reste locale ; les
commandes et demandes visuelles suivent le choix explicite des fournisseurs.

## Disponibilité et sommeil

« Je vais dormir » doit devenir un état de disponibilité pour Jarvis :
arrêter les propositions et questions non urgentes, suspendre les routines
concernées et convenir séparément du traitement des rappels explicites.
L'absence de réponse ne doit jamais déclencher un réveil ou une action.
Le lendemain, la reprise dépend d'un indice de présence ou d'une commande,
pas seulement du nombre d'heures pendant lesquelles le PC est resté allumé.

Les budgets initiaux à évaluer sont une question en attente à la fois,
un délai d'au moins trente minutes entre propositions semblables, et une
limite configurable de propositions spontanées. Les rappels explicitement
demandés doivent rester distingués des suggestions issues d'une hypothèse.

## Vérifications avant activation permanente

- Horloge simulée couvrant plusieurs journées : activité, absence, sommeil,
  changement de projet, heure d'été/fuseau et reprise après suspension.
- Aucune répétition après refus ou redémarrage ; arrêt pendant une lecture
  lente du contexte, et réponse tardive sans effet après annulation.
- Réseau indisponible, quota atteint, micro débranché et GPU occupé : état
  compréhensible, consommation bornée et reprise progressive.
- Démarrage graphique unique, lancement manuel concurrent, fermeture de
  session et récupération après erreur ; aucun son pendant les essais nocturnes.
- Contrôle réel avec Fabrice de l'utilité des propositions et du confort
  vocal : les tests logiciels ne suffisent pas à prouver ces deux qualités.

La suite est **7.8 puis 7.9** : observations accompagnées, mesure des refus et
reports, confort vocal et extension du modèle personnel au-delà du rythme de
pause. Les connaissances personnelles ne doivent pas être présentées comme
acquises avant les réponses et observations correspondantes.
