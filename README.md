# Lab 3-5 - Moteur de fusion multimodale

Solution Python des trois séances : conception, structure de fusion, moteur,
interface testable, grammaire vocale, gestes entraînables et rapport.
Source du sujet : https://github.com/truillet/upssitech/blob/master/SRI/5A/IHM/TP/lab3-5_fusion.md
Les illustrations du sujet sont deux JPG et un PNG. Le sujet en ligne porte
encore une échéance de décembre 2025 : confirmer l'échéance actuelle en cours.

## Démarrer en simulation (sans microphone ni Processing)

Python 3.10 ou supérieur, avec Tkinter. Sous Ubuntu :

```sh
sudo apt install python3-tk
python3 app.py
```

Sous Windows, installer Python avec Tcl/Tk puis lancer `start.bat`.
Sous Linux/macOS : `./start.sh` (ou `python3 app.py`).
Trois fenêtres s'ouvrent : palette sans boutons, simulateur vocal, gestes.
Les boutons du simulateur produisent des événements **parole**, pas des clics
sur la palette. Le dessin dans la fenêtre des gestes produit un événement
**geste**. Seuls les clics dans la palette produisent un **pointage**.

### Exemple 1 : création sans couleur/position explicites

1. Envoyer « créer » dans le simulateur vocal.
2. Dessiner un rectangle fermé dans la fenêtre des gestes.
3. Envoyer « valider ». Un rectangle bleu apparaît au centre (400, 250).

Une reconnaissance de geste inférieure à 0,65 est ignorée : recommencer ou
apprendre un tracé personnel. Les modèles fournis sont **géométriques**, pas
un apprentissage effectué auprès d'utilisateurs.

### Exemple 2 : couleur et position

1. Envoyer « créer un cercle rouge ici ».
2. Dans les trois secondes, cliquer vers (180, 180) sur la palette.
3. Envoyer « valider ». Le cercle apparaît au point indiqué.

Le clic peut précéder « ici » de trois secondes au maximum. Un clic ne sert
qu'à une seule désignation. Les coordonnées sont les centres des objets.
Les formes peuvent dépasser le bord lorsque leur centre est proche d'un bord.

### Exemple 3 : couleur prélevée sur un objet

Après avoir créé le cercle rouge de l'exemple 2 :

1. Envoyer « créer un triangle de cette couleur » et cliquer sur le cercle.
2. Envoyer « ici » et cliquer ailleurs.
3. Envoyer « valider ». Le triangle prend la couleur rouge.

La variante « créer un triangle ici de cette couleur » fonctionne : le premier
clic est alors la destination, le deuxième la source de couleur. Prononcer et
pointer chaque référence successivement est préférable. Si deux références
sont prononcées ensemble, les clics suivants les résolvent dans cet ordre.

### Exemple 4 : déplacer, par la voix ou par le geste

1. Envoyer « déplacer cet objet », puis cliquer sur le cercle rouge.
2. Envoyer « ici », puis cliquer vers (500, 300).
3. Envoyer « valider ».

Variante : tracer la flèche de déplacement dans la fenêtre des gestes, puis
prononcer « cet objet » et cliquer sur la source, puis « ici » et cliquer sur
la destination. La flèche initiale est un trait horizontal vers la droite
suivi d'une pointe : aller de gauche à droite, remonter en haut à gauche de
la pointe, revenir à droite, finir en bas à gauche de la pointe.

En cas de superposition : « déplacer ce rectangle rouge » + clic source,
« ici » + clic destination, puis « valider ». S'il reste plusieurs objets
identiques, annuler et pointer une partie exclusive. Aucun choix arbitraire.

### Annulation et délais

« annuler » efface les informations de la commande, pas les objets créés.
Douze secondes d'inactivité annulent la commande. Une désignation et son clic
sont associés si leur écart est inférieur ou égal à trois secondes.
Si ce délai est dépassé, annuler et recommencer la désignation.
Les valeurs 3 s, 12 s et 0,65 sont des choix de conception à calibrer en test
utilisateur, pas des mesures empiriques. Aucun objet n'est créé/déplacé sans
« valider ». Ce mot ferme la commande et laisse les attributs optionnels libres.

## Apprentissages des gestes - séance 1

