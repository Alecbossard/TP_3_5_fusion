"""Trois fenêtres : palette, simulateur vocal et recognizer entraînable."""
import argparse
import queue
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from fusion import FusionEngine, dispatch, SHAPES
from recognizer import Recognizer

class Transport:
    def __init__(self, inbox, bus=None):
        self.inbox=inbox; self.server=None; self.output=None
        if bus:
            from ivy.ivy import IvyServer
            self.server=IvyServer('FusionLab35')
            self.output=IvyServer('PaletteSimulateursLab35')
            self.server.bind_msg(lambda agent,msg: inbox.put(msg),r'^(sra5 (?:Parsed|Text)=.*|OneDollarIvy Template=.*|Palette Point .*)$')
            self.server.start(bus)
            self.output.start(bus)
    def send(self,message):
        if self.output: self.output.send_msg(message)
        else: self.inbox.put(message)
    def feedback(self,message):
        if self.server: self.server.send_msg('ppilot5 Say='+message)
    def close(self):
        for server in (self.output,self.server):
            if server: server.stop()

class App:
    def __init__(self,root,bus=None):
        self.root=root; self.root.title('Palette de dessin - Lab 3-5')
        self.root.resizable(False,False)
        self.engine=FusionEngine(); self.inbox=queue.Queue()
        self.transport=Transport(self.inbox,bus)
        self.recognizer=Recognizer(Path(__file__).parent/'templates'/'gestures.json')
        self.last_feedback=None; self.trace=[]; self.np=0
        self.canvas=tk.Canvas(root,width=800,height=500,bg='#f8fafc',highlightthickness=0)
        self.canvas.pack(); self.canvas.bind('<Button-1>',self.click)
        self.status=tk.StringVar(); ttk.Label(root,textvariable=self.status,wraplength=790,padding=10).pack(fill='x')
        voice=tk.Toplevel(root); voice.title('Simulation de parole (remplaçable par sra5)')
        ttk.Label(voice,text='Écrivez une phrase ou cliquez sur une expression.\nCes boutons simulent la parole; la palette n’a aucun bouton.',padding=10).pack()
        self.phrase=tk.StringVar(value='créer')
        ttk.Entry(voice,textvariable=self.phrase,width=65).pack(padx=10,pady=5)
        ttk.Button(voice,text='Envoyer la phrase',command=lambda:self.say(self.phrase.get())).pack(pady=5)
        panel=ttk.Frame(voice); panel.pack(padx=10,pady=10)
        phrases=['créer','déplacer','cet objet','ici','de cette couleur','rouge','vert','bleu',
                 'rectangle','cercle','triangle','losange','valider','annuler']
        for i,p in enumerate(phrases): ttk.Button(panel,text=p,command=lambda p=p:self.say(p)).grid(row=i//4,column=i%4,padx=3,pady=3,sticky='ew')
        gesture=tk.Toplevel(root); gesture.title('Gestes - reconnaissance et apprentissage')
        ttk.Label(gesture,text='Dessinez un contour fermé ou une flèche vers la droite.\nPour apprendre : choisir un nom, cocher Apprendre et tracer.',padding=10).pack()
        self.learn=tk.BooleanVar(); self.name=tk.StringVar(value='rectangle')
        bar=ttk.Frame(gesture); bar.pack()
        ttk.Combobox(bar,textvariable=self.name,values=sorted(SHAPES|{'deplacer'}),state='readonly').pack(side='left')
        ttk.Checkbutton(bar,text='Apprendre',variable=self.learn).pack(side='left')
        self.gcanvas=tk.Canvas(gesture,width=400,height=280,bg='white'); self.gcanvas.pack(padx=10,pady=10)
        self.gcanvas.bind('<Button-1>',self.begin); self.gcanvas.bind('<B1-Motion>',self.draw)
        self.gcanvas.bind('<ButtonRelease-1>',self.end)
        self.gstatus=tk.StringVar(value='Modèles géométriques initiaux; ajoutez vos tracés personnels.')
        ttk.Label(gesture,textvariable=self.gstatus,wraplength=390,padding=10).pack()
        self.log=tk.Text(voice,width=70,height=10,state='disabled'); self.log.pack(padx=10,pady=10)
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        # Fermer une fenêtre auxiliaire quitte proprement l'ensemble.
        voice.protocol('WM_DELETE_WINDOW',self.close); gesture.protocol('WM_DELETE_WINDOW',self.close)
        root.after(50,self.poll)
    def say(self,phrase):
        if "'" in phrase or '\n' in phrase: return
        self.np+=1
        self.transport.send(f"sra5 Parsed='{phrase}' Confidence=1 NP={self.np} Num_A=0")
    def click(self,e): self.transport.send(f'Palette Point x={e.x} y={e.y}')
    def begin(self,e):
        self.gcanvas.delete('all'); self.trace=[(e.x,e.y)]
    def draw(self,e):
        self.gcanvas.create_line(*self.trace[-1],e.x,e.y,fill='#365b73',width=3)
        self.trace.append((e.x,e.y))
    def end(self,e):
        self.trace.append((e.x,e.y))
        try:
            if self.learn.get():
                self.recognizer.learn(self.name.get(),self.trace)
                self.gstatus.set('Modèle enregistré : '+self.name.get()); return
            score,name=self.recognizer.recognize(self.trace)
            self.gstatus.set(f'{name} : {score:.2f}')
            self.transport.send(f'OneDollarIvy Template={name} Confidence={score:.3f}')
        except ValueError as exc: self.gstatus.set(str(exc))
    def render(self):
        self.canvas.delete('all')
        colors={'rouge':'#e45656','vert':'#39a875','bleu':'#4385d5'}
        for o in self.engine.scene.objects:
            x,y=o.x,o.y; kw=dict(fill=colors[o.color],outline='#23354a',width=2)
            if o.shape=='rectangle': self.canvas.create_rectangle(x-45,y-30,x+45,y+30,**kw)
            elif o.shape=='cercle': self.canvas.create_oval(x-35,y-35,x+35,y+35,**kw)
            elif o.shape=='triangle': self.canvas.create_polygon(x,y-40,x-40,y+35,x+40,y+35,**kw)
            else: self.canvas.create_polygon(x,y-40,x+40,y,x,y+40,x-40,y,**kw)
            self.canvas.create_text(x,y,text=str(o.id),fill='white',font=('Arial',12,'bold'))
        d=self.engine.data
        for point,color,label in [(d.source,'#f59e0b','source'),(d.target,'#8b5cf6','ici'),(d.color_point,'#10b981','couleur')]:
            if point:
                x,y=point; self.canvas.create_oval(x-6,y-6,x+6,y+6,outline=color,width=2)
                self.canvas.create_text(x,y+15,text=label,fill=color)
    def poll(self):
        try:
            while True:
                message=self.inbox.get_nowait()
                dispatch(self.engine,message)
                self.log.configure(state='normal'); self.log.insert('end',message+'\n'); self.log.see('end'); self.log.configure(state='disabled')
        except queue.Empty: pass
        self.engine.tick(); self.render()
        feedback=self.engine.feedback
        self.status.set(f'{self.engine.state.value} | {feedback}')
        if feedback!=self.last_feedback:
            self.transport.feedback(feedback); self.last_feedback=feedback
        self.root.after(50,self.poll)
    def close(self): self.transport.close(); self.root.destroy()

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--ivy',action='store_true')
    parser.add_argument('--bus',default='127.255.255.255:2010'); args=parser.parse_args()
    root=tk.Tk()
    try: App(root,args.bus if args.ivy else None)
    except ImportError:
        root.destroy(); raise SystemExit('Installez ivy-python : python -m pip install -r requirements.txt')
    root.mainloop()
if __name__=='__main__': main()
