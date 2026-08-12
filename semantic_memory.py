from sentence_transformers import SentenceTransformer
import numpy as np


# ============================================================
# MODÈLE D'EMBEDDINGS
# ============================================================

model = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# ============================================================
# TRANSFORMER UN TEXTE EN VECTEUR
# ============================================================

def encode(text):

    return model.encode(
        text,
        normalize_embeddings=True
    )


# ============================================================
# CALCULER LA SIMILARITÉ
# ============================================================

def similarity(text1, text2):

    vector1 = encode(text1)
    vector2 = encode(text2)

    return float(
        np.dot(vector1, vector2)
    )