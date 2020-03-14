![CSViewer](./assets/banner.png)

PyQt GUI um `.csv` Dateien zu visualisieren.

## Installation

CSViewer benötigt python 3.
Das System muss außerdem von PyQt5 unterstützt werden.

### mit make

make wird nicht unbedingt benötigt, macht den gesamten Prozess jedoch wesentlich einfacher.

- `make init` venv initialisieren und dependencies herunterladen
- `make run` von source starten
- `make build exec` programm freezen und dieses ausführen
- `make clean` build-Dateien löschen
- `make gen` requirements.txt durch pip freeze überschreiben

### oder manuell

- (optional) venv erstellen & aktivieren
    - `python3 -m venv ./venv`
        - bash/zsh: `source ./venv/bin/activate`
        - batch: `./venv/Scripts/activate.bat`
        - für andere Shells: [mehr Infos zu venv hier](https://docs.python.org/3/library/venv.html)
- `pip install -r requirements.txt` dependencies herunterladen
- `python3 CSViewer.py` source ausführen
- für builds, siehe den [makefile](makefile#L32)

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
    - Das anclicken eines Elements aktiviert dieses, woduch es graphisch verschoben werden kann.
    - Checkbox: zeigt sowohl die Farbe des Elements an und kann das Element temporär deaktivieren.
    - Dateiname
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
        - Ein aktiver, gehighlighteter Graph kann durch click and drag der linken Maustatste verschoben werden.
    - Cursor und Positionen:
        - Es existiert immer ein Cursor für die x-Achse
        - Jeder weitere Plot erstellt einen eigenen Cursor in seiner Farbe auf der y-Achse
        - Die Werte der Graphen, an der der x-Stelle der Maus kann man unter dem Viewer in dem Info Feld ablesen.

## TODO

- Automatische Zuweisung der Daten auch mit arbiträren Header Namen ("Zeit", "Messung" -&gt; "x", "y")
- ~~Programm Icon~~
- ~~Compiled release (.exe, .dmg, ...?)~~
- Testen auf Linux (?)
- ~~Cursor beim Verschieben von Graphen ändern~~
- Graph und DataFile Klassen zusammenfassen, villeicht durch SignalProxies
