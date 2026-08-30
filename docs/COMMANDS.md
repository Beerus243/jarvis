# Catalogue des commandes — JARVIS

Catalogue basé sur `core/intent.py`, `core/dispatcher.py`, `tools/` et le brain actuels.

## Commandes opérationnelles

### Système

| Commande | Variantes reconnues | Action | État |
|---|---|---|---|
| Heure | `quelle heure`, `il est quelle heure`, `time` | `get_time()` | ✅ Fonctionnelle |
| Salutation | `bonjour`, `salut`, `hey`, `coucou` | réponse locale | ✅ Fonctionnelle |

### Navigation et applications

| Commande | Variantes reconnues | Action | État |
|---|---|---|---|
| Navigateur | `ouvre chrome`, `ouvre le navigateur`, `lance chrome` | `open_browser()` | ✅ Fonctionnelle |
| Firefox | `ouvre firefox`, `lance firefox` | `open_application("firefox")` | ✅ Fonctionnelle |
| Terminal | `ouvre le terminal`, `ouvre konsole` | `open_application("terminal")` | ✅ Fonctionnelle |
| VS Code | `ouvre vscode`, `ouvre visual studio code` | `open_application("vscode")` | ✅ Fonctionnelle |
| Dossier | `ouvre un dossier`, `ouvre Documents` | `open_folder()` | ⚠️ Partielle |
| Site web | `ouvre un site`, `ouvre Google` | `open_website()` | ⚠️ Partielle |
| Projet | `ouvre mon projet X`, `open project X` | `OPEN_PROJECT` | ⚠️ À valider |

### Spotify

| Commande | Variantes reconnues | Action | État |
|---|---|---|---|
| Ouvrir Spotify | `ouvre spotify`, `lance spotify`, `ouvre la musique` | `open_musique()` | ✅ Fonctionnelle |
| Jouer artiste/titre | `mets du Damso`, `joue Damso` | `play_track()` | ⚠️ Partielle (client/API à valider) |
| Pause | `pause Spotify`, `pause la musique` | `pause()` | ⚠️ À valider |
| Reprise | `reprends la musique`, `continue Spotify` | `resume()` | ⚠️ À valider |
| Suivant | `suivant`, `chanson suivante` | `next_track()` | ⚠️ À valider |
| Précédent | `précédent`, `morceau précédent` | `previous_track()` | ⚠️ À valider |

### Web

| Commande | Variantes reconnues | Action | État |
|---|---|---|---|
| Recherche Google | requête de recherche web | `search_web()` | ⚠️ À valider |
| Recherche Wikipédia | requête Wikipédia | `search_wikipedia()` | ⚠️ À valider |

## Capacités présentes mais dépendantes du contexte

- mémoire personnelle : identité, couleur, goûts, état subjectif et activité ;
- mémoire projet : langage, frontend, backend, base de données, stack ;
- contexte PC et fenêtres KWin en lecture seule ;
- actions planifiées et politique de sécurité.

Ces capacités sont traitées par le brain/orchestrateur et ne sont pas toutes des commandes vocales directes.

## Environment Commands

| Commande | Intention | Effet | Risque | Confirmation |
|---|---|---|---|---|
| `vérifie mon environnement` | `ENVIRONMENT_AUDIT` | Audit local des capacités | Lecture seule | Non |
| `vérifie Flutter` | `FLUTTER_AUDIT` | État Flutter/Dart | Lecture seule | Non |
| `vérifie Android` | `ANDROID_AUDIT` | État SDK, ADB et outils | Lecture seule | Non |
| `vérifie Java` | `JDK_AUDIT` | État Java/JDK/javac | Lecture seule | Non |
| `qu'est-ce qui manque ?` | `ENVIRONMENT_GAPS` | Liste des composants manquants | Lecture seule | Non |
| `suis-je prêt pour compiler Flutter Android ?` | `FLUTTER_ANDROID_BUILD_CHECK` | Vérification de compilation | Lecture seule | Non |
| `prépare mon environnement Android` | `ENVIRONMENT_REPAIR_PLAN` | Prépare un plan contrôlé | Planification | Non |
| `installe le JDK` | `JDK_INSTALL` | Installation user-space validée | Modification | Oui |
| `installe les outils Android` | `ANDROID_TOOLS_INSTALL` | Installation user-space validée | Modification | Oui |
| `montre-moi ce que tu ferais` | Dry-run | Affiche le plan sans effet | Lecture seule | Non |
| `confirme` / `annule` | Confirmation/annulation | Exécute ou annule un plan en attente | Sensible | Contexte requis |

## Environment Confirmation

Un plan de réparation sensible est conservé temporairement (10 minutes) avec un identifiant unique. Il n'est jamais exécuté immédiatement.

Confirmations reconnues : `oui`, `confirme`, `je confirme`, `vas-y`, `exécute`, `lance`, `d'accord`, `ok`.

Annulations reconnues : `non`, `annule`, `annuler`, `pas maintenant`, `laisse tomber`, `stop`.

Sans plan valide en attente, ces réponses n'exécutent aucune installation.

## Environment Repair Flow

`Audit → Plan → Confirmation → Revalidation → InstallationEngine → Verification → Final audit`.
Un plan confirmé sans artefact officiel validé est invalidé (`PLAN_INVALIDATED`) et aucune modification n'est effectuée.

## Environment Readiness States

- `READY` : tous les prérequis sont présents.
- `PARTIAL` : certains composants manquent mais une action est possible.
- `REPAIRABLE_OFFLINE` : une réparation locale/cache est disponible.
- `REPAIRABLE_ONLINE` : une source réseau officielle est nécessaire.
- `BLOCKED_NETWORK` : aucune source validée n'est disponible hors ligne et le réseau est inaccessible.

## Non exposé ou non garanti

- fermeture réelle d’une fenêtre/application ;
- commandes système arbitraires ;
- contrôle vocal en une seule phrase `Hey Jarvis, commande` ;
- contrôle Spotify garanti sans client/API correctement disponible.
