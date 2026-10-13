"""Vocabulaire et normalisation partagés entre les modalités."""

import unicodedata

SHAPES = {"rectangle", "cercle", "triangle", "losange"}
COLORS = {"rouge", "vert", "bleu"}


def normalize(text):
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    ).strip()
