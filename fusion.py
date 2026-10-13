"""Moteur indépendant de Tk et d'Ivy : horloge injectable, fusion et scène."""
from dataclasses import dataclass, field
from enum import Enum
import re
import time
import unicodedata

SHAPES = {'rectangle', 'cercle', 'triangle', 'losange'}
COLORS = {'rouge', 'vert', 'bleu'}

def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                   if unicodedata.category(c) != 'Mn').strip()

class State(Enum):
    IDLE = 'REPOS'
    COLLECTING = 'COLLECTE'
    WAITING = 'ATTENTE'
    AMBIGUOUS = 'AMBIGUITE'
    EXECUTING = 'EXECUTION'
    ERROR = 'ERREUR'

@dataclass
class Object:
    id: int
    shape: str
    color: str
    x: float
    y: float

    def contains(self, x, y):
        dx, dy = abs(x-self.x), abs(y-self.y)
        if self.shape == 'rectangle': return dx <= 45 and dy <= 30
        if self.shape == 'cercle': return dx*dx+dy*dy <= 35**2
        if self.shape == 'losange': return dx/40+dy/40 <= 1
        # Barycentric test for triangle vertices (0,-40),(-40,35),(40,35).
        return -40 <= y-self.y <= 35 and dx <= (y-self.y+40)*40/75

class Scene:
    def __init__(self):
        self.objects = []
        self.next_id = 1
    def create(self, shape, color='bleu', position=(400,250)):
        obj = Object(self.next_id, shape, color, *position)
        self.next_id += 1
        self.objects.append(obj)
        return obj
    def at(self, point):
        return [o for o in self.objects if o.contains(*point)]
    def select(self, point, shape=None, color=None):
        return [o for o in self.at(point) if (not shape or o.shape == shape)
                and (not color or o.color == color)]

@dataclass
class FusionData:
    action: str | None = None
    shape: str | None = None
    color: str | None = None
    source: tuple | None = None
    target: tuple | None = None
    color_point: tuple | None = None
    references: list = field(default_factory=list) # (role, timestamp)
    points: list = field(default_factory=list)     # (point, timestamp)
    origins: dict = field(default_factory=dict)  # substantive slots only
    last: float | None = None
    def reset(self):
        fresh = FusionData()
        self.__dict__.update(fresh.__dict__)
    def assign(self, key, value, modality):
        old = getattr(self, key)
        if old is not None and old != value:
            raise ValueError(f'Conflit pour {key} : {old} / {value}. Annulez puis recommencez.')
        if old is None:
            setattr(self, key, value)
            self.origins[key] = modality
        elif key in {'action', 'shape'} and modality == 'parole':
            # Une phrase portant toute la commande ne devient pas multimodale
            # par simple répétition d'un geste déjà reçu.
            self.origins[key] = 'parole'
    def modalities(self):
        return set(self.origins.values())

