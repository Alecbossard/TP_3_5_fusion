"""Modèle de la palette et sélection géométrique des objets."""

from dataclasses import dataclass


@dataclass
class Object:
    id: int
    shape: str
    color: str
    x: float
    y: float

    def contains(self, x, y):
        dx, dy = abs(x - self.x), abs(y - self.y)
        if self.shape == "rectangle":
            return dx <= 45 and dy <= 30
        if self.shape == "cercle":
            return dx * dx + dy * dy <= 35**2
        if self.shape == "losange":
            return dx / 40 + dy / 40 <= 1
        # Barycentric test for triangle vertices (0,-40),(-40,35),(40,35).
        return -40 <= y - self.y <= 35 and dx <= (y - self.y + 40) * 40 / 75


class Scene:
    def __init__(self):
        self.objects = []
        self.next_id = 1

    def create(self, shape, color="bleu", position=(400, 250)):
        obj = Object(self.next_id, shape, color, *position)
        self.next_id += 1
        self.objects.append(obj)
        return obj

    def at(self, point):
        return [o for o in self.objects if o.contains(*point)]

    def select(self, point, shape=None, color=None):
        return [
            o
            for o in self.at(point)
            if (not shape or o.shape == shape) and (not color or o.color == color)
        ]
