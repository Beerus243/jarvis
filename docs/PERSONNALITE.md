# Personnalité et réponses de Jarvis

Fabrice a choisi un **majordome élégant, dans l’esprit d’Iron Man** : calme,
vouvoiement et esprit discret. Le ton est défini dans `personality/dialogue.py`
et partagé entre les échanges sociaux locaux et le dialogue Groq.

## Comportement

- Salutations et présence courtes, avec variation pour éviter une répétition
  immédiate. « Monsieur » reste occasionnel.
- Réponse utile en premier, normalement deux à quatre phrases ; une phrase
  pour un fait simple. L’explication détaillée reste accessible sur demande.
- Pas de plaisanterie au détriment de Fabrice, d’une erreur ou d’une inquiétude.
- Pas de souvenir inventé, de café prétendument prêt ni de vérification annoncée
  sans preuve. Le prompt précise les capacités locales et les limites du dialogue.
- Une question précise quand il manque une information essentielle, sans
  invitation automatique à chaque fin de réponse.
- Les résultats des actions, les réponses mémoire et les réponses générées
  ne sont plus remplacés ensuite par une répartie du moteur historique.
- Les mots d’une blague dans une vraie question ne suffisent plus à détourner
  la demande. Une phrase telle que « ça va marcher si je change cette ligne ? »
  reste une question.

Les comptes rendus opérationnels conservent leurs formulations et leurs
paramètres exacts. La personnalité ne reformule pas une confirmation, un chemin,
un échec ou un résultat d’outil pour uniformiser artificiellement le ton.

## Réglages vocaux

Dire « Jarvis », puis :

| Commande | Effet |
|---|---|
| « Réponds plus court » ou « Sois plus concis » | Réponses de dialogue plus brèves. |
| « Réponses normales » | Rétablit la longueur habituelle. |
| « Sans humour » ou « Reste sérieux » | Désactive les plaisanteries. |
| « Remets un peu d’humour » | Réactive une touche d’esprit. |
| « Tutoie-moi » / « Vouvoie-moi » | Change la manière de s’adresser à Fabrice dans le dialogue. |
| « Ta personnalité » | Résume le style sélectionné. |
| « Explique en détail… » ou « Développe ta réponse… » | Demande une explication plus complète pour cette réponse. |

Les préférences sont conservées localement dans SQLite, sous
`settings/dialogue`, et relues à chaque échange. Elles ne nécessitent pas de
réentraîner le modèle. La longueur demandée est une consigne au modèle, pas
une garantie de nombre de mots. Une sortie coupée par la limite du fournisseur
est signalée, sans présenter la réponse comme complète.

## Lecture vocale

Kokoro et la voix `ff_siwis` sont conservés. La mise en forme orale enlève les
marqueurs de titres, de listes et de gras ainsi que les délimiteurs de code
inline. Les liens Markdown sont lus par leur intitulé. Les blocs de code sont
annoncés comme disponibles dans la réponse écrite au lieu d’être récités.
Le texte intégral reste dans la réponse et l’historique ; les résultats et
les messages d’échec ne sont pas supprimés.

## Vérification

Les tests `test_v7_dialogue.py` vérifient le routage local, les préférences,
la protection des résultats d’action, la séparation entre consigne système
et mémoire, les réponses vides ou tronquées, les erreurs réseau et la mise
en forme pour Kokoro. Les appels distants de ces tests sont simulés.

Deux questions fictives sont également utilisées pour contrôler le dialogue
Groq sans historique personnel ni diffusion audio. Ces exemples ne remplacent
pas l’évaluation du confort et de la pertinence avec Fabrice en conversation.

Les vérifications ciblées passent : 136 tests de diagnostic, de commandes
principales et de dialogue ; 39 tests de dialogue, d’état utilisateur et de
suivi de conversation. Les deux réponses Groq obtenues sur les questions
fictives comptaient 55 et 58 mots, sans prétendre avoir exécuté d’action.
Le résultat de la régression finale est inscrit après son exécution.

Le service utilisateur a été rechargé après les tests ciblés. Vérification du
15 septembre 2026 : Kokoro chargé, voix `ff_siwis`, état `active/running`,
aucun redémarrage automatique, puis « micro prêt » à 10 h 40 min 27 s.
L’erreur CUDA déjà présente subsiste : Kokoro fonctionne actuellement sur CPU.
Aucune synthèse sonore n’a été déclenchée par les essais de personnalité.
