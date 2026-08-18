from voice.listen import listen

print("================================")
print("      TEST MICROPHONE")
print("================================")
print("Parle après le signal...")

message = listen()

print("Texte reconnu :", message)