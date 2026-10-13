# Lab 3-5 - Moteur de fusion multimodale

Solution Python des trois séances : conception, structure de fusion, moteur,
interface testable, grammaire vocale, gestes entraînables et rapport.
Source du sujet : https://github.com/truillet/upssitech/blob/master/SRI/5A/IHM/TP/lab3-5_fusion.md
Les illustrations du sujet sont deux JPG et un PNG. Le sujet en ligne porte
encore une échéance de décembre 2025 : confirmer l'échéance actuelle en cours.

## Organisation du dépôt

La racine du dépôt correspond à `TP_Fusion_Multimodale/`; le nom du dépôt
GitHub reste `TP_3_5_fusion`. Les logiciels externes sont séparés de notre code.

| Dossier / fichier | Contenu |
| --- | --- |
| `outils/` | Emplacements et consignes des logiciels du cours |
| `src/moteur_fusion/` | Point d'entrée, contrôleur, contexte, transport Ivy et modèle de scène |
| `src/simulateur_vocal/` | Panneau de simulation et grammaire `grammar.grxml` |
| `src/reconnaissance_gestuelle/` | Recognizer, fenêtre d'apprentissage et modèles JSON |
| `src/palette/` | Palette Tkinter sans boutons |
| `src/main.py` | Lanceur Python de l'application |
| `docs/` | Sujet, rapport, diagrammes, captures et résultats des tests |
| `tests/` | Scénarios métier, intégration Ivy et vérification de l'interface |
| `scripts/` | Lanceurs Windows et lanceur de développement Linux/macOS |
| `requirements.txt` | Dépendance optionnelle `ivy-python` |
| `.gitignore` | Environnements locaux, caches et binaires des outils |

Les dossiers `outils/OneDollarIvy`, `outils/Palette`, `outils/ppilot5_3.3`,
`outils/Processing`, `outils/sra5` et `outils/visionneur_1_2` contiennent pour
l'instant leurs instructions. Les logiciels ne sont pas présents dans ce dépôt
et ne sont pas requis pour le mode simulation. Copier les outils du cours dans
ces emplacements pour les essais externes.

## Démarrer en simulation (sans microphone ni Processing)

Environnement utilisé sur les postes du groupe : **Windows avec Python 3.15**.
Installer Python avec le composant **Tcl/Tk**. Le mode simulation ne nécessite
aucune bibliothèque Python supplémentaire, aucun microphone et aucun agent Ivy.

Ouvrir la racine du projet contenant `README.md` et le dossier `src/` dans l'Explorateur, saisir `cmd` dans la
barre d'adresse, puis appuyer sur Entrée. Exécuter :

```bat
py -3.15 --version
py -3.15 src/main.py
```

Ces commandes fonctionnent aussi dans PowerShell. Lancer toujours la commande
Python depuis la racine du projet; les fichiers `.bat` peuvent être lancés
depuis l’Explorateur, indépendamment du dossier courant. On peut également
faire un double-clic sur `scripts/lancer_simulation.bat`. Les lanceurs
utilisent `.venv` lorsqu’il existe, sinon `py -3.15`.
Si plusieurs versions sont installées, préférer `py -3.15 src/main.py` pour choisir
explicitement la version du groupe.

Si `py` n'est pas reconnu mais que `python --version` affiche bien Python 3.15,
utiliser `python src/main.py`. Sur les postes disposant d'Altair, `python` peut pointer
vers le Python d'Altair : utiliser le lanceur `py` pour sélectionner Python 3.15.

Pour vérifier Tkinter :

```bat
py -3.15 -m tkinter
```

Une petite fenêtre de démonstration doit s'ouvrir; la fermer après vérification.
Au lancement de l'application, trois fenêtres s'ouvrent : palette sans boutons, simulateur vocal, gestes.
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
Les points sont sauvegardés dans `src/reconnaissance_gestuelle/templates/gestures.json`. Ajouter 3 à 5
variantes personnelles pour rectangle, cercle, triangle, losange, deplacer,
puis décocher « Apprendre ». Tester chaque geste 10 fois; conserver les taux
observés pour le rapport final. L'apprentissage utilisateur reste à effectuer.

Le recognizer inclus est une variante inspirée de $1, conservant l'orientation
pour distinguer losange et rectangle. Il n'implémente pas le $1 canonique.
Pour OneDollarIvy : apprendre avec L les noms `rectangle`, `cercle`, `triangle`,
`losange`, `deplacer`; exporter avec E; reconnaître avec R. Ne pas mélanger
les deux recognizers pour une même commande.

## Microphone, synthèse et gestes personnels sous Windows

Un lanceur dédié prépare les deux agents vocaux et le moteur Ivy :

```bat
py -3.15 -m pip install -r requirements.txt
scripts\tester_materiel.bat
```

Avec `.venv`, installer la dépendance via `.venv\Scripts\python.exe`.
Le lanceur cherche les agents sous `outils/`, télécharge leurs ZIP officiels
s'ils sont absents, puis démarre ppilot5, la palette Ivy et sra5. Il faut un
microphone configuré et un moteur SAPI français disponible sur Windows.
Le lancement des fenêtres ne prouve pas que la reconnaissance fonctionne.

Suivre [le protocole des essais matériels](docs/essais_materiels.md) pour tester
la synthèse, une création réellement prononcée et l'apprentissage de ses
propres tracés. Les résultats physiques restent à relever sur le poste.

## Ivy et outils externes

```bat
py -3.15 -m pip install -r requirements.txt
py -3.15 src/main.py --ivy --bus 127.255.255.255:2010
```

La compatibilité de la dépendance `ivy-python` avec Python 3.15 reste à vérifier
sur les postes du groupe; elle n'a pas été validée par les tests joints.

