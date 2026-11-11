# Prüfstatus – 2026.11.11-preview.1

Stand 11.11.2026. Diese Ausgabe bleibt eine **Windows-Preview / ein Installationskandidat**. Die folgenden Nachweise gehören zum aktuellen bereinigten Paket. Historische Ergebnisse stehen getrennt unter [Oktober](PRUEFSTATUS-20261021.md) und [erster Paketprüfung](PRUEFSTATUS-20261013.md).

| Neu durchgeführte Prüfung | Ergebnis |
|---|---|
| Tatsächlicher Einstieg | Install.bat über den Windows-Kommandointerpreter ausgeführt; lesbare Install.ps1 und Windows PowerShell 5.1; kein Setup.exe |
| Getrennte Einrichtung | Neue CPython-3.12.15-Laufzeit, 19 App-Pakete und 127 RVC-Pakete aus Hash-Locks; LM 4B, Standard/XL und optional MMS installiert. Verifizierte allgemeine Downloads wurden nach erneutem Hashcheck als Cache verwendet; keine privaten Aufnahmen, Profile oder Python-Umgebungen kopiert |
| Wiederaufnahme ohne Netz | Install.bat erneut mit -NoNetwork/-Cpu/XL/optionalem MMS ausgeführt; native Laufzeit und Modelle wiederverwendet, Paketumgebungen geprüft, CPU-Wahl gespeichert |
| Zertifikate | certifi 2026.10.23 in beiden neuen Umgebungen. Außer dieser Sammlung bleiben RVC-Rechenpakete und Quellpatch beim früheren Stand; die private RVC-Installation wurde nicht geändert |
| RVC-Umgebung | Feste Quellrevision und Patch auf elf Dateien, Trainingsgrundmodelle, Imports und endliche PyTorch-CUDA-Matrix geprüft; Torch 2.7.1+cu118 |
| Python | 54 Tests bestanden: zehn öffentliche API-/Neutralitätsfälle, neun Abruf-/Einstellungsfälle, 14 CPU-/Prozessfälle und 21 neue Export-/Zugangs-/EQ-/Längen-/Lyrics-/Migrations-/Queue-Fälle |
| JavaScript | Sieben Prüfgruppen bestanden: Deep-Modellwahl, Vorschau→Vollfassung, Mikrofonidee, Sprachen, Player/Hörmarken, Tastenkürzel und neue Zeit-/Export-/QR-Helfer |
| PowerShell | Zwei native Prüfgruppen bestanden: reale CPU-/Auto-Konfiguration und Optionsplan; Laufzeitaustausch mit Wiederverwendung, Backup/Rücksetzen, belegtem Port, Hash-/ZIP-/Pfadschutz |
| Laufender Paketserver | Getrennt auf Loopback-Port 18768 gestartet; leere Bibliothek und Profilbibliothek, Standard-/XL-Dateien, CPU-Voreinstellung und Remote aus/Port 8767 geprüft; danach beendet |
| Standard | Reale Generierung mit 80 Schritten, LM=CPU und GPU-Synthese CUDA0, anschließend Höhenausgleich und nativer MP3-Export |
| XL | Reale Generierung mit 80 Schritten, LM=CPU und GPU-Synthese CUDA0, anschließend Höhenausgleich und nativer MP3-Export |
| Einstellungen | Nach den Renderproben in der Testinstallation wieder Automatisch, Standard, Höhen aus und WAV gesetzt. Persönliche Einstellungen in der privaten Arbeitsfassung wurden nicht verändert |

## Gemessene kurze Renderproben

- **STANDARD**: 7.04 Sekunden Audio, 48000 Hz Stereo; 27.20 Sekunden für Generierung, Höhenausgleich und MP3-Download; MP3 169,344 Bytes.
- **XL**: 7.60 Sekunden Audio, 48000 Hz Stereo; 26.50 Sekunden für Generierung, Höhenausgleich und MP3-Download; MP3 182,592 Bytes.

