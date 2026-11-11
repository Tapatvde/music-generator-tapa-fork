# Prüfstatus – 2026.10.21-preview.1

Stand 21.10.2026. Diese Ausgabe ist eine **Preview / ein Installationskandidat**. Die folgende Tabelle beschreibt die neue Paketprüfung; frühere Ergebnisse stehen getrennt unter [Prüfstatus vom 13.10.2026](PRUEFSTATUS-20261013.md).

| Neu geprüfter Bereich | Ergebnis |
|---|---|
| Transparenter Einstieg | Install.bat → Install.ps1, Windows PowerShell 5.1; kein EXE-Setup |
| Getrennte Neuinstallation | Neue CPython-3.12.15-Laufzeit; 18 App-Pakete und 127 RVC-Pakete aus den Versions-/Hash-Locks eingerichtet. Standard, XL, LM 4B und optional MMS aus verifizierten allgemeinen Downloads eingerichtet; keine privaten Aufnahmen oder Profile kopiert |
| RVC-Laufzeit | Feste Quellrevision und Patch auf elf Dateien geprüft; PyTorch 2.7.1+cu118, CUDA-Matrix und Trainingsgrundmodelle in der neuen Installation geprüft |
| Laufender Server | Neue Installation ohne persönliche Profile/Songs gestartet; CPU-Auswahl des Installers gelesen, per API auf Automatisch zurückgestellt, XL erkannt und lesender Original-Updatepfad geprüft; Testserver anschließend beendet |
| Paket-API | 10 Prüfungen für leere Profilbibliothek, neutrale Vorgaben, Import, Entfernen/Wiederherstellen, Deep-Vollfassung, Vorschaugrenzen, Update-Sperre und Fehlermeldungen bestanden |
| Verbindungs-/Einstellungsregression | Neun zusätzliche Prüfungen für Zahlen, Modellwahl, Fork-Stopp und Abrufwiederholung bestanden |
| CPU-Konfiguration und Prozesse | 14 Prüfungen für CPU/Auto, Konfigurationsschutz, Validierung, eigenen Serverstart, CLI-Gerätewahl und Aufräumen nach Erfolg/Fehler/Abbruch bestanden |
| Oberfläche als JavaScript | Sechs Prüfgruppen für Modellwahl, Vorschau→Vollfassung, Mikrofonidee, Tastenkürzel, Sprachen und Player/Hörmarken bestanden. Mikrofon nur simuliert, keine echte Aufnahme |
| Windows-Installer | Zwei native PowerShell-Prüfgruppen: echte CPU-/Auto-Konfigurationsdateien und Optionsplan; native Laufzeit mit Wiederverwendung, Sicherung/Rücksetzen, Port-/Hash-/ZIP-/Pfadschutz. Synthetische Archive und Dateien, keine Nutzerdaten |
| Offline-Wiederaufnahme | Vollständiger Installer erneut mit -NoNetwork, -Cpu, XL und optionalem MMS ausgeführt; verifizierte Laufzeit/Modelle und beide Paketumgebungen wiederverwendet, CPU-Wahl gespeichert |
| Neuer nativer Musikserver | Fester Original-Build 6013134 aus der ZIP mit erwartetem SHA-256; in der getrennten Installation tatsächlich ausgeführt |
| Standard-Render | LM automatisch, Synthese CUDA0; gültige 48-kHz-Stereo-WAV, 7,20 Sekunden Audio, 10,39 Sekunden Laufzeit |
| XL-Render | LM tatsächlich CPU, Synthese CUDA0; gültige 48-kHz-Stereo-WAV, 7,04 Sekunden Audio, 22,45 Sekunden Laufzeit |

Die Renderproben sind kurze technische Instrumentalproben mit 50 Schritten. Die Requestlänge war jeweils zehn Sekunden; das Modell lieferte die oben gemessenen kürzeren Ausgaben. Das belegt den technischen Ablauf, keine musikalische Qualitätsverbesserung oder Identität einer Sängerperson.

## Während dieser Vorbereitung behoben

Windows PowerShell 5.1 übergab einen untypisierten Nullwert beim atomaren Dateiaustausch als ungültigen Backup-Pfad. Der Installer verwendet nun ausdrücklich NullString.Value; der reale Dateischreibtest besteht.

Die neue native Engine ignorierte die bisherige GGML_BACKEND-Umgebungswahl für das Sprachmodell. Die echte Probe erkannte, dass es trotz CPU-Auswahl auf CUDA lief. Der Veröffentlichungsstand setzt zusätzlich den dokumentierten Startparameter `--device CPU` ausschließlich am CPU-Kindprozess. Die erneute Probe weist LM=CPU und Synthese=CUDA0 nach; die Tests prüfen auch den konkreten Parameter.

## Historische Entwicklungsregression

Vor dem Paketexport bestand die lokale Entwicklungsfassung 138 Python-Prüfungen und sechs JavaScript-Prüfgruppen. Stimmen, Training, Instrumental, Deep, XL, Tonlagen, Harmonien, Pegel und Reparaturen waren enthalten. Diese 138 werden **nicht** als zusätzlich neu ausgeführte Tests des bereinigten Pakets gezählt; hier wurden 33 Python-Tests, sechs JavaScript- und zwei PowerShell-Prüfgruppen ausgeführt.

## Grenzen

- Die neue Installation und die Renderproben liefen getrennt auf demselben Windows-Rechner mit RTX 4080 / 16 GB und NVIDIA CUDA-Treiber-API 13.4. Ein anderer Rechner und weitere GPU-/Treibervarianten sind nicht abgenommen.
- Die LM-Optionen 0.6B und 1.7B haben feste Quellen/Hashes, wurden in diesem Durchlauf nicht zusätzlich installiert oder gerendert. LM 4B wurde geprüft.
- Stimmtraining, Stimm-/Harmonieumwandlung und Instrumental wurden in der früheren Paketvorbereitung technisch erprobt; hier wurden Umgebung, Assets, API und unveränderte Verarbeitungsdateien geprüft. Kein neuer vollständiger Trainingslauf und keine neue unabhängige Hörabnahme.
- MMS_FA wurde nach ausdrücklicher Lizenzwahl installiert. Eine neue Abnahme der zeitlichen Textzuordnung eines echten Songs wurde nicht durchgeführt.
- Tonlagen, Trennung, Harmonien und Pegelkorrektur können Artefakte erzeugen. Weitere Rechenzeit garantiert kein besseres Ergebnis.
- Mac/Linux, jede NVIDIA-Generation und MIDI sind keine Zusage dieser Windows-Preview.

Quellinhalt und SHA-256-Werte sind in PACKAGE-CONTENTS.json und SHA256SUMS.txt nachvollziehbar. Private Entwicklungshistorie, Songs, Aufnahmen und Profile werden nicht veröffentlicht. Download-/Versionsbindung und Lizenzen stehen in downloads-manifest.json beziehungsweise [LIZENZEN.md](LIZENZEN.md).

## Versionsgrenze

Die Originalbasis dieser Ausgabe ist fest auf 8c522ee gesetzt. Während der Paketvorbereitung zeigte die lesende Prüfung bereits acht spätere Original-Commits. Diese sind nicht Bestandteil dieser Preview und werden nicht ungeprüft übernommen. Der Updateknopf kann deshalb weitere Änderungen melden.
