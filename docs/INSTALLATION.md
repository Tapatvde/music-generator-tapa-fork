# Installation, Komponenten und Fehlerhilfe

## Unterstützter Kandidat

Windows x64 mit NVIDIA-GPU. Der Musikserver wird als geprüfter vorgefertigter Windows-Build geladen und benötigt eine CUDA-13-kompatible NVIDIA-Treiberversion. Die RVC-Laufzeit verwendet separat PyTorch 2.7.1 + CUDA 11.8; beide Laufzeiten können nebeneinander verwendet werden. Die benötigten cuBLAS-13- und Visual-C++-Bibliotheken werden als geprüfte Bibliotheksdateien im Programmordner abgelegt, ohne ein systemweites EXE-Setup. Der Grafiktreiber wird vom Nutzer separat gepflegt. Für RVC werden RTX-50/Blackwell-GPUs in diesem Kandidaten abgewiesen; Musik allein kann getrennt installiert werden. Der native CUDA-13-Build setzt Compute Capability 7.5 oder neuer voraus; ältere NVIDIA-Generationen werden abgewiesen. Weitere Rechner sind nicht allgemein abgenommen.

## Doppelklick-Ablauf

1. ZIP vollständig in einen neuen beschreibbaren Ordner entpacken. Kurzer lokaler Pfad ist empfehlenswert; Leerzeichen sind zulässig. Nach Installation den Ordner nicht einfach verschieben, da virtuelle Python-Umgebungen den Installationspfad speichern.
2. Install.bat starten. Dieses Skript ruft die vollständig lesbare Install.ps1 auf. Die Ausführungsrichtlinie wird nur für diesen PowerShell-Prozess angegeben; keine dauerhafte systemweite Umstellung.
3. Sprachmodell wählen: 0.6B für geringeren Speicherbedarf, 1.7B als vorsichtige Voreinstellung, 4B für größeren Speicher und komplexere Planung. Dieses Modell ist vom Klangmodell getrennt.
4. Optional XL wählen. Standard-SFT 2B bleibt vorhanden; XL-SFT 4B ist etwa 5,31 GB groß. Die Wahl erhöht Rechen- und Speicherbedarf.
5. Für eigene Stimmen RVC mit installieren. Es werden Quellcode, die dokumentierten Anpassungen, PyTorch, Werkzeuge, HuBERT, RMVPE, Trennmodell und 40-kHz-Trainingsgrundmodelle eingerichtet.
6. Den automatischen Textabgleich nur für nichtkommerzielle Nutzung wählen. Ohne ihn funktionieren Stimmumwandlung und manuelle Refrainzeiten; automatische Lyrics-Zuordnung und Abschnittstonlagen benötigen ihn und geben ansonsten eine verständliche Meldung aus.
7. Das Skript prüft Paketdateien, Download-Prüfsummen, RVC-Patch, Python-Importe und CUDA. Danach startet die App, sofern kein NoStart angegeben wurde.

Die Abnahme der Stimmähnlichkeit erfolgt durch Anhören eines anderen Songs. Die technische Installationsprüfung trainiert keine eigene Stimme und ist kein musikalischer Qualitätstest.

## Nachvollziehbarer Downloadweg

| Bestandteil | Quelle / Bindung | Ziel |
|---|---|---|
| uv 0.13.0 | offizielles GitHub-Release, erwarteter SHA-256 | engine/tools |
| CPython 3.12.15 | python-build-standalone, Build 20261009, fester SHA-256 | engine/runtime/python |
| Musikserver und GGML | festes Original-Release engine-win64-6013134, ZIP-SHA-256 | engine/acestep.cpp/build/Release |
| CUDA-13-/VC++-DLLs | versionierte Wheel-Dateien auf PyPI, erwartete Hashes | neben dem Musikserver |
| ACE-Modelle | feste Hugging-Face-Revision 666ac70204440867d8c01ba4b119cc79c95b370a | engine/acestep.cpp/models |
| RVC-Code | feste Revision 81eed5e8f68b6bed1789f682fe78cdd324495afc, Archiv-SHA und sichtbarer Patch | engine/rvc |
| Stimmgrundmodelle / FFmpeg | feste Hugging-Face-Revision aus downloads-manifest.json | engine/rvc/assets und engine/rvc |
| Trennmodell | feste Revision f02318ef92c43472777ed7aeeded3d2b29a68b58 | engine/rvc/assets/pymss_weights |
| Optional MMS_FA | offizieller PyTorch/Meta-Download, fester Soll-Hash, CC-BY-NC-4.0 | engine/chorus-aligner |
| Python-Pakete | vollständige Versions-/Hash-Locks einschließlich konkreter Torch-Wheels | .venv und engine/rvc/.venv |

