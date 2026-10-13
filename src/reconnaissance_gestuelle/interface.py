"""Fenêtre de reconnaissance et d'apprentissage des tracés."""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from moteur_fusion.vocabulaire import SHAPES
from .reconnaisseur import Recognizer

TEMPLATES_PATH = Path(__file__).parent / "templates" / "gestures.json"


class FenetreGestes:
    def __init__(self, root, send, close):
        self.send = send
        self.trace = []
        self.recognizer = Recognizer(TEMPLATES_PATH)
        self.window = tk.Toplevel(root)
        self.window.title("Gestes - reconnaissance et apprentissage")
        ttk.Label(
            self.window,
            text="Dessinez un contour fermé ou une flèche vers la droite.\nPour apprendre : choisir un nom, cocher Apprendre et tracer.",
            padding=10,
        ).pack()
        self.learn = tk.BooleanVar()
        self.name = tk.StringVar(value="rectangle")
        bar = ttk.Frame(self.window)
        bar.pack()
        ttk.Combobox(
            bar,
            textvariable=self.name,
            values=sorted(SHAPES | {"deplacer"}),
            state="readonly",
        ).pack(side="left")
        ttk.Checkbutton(bar, text="Apprendre", variable=self.learn).pack(side="left")
        self.gcanvas = tk.Canvas(self.window, width=400, height=280, bg="white")
        self.gcanvas.pack(padx=10, pady=10)
        self.gcanvas.bind("<Button-1>", self.begin)
        self.gcanvas.bind("<B1-Motion>", self.draw)
        self.gcanvas.bind("<ButtonRelease-1>", self.end)
        self.gstatus = tk.StringVar(
            value="Modèles géométriques initiaux; ajoutez vos tracés personnels."
        )
        ttk.Label(
            self.window, textvariable=self.gstatus, wraplength=390, padding=10
        ).pack()
        self.window.protocol("WM_DELETE_WINDOW", close)

    def begin(self, e):
        self.gcanvas.delete("all")
        self.trace = [(e.x, e.y)]

    def draw(self, e):
        self.gcanvas.create_line(*self.trace[-1], e.x, e.y, fill="#365b73", width=3)
        self.trace.append((e.x, e.y))

    def end(self, e):
        self.trace.append((e.x, e.y))
        try:
            if self.learn.get():
                self.recognizer.learn(self.name.get(), self.trace)
                self.gstatus.set("Modèle enregistré : " + self.name.get())
                return
            score, name = self.recognizer.recognize(self.trace)
            self.gstatus.set(f"{name} : {score:.2f}")
            self.send(f"OneDollarIvy Template={name} Confidence={score:.3f}")
        except ValueError as exc:
            self.gstatus.set(str(exc))
