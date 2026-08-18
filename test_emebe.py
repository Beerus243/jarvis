from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


print("================================")
print("TEST EMBEDDINGS JARVIS")
print("================================")


model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


phrase_1 = "Mon backend utilise FastAPI"

phrase_2 = "Quelle technologie gère le serveur ?"

phrase_3 = "Je vais regarder un film ce soir"


embedding_1 = model.encode(
    phrase_1,
    convert_to_tensor=True
)

embedding_2 = model.encode(
    phrase_2,
    convert_to_tensor=True
)

embedding_3 = model.encode(
    phrase_3,
    convert_to_tensor=True
)


similarity_backend = cos_sim(
    embedding_1,
    embedding_2
)

similarity_different = cos_sim(
    embedding_1,
    embedding_3
)


print()
print("Phrase 1 :", phrase_1)
print("Phrase 2 :", phrase_2)
print("Phrase 3 :", phrase_3)

print()
print(
    "Similarité backend :",
    similarity_backend.item()
)

print(
    "Similarité différente :",
    similarity_different.item()
)