En mode Ivy, deux agents réels échangent les entrées : `PaletteSimulateursLab35`
et `FusionLab35`. Une file thread-safe relaie les callbacks au thread Tk.
Le mode local fonctionne sans dépendance Ivy et conserve les mêmes messages.
Laisser quelques secondes au démarrage Ivy pour la découverte des agents.

### sra5 / Windows

Télécharger sra5 depuis le dépôt du cours et lancer (adapter le chemin) :

```bat
sra5.exe -b 127.255.255.255:2010 -p off -g "C:\chemin\tp_fusion\src\simulateur_vocal\grammar.grxml"
```

La grammaire est **orthographique**, sans sortie sémantique SAPI : utiliser
`-p off`. Le moteur accepte alors `sra5 Text=... Confidence=...`.
Le simulateur utilise le format `Parsed` imposé par le sujet, avec des
expressions correspondant aux concepts acceptés. `src/simulateur_vocal/grammar.grxml` n'a pas
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
La synthèse réelle reste à tester sur les postes Windows du groupe.

La palette est **notre implémentation Tkinter**, ce qui est autorisé par le
sujet. Elle ne prétend pas être compatible avec le protocole de `Palette.zip`.

## Tests et fichiers

Depuis le dossier du projet :

```bat
py -3.15 -m unittest discover -s tests -v
```

Pour tester uniquement le moteur et les gestes, sans installer Ivy :

```bat
py -3.15 -m unittest discover -s tests -p test_fusion.py -v
```

Les résultats joints dans `docs/validation.txt` ont été produits dans
l'environnement de préparation sous Linux avec Python 3.12; ils ne constituent
pas une validation sous Windows/Python 3.15. Relancer les tests sur les postes du
groupe pour documenter les résultats de cet environnement.

Installer ivy-python pour le test d'intégration réseau. Le test d'interface
nécessite un écran et est ignoré sur Linux sans affichage. Les 31 méthodes ont
été exécutées après refactoring sous Linux/Python 3.12, avec un écran virtuel;
leur sortie est dans `docs/validation_refactoring.txt`. `docs/validation.txt`
contient la sortie obtenue ici. `tests/test_fusion.py` couvre les règles métier;
`tests/test_ivy.py` vérifie le vrai bus local. Le test des 24 permutations
compte comme une méthode de test. Le chargement Windows SAPI, le microphone,
ppilot5 et la reconnaissance de gestes humains nécessitent un essai local.

### Responsabilités des modules

- `src/moteur_fusion/main.py` : paramètres de lancement et création de l'application.
- `src/moteur_fusion/application.py` : assemblage des fenêtres et file d'événements.
- `src/moteur_fusion/controleur.py` : automate, temporisation et règles d'exécution.
- `src/moteur_fusion/contexte_fusion.py` : commande en cours et provenance des slots.
- `src/moteur_fusion/communication_ivy.py` : transport local/Ivy et parseurs des messages.
- `src/moteur_fusion/scene.py` : objets et sélection géométrique.
- `src/moteur_fusion/etats.py`, `vocabulaire.py` : états et vocabulaire partagé.
- `src/simulateur_vocal/interface.py` : expressions vocales simulées et journal.
- `src/reconnaissance_gestuelle/` : recognizer et apprentissage.
- `src/palette/interface.py` : dessin des formes et pointage.

Le rapport PDF et les captures décrivent les comportements initiaux; leur code
a ensuite été réorganisé sans changer les commandes. Le rapport Markdown et les
diagrammes ont été mis à jour avec les noms des modules refactorés.

### Mettre à jour une copie locale

Depuis la racine du dépôt, après avoir enregistré ses modifications :

```bat
git pull --ff-only
```

Il n'est pas nécessaire de recloner le dépôt. Le point d'entrée est maintenant
`src/main.py`; les anciens fichiers `app.py`, `fusion.py`, `recognizer.py` et les
lanceurs à la racine ont été remplacés par les modules et scripts ci-dessus.

Avant de rendre : réaliser les essais matériels, personnaliser les modèles de
gestes, renseigner les auteurs dans le rapport et vérifier l'échéance donnée
en cours. Ne pas présenter les modèles synthétiques comme un apprentissage
réalisé en séance ni les tests automatiques comme des essais utilisateurs.

### Références de protocoles

- https://github.com/truillet/ivy/blob/master/agents/doc_sra5.md
- https://github.com/truillet/ivy/blob/master/agents/doc_ppilot5.md
- https://github.com/truillet/OneDollarIvy/blob/main/OneDollarIvy.pde
- https://github.com/truillet/ivy/blob/master/code/ivyfirst3.py



## Accents des agents Windows

Le transport du projet utilise `compatibilite_ivy.py` pour recevoir les trames
UTF-8 et celles des anciens agents Windows encodées en CP1252. Les trames TCP
sont assemblées jusqu'au saut de ligne avant décodage, afin de préserver les
accents UTF-8 coupés entre deux lectures. La bibliothèque installée et les
autres applications Python ne sont pas modifiées.

Si une ancienne copie affiche `UnicodeDecodeError` dans `ivy.py`, fermer les
fenêtres du moteur, récupérer le correctif avec `git pull --ff-only`, puis
relancer `py -3.15 src/main.py --ivy`. Le message « Agent Ivy Windows détecté »
est informatif et indique que le décodage CP1252 a été utilisé.

La réception d'une phrase accentuée en CP1252 a été vérifiée sur une connexion
TCP réelle. Les 36 tests du projet passent sous Linux/Python 3.12 avec un écran
virtuel; la validation physique Windows reste à effectuer sur le poste.

