from text_normalizer import normalize_text
from project_parser import parse_project_information
from project_questions import detect_project_question
from intent import detect_intent


# ============================================================
# TYPES D'OPÉRATIONS
# ============================================================

READ_MEMORY = "READ_MEMORY"
UPDATE_MEMORY = "UPDATE_MEMORY"
ACTION = "ACTION"
ASK_AI = "ASK_AI"


# ============================================================
# DÉTECTER L'OPÉRATION
# ============================================================

def detect_operation(message):

    text = normalize_text(message)

    # ========================================================
    # 1. INFORMATION SUR LE PROJET
    # ========================================================

    project_information = parse_project_information(
        message
    )

    if project_information:

        return UPDATE_MEMORY


    # ========================================================
    # 2. ACTION
    # ========================================================

    intent = detect_intent(message)

    if intent:

        return ACTION


    # ========================================================
    # 3. QUESTION SUR LE PROJET
    # ========================================================

    project_question = detect_project_question(
        message
    )

    if project_question:

        return READ_MEMORY


    # ========================================================
    # 4. QUESTION GÉNÉRALE
    # ========================================================

    if (
        text.endswith("?")
        or text.startswith("pourquoi ")
        or text.startswith("comment ")
        or text.startswith("qu est ce ")
        or text.startswith("qu'est-ce ")
    ):

        return ASK_AI


    # ========================================================
    # 5. PAR DÉFAUT
    # ========================================================

    return ASK_AI