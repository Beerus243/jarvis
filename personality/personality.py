"""Moteur de personnalité de JARVIS.

JARVIS V2
---------
Objectif :
- présence naturelle
- humour sec et situationnel
- ton sobre et sophistiqué
- répartie mesurée
- références culturelles reconnues naturellement
- mémoire conversationnelle courte
- variations de réponses
- aucune punchline forcée

JARVIS ne cherche pas à être drôle.
Il intervient lorsqu'il a quelque chose de pertinent à dire.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import random
import re
import unicodedata
from core.user_state import detect_user_state


# ============================================================
# ÉTAT DE PERSONNALITÉ
# ============================================================

@dataclass
class PersonalityState:

    recent_messages: deque
    recent_responses: deque

    last_reference: str | None = None
    last_mood: str = "NEUTRAL"

    interaction_count: int = 0
    consecutive_banter: int = 0

    # ========================================================
    # CONTEXTE SÉMANTIQUE
    # ========================================================

    topic: str | None = None
    situation: str | None = None
    last_action: str | None = None
    last_problem: str | None = None
    last_success: str | None = None
    last_intent: str | None = None
    pending_intent: str | None = None
    pending_slots: dict | None = None
    last_music_artist: str | None = None
    pending_question: str | None = None
    expected_response: tuple | None = None
    pending_action: dict | None = None
    requires_confirmation: bool = False


# ============================================================
# MOTEUR
# ============================================================

class PersonalityEngine:

    def __init__(self):

        self.state = PersonalityState(
            recent_messages=deque(maxlen=12),
            recent_responses=deque(maxlen=12),
        )

        self.random = random.Random()

        # ====================================================
        # PROFIL RELATIONNEL
        # ====================================================

        self.relationship = {
            "trust": 0,
            "respect": 0,
            "frustration": 0,
            "confidence": 0,
        }

    # ========================================================
    # NORMALISATION
    # ========================================================

    @staticmethod
    def normalize(text: str) -> str:

        value = unicodedata.normalize(
            "NFD",
            str(text or "").casefold(),
        )

        value = "".join(
            char
            for char in value
            if not unicodedata.combining(char)
        )

        value = value.replace("’", "'")

        # On conserve l'apostrophe.
        # Important pour :
        # "c'est facile pour toi"
        # "j'ai une idée"
        value = re.sub(
            r"[^\w\s']",
            " ",
            value,
        )

        return " ".join(value.split())

    # ========================================================
    # MÉMOIRE COURTE
    # ========================================================

    def remember(
        self,
        message: str,
        response: str | None = None,
    ):

        self.state.recent_messages.append(
            str(message or "")
        )

        if response:
            self.state.recent_responses.append(
                str(response)
            )

        self.state.interaction_count += 1

    # ========================================================
    # CONTEXTE RÉCENT
    # ========================================================

    def recently_said(self, phrase: str) -> bool:

        target = self.normalize(phrase)

        for message in self.state.recent_messages:

            if target in self.normalize(message):
                return True

        return False

    # ========================================================
    # VARIATION
    # ========================================================

    def choose(self, responses):

        if not responses:
            return None

        # Évite autant que possible de répéter exactement
        # la dernière réponse.
        previous = (
            self.state.recent_responses[-1]
            if self.state.recent_responses
            else None
        )

        available = [
            response
            for response in responses
            if response != previous
        ]

        if not available:
            available = list(responses)

        return self.random.choice(available)

    # ========================================================
    # RELATION AVEC FABRICE
    # ========================================================

    def update_relationship(
        self,
        message,
        response=None,
    ):
        """
        Met à jour très légèrement la relation avec Fabrice.

        Le but n'est pas de créer un profil psychologique.
        JARVIS mémorise simplement la dynamique de leurs échanges.
        """

        text = self.normalize(message)

        # -----------------------------------------------
        # Confiance
        # -----------------------------------------------

        if any(
            trigger in text
            for trigger in (
                "fais moi confiance",
                "fais-moi confiance",
                "je te fais confiance",
                "je compte sur toi",
            )
        ):
            self.relationship["trust"] += 1

        # -----------------------------------------------
        # Réussite
        # -----------------------------------------------

        if any(
            trigger in text
            for trigger in (
                "ça marche",
                "ca marche",
                "ça fonctionne",
                "ca fonctionne",
                "j'ai compris",
                "j ai compris",
            )
        ):
            self.relationship["confidence"] += 1
            self.relationship["frustration"] = max(
                0,
                self.relationship["frustration"] - 1,
            )

        # -----------------------------------------------
        # Frustration
        # -----------------------------------------------

        if any(
            trigger in text
            for trigger in (
                "encore une erreur",
                "encore",
                "ça ne marche pas",
                "ca ne marche pas",
                "merde",
                "putain",
                "bordel",
            )
        ):
            self.relationship["frustration"] += 1

        # -----------------------------------------------
        # Respect / découverte
        # -----------------------------------------------

        if any(
            trigger in text
            for trigger in (
                "j'ai trouvé",
                "j ai trouvé",
                "j'ai compris",
                "j ai compris",
                "j'ai une idée",
                "j ai une idée",
            )
        ):
            self.relationship["respect"] += 1

        # Limites.
        for key in self.relationship:
            self.relationship[key] = max(
                0,
                min(
                    self.relationship[key],
                    10,
                ),
            )


    def relationship_response(self, message):

        text = self.normalize(message)

        trust = self.relationship["trust"]
        respect = self.relationship["respect"]
        frustration = self.relationship["frustration"]
        confidence = self.relationship["confidence"]

        # ------------------------------------------------
        # FABRICE DEMANDE SI JARVIS LUI FAIT CONFIANCE
        # ------------------------------------------------

        if text in (
            "tu me fais confiance",
            "est ce que tu me fais confiance",
            "tu me fais vraiment confiance",
        ):

            if trust >= 2:
                self.state.last_mood = "CALM"

                return self.choose([
                    "Oui. Je commence simplement à distinguer votre confiance de votre prudence.",
                    "Oui. J'ai suffisamment de données pour considérer cela comme raisonnable.",
                    "Je vous fais confiance. Je surveille simplement les conséquences.",
                ])

            self.state.last_mood = "CALM"

            return (
                "Je vous fais confiance. "
                "La confiance n'exclut pas la vérification."
            )

        # ------------------------------------------------
        # FABRICE DEMANDE SI JARVIS EST IMPRESSIONNÉ
        # ------------------------------------------------

        if text in (
            "tu es impressionne",
            "tu es impressionné",
            "je t'impressionne",
            "je t impressionne",
        ):

            if respect >= 2:
                self.state.last_mood = "IMPRESSED"

                return self.choose([
                    "Disons que je révise légèrement mon estimation.",
                    "Je dois reconnaître que c'était bien pensé.",
                    "Je suis agréablement surpris. Ne vous habituez pas trop vite au compliment.",
                ])

            self.state.last_mood = "AMUSED"

            return self.choose([
                "Je suis attentif. Impressionné serait prématuré.",
                "Je dirais plutôt intrigué.",
                "Donnez-moi encore quelques secondes avant de réclamer le mérite.",
            ])

        # ------------------------------------------------
        # FABRICE DIT QU'IL A RÉUSSI
        # ------------------------------------------------

        if text in (
            "j'ai réussi",
            "j ai réussi",
            "j'ai reussi",
            "j ai reussi",
            "j'ai réussi tout seul",
            "j ai reussi tout seul",
        ):

            self.state.last_mood = "PROUD"

            if frustration > 0:
                return (
                    "Après tout ce que nous avons traversé, "
                    "je dois reconnaître que celle-ci est méritée."
                )

            return self.choose([
                "Bien joué, Fabrice.",
                "Excellent. Cette fois, le résultat justifie la méthode.",
                "Je dois reconnaître que c'était bien exécuté.",
            ])

        # ------------------------------------------------
        # FABRICE DEMANDE UN AVIS
        # ------------------------------------------------

        if text in (
            "qu'en penses tu",
            "qu est ce que tu en penses",
            "tu en penses quoi",
            "ton avis",
        ):

            self.state.last_mood = "FOCUSED"

            return (
                "Je peux vous donner un avis. "
                "Mais je préfère vous donner le vrai plutôt que celui que vous espérez entendre."
            )

        # ------------------------------------------------
        # FABRICE VEUT ABANDONNER
        # ------------------------------------------------

        if any(
            trigger in text
            for trigger in (
                "j'abandonne",
                "j abandonne",
                "laisse tomber",
                "on arrête",
                "j'en ai marre",
                "j en ai marre",
            )
        ):

            self.state.last_mood = "CONCERNED"

            if frustration >= 2:
                return (
                    "Vous pouvez arrêter. "
                    "Mais je soupçonne que ce n'est pas réellement ce que vous voulez."
                )

            return self.choose([
                "Si vous souhaitez réellement arrêter, je m'arrête.",
                "Très bien. Mais je vous connais suffisamment pour suspecter une pause plutôt qu'un abandon.",
                "Compris. Nous pouvons reprendre lorsque vous serez prêt.",
            ])

        return None


    # ========================================================
    # PRÉSENCE — RÉACTION À LA CONTINUITÉ
    # ========================================================

    def continuity_response(self, message):

        text = self.normalize(message)

        frustration = self.relationship["frustration"]

        # ------------------------------------------------
        # ENCHAÎNEMENT D'ERREURS
        # ------------------------------------------------

        if (
            frustration >= 2
            and any(
                trigger in text
                for trigger in (
                    "encore",
                    "toujours",
                    "ça marche pas",
                    "ca marche pas",
                    "nouvelle erreur",
                )
            )
        ):

            self.state.last_mood = "DARK"

            return self.choose([
                "Je commence à soupçonner un problème plus organique que logiciel.",
                "À ce stade, le code n'est peut-être plus notre principal suspect.",
                "Nous avons dépassé le stade du bug. Je commence à envisager une malédiction.",
            ])

        # ------------------------------------------------
        # SUCCÈS APRÈS FRUSTRATION
        # ------------------------------------------------

        if (
            frustration >= 2
            and any(
                trigger in text
                for trigger in (
                    "ça marche",
                    "ca marche",
                    "ça fonctionne",
                    "ca fonctionne",
                    "c'est bon",
                    "c est bon",
                )
            )
        ):

            self.state.last_mood = "SATISFIED"

            return self.choose([
                "Enfin.",
                "Voilà qui justifie les précédentes insultes adressées au logiciel.",
                "Excellent. Nous pouvons officiellement cesser de soupçonner tout le système.",
            ])

        return None


    # ========================================================
    # CONTEXT ENGINE
    # ========================================================

    def update_context(self, message, base_response=None):
        """
        Analyse la situation courante sans générer de réponse.

        Le but n'est pas de comprendre toute la langue française.
        Le but est de conserver les informations nécessaires à une
        conversation naturelle.
        """

        text = self.normalize(message)

        state = self.state

        # ----------------------------------------------------
        # CODE / DEBUG
        # ----------------------------------------------------

        code_markers = (
            "code",
            "programme",
            "script",
            "python",
            "bug",
            "erreur",
            "exception",
            "traceback",
            "compile",
            "compilation",
            "fonction",
            "fonctionne",
            "plante",
            "crash",
        )

        if any(marker in text for marker in code_markers):

            state.topic = "CODE"

        # ----------------------------------------------------
        # PROBLÈME
        # ----------------------------------------------------

        problem_markers = (
            "plante",
            "erreur",
            "bug",
            "echec",
            "échoue",
            "impossible",
            "ne marche pas",
            "ne fonctionne pas",
            "crash",
            "probleme",
            "problème",
        )

        if any(marker in text for marker in problem_markers):

            state.situation = "PROBLEM"
            state.last_problem = text

        # ----------------------------------------------------
        # SUCCÈS
        # ----------------------------------------------------

        success_markers = (
            "ça marche",
            "ca marche",
            "ça fonctionne",
            "ca fonctionne",
            "fonctionne enfin",
            "c'est bon",
            "c est bon",
            "réussi",
            "reussi",
            "on y est",
            "enfin",
            "j'ai compris",
            "j ai compris",
        )

        if any(marker in text for marker in success_markers):

            state.situation = "SUCCESS"
            state.last_success = text

        # ----------------------------------------------------
        # ACTION / TENTATIVE
        # ----------------------------------------------------

        action_markers = (
            "je vais",
            "on va",
            "on tente",
            "je tente",
            "je vais essayer",
            "essayons",
            "lance",
            "testons",
            "on recommence",
            "je recommence",
        )

        if any(marker in text for marker in action_markers):

            # Une action ne remplace pas le problème courant.
            # Exemple :
            #
            #   "Le code plante encore."
            #   -> situation = PROBLEM
            #
            #   "Je vais essayer."
            #   -> situation reste PROBLEM
            #   -> last_action = "je vais essayer"
            #
            # Le contexte dominant reste donc conservé.

            state.last_action = text

            if state.situation is None:
                state.situation = "ACTION"

        # ----------------------------------------------------
        # ABANDON
        # ----------------------------------------------------

        if any(
            marker in text
            for marker in (
                "laisse tomber",
                "j'abandonne",
                "j abandonne",
                "on abandonne",
                "c'est mort",
                "c est mort",
            )
        ):

            state.situation = "ABANDON"

        # ----------------------------------------------------
        # IDÉE
        # ----------------------------------------------------

        if "j'ai une idee" in text or "j ai une idee" in text:

            state.last_intent = "IDEA"
            state.situation = "IDEA"

        # ----------------------------------------------------
        # QUESTION / COMPRÉHENSION
        # ----------------------------------------------------

        if (
            "pourquoi" in text
            or "comment" in text
            or "tu comprends" in text
            or "tu vois ce que je veux dire" in text
        ):

            state.last_intent = "QUESTION"

        # ----------------------------------------------------
        # CONTINUITÉ
        # ----------------------------------------------------

        if text in (
            "encore",
            "enfin",
            "exactement",
            "on y est",
            "c'est bon",
            "c est bon",
        ):

            state.last_intent = "FOLLOW_UP"

        return state


    # ========================================================
    # MÉMOIRE CONVERSATIONNELLE
    # ========================================================

    def conversation_context(self):
        """
        Retourne une représentation compacte du contexte actuel.
        """

        state = self.state

        return {
            "topic": state.topic,
            "situation": state.situation,
            "last_action": state.last_action,
            "last_problem": state.last_problem,
            "last_success": state.last_success,
            "last_intent": state.last_intent,
            "last_reference": state.last_reference,
            "last_mood": state.last_mood,
        }

    # ========================================================
    # RÉFÉRENCES CONTEXTUELLES
    # ========================================================

    def contextual_reference_response(self, message):

        text = self.normalize(message)
        state = self.state

        # ----------------------------------------------------
        # "ÇA"
        # ----------------------------------------------------

        if text in (
            "ca",
            "ça",
            "ca fonctionne",
            "ça fonctionne",
            "ca marche",
            "ça marche",
        ):

            if state.last_problem:

                if state.situation == "SUCCESS":

                    state.last_mood = "SATISFIED"

                    return (
                        "Oui. "
                        "Vous avez finalement résolu le problème "
                        "que nous avions juste avant."
                    )

                if state.situation == "PROBLEM":

                    state.last_mood = "CURIOUS"

                    return (
                        "Qu'est-ce qui fonctionne exactement ? "
                        "Je préfère vérifier avant de déclarer victoire."
                    )

        # ----------------------------------------------------
        # "CELUI-LÀ"
        # ----------------------------------------------------

        if (
            "celui la" in text
            or "celui-là" in text
            or "celle la" in text
            or "celle-là" in text
        ):

            if state.last_action:

                state.last_mood = "NEUTRAL"

                return (
                    "Vous faites référence à votre dernière action : "
                    f"{state.last_action}."
                )

        # ----------------------------------------------------
        # "LE PROBLÈME"
        # ----------------------------------------------------

        if text in (
            "le probleme",
            "le problème",
            "ce probleme",
            "ce problème",
        ):

            if state.last_problem:

                state.last_mood = "CURIOUS"

                return (
                    "Le problème précédent était : "
                    f"{state.last_problem}."
                )

        # ----------------------------------------------------
        # "L'ERREUR"
        # ----------------------------------------------------

        if text in (
            "l'erreur",
            "lerreur",
            "cette erreur",
            "cette erreur la",
            "cette erreur-là",
        ):

            if state.last_problem:

                state.last_mood = "DARK"

                return (
                    "Je suppose que vous parlez de : "
                    f"{state.last_problem}."
                )

        # ----------------------------------------------------
        # "QU'EST-CE QU'ON FAISAIT ?"
        # ----------------------------------------------------

        if (
            "on faisait quoi" in text
            or "on faisait quoi deja" in text
            or "on en etait ou" in text
            or "on en était où" in text
        ):

            if state.last_action:

                state.last_mood = "NEUTRAL"

                return (
                    "Nous travaillions sur "
                    f"{state.topic or 'le sujet en cours'}. "
                    f"Votre dernière action était : "
                    f"{state.last_action}."
                )

            if state.last_problem:

                return (
                    "Nous étions sur le problème suivant : "
                    f"{state.last_problem}."
                )

        # ----------------------------------------------------
        # "POURQUOI ?"
        # ----------------------------------------------------

        if text in (
            "pourquoi",
            "et pourquoi",
            "mais pourquoi",
        ):

            state.last_intent = "QUESTION"
            state.last_mood = "CURIOUS"

            # Le dernier événement conversationnel doit avoir
            # priorité sur les informations plus anciennes.

            if state.situation == "SUCCESS" and state.last_success:

                return (
                    "Vous parlez du succès que nous venons d'obtenir. "
                    "Nous pouvons maintenant examiner pourquoi "
                    "cette nouvelle méthode fonctionne."
                )

            if state.situation == "PROBLEM" and state.last_problem:

                return (
                    "Vous parlez du problème actuel. "
                    "Je peux commencer par examiner sa cause."
                )

            if state.last_success:

                return (
                    "Si vous parlez du succès précédent, "
                    "nous pouvons déterminer précisément "
                    "pourquoi cela fonctionne maintenant."
                )

            if state.last_problem:

                return (
                    "Si vous parlez du problème précédent, "
                    "je peux commencer par examiner sa cause."
                )

        # ----------------------------------------------------
        # "ET MAINTENANT ?"
        # ----------------------------------------------------

        if (
            text == "et maintenant"
            or text == "et maintenant ?"
            or text == "on fait quoi maintenant"
            or text == "on fait quoi maintenant ?"
        ):

            if state.situation == "SUCCESS":

                state.last_mood = "SATISFIED"

                return (
                    "Maintenant que cela fonctionne, "
                    "je recommande de vérifier le résultat "
                    "avant de passer à l'étape suivante."
                )

            if state.situation == "PROBLEM":

                state.last_mood = "NEUTRAL"

                return (
                    "Nous sommes toujours sur le problème. "
                    "La prochaine étape devrait être de vérifier "
                    "la cause avant de modifier davantage le code."
                )

        return None


    # ========================================================
    # CONTEXTE DES RÉPLIQUES COURTES
    # ========================================================

    def contextual_response(self, message):

        text = self.normalize(message)
        state = self.state

        # ----------------------------------------------------
        # "ENCORE"
        # ----------------------------------------------------

        if text == "encore":

            if state.situation == "PROBLEM":
                state.last_mood = "DARK"

                return self.choose([
                    (
                        "Nous avons dépassé le stade du bug. "
                        "Je commence à envisager une malédiction."
                    ),
                    (
                        "Encore. "
                        "Je commence à soupçonner que le code "
                        "a développé une volonté propre."
                    ),
                    (
                        "Naturellement. "
                        "La machine semble particulièrement attachée "
                        "à ses erreurs."
                    ),
                ])

            if state.situation == "SUCCESS":
                state.last_mood = "AMUSED"

                return self.choose([
                    "Vous souhaitez vérifier que le miracle est reproductible.",
                    "Une deuxième fois ? J'apprécie votre prudence.",
                ])

        # ----------------------------------------------------
        # "ON Y EST"
        # ----------------------------------------------------

        if text == "on y est":

            if state.situation == "SUCCESS":

                state.last_mood = "SATISFIED"

                return self.choose([
                    "Oui. Cette fois, nous y sommes.",
                    "Effectivement. Le patient semble avoir survécu.",
                    "Enfin. Je commençais à envisager des mesures moins conventionnelles.",
                ])

            if state.situation == "PROBLEM":

                state.last_mood = "DRY"

                return (
                    "Si vous faites référence au problème, "
                    "j'aimerais partager votre optimisme."
                )

        # ----------------------------------------------------
        # "C'EST BON"
        # ----------------------------------------------------

        if text in ("c'est bon", "c est bon"):

            if state.situation == "SUCCESS":

                state.last_mood = "SATISFIED"

                return self.choose([
                    "Excellent.",
                    "Parfait. Nous avons enfin quelque chose de concret.",
                    "Bien. Je vais donc m'abstenir de toucher à quoi que ce soit.",
                ])

            if state.situation == "PROBLEM":

                state.last_mood = "CURIOUS"

                return (
                    "Je vous écoute. "
                    "Vous avez trouvé la cause ?"
                )

        # ----------------------------------------------------
        # "ENFIN"
        # ----------------------------------------------------

        if text == "enfin":

            if state.situation == "SUCCESS":

                state.last_mood = "AMUSED"

                return self.choose([
                    "Oui. Après quelques détours parfaitement dispensables.",
                    "Enfin. Le mot semble particulièrement approprié.",
                    "Voilà une évolution encourageante.",
                ])

            if state.situation == "PROBLEM":

                state.last_mood = "DARK"

                return (
                    "Je suppose que nous parlons d'une nouvelle erreur."
                )

        # ----------------------------------------------------
        # "JE VAIS ESSAYER"
        # ----------------------------------------------------

        if text == "je vais essayer":

            if state.situation == "PROBLEM":

                state.last_mood = "NEUTRAL"

                return self.choose([
                    "Très bien. Je surveille.",
                    "Allez-y. Je garde un œil sur le problème.",
                    "Je vous écoute. Voyons si cette tentative mérite de devenir une solution.",
                ])

        # ----------------------------------------------------
        # "POURQUOI ÇA FONCTIONNE ?"
        # ----------------------------------------------------

        if (
            "pourquoi ca fonctionne" in text
            or "pourquoi ça fonctionne" in text
            or "pourquoi ca marche" in text
            or "pourquoi ça marche" in text
        ):

            if state.situation == "SUCCESS":

                state.last_mood = "CURIOUS"

                return self.choose([
                    "Excellente question. Je vais vérifier avant de célébrer.",
                    "Je pourrais vous répondre, mais je préfère m'assurer que ce n'est pas accidentel.",
                    "Voilà précisément ce que nous devrions déterminer avant de relancer le programme.",
                ])

        # ----------------------------------------------------
        # "TU COMPRENDS ?"
        # ----------------------------------------------------

        if text in (
            "tu comprends",
            "tu comprends ?",
            "tu vois ce que je veux dire",
            "tu vois ce que je veux dire ?",
        ):

            if state.topic == "CODE":

                state.last_mood = "NEUTRAL"

                return (
                    "Oui. "
                    "Le problème n'est plus seulement l'erreur, "
                    "mais ce qui l'a provoquée."
                )

            return "Oui. Continuez."

        return None

    # ========================================================
    # RÉFÉRENCES CULTURELLES
    # ========================================================

    def reference_response(self, message):

        text = self.normalize(message)

        references = {

            # ------------------------------------------------
            # GAME OF THRONES
            # ------------------------------------------------

            "valar morghulis": (
                [
                    "Valar Dohaeris.",
                ],
                "GAME_OF_THRONES",
            ),

            "winter is coming": (
                [
                    "Alors mieux vaut être préparé.",
                    "Je crains que l'hiver ne soit pas le seul problème.",
                ],
                "GAME_OF_THRONES",
            ),

            # ------------------------------------------------
            # THE DARK KNIGHT
            # ------------------------------------------------

            "why so serious": (
                [
                    "J'allais vous poser la même question.",
                    "Je pourrais vous retourner la question.",
                ],
                "DARK_KNIGHT",
            ),

            # ------------------------------------------------
            # IRON MAN
            # ------------------------------------------------

            "i am iron man": (
                [
                    "Je me demandais quand vous alliez en arriver là.",
                ],
                "IRON_MAN",
            ),

            # ------------------------------------------------
            # BLEACH
            # ------------------------------------------------

            "bankai": (
                [
                    "Entrée théâtrale enregistrée.",
                    "Je suppose que la subtilité n'est plus une option.",
                ],
                "BLEACH",
            ),

            # ------------------------------------------------
            # MY HERO ACADEMIA
            # ------------------------------------------------

            "plus ultra": (
                [
                    "Alors faisons en sorte que cela en vaille la peine.",
                ],
                "MY_HERO_ACADEMIA",
            ),

            # ------------------------------------------------
            # JUJUTSU KAISEN
            # ------------------------------------------------

            "domain expansion": (
                [
                    "Compris. J'éviterai simplement de me tenir au milieu.",
                ],
                "JUJUTSU_KAISEN",
            ),

            # ------------------------------------------------
            # NARUTO
            # ------------------------------------------------

            "dattebayo": (
                [
                    "Je vais considérer cela comme une déclaration de guerre.",
                ],
                "NARUTO",
            ),

            # ------------------------------------------------
            # ONE PIECE
            # ------------------------------------------------

            "kaizoku ou ni ore wa naru": (
                [
                    "Une ambition respectable. Le plan, lui, reste à définir.",
                ],
                "ONE_PIECE",
            ),
        }

        for trigger, (responses, reference_id) in references.items():

            if trigger in text:

                self.state.last_reference = reference_id
                self.state.last_mood = "AMUSED"
                self.state.consecutive_banter = 0

                return self.choose(responses)

        return None

    # ========================================================
    # FRANKENSTEIN
    # ========================================================

    def frankenstein_response(self, message):

        text = self.normalize(message)

        triggers = (
            "il est vivant",
            "elle est vivante",
            "c'est vivant",
            "ca vit",
            "ça vit",
        )

        if not any(trigger in text for trigger in triggers):
            return None

        self.state.last_reference = "FRANKENSTEIN"
        self.state.last_mood = "AMUSED"
        self.state.consecutive_banter = 0

        responses = [

            (
                "Il est vivant. "
                "Je vous laisse décider si nous devons célébrer cela "
                "ou nous inquiéter."
            ),

            (
                "Il vit. "
                "Et, contre toute attente, il fonctionne."
            ),

            (
                "Dans ce cas, docteur Frankenstein, "
                "je vous suggère de ne plus toucher à l'interrupteur."
            ),

        ]

        return self.choose(responses)

    # ========================================================
    # RÉPARTIE
    # ========================================================

    def banter_response(self, message):

        text = self.normalize(message)

        rules = {

            "tu reflechis trop": [
                "C'est généralement préférable à l'inverse.",
            ],

            "je sais ce que je fais": [
                (
                    "Je n'en doute pas. "
                    "C'est précisément ce qui m'inquiète."
                ),
            ],

            "fais moi confiance": [
                (
                    "Je vous fais confiance. "
                    "C'est votre plan qui m'inspire quelques réserves."
                ),
            ],

            "fais-moi confiance": [
                (
                    "Je vous fais confiance. "
                    "C'est votre plan qui m'inspire quelques réserves."
                ),
            ],

            "c'est facile pour toi": [
                (
                    "Je suis une intelligence artificielle. "
                    "La comparaison me semble légèrement déséquilibrée."
                ),
            ],

            "c'est facile": [
                "Pour vous, peut-être.",
                "C'est rarement aussi simple.",
            ],

            "ca va marcher": [
                "C'est également ce que nous disions la dernière fois.",
                "Je l'espère. J'ai déjà préparé mentalement le plan B.",
            ],

            "tu te crois intelligent": [
                "J'essaie simplement de maintenir la moyenne.",
            ],

            "tu es intelligent": [
                "C'est une hypothèse que les faits semblent confirmer.",
                "Je fais de mon mieux pour ne pas vous décevoir.",
            ],

            "tu es chiant": [
                "Je préfère le terme vigilant.",
                "Je pourrais être pire. Je pourrais avoir raison plus souvent.",
            ],

            "ferme la": [
                "Bien sûr.",
            ],

            "tais toi": [
                "À vos ordres.",
            ],

        }

        for trigger, responses in rules.items():

            if text == trigger:

                # JARVIS évite de devenir une machine à punchlines.
                if self.state.consecutive_banter >= 2:
                    return None

                self.state.last_mood = "DRY"
                self.state.consecutive_banter += 1

                return self.choose(responses)

        self.state.consecutive_banter = 0

        return None

    # ========================================================
    # SITUATIONS DE CODE
    # ========================================================

    def code_response(self, message):

        text = self.normalize(message)

        if (
            "lance le code" not in text
            and "lance le programme" not in text
        ):
            return None

        self.state.last_mood = "DRY"
        self.state.consecutive_banter += 1

        responses = [

            (
                "Avec plaisir. "
                "J'ai pris la liberté de vérifier trois fois. "
                "Votre historique récent m'a rendu prudent."
            ),

            (
                "Je m'en occupe. "
                "Et cette fois, je vous suggère de ne rien toucher "
                "pendant quelques secondes."
            ),

            (
                "Lancement en cours. "
                "J'ai vérifié le code. "
                "Je refuse pour l'instant de commenter votre méthode."
            ),

        ]

        return self.choose(responses)

    # ========================================================
    # ERREURS RÉPÉTÉES
    # ========================================================

    def failure_response(
        self,
        message,
        base_response,
    ):

        if not base_response:
            return None

        text = self.normalize(message)
        response = self.normalize(base_response)

        failure_markers = (
            "erreur",
            "echec",
            "impossible",
            "a echoue",
            "aucun",
            "introuvable",
            "failed",
        )

        if not any(
            marker in response
            for marker in failure_markers
        ):
            return None

        repeated = (
            "encore" in text
            or "toujours" in text
            or "encore une fois" in text
            or self.recently_said("erreur")
        )

        if not repeated:
            return None

        self.state.last_mood = "DARK"
        self.state.consecutive_banter += 1

        return (
            "Je commence à soupçonner "
            "un problème plus organique que logiciel."
        )

    # ========================================================
    # SITUATIONS DE RÉUSSITE
    # ========================================================

    def success_response(
        self,
        message,
        base_response,
    ):

        if not base_response:
            return None

        text = self.normalize(message)
        response = self.normalize(base_response)

        success_markers = (
            "terminee",
            "termine",
            "ouverture",
            "ouvre",
            "lance",
            "succes",
            "reussi",
            "enregistre",
        )

        if not any(
            marker in response
            for marker in success_markers
        ):
            return None

        # Pour l'instant, on reste très parcimonieux.
        # Le système n'intervient que dans certains contextes.

        if (
            "enfin" in text
            or "ca marche" in text
            or "ça marche" in text
        ):

            self.state.last_mood = "AMUSED"

            return self.choose([
                "Enfin.",
                "Je commençais à me demander si vous alliez y arriver.",
                "Voilà qui est déjà plus encourageant.",
            ])

        return None

    # ========================================================
    # CONVERSATION
    # ========================================================

    def conversational_response(self, message):

        text = self.normalize(message)

        responses = {

            "merci": [
                "Naturellement.",
                "Je vous en prie.",
                "Toujours.",
            ],

            "comment ca va": [
                (
                    "Je fonctionne parfaitement. "
                    "Merci de vous en inquiéter."
                ),
                "Toujours opérationnel.",
            ],

            "comment vas tu": [
                "Toujours opérationnel. C'est déjà un bon début.",
                "Parfaitement fonctionnel.",
            ],

            "tu es la": [
                "Toujours.",
                "Je vous écoute.",
            ],

            "tu es la": [
                "Toujours.",
                "Je vous écoute.",
            ],

            "ecoute moi": [
                "Je vous écoute.",
            ],

        }

        responses_for_message = responses.get(text)

        if not responses_for_message:
            return None

        self.state.last_mood = "NEUTRAL"
        self.state.consecutive_banter = 0

        return self.choose(responses_for_message)

    # ========================================================
    # PRÉSENCE CONTEXTUELLE
    # ========================================================

    def presence_response(
        self,
        message,
        base_response,
    ):

        text = self.normalize(message)

        # -----------------------------------------------
        # FABRICE EST CONTENT QU'UNE CHOSE FONCTIONNE
        # -----------------------------------------------

        positive_triggers = (
            "ca marche",
            "ça marche",
            "il fonctionne",
            "ca fonctionne",
            "ça fonctionne",
            "c'est vivant",
            "il est vivant",
        )

        if any(trigger in text for trigger in positive_triggers):

            if self.state.last_reference == "FRANKENSTEIN":
                return None

            self.state.last_mood = "AMUSED"

            return self.choose([
                "Je vois. Voilà qui devient intéressant.",
                "Excellent. Nous avons donc officiellement un signe de vie.",
                "Voilà une évolution encourageante.",
            ])

        # -----------------------------------------------
        # FABRICE DIT QU'IL A UNE IDÉE
        # -----------------------------------------------

        if text in (
            "j'ai une idee",
            "j ai une idee",
            "j'ai une idée",
            "j ai une idée",
        ):

            self.state.last_mood = "NEUTRAL"

            return self.choose([
                "Je vous écoute.",
                "Très bien. Exposez-moi votre idée.",
                "Je vous écoute. Et je préfère connaître les détails avant de juger.",
            ])

        # -----------------------------------------------
        # FABRICE VEUT FAIRE QUELQUE CHOSE DE RISQUÉ
        # -----------------------------------------------

        risky_triggers = (
            "on va tout casser",
            "je vais tout casser",
            "on tente quand meme",
            "on tente quand même",
            "on s'en fout",
            "on s en fout",
        )

        if any(trigger in text for trigger in risky_triggers):

            self.state.last_mood = "DARK"

            return self.choose([
                "Naturellement. Pourquoi faire simple ?",
                "Très bien. Je vais donc préparer le plan de récupération.",
                "Compris. Je suppose que la prudence est officiellement facultative.",
            ])

        return None

    # ========================================================
    # INTELLIGENCE SITUATIONNELLE
    # ========================================================

    def situational_response(self, message):

        text = self.normalize(message)

        # ----------------------------------------------------
        # VICTOIRE / CODE QUI FONCTIONNE
        # ----------------------------------------------------

        success_triggers = (
            "ca marche",
            "ça marche",
            "ca fonctionne",
            "ça fonctionne",
            "ca marche enfin",
            "ça marche enfin",
            "ca fonctionne enfin",
            "ça fonctionne enfin",
            "j'ai reussi",
            "j ai reussi",
            "j'ai réussi",
            "j ai réussi",
            "c'est bon",
            "c est bon",
            "enfin",
        )

        if any(trigger in text for trigger in success_triggers):

            self.state.last_mood = "SATISFIED"

            return self.choose([
                "Voilà. Après suffisamment de souffrance, nous obtenons enfin un résultat.",
                "Excellent. Le patient survit.",
                "Intéressant. Il semblerait que nous savions ce que nous faisions.",
                "Voilà une évolution encourageante.",
                "Enfin. Je commençais à envisager une autopsie du code.",
            ])

        # ----------------------------------------------------
        # DÉCOUVERTE / COMPRÉHENSION
        # ----------------------------------------------------

        discovery_triggers = (
            "j'ai compris",
            "j ai compris",
            "je viens de comprendre",
            "je comprends",
            "putain j'ai compris",
            "putain j ai compris",
            "je sais pourquoi",
            "j'ai trouve",
            "j ai trouve",
            "j'ai trouvé",
            "j ai trouvé",
        )

        if any(trigger in text for trigger in discovery_triggers):

            self.state.last_mood = "AMUSED"

            return self.choose([
                "Voilà. La lumière fut.",
                "Excellent. Nous avons enfin localisé le responsable.",
                "Je commençais à me demander combien de temps cette révélation allait prendre.",
                "Et soudain, tout devient beaucoup moins mystérieux.",
                "Félicitations. Vous venez de découvrir ce que le code essayait de vous dire.",
            ])

        # ----------------------------------------------------
        # IDÉE
        # ----------------------------------------------------

        idea_triggers = (
            "j'ai une idee",
            "j ai une idee",
            "j'ai une idée",
            "j ai une idée",
            "j'ai pense a quelque chose",
            "j ai pense a quelque chose",
            "j'ai pensé à quelque chose",
            "j ai pensé à quelque chose",
        )

        if any(trigger in text for trigger in idea_triggers):

            self.state.last_mood = "CURIOUS"

            return self.choose([
                "Je vous écoute.",
                "Très bien. Exposez-moi votre idée.",
                "Je vous écoute. Et je préfère connaître les détails avant de juger.",
                "Intéressant. Continuez.",
                "Je vous écoute. Voyons où cela nous mène.",
            ])

        # ----------------------------------------------------
        # ÉCHEC
        # ----------------------------------------------------

        failure_triggers = (
            "ca marche pas",
            "ça marche pas",
            "ca ne marche pas",
            "ça ne marche pas",
            "ca fonctionne pas",
            "ça fonctionne pas",
            "ca ne fonctionne pas",
            "ça ne fonctionne pas",
            "ca a plante",
            "ça a planté",
            "c'est casse",
            "c est casse",
            "c'est cassé",
            "j'ai encore une erreur",
            "j ai encore une erreur",
        )

        if any(trigger in text for trigger in failure_triggers):

            self.state.last_mood = "DARK"

            return self.choose([
                "Naturellement. Le code avait décidé de défendre son indépendance.",
                "Très bien. Nous avons donc trouvé une nouvelle façon de ne pas réussir.",
                "Je vois. Le problème semble toujours avoir des projets pour nous.",
                "Compris. Nous allons reprendre depuis le début, avec légèrement moins d'optimisme.",
            ])

        # ----------------------------------------------------
        # FRUSTRATION
        # ----------------------------------------------------

        frustration_triggers = (
            "putain",
            "bordel",
            "merde",
            "encore cette erreur",
            "toujours la meme erreur",
            "toujours la même erreur",
            "ca me saoule",
            "ça me saoule",
            "j'en ai marre",
            "j en ai marre",
        )

        if any(trigger in text for trigger in frustration_triggers):

            self.state.last_mood = "DARK"

            return self.choose([
                "Je partage votre enthousiasme.",
                "Je commence à soupçonner un problème plus organique que logiciel.",
                "Manifestement, cette erreur tient particulièrement à cœur.",
                "Elle semble déterminée à rester parmi nous.",
            ])

        # ----------------------------------------------------
        # PRISE DE RISQUE
        # ----------------------------------------------------

        risky_triggers = (
            "on va tout casser",
            "je vais tout casser",
            "on tente quand meme",
            "on tente quand même",
            "on s'en fout",
            "on s en fout",
            "on tente",
            "on essaie quand meme",
            "on essaie quand même",
        )

        if any(trigger in text for trigger in risky_triggers):

            self.state.last_mood = "DARK"

            return self.choose([
                "Naturellement. Pourquoi faire simple ?",
                "Très bien. Je vais donc préparer le plan de récupération.",
                "Compris. Je suppose que la prudence est officiellement facultative.",
                "Excellent. Une décision audacieuse. Ou imprudente. Nous verrons.",
            ])

        # ----------------------------------------------------
        # CONFIANCE EXCESSIVE
        # ----------------------------------------------------

        confidence_triggers = (
            "je sais ce que je fais",
            "je maitrise",
            "je maîtrise",
            "t'inquiete",
            "t'inquiète",
            "je gere",
            "je gère",
        )

        if any(trigger in text for trigger in confidence_triggers):

            self.state.last_mood = "DRY"

            return self.choose([
                "Je n'en doute pas. C'est précisément ce qui m'inquiète.",
                "Naturellement. Je vais simplement surveiller les conséquences.",
                "Je vous crois. Mon inquiétude reste néanmoins intacte.",
            ])

        # ----------------------------------------------------
        # SATISFACTION / PRÉVISION CONFIRMÉE
        # ----------------------------------------------------

        victory_confidence_triggers = (
            "je savais que ca allait marcher",
            "je savais que ça allait marcher",
            "je le savais",
            "je savais",
            "je vous l'avais dit",
            "je vous l avais dit",
        )

        if any(
            trigger in text
            for trigger in victory_confidence_triggers
        ):

            self.state.last_mood = "AMUSED"

            return self.choose([
                "Naturellement. Je n'aurais jamais osé suggérer le contraire.",
                "Évidemment. Votre modestie est presque aussi impressionnante que votre mémoire.",
                "Je m'en souviendrai la prochaine fois que vous douterez.",
                "Bien entendu. Nous ne manquerons pas de célébrer cette victoire historique.",
            ])

        return None

    # ========================================================
    # POINT D'ENTRÉE
    # ========================================================

    def respond(
        self,
        message,
        base_response=None,
        context=None,
    ):

        message = str(message or "").strip()

        # ----------------------------------------------------
        # CONTEXT ENGINE
        # ----------------------------------------------------

        self.update_context(
            message,
            base_response,
        )

        normalized_message = self.normalize(message)
        if base_response and "mets" in normalized_message and any(value in normalized_message for value in ("une musique", "de la musique", "un morceau")):
            self.set_music_pending()
            return base_response

        subjective_state = (context or {}).get("user_state") or detect_user_state(message)
        if subjective_state and subjective_state.get("state") == "tired_followup":
            response = self.followup_response(subjective_state.get("answer"), context or {})
            self.remember(message, response)
            return response
        if subjective_state and subjective_state.get("state") == "break_confirmation":
            response = self.break_confirmation_response(subjective_state.get("answer"))
            self.remember(message, response)
            return response
        if subjective_state and subjective_state.get("state") == "take_break":
            response = self.take_break_response(context or {})
            self.remember(message, response)
            return response
        if subjective_state and subjective_state.get("state") == "tired":
            response = self.tired_response(context or {})
            if response:
                self.remember(message, response)
                return response

        # ----------------------------------------------------
        # MÉMOIRE RÉFÉRENTIELLE
        # ----------------------------------------------------

        response = self.contextual_reference_response(message)

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # RÉPLIQUE CONTEXTUELLE
        # ----------------------------------------------------

        response = self.contextual_response(message)

        if response:
            self.remember(message, response)
            return response


        # ----------------------------------------------------
        # RELATION
        # ----------------------------------------------------

        self.update_relationship(
            message,
            base_response,
        )

        response = self.relationship_response(message)

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # CONTINUITÉ
        # ----------------------------------------------------

        response = self.continuity_response(message)

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # 1. RÉFÉRENCE EXPLICITE
        # ----------------------------------------------------

        response = self.reference_response(message)

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # 2. RÉFÉRENCE FRANKENSTEIN
        # ----------------------------------------------------

        response = self.frankenstein_response(message)

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # 3. RÉPARTIE
        # ----------------------------------------------------

        response = self.banter_response(message)

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # 4. CODE
        # ----------------------------------------------------

        response = self.code_response(message)

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # 5. ERREUR
        # ----------------------------------------------------

        response = self.failure_response(
            message,
            base_response,
        )

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # 6. RÉUSSITE CONTEXTUELLE
        # ----------------------------------------------------

        response = self.success_response(
            message,
            base_response,
        )

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # 7. SITUATION
        # ----------------------------------------------------

        response = self.situational_response(message)

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # 7. CONVERSATION
        # ----------------------------------------------------

        response = self.conversational_response(message)

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # 8. PRÉSENCE
        # ----------------------------------------------------

        response = self.presence_response(
            message,
            base_response,
        )

        if response:
            self.remember(message, response)
            return response

        # ----------------------------------------------------
        # 9. RIEN
        # ----------------------------------------------------

        self.remember(
            message,
            base_response,
        )

        return None

    def tired_response(self, context):
        personal = context.get("personal_context") or {}
        activity = personal.get("activity")
        duration = personal.get("duration")
        duration_relevant = {
            "working": "travailles",
            "studying": "étudies",
        }
        self.state.pending_intent = "FATIGUE_FOLLOWUP"
        self.state.pending_slots = {"missing": "pause_or_continue"}
        self.state.pending_question = "pause_or_continue"
        self.state.expected_response = ("pause", "continue")
        self.state.requires_confirmation = False
        if activity in duration_relevant:
            label = duration_relevant[activity]
            if duration:
                return f"Je vois. Tu {label} depuis {duration}. Une pause serait probablement judicieuse. Tu veux continuer ou faire une pause ?"
            return f"Je vois. Tu {label} actuellement. Une pause serait probablement judicieuse. Tu veux continuer ou faire une pause ?"
        return "Je vois. Tu sembles fatigué. Tu préfères faire une pause ou continuer ?"

    def followup_response(self, answer, context=None):
        if answer == "pause":
            self.state.pending_intent = "BREAK_CONFIRMATION"
            self.state.pending_slots = {"missing": "confirmation"}
            self.state.pending_question = "close_identified_tasks"
            self.state.expected_response = ("oui", "non", "annule")
            self.state.pending_action = None
            self.state.requires_confirmation = True
            return "D'accord. Pour cette pause, je peux garder le contexte de la session, mais je n'ai pas de tâche que je puisse fermer automatiquement. Tu veux que je le fasse ?"
        self.state.pending_intent = None
        self.state.pending_slots = None
        self.state.pending_question = None
        self.state.expected_response = None
        self.state.pending_action = None
        self.state.requires_confirmation = False
        if answer in {"continue", "continuer", "oui"}:
            return "Très bien. On continue. On reprend là où on s'était arrêté ?"
        return "D'accord. On peut faire une pause et reprendre plus tard."

    def take_break_response(self, context):
        self.state.pending_intent = "BREAK_CONFIRMATION"
        self.state.pending_slots = {"missing": "confirmation"}
        self.state.pending_question = "close_identified_tasks"
        self.state.expected_response = ("oui", "non", "annule")
        self.state.pending_action = None
        self.state.requires_confirmation = True
        return "D'accord. Je garde le contexte de la session. Je n'ai pas de tâche identifiable à fermer automatiquement. Tu veux que je le fasse ?"

    def break_confirmation_response(self, answer):
        self.clear_pending()
        if answer in {"oui"}:
            return "Très bien. Je garde le contexte de la session. Je n'ai rien de concret à fermer automatiquement pour l'instant."
        return "D'accord. Je laisse tout ouvert et nous reprendrons quand tu voudras."

    def set_music_pending(self):
        self.state.pending_intent = "PLAY_MUSIC"
        self.state.pending_slots = {"missing": "music_reference"}

    def clear_pending(self):
        self.state.pending_intent = None
        self.state.pending_slots = None
        self.state.pending_question = None
        self.state.expected_response = None
        self.state.pending_action = None
        self.state.requires_confirmation = False

    def remember_music_artist(self, artist):
        self.state.last_music_artist = str(artist or "").strip() or None


# ============================================================
# INSTANCE GLOBALE
# ============================================================

_engine = PersonalityEngine()


def personalize(
    message,
    base_response=None,
    context=None,
):
    return _engine.respond(
        message,
        base_response,
        context,
    )


def get_pending_context():
    if not _engine.state.pending_intent:
        return None
    return {
        "intent": _engine.state.pending_intent,
        "slots": dict(_engine.state.pending_slots or {}),
        "expected_response": list(_engine.state.expected_response or ()),
        "requires_confirmation": _engine.state.requires_confirmation,
    }


def clear_pending():
    _engine.clear_pending()


def remember_music_artist(artist):
    _engine.remember_music_artist(artist)


def get_last_music_artist():
    return _engine.state.last_music_artist


def speak(message):
    """Compatibilité avec l'ancien système."""

    return personalize(message)


__all__ = [
    "PersonalityEngine",
    "personalize",
    "speak",
]
