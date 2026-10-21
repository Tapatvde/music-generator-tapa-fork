# Prüfstatus des Installationskandidaten

Stand 13.10.2026. Die Ergebnisse stammen aus dieser Paketvorbereitung. Technische Laufzeitprüfungen und persönliche Hörabnahme sind getrennte Nachweise.

## Aktuell durchgeführte Prüfungen

| Prüfung | Ergebnis |
|---|---|
| Bereinigter Quellordner | Keine Nutzeraudios, Modelle, Datenbank, Zugangsdaten, persönlichen Pfade oder private Git-Historie enthalten; Dateiliste und SHA-256-Prüfsummen separat mitgeliefert |
| Quellsyntax | 34 Python-Dateien, 6 JavaScript-Dateien und 4 PowerShell-Dateien ohne Syntaxfehler |
| Eintrittspunkt | Install.bat ruft lesbare Install.ps1 auf; keine Setup.exe; Windows PowerShell 5.1 verwendet |
| RVC-Grundlage | Festes Quellarchiv geprüft; sichtbarer Patch auf 11 Dateien angewendet; Markierung mit Quellrevision und Datei-Hashes kontrolliert |
| Neue Installation | Neue Python-3.12.15-Laufzeit, neue App- und RVC-Umgebungen; 18 App- und 127 RVC-Pakete aus Hash-Locks eingerichtet; Standard, XL, LM 4B und optional MMS installiert |
| Wiederaufnahme | Erledigte Dateien wiederverwendet; vorhandene Einstellungen erhalten; unterbrochenes RVC-Archiv erfolgreich neu geladen, weil der Anbieter keine Byte-Range unterstützt |
| Download-/Schutzprobe | RVC-Archiv über den tatsächlichen curl-Downloadweg geladen und gehasht; falscher Cache und Pfad außerhalb des Programmordners ausdrücklich abgewiesen |
| Musik-only-Option | Separater neuer Ordner ohne RVC-Python/Stimmgrundmodelle; Audioimport/Deep-Vollauftrag und alle zehn API-Fälle erfolgreich |
| Offline-Cache-Probe | Vollständige zweite Einrichtung aus verifizierten allgemeinen Downloads und Paketcache ohne neue Netzwerkdownloads erfolgreich |
| GPU | RTX 4080 / 16 GB; CUDA-Treiber-API, PyTorch 2.7.1+cu118, endliche CUDA-Matrixergebnisse und lokale Trainingsgrundmodelle geprüft |
| Musikgeneration | Standard und XL jeweils erfolgreich über den neu geladenen nativen Windows-Musikserver gerendert; 48-kHz-Ausgaben mit endlichem, nichtleerem Signal |
| Trainingsablauf | 48 Sekunden synthetisches, nichtpersönliches Tonmaterial importiert; 50 Trainingsrunden, Modell-/Indexexport, anschließende Umwandlungsprobe und Anzeige im Dropdown erfolgreich |
| Stimmauftrag | Neu generierter Gesang mit dem neuen Testprofil umgewandelt; manuelle höhere Oktavharmonie (+12) und beide Pegelstabilisierungen aktiv; gültige Ausgaben und Exporte |
| Instrumental | Instrumentalversion der exakt gewählten Stimmfassung erfolgreich exportiert; Schutz der Quelldatei bestätigt |
| API-Prüfungen | 10 bestandene Fälle: Originalimport, neutrale Vorgaben, Deep-Vollaufträge, Vorschaugrenze, Profilentfernung/Wiederherstellung, Validierung, Fehlermeldungen und geschützte Updateprüfung |
| Oberfläche | Simple/Deep Mode, sichtbare Standard-/XL-Auswahl und neues synthetisches Profil in der Profilverwaltung geprüft |
| Lizenz/Herkunft | Original-LICENSE unverändert; Code, Modelle, Laufzeiten und optionale NC-Komponente getrennt dokumentiert |
| GitHub | Öffentlicher Fork korrekt angelegt; Konto-/Repositoryfreigabe und erfolgreicher Schreibtest geprüft; Quellpaket als Preview, keine nummerierte stabile Freigabe |

