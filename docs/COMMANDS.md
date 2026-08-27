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

## Non exposé ou non garanti

- fermeture réelle d’une fenêtre/application ;
- commandes système arbitraires ;
- contrôle vocal en une seule phrase `Hey Jarvis, commande` ;
- contrôle Spotify garanti sans client/API correctement disponible.
