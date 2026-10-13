"""Automate et règles de fusion, indépendants de Tkinter et Ivy."""

import re
import time

from .contexte_fusion import ContexteFusion
from .etats import EtatDialogue
from .scene import Scene
from .vocabulaire import SHAPES, COLORS, normalize


class ControleurDialogue:
    PAIR_WINDOW = 3.0
    TIMEOUT = 12.0
    MIN_CONFIDENCE = 0.65

    def __init__(self, scene=None, clock=time.monotonic):
        self.scene = scene if scene is not None else Scene()
        self.clock = clock
        self.data = ContexteFusion()
        self.state = EtatDialogue.IDLE
        self.feedback = (
            "Prêt. Combinez parole, geste et/ou pointage, puis dites valider."
        )
        self.history = []

    def status(self, message, state=None):
        self.feedback = message
        if state:
            self.state = state
        self.history.append((self.clock(), self.state.value, message))

    def reset(self, message="Commande annulée."):
        self.data.reset()
        self.status(message, EtatDialogue.IDLE)

    def tick(self):
        now = self.clock()
        if self.data.last is not None and now - self.data.last > self.TIMEOUT:
            self.reset("Délai dépassé : commande annulée.")
        # Retire uniquement les clics non liés trop anciens. Une référence déjà
        # résolue reste valable jusqu'à validation ou expiration de session.
        self.data.points[:] = [
            (p, t) for p, t in self.data.points if now - t <= self.PAIR_WINDOW
        ]

    def touch(self):
        self.tick()
        self.data.last = self.clock()
        if self.state == EtatDialogue.IDLE:
            self.state = EtatDialogue.COLLECTING

    def gesture(self, name, confidence=1.0):
        name = normalize(name)
        name = {"circle": "cercle", "diamond": "losange", "move": "deplacer"}.get(
            name, name
        )
        if (
            name not in SHAPES | {"deplacer"}
            or not 0 <= confidence <= 1
            or confidence < self.MIN_CONFIDENCE
        ):
            self.status("Geste inconnu ou confiance insuffisante.")
            return
        if self.state == EtatDialogue.ERROR:
            self.status("Commande en conflit : dites annuler.", EtatDialogue.ERROR)
            return
        self.touch()
        try:
            self.data.assign("action" if name == "deplacer" else "shape", name, "geste")
            self.resolve()
            self.status("Geste reçu : " + name, EtatDialogue.COLLECTING)
        except ValueError as e:
            self.status(str(e), EtatDialogue.ERROR)

    def point(self, x, y):
        if self.state == EtatDialogue.ERROR:
            self.status("Commande en conflit : dites annuler.", EtatDialogue.ERROR)
            return
        if not (0 <= x <= 800 and 0 <= y <= 500):
            self.status("Point hors de la palette.")
            return
        self.touch()
        self.data.points.append(((x, y), self.clock()))
        try:
            self.resolve()
            self.status("Pointage reçu.", EtatDialogue.COLLECTING)
        except ValueError as e:
            self.status(str(e), EtatDialogue.ERROR)

    def reference(self, role):
        if getattr(self.data, role) is None and not any(
            r == role for r, t in self.data.references
        ):
            self.data.references.append((role, self.clock()))

    def resolve(self):
        d = self.data
        # FIFO des désignations; clic le plus proche de chaque désignation.
        # Chaque clic est consommé une fois : source != destination par défaut.
        for role, rt in list(d.references):
            candidates = [
                (abs(t - rt), i, p)
                for i, (p, t) in enumerate(d.points)
                if abs(t - rt) <= self.PAIR_WINDOW
            ]
            if candidates:
                _, i, point = min(candidates)
                d.assign(role, point, "pointage")
                d.points.pop(i)
                d.references.remove((role, rt))
        if d.color_point is not None and d.color is None:
            colors = {o.color for o in self.scene.at(d.color_point)}
            if len(colors) == 1:
                d.assign("color", colors.pop(), "pointage")
            elif not colors:
                raise ValueError(
                    "Aucune forme au point de couleur. Annulez puis recommencez."
                )
            else:
                self.status(
                    "Plusieurs couleurs au point indiqué : dites rouge, vert ou bleu.",
                    EtatDialogue.AMBIGUOUS,
                )

    def speech(self, phrase, confidence=1.0):
        if not 0 <= confidence <= 1 or confidence < self.MIN_CONFIDENCE:
            self.status("Parole ignorée : confiance insuffisante.")
            return
        text = normalize(phrase)
        aliases = {
            "creer": "creer",
            "deplacer": "deplacer",
            "cetobjet": "cet objet",
            "cettecouleur": "de cette couleur",
            "valider": "valider",
            "annuler": "annuler",
        }
        text = aliases.get(text, text)
        words = re.findall(r"[a-z]+", text)
        vocabulary = (
            SHAPES
            | COLORS
            | {
                "creer",
                "cree",
                "dessiner",
                "deplacer",
                "deplace",
                "ici",
                "cet",
                "cette",
                "ce",
                "objet",
                "forme",
                "couleur",
                "de",
                "un",
                "une",
                "le",
                "la",
                "a",
                "en",
                "valider",
                "annuler",
            }
        )
        if not words or any(w not in vocabulary for w in words):
            self.status("Expression inconnue. Consultez le panneau de simulation.")
            return
        if text == "annuler":
            self.reset()
            return
        if text == "valider":
            self.validate()
            return
        if "valider" in words or "annuler" in words:
            self.status("Prononcez valider ou annuler séparément.")
            return
        if self.state == EtatDialogue.ERROR:
            self.status("Commande en conflit : dites annuler.", EtatDialogue.ERROR)
            return
        self.touch()
        try:
            for w in words:
                if w in {"creer", "cree", "dessiner"}:
                    self.data.assign("action", "creer", "parole")
                elif w in {"deplacer", "deplace"}:
                    self.data.assign("action", "deplacer", "parole")
                elif w in SHAPES:
                    self.data.assign("shape", w, "parole")
                elif w in COLORS:
                    # En cas de couleur prélevée ambiguë, la parole désambiguïse.
                    self.data.assign("color", w, "parole")
            # Références dans l'ordre de la phrase, pas dans un ordre codé fixe.
            for m in re.finditer(
                r"de cette couleur|cette couleur|cet objet|ce (?=rectangle|cercle|triangle|losange)|ici",
                text,
            ):
                term = m.group()
                self.reference(
                    "color_point"
                    if "couleur" in term
                    else "target" if term == "ici" else "source"
                )
            self.resolve()
            if self.state not in {EtatDialogue.ERROR, EtatDialogue.AMBIGUOUS}:
                self.status(
                    "Parole reçue. Complétez puis dites valider.",
                    EtatDialogue.COLLECTING,
                )
        except ValueError as e:
            self.status(str(e), EtatDialogue.ERROR)

    def validate(self):
        self.tick()
        d = self.data
        if self.state == EtatDialogue.ERROR:
            self.status("Commande en conflit : dites annuler.", EtatDialogue.ERROR)
            return None
        missing = []
        if not d.action:
            missing.append("action")
        if d.action == "creer" and not d.shape:
            missing.append("forme")
        if d.action == "deplacer":
            if d.source is None:
                missing.append("objet source (cet objet + clic)")
            if d.target is None:
                missing.append("destination (ici + clic)")
        if d.references:
            missing.append("clic associé à " + ", ".join(r for r, t in d.references))
        if d.color_point is not None and d.color is None:
            missing.append("couleur à désambiguïser")
        if len(d.modalities()) < 2:
            missing.append("seconde modalité apportant une information")
        if missing:
            self.status("Il manque : " + "; ".join(missing) + ".", EtatDialogue.WAITING)
            return None
        self.status("Exécution.", EtatDialogue.EXECUTING)
        if d.action == "creer":
            obj = self.scene.create(d.shape, d.color or "bleu", d.target or (400, 250))
            message = f"{obj.shape} {obj.color} créé (objet {obj.id})."
        else:
            candidates = self.scene.select(d.source, d.shape, d.color)
            if len(candidates) != 1:
                self.status(
                    (
                        "Aucun objet correspondant."
                        if not candidates
                        else "Plusieurs objets : précisez forme/couleur ou annulez et pointez une zone exclusive."
                    ),
                    EtatDialogue.AMBIGUOUS,
                )
                return None
            obj = candidates[0]
            obj.x, obj.y = d.target
            message = f"Objet {obj.id} déplacé."
        self.reset(message)
        return obj
