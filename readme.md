![CSViewer](./assets/logo.png)

PyQt GUI um `.csv` Dateien zu visualisieren.

## Installation

CSViewer benötigt python 3.
Das System muss außerdem von PyQt5 unterstützt werden.

- `pip install -r requirements.txt`
- `python CSViewer.py`

## Getting Started

Das Programm ist in 3 Sektionen aufgeteilt.

1. Die _Toolbar_ oben. Enthält Buttons zur Interaktion mit dem Programm.
    - Hinzufügen: Fügt eine `.csv` Datei von dem File System hinzu.
    - Entfernen: Löscht die momentan ausgewählte Datei aus dem Programm. Die originale Datei bleibt unverändert.
    - Speichern: Speichert das gesamte momentane Setup. Die Daten können eingebettet werden.
    - Laden: Lädt eine gespeicherte `.csviewer` Datei oder eine äquivalente `.json` Datei. Die Richtigkeit wird nicht überprüft.
    - Ansicht: Passt die x und y-Achsen so an, dass alle aktiven Graphen sichtbar sind.
2. Die _File List_ links. Zeigt alle geladenen Dateien an.
    Die Reihenfolge der Objekte kann durch drag and drop verändert werden. Dies beeinflusst die Reihenfolge in der die Daten gerendert werden.
    - Checkbox: zeigt sowohl die Farbe des Elements an und kann das Element temporär deaktivieren.
    - Dateiname
    - Offset: x-Offset der Daten
    - Einstellungen:
        - Farbe und Breite verändern die visuelle Repräsentation der Datenpunkte
        - Interpolation:
            - Keine: Die Datenpunkte der Datei werden genau so angezeigt
            - Lineare: Die Punkte werden linear miteinander verbunden
            - Bezier: Die Punkte werden durch eine Bezierkurve verbunden. Die Messpunkte bleiben unverändert.
        - Anzahl: Die Anzahl der Punkte die durch lineare oder Bezier Interpolation berechnet werden.
        - Filter: Filtert den Datensatz (vor allen anderen Operationen) durch einen eindimensionalen Gausschen Filter. Der Wert kontrolliert Sigma. Die Messpunkte werden dadurch verändert!
        - Integration: positive Werte integrieren die Funktion numerisch, negative differenzieren sie. Aufgrund der numerischen Implementation ist keine Genauigkeit anzunehmen!
3. Der _Plot Viewer_ rechts. Zeigt die Daten visuell an.
    - Steuerung:
        - Linke Maustaste bewegt die Ansicht.
        - Rechte Maustaste verändert die Skalierung
        - Scroll Rad vergrößert / verkleinert die Ansicht.
    - Cursor und Positionen:
        - Es existiert immer ein Cursor für die x-Achse
        - Jeder weitere Plot erstellt einen eigenen Cursor in seiner Farbe auf der y-Achse
        - Die Werte der Graphen, an der der x-Stelle der Maus kann man unter dem Viewer in dem Info Feld ablesen.

## TODO

- Automatische Zuweisung der Daten auch mit arbiträren Header Namen ("Zeit", "Messung" -&gt; "x", "y")
- ~~Eigenes Pyqtgraph Objekt~~:
    - ~~Deaktivieren des Kontextmenüs (manche Optionen können das Programm zum Absturz bringen)~~
    - ~~Veränderbare rendering Reihenfolge durch Drag-and-drop verschieben von Elementen der File List~~
    - ~~Visuelles verschieben von Graphen für intuitive Kontrolle über x und y Offset (?)~~ Warscheinlich nicht/schwer möglich.
- Programm Icon
- ~~Optionen beim speichern (Daten einbetten, Farben speichern, etc.)~~
- Compiled release (.exe, .dmg, ...?)
- Testen auf Linux (?)
