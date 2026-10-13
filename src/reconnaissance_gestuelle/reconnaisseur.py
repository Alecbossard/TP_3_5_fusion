"""Reconnaissance par 64 points rééchantillonnés, inspirée de $1.
Orientation préservée pour distinguer rectangle et losange. Ni rotation
optimisée ni normalisation à l'angle indicatif : ce n'est pas le $1 canonique.
"""

import json
import math
from pathlib import Path


def sample(points, n=64):
    if len(points) < 2:
        raise ValueError("Trace trop courte")
    lengths = [0.0]
    for a, b in zip(points, points[1:]):
        lengths.append(lengths[-1] + math.dist(a, b))
    if lengths[-1] < 10:
        raise ValueError("Trace trop courte")
    result = []
    j = 1
    for k in range(n):
        target = lengths[-1] * k / (n - 1)
        while j < len(lengths) - 1 and lengths[j] < target:
            j += 1
        ratio = (
            (target - lengths[j - 1]) / (lengths[j] - lengths[j - 1])
            if lengths[j] > lengths[j - 1]
            else 0
        )
        a, b = points[j - 1], points[j]
        result.append((a[0] + ratio * (b[0] - a[0]), a[1] + ratio * (b[1] - a[1])))
    lo = [min(p[d] for p in result) for d in (0, 1)]
    scale = max(max(p[d] for p in result) - lo[d] for d in (0, 1))
    mean = [sum(p[d] for p in result) / n for d in (0, 1)]
    return [((x - mean[0]) / scale, (y - mean[1]) / scale) for x, y in result]


class Recognizer:
    def __init__(self, path):
        self.path = Path(path)
        self.templates = json.loads(self.path.read_text(encoding="utf-8"))

    def learn(self, name, points):
        sample(points)
        self.templates.setdefault(name, []).append(points)
        self.path.write_text(
            json.dumps(self.templates, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def recognize(self, points):
        trace = sample(points)
        ranked = []
        for name, templates in self.templates.items():
            best = math.inf
            for raw in templates:
                template = sample(raw)
                # Permet les deux sens et les points de départ différents des
                # contours fermés; une flèche de déplacement reste directionnelle.
                variants = [template, template[::-1]]
                if name != "deplacer":
                    variants = [v[i:] + v[:i] for v in variants for i in range(64)]
                best = min(
                    best,
                    min(
                        sum(math.dist(a, b) for a, b in zip(trace, v)) / 64
                        for v in variants
                    ),
                )
            ranked.append((max(0, 1 - best / 0.7071), name))
        return max(ranked)
