# Audit de validation V6.9 — 15 septembre 2026

Audit demandé avant le démarrage du développement V7. Exécution avec
`.venv-kokoro-cuda/bin/python`, dans les copies temporaires créées par
`scripts.test_v5`. Les tests travaillent sur une copie : les mémoires et rappels
réels de Fabrice ne sont pas modifiés. Aucun microphone n'a été enregistré, aucune
capture du bureau n'a été envoyée et aucune annonce vocale n'a été jouée
pendant cet audit.

## Défauts reproduits puis corrigés

- Une lecture lente du contexte conservait le verrou d'une routine : une
  demande d'arrêt attendait le capteur. La lecture s'effectue maintenant
  hors verrou et son résultat est invalidé après arrêt ou réactivation.
- Silence et dialogue n'étaient vérifiés qu'avant cette lecture. Ils sont
  revérifiés avant de démarrer la surveillance, ainsi que le fournisseur,
  l'horaire et la date limite.
- Des noms comme `barcode-scanner` ou `video-decoder` étaient reconnus comme
  un contexte de programmation à cause du fragment « code ». Le contrôle
  utilise maintenant des noms d'application précis et des mots de tâche.
- Une erreur de routine pouvait arrêter une surveillance indépendante.
  Le runtime traite séparément l'échec de la routine et celui de la surveillance.
- Une réponse locale dont `message` était nul ou de mauvais type provoquait
  une exception interne. La forme est maintenant validée et produit une
  erreur opérationnelle explicite ; aucun repli vers Groq n'est ajouté.

- La première passe générale a aussi révélé un cache PC déjà expiré à la
  fin d'une collecte lente. Son délai de validité commence maintenant après
  la collecte et utilise une horloge monotone, tandis que `observed_at`
  conserve une date réelle. Deux cas simulés couvrent le capteur lent et
  un changement de l'heure système.

Neuf nouveaux cas ont échoué sur le code initial, reproduisant les premiers défauts.
Après correction, la série ciblée de 131 tests a réussi. Le fichier de
stabilité enrichi passe 20 tests, dont les applications légitimes, les
capacités locales invalides et les résultats de contexte arrivant trop tard.

## Environnement vérifié silencieusement

- `pip check` : aucune dépendance cassée dans le venv Kokoro CUDA.
- `main.py --help` : entrée CLI fonctionnelle, mode vocal conservé par défaut.
- Rapport V6 : modules vocaux, FFmpeg, Spectacle et KWin disponibles ; présence
  de la webcam constatée sans l'ouvrir.
- GPU : GeForce 930MX, 2004 Mio au total, 486 Mio libres lors du contrôle,
  pilote 470.256.02. Cette mesure ne prouve pas qu'un modèle de vision local
  peut fonctionner confortablement.
- Ollama et modèle local non configurés ; aucune inférence locale réelle testée.
- Compilation Python et contrôle des espaces du diff : sans erreur.

## Résultat final du contrôle général

**861 tests réussis, aucun échec**, en 329,30 secondes (5 min 29 s), après
les correctifs et avec les 22 nouveaux tests de stabilité inclus.

Commande exécutée :

```bash
.venv-kokoro-cuda/bin/python -m scripts.test_v5 --maxfail=1 --tb=short
```

La première passe avait terminé avec 838 réussites et un échec du cache PC
(`test_pc_context_cache_reuses_value`, 713,01 s). Cet échec est corrigé et le
test passe dans la validation finale. Les durées des deux passes ne constituent
pas un benchmark : la charge de la machine et l'état des caches peuvent varier.

Quatre avertissements subsistent : dépréciation de l'extraction TAR, modules
Python `aifc` et `audioop`, et NVML inaccessible dans le test isolé. Le contrôle
matériel effectué séparément accède bien à la GeForce 930MX. Aucune mise à
jour de Torch, CUDA ou Kokoro n'a été effectuée.

La validation logicielle de la V6.9 est verte. Cela permet de commencer les
fondations V7 en conservant les essais matériels accompagnés ci-dessous
comme critères de validation de l'usage quotidien.

## Limites de cette validation

Les essais automatiques utilisent des doubles pour les périphériques et
services externes ; la détection réelle de la voix de Fabrice, l'interruption
pendant la parole et la sélection/finalisation vidéo nécessitent encore un
parcours accompagné. Les captures réelles du lot précédent sont décrites
dans [V6.9](V6_9.md), sans les présenter comme de nouveaux essais nocturnes.
Aucun test de plusieurs heures en temps réel ni démarrage automatique à la
connexion n'est revendiqué.

La [roadmap V7](ROADMAP_V7.md) formalise le modèle personnel, les questions,
l'anticipation, les états de disponibilité et le démarrage à la session
graphique. La version exécutable reste V6.9 ; la V7 n'est pas activée ici.
