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


# ============================================================
# RECHERCHE SÉMANTIQUE
# ============================================================

def search_semantic_memory(query, souvenirs, limit=3):

    if not souvenirs:
        return []


    # --------------------------------------------------------
    # Transformer la question en embedding
    # --------------------------------------------------------

    query_embedding = encode(query)


    results = []


    # --------------------------------------------------------
    # Comparer avec chaque souvenir
    # --------------------------------------------------------

    for souvenir in souvenirs:

        embedding = souvenir.get("embedding")

        if not embedding:
            continue


        score = similarity(
            query_embedding,
            embedding
        )


        results.append({
            "souvenir": souvenir,
            "score": score
        })


    # --------------------------------------------------------
    # Trier du plus proche au moins proche
    # --------------------------------------------------------

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    # --------------------------------------------------------
    # Retourner les meilleurs résultats
    # --------------------------------------------------------

    return results[:limit]