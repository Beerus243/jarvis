from sentence_transformers import SentenceTransformer
import numpy as np


# ============================================================
# MODÈLE D'EMBEDDINGS
# ============================================================

model = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# ============================================================
# TRANSFORMER UN TEXTE EN EMBEDDING
# ============================================================

def encode(text):

    vector = model.encode(
        text,
        normalize_embeddings=True
    )

    return vector.tolist()


# ============================================================
# CALCULER LA SIMILARITÉ
# ============================================================

def similarity(vector1, vector2):

    vector1 = np.array(vector1)
    vector2 = np.array(vector2)

    return float(
        np.dot(vector1, vector2)
    )


# ============================================================
# EMBEDDING D'UN SOUVENIR
# ============================================================

def create_memory_embedding(content):

    return encode(content)