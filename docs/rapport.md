# Lab 3-5 - Conception d'un moteur de fusion multimodale

Solution de référence en Python, préparée le 13 octobre 2026.
Les noms des auteurs et les résultats des essais sur les postes du TP sont
à renseigner avant remise. Le PDF associé est une synthèse de ce rapport.

## Séance 1 - Spécifier les interactions

### Objectif et contraintes
Le système crée et déplace rectangles, cercles, triangles et losanges sur une
palette sans boutons. Il combine parole, reconnaissance gestuelle et pointage.
Toutes les commandes exécutées doivent contenir des informations complémentaires
provenant d'au moins deux modalités. « valider » n'est pas compté comme une
nouvelle modalité. Une parole contenant toute la commande reste donc refusée.
La couleur et la position sont optionnelles pour la création; les valeurs par
défaut sont bleu et (400,250). Le déplacement conserve la couleur de l'objet.
Sa couleur parlée est un filtre de sélection, pas un recoloriage.

### Grammaire de parole
Les commandes complètes ou leurs fragments sont acceptés :

| Élément | Expressions | Sémantique |
|---|---|---|
| Action | créer / dessiner / déplacer | action |
| Forme | rectangle / cercle / triangle / losange | shape |
| Couleur | rouge / vert / bleu | color |
| Source | cet objet / ce rectangle, etc. | demande source |
| Destination | ici | demande target |
| Prélèvement | de cette couleur | demande color_point |
| Clôture | valider | vérification et exécution |
| Contrôle | annuler | remise à zéro |

Exemples : « créer » + geste rectangle; « créer un cercle rouge ici » + clic;
« déplacer ce rectangle rouge ici » + deux clics. Les fragments sont cumulés
sans imposer un ordre action/forme/couleur/position. La grammaire SRGS fournie
s'utilise en mode orthographique sra5 (-p off); le simulateur fournit des
messages Parsed. Le parseur normalise accents, majuscules, points/virgules du
score. Les concepts compacts cetobjet et cettecouleur sont aussi acceptés.

### Grammaire gestuelle et apprentissage
Rectangle : contour fermé rectangulaire; cercle : boucle; triangle : trois
segments fermés; losange : contour orienté à 45 degrés; deplacer : flèche vers
la droite. Les quatre premiers fournissent la forme et la flèche fournit
l'action. Il n'existe aucun geste de couleur : une couleur explicite est
prononcée, ou la parole demande le prélèvement d'une couleur par un clic.
Le recognizer inclus rééchantillonne les tracés à 64 points, normalise translation
et échelle, puis compare aux modèles. L'orientation est conservée pour éviter
la confusion rectangle/losange. C'est une variante inspirée de $1 et non une
reproduction exacte. Les contours acceptent différents points de départ et
les deux sens. Les modèles initiaux sont synthétiques. L'interface sauvegarde
les nouveaux tracés; l'apprentissage de 3 à 5 variantes par geste puis les
10 essais de chaque geste doivent être réalisés par l'utilisateur. Aucun
résultat de reconnaissance humaine n'est inventé.

### Fusion temporelle et chronogrammes
Une commande est une transaction terminée par « valider ». Ce choix évite
qu'une forme soit créée avant l'arrivée d'une couleur optionnelle. Douze
secondes d'inactivité annulent la transaction; 0,65 est le seuil de confiance.
Une désignation et son clic sont associés dans une fenêtre de plus ou moins
3 secondes. Les timestamps sont ceux de réception sur le moteur, issus d'une
horloge monotone. Ce n'est pas une datation de la parole au microphone.

| Temps (s) | Parole | Geste | Pointage | Effet |
|---|---|---|---|---|
| 0 | créer | | | action |
| 1 | | rectangle | | forme |
| 2 | rouge | | | couleur |
| 3 | | | (180,180) | clic tamponné |
| 4 | ici | | | clic associé à la destination |
| 5 | valider | | | rectangle rouge créé |

| Temps (s) | Parole | Geste | Pointage | Effet |
|---|---|---|---|---|
| 0 | | deplacer | | action |
| 1 | cet objet | | | attente source |
| 2 | | | objet | source |
| 3 | ici | | | attente destination |
| 4 | | | (500,300) | destination |
| 5 | valider | | | objet déplacé |

