"""Assemblage des composants et traitement de la file dans le thread Tk."""

import queue
from .controleur import ControleurDialogue
from .communication_ivy import CommunicationIvy, dispatch
from palette.interface import PaletteDessin
from simulateur_vocal.interface import SimulateurVocal
from reconnaissance_gestuelle.interface import FenetreGestes


class Application:
    def __init__(self, root, bus=None):
        self.root = root
        self.root.title("Palette de dessin - Lab 3-5")
        self.root.resizable(False, False)
        self.engine = ControleurDialogue()
        self.inbox = queue.Queue()
        self.transport = CommunicationIvy(self.inbox, bus)
        self.palette = PaletteDessin(root, self.transport.send)
        self.voice = SimulateurVocal(root, self.transport.send, self.close)
        self.gesture = FenetreGestes(root, self.transport.send, self.close)
        self.last_feedback = None
        self.closed = False
        self.after_id = root.after(50, self.poll)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def poll(self):
        if self.closed:
            return
        try:
            while True:
                message = self.inbox.get_nowait()
                dispatch(self.engine, message)
                self.voice.log_message(message)
        except queue.Empty:
            pass
        self.engine.tick()
        self.palette.render(self.engine.scene, self.engine.data)
        feedback = self.engine.feedback
        self.palette.status.set(f"{self.engine.state.value} | {feedback}")
        if feedback != self.last_feedback:
            self.transport.feedback(feedback)
            self.last_feedback = feedback
        self.after_id = self.root.after(50, self.poll)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.root.after_cancel(self.after_id)
        self.transport.close()
        self.root.destroy()