Der Musikserver wird aus dem festen [Original-Release engine-win64-6013134](https://github.com/rabbitfiremediacreation/music-generator/releases/tag/engine-win64-6013134) geladen. Der Installer prüft den ZIP-Hash vor dem Entpacken, prüft Zielpfade und erhält eine vorherige Laufzeit als Release.previous-Ordner. Modelle liegen außerhalb dieses Austauschs. Fremde Prozesse werden nicht beendet. Eine bereits vollständig geprüfte Laufzeit wird wiederverwendet. Keine Prüfsummen entfernen.

Auch mit `-MusicOnly` werden die kleinen RVC-Quelldateien sowie FFmpeg/FFprobe für Audioimport und Deep Mode eingerichtet. Die große RVC-Python-Umgebung und Stimmgrundmodelle entfallen dabei. RVC lässt sich später durch erneuten Install.bat-Aufruf ergänzen.

## Wiederaufnahme und Einstellungen

Ein fehlgeschlagener Download bleibt als `.part` im lokalen Downloadcache; Install.bat erneut starten setzt ihn fort. Unterstützt der Anbieter keine Byte-Range, bleibt das Teilstück erhalten und der Download beginnt erneut. Vollständig geladene Dateien werden geprüft und wiederverwendet. Abweichende vorhandene Modelldateien werden nicht überschrieben. Eine vollständig heruntergeladene Datei mit falschem Hash wird als `.bad-*` zur Untersuchung erhalten. Laufende eigene App vor erneuter Installation über OFF beenden. Aufnahmen und trainierte Profile liegen unter data und werden nicht zur Veröffentlichung kopiert.

Voreinstellungen werden bei einer neuen Installation angelegt; vorhandene Einstellungen bleiben erhalten. Ohne -Cpu/-Auto bleibt die gespeicherte CPU-Wahl erhalten. Die Schalter schließen sich aus; Automatisch erhält das bisherige MODE-Testergebnis. Die Gerätewahl kann später unter Zahnrad geändert werden und gilt im Fork ab dem nächsten Auftrag. Wird XL später nachgeladen, kann es anschließend in Setup beziehungsweise im Deep Mode gewählt werden. Der eigene Updater meldet nur Änderungen des Originals und überschreibt den Fork niemals automatisch. Die Prüfung funktioniert auch bei einer ZIP-Installation ohne Git.

## Optionen für erfahrene Nutzer

```text
Install.bat -Yes -LM 4B -XL -NoStart
Install.bat -Yes -MusicOnly -LM 1.7B -NoStart
Install.bat -Yes -Alignment -AcceptNonCommercialLicense -NoStart
Install.bat -PlanOnly -LM 4B -XL
Install.bat -Yes -LM 4B -Cpu -NoStart
Install.bat -Yes -LM 4B -Auto -NoStart
```

`-Yes` übernimmt die angegebenen Optionen ohne Fragen: RVC ist dabei enthalten, XL und MMS bleiben ohne ausdrückliche Optionen aus. `-PlanOnly` zeigt den Plan und schreibt nichts. `-AssetCache`, `-WheelCache`, `-NoNetwork` und `-SkipGpuCheck` sind Prüf-/Administrationsoptionen; sie gehören nicht zum normalen Doppelklick-Ablauf. Hardwareprüfung nicht umgehen, um eine inkompatible GPU als unterstützt darzustellen.

## Typische Fehler

- **Keine NVIDIA-GPU / Treiber zu alt:** offiziellen NVIDIA-Treiber aktualisieren. Der Installer ändert keine Treiber.
- **Hash stimmt nicht:** Download nicht verwenden; Netzwerkproblem oder geänderte Anbieterdatei prüfen. Log unter data/installation.log. Eine abweichende existierende Datei bleibt erhalten.
- **Wenig Speicherplatz:** freien Platz für Modelle, Downloadcache und entpackte Laufzeiten bereitstellen. ZIP selbst ist klein; installierter Umfang ist wesentlich größer.
- **Port 8766 belegt:** andere Instanz beenden oder getrennte Installation nicht gleichzeitig starten. Fremde Dienste werden nicht beendet.
- **Kein Stimmprofil:** trockene Soloaufnahmen über Stimmprofile verwalten importieren und Training abschließen; ein Import allein ist noch kein Modell.
- **Automatischer Refrainabgleich fehlt:** manuelle Zeiten verwenden oder den optionalen NC-Abgleich ausdrücklich installieren.
- **Unnatürliche Tonlage / unsichere Abschnittszuordnung:** Umfang prüfen, kurze Vorschau abhören, manuelle Zeitkorrektur verwenden. Eine gewünschte Lage außerhalb des Umfangs wird nicht zuverlässig erzeugt.
- **Abbruch während Training:** vorhandene Aufnahmen/Trainingsstände bleiben lokal. Nicht mehrere Trainingseinträge desselben Profils parallel starten.

## Deinstallation

App mit OFF beenden, eigene Songs und Profile sichern und anschließend ausschließlich den selbst gewählten Programmordner entfernen. Es gibt keinen automatischen Löschbefehl für Nutzerdaten, keinen Dienst, keine Registry-Installation und keine global installierte Python-Umgebung.
