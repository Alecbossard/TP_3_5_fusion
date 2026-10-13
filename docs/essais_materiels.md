# Essais réels sous Windows : microphone, synthèse et gestes

Ce document décrit des essais à réaliser sur le poste. Aucun succès physique
n'a été constaté à distance : les tests automatiques précédents simulent les
résultats de reconnaissance. Noter les observations réelles dans le tableau.

## 1. Préparer et lancer

Depuis la racine du dépôt, dans cmd :

```bat
git pull --ff-only
py -3.15 -m pip install -r requirements.txt
scripts\tester_materiel.bat
```

Avec un environnement `.venv`, installer la dépendance dedans :

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Le script utilise `.venv` s'il existe, sinon Python 3.15. Il cherche les
exécutables même dans les sous-dossiers de `outils/sra5` et
`outils/ppilot5_3.3`. S'ils sont absents, il télécharge les ZIP officiels du
cours et conserve tous leurs fichiers (notamment les DLL) dans ces dossiers.
Pour désactiver le téléchargement : `scripts\tester_materiel.bat --sans-telechargement`.
Pour contrôler les fichiers sans démarrer d'agent :
`scripts\tester_materiel.bat --verifier`.

Fermer les instances précédentes de la palette, sra5 et ppilot5. Le script
lance la synthèse, le moteur en mode Ivy, puis le recognizer vocal sur le bus
127.255.255.255:2010. Fermer la palette arrête les agents créés par le script.
Les logiciels sont locaux; les exécutables ne sont pas poussés sur GitHub.

Dans Windows, vérifier que le bon microphone est sélectionné et qu'il réagit
quand on parle. Autoriser son accès aux applications de bureau. sra5 requiert
un moteur SAPI français. La présence de Python et des exécutables ne garantit
pas que le moteur de reconnaissance français est installé.

Le chargement réel de `grammar.grxml` dans SAPI reste à vérifier : surveiller
la fenêtre sra5, et relever toute erreur. Le script lance le mode orthographique
`-p off`; les résultats attendus sont `sra5 Text=... Confidence=...`.

## 2. Tester la synthèse seule

Dans le panneau de simulation vocale, cliquer **valider** avec une commande
vide. Le moteur doit afficher les informations manquantes et ppilot5 doit
les prononcer. Ce clic teste la synthèse, pas le microphone.

Si le retour écrit fonctionne sans son, regarder ppilot5 et vérifier la sortie
audio Windows et la voix SAPI disponible. Utiliser un casque pour éviter que
sra5 reconnaisse les paroles synthétisées par ppilot5.

## 3. Tester le microphone avec sra5

Ne pas utiliser les boutons de simulation pour cet essai.

1. Dire **annuler** pour remettre la commande à zéro.
2. Dire **créer un cercle rouge ici**.
3. Cliquer sur la palette dans les trois secondes après la désignation.
4. Dire **valider**.

Observer trois niveaux indépendants : sra5 reconnaît-il la phrase ? Un message
`sra5 Text=...` arrive-t-il dans le journal de l'application ? Le cercle rouge
apparaît-il et la confirmation est-elle prononcée ? Un résultat reconnu avec
une confiance inférieure à 0,65 est ignoré par le moteur.

Si « ici » et le clic sont séparés de plus de trois secondes, dire annuler et
recommencer. Ne pas confondre une reconnaissance réussie et une fusion expirée.

## 4. Apprendre et tester ses propres gestes

L'interface incluse fonctionne sans Processing/OneDollarIvy.

1. Dans la fenêtre des gestes, choisir **rectangle** et cocher **Apprendre**.
2. Tracer trois rectangles fermés différents. Chaque tracé ajoute un modèle
   personnel dans `src/reconnaissance_gestuelle/templates/gestures.json`.
3. Décocher **Apprendre**.
4. Dire **annuler**, puis **créer** au microphone.
5. Tracer un rectangle; vérifier le nom et le score affichés.
6. Dire **valider**. La forme doit apparaître et la confirmation être prononcée.
7. Répéter pour cercle, triangle, losange, puis deplacer avec la flèche.

Effectuer dix essais de reconnaissance par geste et relever succès/échecs et
scores. Les modèles synthétiques initiaux restent présents : ces essais évaluent
la banque combinée. Ne pas les présenter comme une comparaison avant/après
isolant l'effet de l'apprentissage personnel.

Pour tester le déplacement avec la flèche : créer d'abord un objet, dire
annuler, tracer la flèche deplacer, dire cet objet et cliquer sur la source,
puis dire ici et cliquer sur la destination, enfin dire valider.

## Observations à compléter après essais

| Essai | Résultat attendu | Résultat observé |
| --- | --- | --- |
| Synthèse seule | Le retour affiché est prononcé | À tester |
| Microphone | sra5 reconnaît la phrase française | À tester |
| Transmission | Le message Text apparaît dans le journal | À tester |
| Création réelle | Cercle rouge au point désigné | À tester |
| Gestes personnels | Nom et score pour dix essais par geste | À tester |
| Voix + geste | Forme créée après créer / geste / valider | À tester |
| Déplacement | Seul l'objet désigné change de position | À tester |

Noter la version effective de Python (`py -3.15 --version`), les versions des
agents et le moteur SAPI. En cas d'échec, conserver l'erreur des consoles et
le message du journal; ne pas déclarer les essais validés sur la seule base
du démarrage des fenêtres.
