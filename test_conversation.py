from conversation import add_message, get_last_message


add_message("user", "Ouvre mon navigateur")

print("Dernier message :")
print(get_last_message())


add_message("jarvis", "J'ouvre ton navigateur.")

print("Dernier message :")
print(get_last_message())