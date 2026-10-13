# Logiciels fournis pour le TP

Ces emplacements accueillent les logiciels externes du cours. Ils sont séparés
du code Python développé dans `src/`. Les exécutables ne sont pas fournis ici.
Le mode simulation fonctionne sans ces logiciels.

| Dossier | Rôle |
| --- | --- |
| `OneDollarIvy/` | Sketch Processing de reconnaissance des gestes |
| `Palette/` | Palette Processing fournie par le cours |
| `ppilot5_3.3/` | Synthèse vocale SAPI sous Windows |
| `Processing/` | Environnement d'exécution des sketches |
| `sra5/` | Reconnaissance vocale SAPI sous Windows |
| `visionneur_1_2/` | Inspection des agents et messages Ivy |

Utiliser le même bus `127.255.255.255:2010` dans les agents.
Le moteur fourni pilote notre palette Tkinter; le branchement à la palette
Processing nécessite un adaptateur à son protocole, qui n'est pas fourni.
Les binaires volumineux sont ignorés par `.gitignore`; les sources et README
peuvent être versionnés. Ne pas déposer un environnement Python dans ce dossier.
