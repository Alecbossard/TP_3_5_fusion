"""Réception Ivy UTF-8 et compatibilité avec les agents Windows CP1252.

ivy-python 4 décode chaque recv() en UTF-8. Les anciens agents du cours
peuvent transmettre des accents Windows-1252; un caractère UTF-8 peut aussi
être coupé entre deux recv(). Cet adaptateur local reconstruit d'abord les
trames délimitées par LF, puis décode chaque trame. Aucun fichier installé
et aucun comportement global de la bibliothèque ne sont modifiés.
"""

import logging
import socket

LOGGER = logging.getLogger(__name__)


class DecodeurTrames:
    def __init__(self):
        self.pending = b""
        self.legacy_detected = False

    def feed(self, chunk):
        parts = (self.pending + chunk).split(b"\n")
        self.pending = parts.pop()
        decoded = []
        for frame in parts:
            try:
                text = frame.decode("utf-8")
            except UnicodeDecodeError:
                text = frame.decode("cp1252")
                self.legacy_detected = True
            decoded.append(text)
        return decoded


def creer_serveur_compatible(name):
    # Import différé : la simulation locale ne requiert pas ivy-python.
    from ivy.ivy import (
        IvyServer,
        IvyHandler,
        encode_message,
        START_INIT,
        ADD_REGEXP,
        END_INIT,
    )

    class GestionnaireCompatible(IvyHandler):
        def handle(self):
            ip, port = self.client_address
            connection = self.request
            decoder = DecodeurTrames()
            warned = False
            try:
                client = self.server.get_client(ip, port)
            except ValueError:
                client = self.server.register_client(ip, port, connection)
            try:
                connection.sendall(
                    encode_message(START_INIT, self.server.port, self.server.agent_name)
                )
                for index, subscription in self.server.get_subscriptions():
                    connection.sendall(encode_message(ADD_REGEXP, index, subscription))
                connection.sendall(encode_message(END_INIT, 0))
                while self.server.isAlive():
                    try:
                        chunk = connection.recv(1024)
                    except socket.timeout:
                        continue
                    if not chunk:
                        return
                    frames = decoder.feed(chunk)
                    if decoder.legacy_detected and not warned:
                        LOGGER.warning(
                            "Agent Ivy Windows détecté : réception des accents en CP1252."
                        )
                        warned = True
                    for frame in frames:
                        if not self.process_ivymessage(frame, client):
                            return
            except (OSError, UnicodeDecodeError) as exc:
                LOGGER.warning("Connexion Ivy interrompue : %s", exc)
            finally:
                self.server.remove_client(ip, port)

    server = IvyServer(name)
    # SocketServer utilise cette classe pour les connexions entrantes ainsi
    # que pour les connexions initiées via la découverte UDP d'Ivy.
    server.RequestHandlerClass = GestionnaireCompatible
    return server
