# Diagrammes de conception

Chaque fichier `.mmd` contient un seul diagramme Mermaid : classes, automate,
chronogramme de création ou chronogramme de déplacement. Les ouvrir dans un
éditeur Mermaid ou une extension VS Code prenant en charge ce format.

Après refactoring : `Application` assemble `CommunicationIvy`,
`ControleurDialogue` et les trois interfaces. `ContexteFusion` et `Scene`
restent indépendants des fenêtres et du réseau.