Dans la fenêtre des gestes, choisir un nom, cocher « Apprendre », puis tracer.
Les points sont sauvegardés dans `templates/gestures.json`. Ajouter 3 à 5
variantes personnelles pour rectangle, cercle, triangle, losange, deplacer,
puis décocher « Apprendre ». Tester chaque geste 10 fois; conserver les taux
observés pour le rapport final. L'apprentissage utilisateur reste à effectuer.

Le recognizer inclus est une variante inspirée de $1, conservant l'orientation
pour distinguer losange et rectangle. Il n'implémente pas le $1 canonique.
Pour OneDollarIvy : apprendre avec L les noms `rectangle`, `cercle`, `triangle`,
`losange`, `deplacer`; exporter avec E; reconnaître avec R. Ne pas mélanger
les deux recognizers pour une même commande.

## Ivy et outils externes

```sh
python3 -m pip install -r requirements.txt
python3 app.py --ivy --bus 127.255.255.255:2010
```

En mode Ivy, deux agents réels échangent les entrées : `PaletteSimulateursLab35`
et `FusionLab35`. Une file thread-safe relaie les callbacks au thread Tk.
Le mode local fonctionne sans dépendance Ivy et conserve les mêmes messages.
Laisser quelques secondes au démarrage Ivy pour la découverte des agents.

### sra5 / Windows

Télécharger sra5 depuis le dépôt du cours et lancer (adapter le chemin) :

```bat
sra5.exe -b 127.255.255.255:2010 -p off -g "C:\chemin\tp_fusion\grammar.grxml"
```

La grammaire est **orthographique**, sans sortie sémantique SAPI : utiliser
`-p off`. Le moteur accepte alors `sra5 Text=... Confidence=...`.
Le simulateur utilise le format `Parsed` imposé par le sujet, avec des
expressions correspondant aux concepts acceptés. `grammar.grxml` n'a pas
été chargée ici dans SAPI : vérifier le chargement et la langue française
sur Windows. Sra5 et ppilot5 ne sont pas inclus dans l'archive.

### OneDollarIvy / Processing

https://github.com/truillet/OneDollarIvy
Installer la bibliothèque Ivy dans Processing, ouvrir le sketch et apprendre
les noms ci-dessus. L'agent du dépôt utilise déjà 127.255.255.255:2010.
Messages reçus : `OneDollarIvy Template=rectangle Confidence=0,92`.

### Synthèse optionnelle

Lancer `ppilot5.exe -b 127.255.255.255:2010`. Le moteur émet
`ppilot5 Say=...`. Sans ppilot5, les retours restent visibles dans la palette.
La synthèse réelle n'a pas été testée dans cet environnement Linux.

La palette est **notre implémentation Tkinter**, ce qui est autorisé par le
sujet. Elle ne prétend pas être compatible avec le protocole de `Palette.zip`.

## Tests et fichiers

Depuis le dossier du projet :

```sh
python3 -m unittest discover -s tests -v
```

Installer ivy-python pour le test d'intégration réseau. `docs/validation.txt`
contient la sortie obtenue ici. `tests/test_fusion.py` couvre les règles métier;
`tests/test_ivy.py` vérifie le vrai bus local. Le test des 24 permutations
compte comme une méthode de test. Le chargement Windows SAPI, le microphone,
ppilot5 et la reconnaissance de gestes humains nécessitent un essai local.

- `fusion.py` : Scene, Object, FusionData, automate, parseurs.
- `recognizer.py` : reconnaissance et apprentissage des gestes.
- `app.py` : fenêtres, file d'événements, transport Ivy/local.
- `grammar.grxml` : phrases et fragments vocaux.
- `docs/rapport.md`, `docs/Rapport_Lab3_5.pdf` : conception et validation.
- `docs/diagrammes.mmd` : chronogrammes, classes, états.
- `start.sh`, `start.bat` : points d'entrée.

Avant de rendre : réaliser les essais matériels, personnaliser les modèles de
gestes, renseigner les auteurs dans le rapport et vérifier l'échéance donnée
en cours. Ne pas présenter les modèles synthétiques comme un apprentissage
réalisé en séance ni les tests automatiques comme des essais utilisateurs.

### Références de protocoles

- https://github.com/truillet/ivy/blob/master/agents/doc_sra5.md
- https://github.com/truillet/ivy/blob/master/agents/doc_ppilot5.md
- https://github.com/truillet/OneDollarIvy/blob/main/OneDollarIvy.pde
- https://github.com/truillet/ivy/blob/master/code/ivyfirst3.py