class FusionEngine:
    PAIR_WINDOW = 3.0
    TIMEOUT = 12.0
    MIN_CONFIDENCE = .65
    def __init__(self, scene=None, clock=time.monotonic):
        self.scene = scene if scene is not None else Scene()
        self.clock = clock
        self.data = FusionData()
        self.state = State.IDLE
        self.feedback = 'Prêt. Combinez parole, geste et/ou pointage, puis dites valider.'
        self.history = []
    def status(self, message, state=None):
        self.feedback = message
        if state: self.state = state
        self.history.append((self.clock(), self.state.value, message))
    def reset(self, message='Commande annulée.'):
        self.data.reset()
        self.status(message, State.IDLE)
    def tick(self):
        now = self.clock()
        if self.data.last is not None and now-self.data.last > self.TIMEOUT:
            self.reset('Délai dépassé : commande annulée.')
        # Retire uniquement les clics non liés trop anciens. Une référence déjà
        # résolue reste valable jusqu'à validation ou expiration de session.
        self.data.points[:] = [(p,t) for p,t in self.data.points if now-t <= self.PAIR_WINDOW]
    def touch(self):
        self.tick()
        self.data.last = self.clock()
        if self.state == State.IDLE: self.state = State.COLLECTING
    def gesture(self, name, confidence=1.0):
        name = normalize(name)
        name = {'circle':'cercle','diamond':'losange','move':'deplacer'}.get(name,name)
        if name not in SHAPES | {'deplacer'} or not 0 <= confidence <= 1 or confidence < self.MIN_CONFIDENCE:
            self.status('Geste inconnu ou confiance insuffisante.'); return
        if self.state == State.ERROR:
            self.status('Commande en conflit : dites annuler.', State.ERROR); return
        self.touch()
        try:
            self.data.assign('action' if name == 'deplacer' else 'shape', name, 'geste')
            self.resolve()
            self.status('Geste reçu : '+name, State.COLLECTING)
        except ValueError as e: self.status(str(e), State.ERROR)
    def point(self, x, y):
        if self.state == State.ERROR:
            self.status('Commande en conflit : dites annuler.', State.ERROR); return
        if not (0 <= x <= 800 and 0 <= y <= 500):
            self.status('Point hors de la palette.'); return
        self.touch()
        self.data.points.append(((x,y), self.clock()))
        try:
            self.resolve()
            self.status('Pointage reçu.', State.COLLECTING)
        except ValueError as e: self.status(str(e), State.ERROR)
    def reference(self, role):
        if getattr(self.data, role) is None and not any(r == role for r,t in self.data.references):
            self.data.references.append((role,self.clock()))
    def resolve(self):
        d = self.data
        # FIFO des désignations; clic le plus proche de chaque désignation.
        # Chaque clic est consommé une fois : source != destination par défaut.
        for role, rt in list(d.references):
            candidates = [(abs(t-rt),i,p) for i,(p,t) in enumerate(d.points)
                          if abs(t-rt) <= self.PAIR_WINDOW]
            if candidates:
                _, i, point = min(candidates)
                d.assign(role, point, 'pointage')
                d.points.pop(i)
                d.references.remove((role,rt))
        if d.color_point is not None and d.color is None:
            colors = {o.color for o in self.scene.at(d.color_point)}
            if len(colors) == 1: d.assign('color', colors.pop(), 'pointage')
            elif not colors: raise ValueError('Aucune forme au point de couleur. Annulez puis recommencez.')
            else: self.status('Plusieurs couleurs au point indiqué : dites rouge, vert ou bleu.', State.AMBIGUOUS)
    def speech(self, phrase, confidence=1.0):
        if not 0 <= confidence <= 1 or confidence < self.MIN_CONFIDENCE:
            self.status('Parole ignorée : confiance insuffisante.'); return
        text = normalize(phrase)
        aliases = {'creer':'creer','deplacer':'deplacer','cetobjet':'cet objet',
                   'cettecouleur':'de cette couleur','valider':'valider','annuler':'annuler'}
        text = aliases.get(text,text)
        words = re.findall(r'[a-z]+', text)
        vocabulary = SHAPES | COLORS | {'creer','cree','dessiner','deplacer','deplace',
            'ici','cet','cette','ce','objet','forme','couleur','de','un','une','le','la','a','en',
            'valider','annuler'}
        if not words or any(w not in vocabulary for w in words):
            self.status('Expression inconnue. Consultez le panneau de simulation.'); return
        if text == 'annuler': self.reset(); return
        if text == 'valider': self.validate(); return
        if 'valider' in words or 'annuler' in words:
            self.status('Prononcez valider ou annuler séparément.'); return
        if self.state == State.ERROR:
            self.status('Commande en conflit : dites annuler.', State.ERROR); return
        self.touch()
        try:
            for w in words:
                if w in {'creer','cree','dessiner'}: self.data.assign('action','creer','parole')
                elif w in {'deplacer','deplace'}: self.data.assign('action','deplacer','parole')
                elif w in SHAPES: self.data.assign('shape',w,'parole')
                elif w in COLORS:
                    # En cas de couleur prélevée ambiguë, la parole désambiguïse.
                    self.data.assign('color',w,'parole')
            # Références dans l'ordre de la phrase, pas dans un ordre codé fixe.
            for m in re.finditer(r'de cette couleur|cette couleur|cet objet|ce (?=rectangle|cercle|triangle|losange)|ici',text):
                term=m.group()
                self.reference('color_point' if 'couleur' in term else 'target' if term=='ici' else 'source')
            self.resolve()
            if self.state not in {State.ERROR,State.AMBIGUOUS}:
                self.status('Parole reçue. Complétez puis dites valider.',State.COLLECTING)
        except ValueError as e: self.status(str(e), State.ERROR)
    def validate(self):
        self.tick()
        d = self.data
        if self.state == State.ERROR:
            self.status('Commande en conflit : dites annuler.', State.ERROR); return None
        missing=[]
        if not d.action: missing.append('action')
        if d.action == 'creer' and not d.shape: missing.append('forme')
        if d.action == 'deplacer':
            if d.source is None: missing.append('objet source (cet objet + clic)')
            if d.target is None: missing.append('destination (ici + clic)')
        if d.references: missing.append('clic associé à '+', '.join(r for r,t in d.references))
        if d.color_point is not None and d.color is None: missing.append('couleur à désambiguïser')
        if len(d.modalities()) < 2: missing.append('seconde modalité apportant une information')
        if missing:
            self.status('Il manque : '+'; '.join(missing)+'.',State.WAITING); return None
        self.status('Exécution.', State.EXECUTING)
        if d.action == 'creer':
            obj=self.scene.create(d.shape,d.color or 'bleu',d.target or (400,250))
            message=f'{obj.shape} {obj.color} créé (objet {obj.id}).'
        else:
            candidates=self.scene.select(d.source,d.shape,d.color)
            if len(candidates)!=1:
                self.status('Aucun objet correspondant.' if not candidates else
                            'Plusieurs objets : précisez forme/couleur ou annulez et pointez une zone exclusive.',
                            State.AMBIGUOUS)
                return None
            obj=candidates[0]
            obj.x,obj.y=d.target
            message=f'Objet {obj.id} déplacé.'
        self.reset(message)
        return obj

SRA = re.compile(r"^sra5 Parsed='([^']*)' Confidence='?([0-9]+(?:[.,][0-9]+)?)'? NP='?\d+'? Num_A='?\d+'?$",re.I)
GESTURE = re.compile(r'^OneDollarIvy Template=(\S+) Confidence=([0-9]+(?:[.,][0-9]+)?)$',re.I)
POINT = re.compile(r'^Palette Point x=(\d+(?:\.\d+)?) y=(\d+(?:\.\d+)?)$')
TEXT = re.compile(r"^sra5 Text=(.*?) Confidence='?([0-9]+(?:[.,][0-9]+)?)'?$",re.I)

def dispatch(engine, message):
    m=SRA.fullmatch(message) or TEXT.fullmatch(message)
    if m: engine.speech(m[1].strip("'"),float(m[2].replace(',','.'))); return True
    m=GESTURE.fullmatch(message)
    if m: engine.gesture(m[1],float(m[2].replace(',','.'))); return True
    m=POINT.fullmatch(message)
    if m: engine.point(float(m[1]),float(m[2])); return True
    return False
