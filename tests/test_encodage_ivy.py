"""Régressions : accents Windows, UTF-8 fractionné et réception TCP réelle."""

import queue
import socket
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from moteur_fusion.compatibilite_ivy import DecodeurTrames, creer_serveur_compatible
from moteur_fusion.communication_ivy import dispatch
from moteur_fusion.controleur import ControleurDialogue


class EncodageTests(unittest.TestCase):
    def test_cp1252_preserves_accents(self):
        decoder = DecodeurTrames()
        self.assertEqual(
            decoder.feed("créer un cercle\n".encode("cp1252")), ["créer un cercle"]
        )
        self.assertTrue(decoder.legacy_detected)

    def test_utf8_split_at_every_byte(self):
        data = "créer à cet endroit\n".encode("utf-8")
        for split in range(1, len(data)):
            decoder = DecodeurTrames()
            self.assertEqual(decoder.feed(data[:split]), [])
            self.assertEqual(decoder.feed(data[split:]), ["créer à cet endroit"])
            self.assertFalse(decoder.legacy_detected)

    def test_multiple_frames_and_incomplete_tail(self):
        decoder = DecodeurTrames()
        self.assertEqual(
            decoder.feed(b"premier\ndeuxieme\ntroi"), ["premier", "deuxieme"]
        )
        self.assertEqual(decoder.feed(b"sieme\n"), ["troisieme"])

    def test_mixed_peers_formats(self):
        decoder = DecodeurTrames()
        data = "créer\n".encode("cp1252") + "déplacer\n".encode("utf-8")
        self.assertEqual(decoder.feed(data), ["créer", "déplacer"])

    def test_legacy_agent_over_real_tcp(self):
        from ivy.ivy import encode_message, START_INIT, END_INIT, MSG

        inbox = queue.Queue()
        server = creer_serveur_compatible("TestEncodingReceiver")
        index = server.bind_msg(lambda agent, message: inbox.put(message), r"^(.*)$")
        server.start("127.255.255.255:2039")
        try:
            with socket.create_connection(
                ("127.0.0.1", server.port), timeout=3
            ) as connection:
                connection.sendall(
                    encode_message(START_INIT, 42420, "LegacySra5")
                    + encode_message(END_INIT, 0)
                )
                message = "sra5 Text='créer un cercle rouge ici' Confidence=0,9"
                frame = (
                    encode_message(MSG, index, [message])
                    .decode("utf-8")
                    .encode("cp1252")
                )
                # Octet 0xe9 tel que reçu du poste Windows de l'utilisateur.
                self.assertIn(b"\xe9", frame)
                connection.sendall(frame)
                received = inbox.get(timeout=3)
                self.assertEqual(received, message)
                engine = ControleurDialogue()
                self.assertTrue(dispatch(engine, received))
                self.assertEqual(engine.data.action, "creer")
                self.assertEqual(engine.data.shape, "cercle")
                # Une seconde phrase reste reçue sur la même connexion.
                connection.sendall(
                    encode_message(MSG, index, ["sra5 Text='créer' Confidence=0.9"])
                    .decode("utf-8")
                    .encode("cp1252")
                )
                self.assertEqual(
                    inbox.get(timeout=3), "sra5 Text='créer' Confidence=0.9"
                )
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
