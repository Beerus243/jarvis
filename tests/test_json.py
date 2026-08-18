import json
from config.settings import MEMORY_FILE

user = {
    "name" : "Fabrice",
    "postnom" : "Malanga",
    "ville" : "Kinshasa",
    "passion" : "Informatique,anime,jeux vidéo"

}

print(json.dumps(user))
with open(MEMORY_FILE, "w", encoding="utf-8") as f:
    json.dump(user, f)
