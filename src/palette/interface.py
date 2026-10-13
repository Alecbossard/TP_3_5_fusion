"""Palette Tkinter sans boutons; affichage et émission des pointages."""

import tkinter as tk
from tkinter import ttk


class PaletteDessin:
    def __init__(self, root, send):
        self.canvas = tk.Canvas(
            root, width=800, height=500, bg="#f8fafc", highlightthickness=0
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", lambda e: send(f"Palette Point x={e.x} y={e.y}"))
        self.status = tk.StringVar()
        ttk.Label(root, textvariable=self.status, wraplength=790, padding=10).pack(
            fill="x"
        )

    def render(self, scene, contexte):
        self.canvas.delete("all")
        colors = {"rouge": "#e45656", "vert": "#39a875", "bleu": "#4385d5"}
        for o in scene.objects:
            x, y = o.x, o.y
            kw = dict(fill=colors[o.color], outline="#23354a", width=2)
            if o.shape == "rectangle":
                self.canvas.create_rectangle(x - 45, y - 30, x + 45, y + 30, **kw)
            elif o.shape == "cercle":
                self.canvas.create_oval(x - 35, y - 35, x + 35, y + 35, **kw)
            elif o.shape == "triangle":
                self.canvas.create_polygon(
                    x, y - 40, x - 40, y + 35, x + 40, y + 35, **kw
                )
            else:
                self.canvas.create_polygon(
                    x, y - 40, x + 40, y, x, y + 40, x - 40, y, **kw
                )
            self.canvas.create_text(
                x, y, text=str(o.id), fill="white", font=("Arial", 12, "bold")
            )
        d = contexte
        for point, color, label in [
            (d.source, "#f59e0b", "source"),
            (d.target, "#8b5cf6", "ici"),
            (d.color_point, "#10b981", "couleur"),
        ]:
            if point:
                x, y = point
                self.canvas.create_oval(
                    x - 6, y - 6, x + 6, y + 6, outline=color, width=2
                )
                self.canvas.create_text(x, y + 15, text=label, fill=color)