Die Anfragen betrugen jeweils zehn Sekunden; die kürzeren tatsächlich gelieferten Ausgaben sind oben angegeben. Diese Instrumentalproben belegen den technischen Ablauf und keine musikalische Qualitätsverbesserung oder Sängeridentität. Beide eigenen Modellserver wurden nach jedem Auftrag beendet. Verwendet wurde der fest geprüfte native Build 6013134; der Download wählte den mitgelieferten mp3-codec.

## Erhalt unserer Funktionen

RVC-Quellpatch und Rechenbibliotheken bleiben erhalten; die öffentlichen Stimmvorgaben sind weiter neutral und beziehen sich nicht auf eine persönliche Beispielstimme. Stimmprofilbibliothek/-training, Entfernen/Wiederherstellen, Instrumentalgrundlagen, Tonlagen-/Harmonie-/Pegelsteuerung, Deep/XL und Vorschau→Vollfassung bleiben enthalten. Die neuen Tests prüfen insbesondere, dass Höhenausgleich nicht erneut auf RVC-/Instrumentalableitungen angewandt wird und der MP3-Export die Quelle nicht ersetzt.

Die private Entwicklungsfassung bestand vor dem Export 159 Python-Prüfungen und sieben JavaScript-Prüfgruppen. Diese Zahlen sind historische Entwicklungsnachweise und werden nicht zu den 54 neuen Python-Paketprüfungen hinzugezählt.

## Offene Abnahme und Versionsgrenze

- Die neue Einrichtung lief getrennt auf demselben Windows-Rechner mit RTX 4080 / 16 GB und NVIDIA-Treiber-API 13.5. Ein anderer PC, weitere GPU-/Treibervarianten und Mac/Linux sind nicht abgenommen.
- Die Sprachmodellvarianten 0.6B/1.7B besitzen feste Quellen/Hashes, wurden hier nicht zusätzlich installiert oder gerendert. Geprüft wurde LM 4B.
- Kein neuer vollständiger Stimmtrainingslauf, keine echte Mikrofonaufnahme und keine unabhängige musikalische Hörabnahme. Die frühere technische Trainings-/Stimmprobe ist im historischen Bericht dokumentiert.
- Die nullable started_at-Migration wurde an einer alten Testtabellenstruktur und auf Wiederholbarkeit geprüft. Eine automatische Migration von Aufnahmen und Stimmprofilen zwischen getrennten Installationsordnern ist nicht enthalten.
- Der Handy-Zugriff blieb ausgeschaltet. Port-/Token-/API-Grenzen wurden simuliert; es wurde kein Heimnetzlistener geöffnet, keine Firewall geändert und keine physische iPhone-App getestet.
- Kein vollständiger zehnminütiger Render. Die Länge ist eine technische Obergrenze und kann viel Speicher und Zeit benötigen.
- MMS_FA wurde nur nach ausdrücklicher Lizenzwahl installiert; keine neue Abnahme der Text-Zeit-Zuordnung eines echten Songs. CC-BY-NC-4.0 bleibt zu beachten.
- Tonhöhen, Trennung, Harmonien und Pegelhilfen können hörbare Fehler erzeugen. Mehr Schritte oder Trainingsrunden garantieren keine bessere Hörqualität.
- Originalbasis dieser Ausgabe ist fest **32b049865f0a4677d42e034b56a091c250cc2b56**. Die neue Desktop-App des Originalentwicklers ist ein separates Projekt.

Das Paket enthält keine Songs, persönlichen Aufnahmen, trainierten Stimmprofile, Zugangsdaten oder private Git-Historie. Alle Dateien sind in PACKAGE-CONTENTS.json und SHA256SUMS.txt erfasst; große Downloads sind separat mit Revisionen und Hashes dokumentiert. Die jeweiligen Lizenzen bleiben getrennt.
