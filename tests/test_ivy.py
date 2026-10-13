"""Vrai aller-retour Ivy local, avec attente explicite des messages attendus."""

import queue
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from moteur_fusion.communication_ivy import CommunicationIvy, dispatch
from moteur_fusion.controleur import ControleurDialogue


class IvyIntegration(unittest.TestCase):
    def test_bus_roundtrip(self):
        inbox = queue.Queue()
        bus = CommunicationIvy(inbox, "127.255.255.255:2035")
        try:
            action = "sra5 Parsed='créer' Confidence=1 NP=1 Num_A=0"
            # La découverte peut perdre les premières émissions. Les retries
            # peuvent aussi produire des doublons, que l'attente suivante filtre.
            deadline = time.monotonic() + 5
            while True:
                bus.send(action)
                try:
                    message = inbox.get(timeout=0.15)
                    if message == action:
                        break
                except queue.Empty:
                    if time.monotonic() > deadline:
                        self.fail("Pas de découverte Ivy locale")
            engine = ControleurDialogue()
            self.assertTrue(dispatch(engine, message))

            def receive(expected):
                limit = time.monotonic() + 3
                while True:
                    remaining = limit - time.monotonic()
                    if remaining <= 0:
                        self.fail("Message Ivy attendu non reçu : " + expected)
                    try:
                        candidate = inbox.get(timeout=remaining)
                    except queue.Empty:
                        self.fail("Message Ivy attendu non reçu : " + expected)
                    if candidate == expected:
                        return candidate

            gesture = "OneDollarIvy Template=rectangle Confidence=0,95"
            bus.send(gesture)
            self.assertTrue(dispatch(engine, receive(gesture)))
            validation = "sra5 Parsed='valider' Confidence=1 NP=2 Num_A=0"
            bus.send(validation)
            self.assertTrue(dispatch(engine, receive(validation)))
            self.assertEqual(len(engine.scene.objects), 1)
        finally:
            bus.close()


if __name__ == "__main__":
    unittest.main()
