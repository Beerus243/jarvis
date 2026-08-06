import json

user = {
    "name" : "Fabrice",
    "postnom" : "Malanga",
    "ville" : "Kinshasa",
    "passion" : "Informatique,anime,jeux vidéo"

}

print(json.dumps(user))
with open("user.json", "w") as f:
    json.dump(user, f)