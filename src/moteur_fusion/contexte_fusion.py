"""Informations temporaires de la commande multimodale en cours."""

from dataclasses import dataclass, field


@dataclass
class ContexteFusion:
    action: str | None = None
    shape: str | None = None
    color: str | None = None
    source: tuple | None = None
    target: tuple | None = None
    color_point: tuple | None = None
    references: list = field(default_factory=list)  # (role, timestamp)
    points: list = field(default_factory=list)  # (point, timestamp)
    origins: dict = field(default_factory=dict)  # substantive slots only
    last: float | None = None

    def reset(self):
        fresh = ContexteFusion()
        self.__dict__.update(fresh.__dict__)

    def assign(self, key, value, modality):
        old = getattr(self, key)
        if old is not None and old != value:
            raise ValueError(
                f"Conflit pour {key} : {old} / {value}. Annulez puis recommencez."
            )
        if old is None:
            setattr(self, key, value)
            self.origins[key] = modality
        elif key in {"action", "shape"} and modality == "parole":
            # Une phrase portant toute la commande ne devient pas multimodale
            # par simple répétition d'un geste déjà reçu.
            self.origins[key] = "parole"

    def modalities(self):
        return set(self.origins.values())
