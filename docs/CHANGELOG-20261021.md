# 2026.10.21-preview.1 – Änderungen seit der öffentlichen Preview vom 13.10.2026

Originalbasis jetzt **8c522ee9bb16362a2e12f883b5cec2d45ed1b1e8** statt **3681b03fe4a91886413f87577ac94e4c2b583416**. 40 Original-Commits wurden geprüft übernommen beziehungsweise an den Fork angepasst. Der Windows-Fork bleibt eine Preview; Mac/Linux des Originals sind keine Freigabe unseres RVC-Pakets.

## Neu und verbessert

- Mikrofonideen aus 5–30 Sekunden Summen, Pfeifen oder Gesang: lokale Tonhöhenmessung und Beschreibung, Prompt/BPM/Tonart/Takt. Im Fork bleiben vorhandener Titel, Lyrics, Sprache, Instrumentalwahl, Stil und Länge erhalten. Kein Kopieren der konkreten Melodie.
- Sprachmodell Automatisch/Nur CPU unter Zahnrad und -Cpu/-Auto im Installer. CPU-LM und GPU-Klangerzeugung laufen als eigene Auftragsprozesse; die feste neue Engine erhält ausdrücklich --device CPU am Sprachmodellprozess. Eigene Prozesse werden auch bei Teilstart oder Abbruch beendet, fremde Dienste bleiben erhalten.
- Verbindungswiederholung beim Abholen fertiger Musikaufträge, ohne die Generierung erneut auszulösen.
- Sicherer Playerwechsel: vorherige Wiedergabe sofort stoppen; bei raschem Wechsel darf nur die zuletzt gewählte Fassung starten. Originalvergleich und Hörmarken bleiben erhalten.
- Neue Stil-Karten, mehr Prompt-Würfelvarianten, zugängliche Karten/Regler/Fokusmarkierungen, Screenreader-Rückmeldungen und Tastenkürzel mit Simple-/Deep-Bezug. Offene Dialoge schützen das Hintergrundformular.
- Zweiklick-Bestätigung für destruktive Song-/Ordner-/Serveraktionen; ungültige Zahlen und Modellwahlen werden zurückgewiesen.
- Fester Original-Engine-Download **6013134** mit SHA-256, geprüftem Entpacken, Laufzeitsicherung und Wiederverwendung. Die bisherigen veränderlichen nativen Einzeldatei-URLs entfallen.
- Windows-Konfigurationsfehler des Originals behoben: Zeilenliste und Zielpfad haben verschiedene PowerShell-Variablennamen. Gerätewahl und Installer-Fallback werden erhalten.
- App-Lock aktualisiert auf Starlette 1.8.0; alle App-/RVC-Paketversionen und Hashes bleiben nachvollziehbar. RVC-Patch und neutrale öffentliche Stimmvorgaben bleiben erhalten.

## Erhaltene Fork-Funktionen

Stimmimport/-training und Bibliothek, Entfernen/Wiederherstellen, Stimmvarianten fertiger Songs, Instrumentalgrundlagen, Stimmumfang/Oktaven/Abschnittslagen, Refrainharmonien, getrennte Pegelstabilisierung, lokale Aussetzer-Reparatur, Simple/Deep Mode, Standard/XL pro Auftrag, Vorschau→Vollfassung und getrennte Exporte. Vollständige Übersicht: [Änderungsnachweis](AENDERUNGEN.md).

## Prüfbarkeit und Grenzen

Install.bat bleibt der Einstieg; kein Setup.exe, keine Modelle oder Sängerprofile im ZIP. Herkunft und Lizenzen sind getrennt dokumentiert, MMS_FA bleibt eine ausdrücklich optionale nichtkommerzielle Komponente. Neu durchgeführte Paketprüfungen und historische Entwicklungsprüfungen sind im [Prüfstatus](PRUEFSTATUS.md) getrennt. Ein anderer PC, sämtliche GPU-/Treibervarianten und eine neue unabhängige musikalische Stimmabnahme bleiben offen.
