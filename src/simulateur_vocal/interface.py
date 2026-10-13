"""Simulateur vocal substituable à sra5 grâce au même protocole."""

import tkinter as tk
from tkinter import ttk


class SimulateurVocal:
    def __init__(self, root, send, close):
        self.send = send
        self.np = 0
        self.window = tk.Toplevel(root)
        self.window.title("Simulation de parole (remplaçable par sra5)")
        ttk.Label(
            self.window,
            text="Écrivez une phrase ou cliquez sur une expression.\nCes boutons simulent la parole; la palette n’a aucun bouton.",
            padding=10,
        ).pack()
        self.phrase = tk.StringVar(value="créer")
        ttk.Entry(self.window, textvariable=self.phrase, width=65).pack(padx=10, pady=5)
        ttk.Button(
            self.window,
            text="Envoyer la phrase",
            command=lambda: self.say(self.phrase.get()),
        ).pack(pady=5)
        panel = ttk.Frame(self.window)
        panel.pack(padx=10, pady=10)
        phrases = [
            "créer",
            "déplacer",
            "cet objet",
            "ici",
            "de cette couleur",
            "rouge",
            "vert",
            "bleu",
            "rectangle",
            "cercle",
            "triangle",
            "losange",
            "valider",
            "annuler",
        ]
        for i, p in enumerate(phrases):
            ttk.Button(panel, text=p, command=lambda p=p: self.say(p)).grid(
                row=i // 4, column=i % 4, padx=3, pady=3, sticky="ew"
            )
        self.log = tk.Text(self.window, width=70, height=10, state="disabled")
        self.log.pack(padx=10, pady=10)
        self.window.protocol("WM_DELETE_WINDOW", close)

    def say(self, phrase):
        if "'" in phrase or "\n" in phrase:
            return
        self.np += 1
        self.send(f"sra5 Parsed='{phrase}' Confidence=1 NP={self.np} Num_A=0")

    def log_message(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
