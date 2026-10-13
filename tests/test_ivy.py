"""Vrai aller-retour Ivy local (pas un mock)."""
import queue
import unittest
from app import Transport
from fusion import FusionEngine, dispatch

class IvyIntegration(unittest.TestCase):
    def test_bus_roundtrip(self):
        inbox=queue.Queue(); bus=Transport(inbox,'127.255.255.255:2035')
        try:
            import time
            deadline=time.monotonic()+5
            while True:
                bus.send("sra5 Parsed='créer' Confidence=1 NP=1 Num_A=0")
                try: message=inbox.get(timeout=.15); break
                except queue.Empty:
                    if time.monotonic()>deadline: self.fail('Pas de découverte Ivy locale')
            e=FusionEngine(); self.assertTrue(dispatch(e,message))
            while not inbox.empty(): inbox.get_nowait()
            bus.send('OneDollarIvy Template=rectangle Confidence=0,95')
            self.assertTrue(dispatch(e,inbox.get(timeout=3)))
            bus.send("sra5 Parsed='valider' Confidence=1 NP=2 Num_A=0")
            self.assertTrue(dispatch(e,inbox.get(timeout=3)))
            self.assertEqual(len(e.scene.objects),1)
        finally: bus.close()
if __name__=='__main__': unittest.main()