Allgemeine vorab geladene Archive und Gewichte dürfen nach erneuter Hashprüfung als Cache wiederverwendet werden. Keine private Python-Umgebung, Aufnahme oder persönliche Stimme wurde in die neue Installation kopiert. Die neuen Python-Pakete wurden aus den dokumentierten Paketquellen eingerichtet.

## Während der Vorbereitung behobene Setupfehler

Der erste Patch-Installer konnte einen fehlenden abschließenden Zeilenumbruch nicht behandeln. Die strikte Patch-Anwendung unterstützt diesen Fall jetzt. Die erste Laufzeitprüfung versuchte außerdem App-Module in der RVC-Umgebung zu importieren, obwohl beide Umgebungen bewusst verschiedene Pydantic-Versionen verwenden. Die Prüfung verwendet jetzt die zur jeweiligen Umgebung gehörenden Module und kontrolliert die lokalen Trainingsdateien direkt. Beide Fehler wurden vor Abschluss des Kandidaten behoben. Beim Test über die BAT-Datei war außerdem die automatische Bereitstellung der PowerShell-Funktion Get-FileHash in einer Aufrufumgebung nicht verfügbar. Der Installer berechnet SHA-256 deshalb direkt über .NET und ruft die Windows-PowerShell ausdrücklich über ihren Systempfad auf.

Ein reines synthetisches Tonbeispiel wurde vom Trennmodell nicht als nutzbarer Gesang erkannt. Die App brach den Auftrag sichtbar ab. Die anschließende Stimm-/Instrumentalprobe verwendete deshalb neu generierten Gesang. Ein einmaliger Verbindungsabbruch des externen Test-Abfrageprogramms während des Trainings betraf nicht den Trainingslauf: Dieser schloss erfolgreich ab und wurde anschließend erneut über die API geprüft.

## Bereits vorhandene technische Basis

Die private Arbeitsfassung bestand zuvor 115 Python-Prüfungen für Queue, RVC, Profile/Training, Instrumental, Deep Mode, XL, Pegel und Gesangsaussetzer sowie weitere Browser-/Sprachprüfungen. Diese historischen Ergebnisse sind lediglich die Ausgangsbasis; sie werden nicht als neu durchgeführte Paketprüfungen gezählt.

## Grenzen und noch offene Abnahme

- Die Installation wurde in getrennten neuen Ordnern auf demselben Entwicklungsrechner geprüft. Ein vollständig anderer Windows-PC, andere GPU-Generationen und ein System ohne vorhandenen Grafiktreiber sind damit nicht abgenommen.
- Standard und XL wurden praktisch gerendert. Die Sprachmodelloptionen 0.6B und 1.7B haben überprüfte Quellen/Hashes, wurden hier aber nicht zusätzlich vollständig installiert und musikalisch geprüft.
- Der synthetische Trainingslauf prüft Einrichtung, Datenfluss, Gewichte, Index und Umwandlung. Er belegt keine natürliche Identität oder Hörqualität einer echten Stimme.
- Die automatische MMS-Textzuordnung wurde als optionale Komponente installiert und ihre Lizenzwahl geprüft; keine neue Abnahme der zeitlichen Zuordnung eines echten Songtexts in diesem Paketlauf.
- Tonlagenplanung, Harmonieintervalle, Gesangstrennung und Pegelkorrektur bleiben hörbare Hilfen mit Fehlergrenzen. Technische Testzahlen ersetzen keine musikalische Hörabnahme.
- Mac/Linux, MIDI und jede NVIDIA-Generation sind keine Zusage dieses Windows-Kandidaten.
- Die nicht dauerhaft versionierten nativen Anbieter-URLs bleiben ein dokumentiertes Bezugsrisiko. Ein Austausch stoppt die Installation wegen des Soll-Hashes.

Der Paketinhalt wird als **Installationskandidat/Preview** bereitgestellt. Eine stabile Versionsnummer und die tatsächliche öffentliche Veröffentlichung werden erst nach Sichtung festgelegt.