L'ordre couleur/position est réversible. Si les deux références sont prononcées
ensemble, les clics suivants les résolvent dans l'ordre de mention. Un clic est
consommé une seule fois. L'appariement suit l'ordre des références, puis le clic
le plus proche temporellement parmi les clics encore disponibles. Ce choix est
déterministe mais ne constitue pas un appariement global optimal. Les clics
antérieurs peuvent démarrer une transaction; ils ne survivent pas à son reset.
Les références expirées non résolues imposent d'annuler et de recommencer.

## Séance 2 - Concevoir le contrôleur

### Architecture et classes
La palette Tkinter est recodée, possibilité explicitement autorisée par le sujet.
Application gère les trois fenêtres; Recognizer produit des événements de geste;
CommunicationIvy convertit les événements en messages identiques en local et sur Ivy.
En mode Ivy, deux agents réels sont ouverts : FusionLab35 et
PaletteSimulateursLab35. Les messages sra5 et OneDollarIvy externes peuvent
remplacer les entrées simulées. Les callbacks déposent les messages dans une
file thread-safe; le thread graphique traite cette file toutes les 50 ms.
ControleurDialogue contient ContexteFusion et applique l'automate. Scene est le modèle
des objets, Object implémente un test géométrique de pointage. La palette lit
ce modèle et l'affiche. Le projet ne fournit pas un adaptateur de Palette.zip.
Les diagrammes Mermaid des classes et états sont livrés dans le dossier diagrammes/;
les figures correspondantes sont dessinées dans le PDF.

### Actions et événements avant l'automate
Événements : parole valide/invalide, geste valide/invalide, clic, valider,
annuler, expiration de session. Actions : stocker un slot, créer une demande
de référence, apparier un clic, vérifier les gardes, sélectionner les objets,
créer/déplacer, produire un retour, réinitialiser la transaction.
Les entrées de faible confiance ou inconnues ne remplissent aucun slot.

### Structure de données
ContexteFusion contient action, shape, color, source, target, color_point;
references stocke les couples (rôle,temps), points les couples (point,temps),
origins l'origine de chaque slot substantiel et last la dernière activité.
assign() détecte les contradictions; une répétition vocale d'action/forme
reprend la provenance parole, pour refuser une phrase devenue autosuffisante;
modalities() calcule les modalités contributrices; reset() remet tous les
champs et tampons à zéro. La réinitialisation a lieu après succès, annulation ou expiration.
Une ambiguïté conserve les données pour permettre une précision; une erreur
bloque l'exécution jusqu'à annulation/expiration.

### Machine à états et matrice états/événements

| État | Entrée valide | Valider | Annuler / délai | Invalide |
|---|---|---|---|---|
| REPOS | COLLECTE + stocker | ATTENTE + champs manquants | REPOS + reset | conserver |
| COLLECTE | COLLECTE + fusion | incomplet: ATTENTE; prêt: EXECUTION | REPOS + reset | conserver |
| ATTENTE | COLLECTE + fusion | même vérification | REPOS + reset | conserver |
| AMBIGUITE | précision puis COLLECTE* | sélection si unique, sinon AMBIGUITE | REPOS + reset | conserver |
| ERREUR | bloquer | bloquer | REPOS + reset | conserver |
| EXECUTION | état transitoire | succès: REPOS; sélection non unique: AMBIGUITE | non applicable | non applicable |

*Une ambiguïté de prélèvement de couleur peut rester AMBIGUITE tant que la
couleur n'est pas résolue. Une contradiction ou un prélèvement vide mène à
ERREUR depuis un état de collecte. EXECUTION est synchrone, jamais un état
où des événements externes sont consommés. Les transitions sont tracées dans
ControleurDialogue.history.

