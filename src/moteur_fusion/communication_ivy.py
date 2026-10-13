"""Transport local/Ivy et décodage des messages des agents."""

import re


class CommunicationIvy:
    def __init__(self, inbox, bus=None):
        self.inbox = inbox
        self.server = None
        self.output = None
        if bus:
            from ivy.ivy import IvyServer

            self.server = IvyServer("FusionLab35")
            self.output = IvyServer("PaletteSimulateursLab35")
            self.server.bind_msg(
                lambda agent, msg: inbox.put(msg),
                r"^(sra5 (?:Parsed|Text)=.*|OneDollarIvy Template=.*|Palette Point .*)$",
            )
            self.server.start(bus)
            self.output.start(bus)

    def send(self, message):
        if self.output:
            self.output.send_msg(message)
        else:
            self.inbox.put(message)

    def feedback(self, message):
        if self.server:
            self.server.send_msg("ppilot5 Say=" + message)

    def close(self):
        for server in (self.output, self.server):
            if server:
                server.stop()


SRA = re.compile(
    r"^sra5 Parsed='([^']*)' Confidence='?([0-9]+(?:[.,][0-9]+)?)'? NP='?\d+'? Num_A='?\d+'?$",
    re.I,
)
GESTURE = re.compile(
    r"^OneDollarIvy Template=(\S+) Confidence=([0-9]+(?:[.,][0-9]+)?)$", re.I
)
POINT = re.compile(r"^Palette Point x=(\d+(?:\.\d+)?) y=(\d+(?:\.\d+)?)$")
TEXT = re.compile(r"^sra5 Text=(.*?) Confidence='?([0-9]+(?:[.,][0-9]+)?)'?$", re.I)


def dispatch(engine, message):
    m = SRA.fullmatch(message) or TEXT.fullmatch(message)
    if m:
        engine.speech(m[1].strip("'"), float(m[2].replace(",", ".")))
        return True
    m = GESTURE.fullmatch(message)
    if m:
        engine.gesture(m[1], float(m[2].replace(",", ".")))
        return True
    m = POINT.fullmatch(message)
    if m:
        engine.point(float(m[1]), float(m[2]))
        return True
    return False
