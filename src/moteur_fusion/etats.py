"""États du contrôleur de dialogue."""

from enum import Enum


class EtatDialogue(Enum):
    IDLE = "REPOS"
    COLLECTING = "COLLECTE"
    WAITING = "ATTENTE"
    AMBIGUOUS = "AMBIGUITE"
    EXECUTING = "EXECUTION"
    ERROR = "ERREUR"