### Gardes d'exécution
Créer : action=creer, forme connue, toutes les désignations résolues, au moins
deux modalités complémentaires. Déplacer : action=deplacer, source et target
connues, références résolues, au moins deux modalités; puis une sélection
unique après filtre forme/couleur. La couleur d'une superposition n'est jamais
choisie arbitrairement. Si plusieurs couleurs sont sous un clic de prélèvement,
un nom de couleur doit être prononcé. Si plusieurs objets identiques restent
sélectionnés, il faut annuler puis choisir une zone exclusive.

## Séance 3 - Implémenter, tester et rendre

### Protocoles
- sra5 Parsed='créer' Confidence=0,8 NP=1 Num_A=0
- sra5 Text=créer un cercle ici Confidence=0.9
- OneDollarIvy Template=rectangle Confidence=0,92
- Palette Point x=180 y=180 (protocole de notre palette)
- ppilot5 Say=Objet 1 déplacé.

Les messages reçus sont interprétés sans exécuter de code. Les callbacks
n'accèdent pas à Tk. Les mots valider/annuler sont des commandes séparées.

### Validation exécutée
30 méthodes unittest passent, dont un test réel de découverte et transmission
sur le bus Ivy local. Une méthode parcourt les 24 permutations de l'action,
du geste, de la couleur et du bloc désignation/clic. Autres cas : création
sans attributs, parole+pointage, déplacement vocal et gestuel, clic avant/après,
référence expirée, annulation, timeout, faible confiance, conflit, superposition,
prélèvement de couleur, absence de double exécution, nettoyage entre commandes,
formats à virgule/point et tests géométriques. La sortie complète est jointe.
L'autotest des modèles vérifie le classement de leurs propres tracés; il ne
mesure pas les performances sur des dessins humains.

### Mode d'emploi et exemples
Lancer py -3.15 src/main.py ou scripts/lancer_simulation.bat. Aucun microphone nécessaire.
Lancer avec --ivy après installation de requirements.txt pour le bus réel.
Le README contient les séquences de création, prélèvement et déplacement,
les commandes de lancement de sra5, OneDollarIvy et ppilot5, et les prérequis.
Les captures du PDF proviennent de l'interface Tkinter réellement lancée
sur un écran virtuel. Trois créations, un déplacement et la reconnaissance
d'un contour losange ont été vérifiés par assertions, via les événements de
l'application. Il ne s'agit pas d'une séance utilisateur ni d'un essai vocal. Les essais microphone/SAPI Windows,
la synthèse et l'apprentissage personnel restent à effectuer sur le poste du TP.

### Limites et pistes
Les seuils temporels et de confiance sont à calibrer avec des utilisateurs.
La fenêtre est calculée à réception et ne corrige pas la latence des recognizers.
Deux références proches peuvent rester sémantiquement ambiguës malgré un
appariement temporel déterministe; les séquences guidées réduisent ce problème.
Le recognizer tolère translation/échelle mais conserve volontairement l'orientation.
L'ajout de suppression/recoloriage n'est pas nécessaire au cahier des charges.

## Organisation du code après refactoring

Le contrôleur est dans `src/moteur_fusion/controleur.py`, le contexte dans
`contexte_fusion.py` et le transport/les parseurs dans `communication_ivy.py`.
Les interfaces sont séparées dans `src/palette`, `src/simulateur_vocal` et
`src/reconnaissance_gestuelle`. Les scripts de lancement sont dans `scripts/`.
Les logiciels externes ont leurs emplacements et instructions dans `outils/`.
Le PDF et les captures initiaux sont conservés; leur description des classes
FusionEngine/FusionData/Transport correspond désormais à
ControleurDialogue/ContexteFusion/CommunicationIvy.

## Sources consultées
- Sujet et trois figures : truillet/upssitech, SRI/5A/IHM/TP/lab3-5_fusion.md.
- OneDollarIvy.pde : format Template/Confidence et commandes d'apprentissage.
- truillet/ivy, agents/doc_sra5.md : modes Text/Parsed, lancement sra5.
- truillet/ivy, agents/doc_ppilot5.md : commande ppilot5 Say.
- truillet/ivy, code/ivyfirst3.py : API Python IvyServer.

Ces sources sont liées dans le README. La date de remise affichée par le sujet
en ligne est ancienne; vérifier celle de l'édition actuelle.

