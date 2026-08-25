// Test de transport uniquement : aucune fenêtre n'est lue ou modifiée.
function pingJarvis() {
    callDBus(
        "org.jarvis.WindowContext",
        "/WindowContext",
        "org.jarvis.WindowContext",
        "Ping",
        function (reply) {
            print("JARVIS_DBus_PING_REPLY:" + reply);
        }
    );
}

pingJarvis();
