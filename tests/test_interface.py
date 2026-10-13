"""Vérification des fenêtres après découpage des composants.
Sous Linux sans écran, ce test est ignoré; Windows le lance normalement.
"""

import os
import sys
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from moteur_fusion.application import Application


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        if os.name != "nt" and not os.environ.get("DISPLAY"):
            self.skipTest("Un écran est requis pour Tkinter")
        self.root = tk.Tk()
        self.application = Application(self.root)
        self.addCleanup(self.application.close)

    def test_three_windows_create_and_move(self):
        app = self.application
        self.root.update()
        self.assertTrue(app.voice.window.winfo_exists())
        self.assertTrue(app.gesture.window.winfo_exists())
        app.voice.say("créer un cercle rouge ici")
        app.transport.send("Palette Point x=150 y=150")
        app.voice.say("valider")
        app.poll()
        obj = app.engine.scene.objects[0]
        self.assertEqual(
            (obj.shape, obj.color, obj.x, obj.y), ("cercle", "rouge", 150, 150)
        )
        app.voice.say("déplacer cet objet")
        app.transport.send("Palette Point x=150 y=150")
        app.voice.say("ici")
        app.transport.send("Palette Point x=300 y=250")
        app.voice.say("valider")
        app.poll()
        self.assertEqual((obj.x, obj.y), (300, 250))
        # Le dessin utilise les callbacks de la nouvelle fenêtre gestuelle.
        points = app.gesture.recognizer.templates["losange"][0]
        app.gesture.begin(SimpleNamespace(x=points[0][0], y=points[0][1]))
        for x, y in points[1:]:
            app.gesture.draw(SimpleNamespace(x=x, y=y))
        app.gesture.end(SimpleNamespace(x=points[-1][0], y=points[-1][1]))
        app.poll()
        self.assertEqual(app.engine.data.shape, "losange")
        self.assertEqual(len(app.palette.canvas.find_all()), 2)
