# Music Generator – Tapa Fork

Ein transparenter Windows-Fork des [Music Generators von ALPHATESTER / rabbitfiremediacreation](https://github.com/rabbitfiremediacreation/music-generator). Er ergänzt lokale Songgenerierung um eigene Stimmprofile, RVC-Stimmumwandlung, Training, Instrumentalversionen, Originalbearbeitung und erweiterte Gesangssteuerung.

**Status: öffentlicher Quellcode- und Installationskandidat, keine endgültig freigegebene stabile Version.** Version **2026.11.11-preview.1**, Stand 11.11.2026, Originalbasis `32b049865f0a4677d42e034b56a091c250cc2b56`. Der Fork ist eigenständig und wird nicht als offizielle Ausgabe des Originalentwicklers dargestellt.

[Preview herunterladen](https://github.com/Tapatvde/music-generator-tapa-fork/releases/tag/2026.11.11-preview.1) · Quellrepository: [Tapatvde/music-generator-tapa-fork](https://github.com/Tapatvde/music-generator-tapa-fork).

## Installation in wenigen Schritten

1. Den vollständigen Ordner aus dem ZIP an einen beschreibbaren Ort entpacken, beispielsweise `C:\MusicGeneratorTapa`. Nicht im ZIP starten und keine vorhandene Musikinstallation überkopieren.
2. **Install.bat doppelklicken.** Es gibt kein `Setup.exe` und kein eigenes binäres Installationsprogramm. Die sichtbaren PowerShell-/Python-Skripte laden Laufzeit, Modelle und Zusatzkomponenten aus den dokumentierten Quellen nach.
3. Sprachmodell, optionales XL-Klangmodell und die Stimmfunktionen auswählen. Für eigene Stimmen ist die RVC-Option erforderlich. Der automatische Text-/Refrainabgleich ist ein separater, nichtkommerzieller Zusatz.
4. Nach der Installation mit **Music Generator ON.bat** starten. Die Oberfläche läuft lokal unter **http://127.0.0.1:8766/**. Mit **Music Generator OFF.bat** beenden.

Voraussetzungen: Windows 10/11 x64, NVIDIA-GPU mit aktuellem CUDA-13-kompatiblem Treiber; für RVC in diesem Kandidaten eine kompatible GPU vor der RTX-50-Generation. Die technische Erprobung bezieht sich auf eine RTX 4080 mit 16 GB VRAM. Mindestens 16 GB RAM empfohlen. Etwa 20 GB freier Platz für Musik allein, 35 GB für Musik und Stimmen, mit XL zusätzlich mindestens 6 GB Reserve. Eigene Aufnahmen, Songs und Trainingsstände benötigen weiteren Platz. Es wird kein Systemtreiber installiert und keine Administratorfreigabe benötigt.

Neue Ausgabe: [Änderungen seit der bisherigen Preview](docs/CHANGELOG-20261111.md).

Details: [Installation und Wiederaufnahme](docs/INSTALLATION.md), [Bedienung](docs/BEDIENUNG.md), [Änderungen gegenüber dem Original](docs/AENDERUNGEN.md), [Lizenzen](docs/LIZENZEN.md), [GitHub-Veröffentlichung](docs/GITHUB.md), [Prüfstatus](docs/PRUEFSTATUS.md).

Die komplette Anleitung lässt sich auch ohne Zusatzprogramm per Doppelklick auf [DOKUMENTATION.html](DOKUMENTATION.html) im Browser lesen. Die Markdown-Dateien bleiben als bearbeitbare Textquellen enthalten. scripts/build-documentation.py erzeugt die HTML-Fassung erneut (benötigt das im RVC-Lock enthaltene Markdown-Paket).

## Was der Fork ergänzt

- WAV-/MP3-Export für einzelne Songs und ZIP-Downloads, ohne die Bibliotheksdatei zu ersetzen.
- Optionaler Höhenausgleich für neue Musik; abgeleitete Stimm-/Instrumentalfassungen werden nicht nochmals gefiltert.
- Songlänge bis zehn Minuten im Simple Mode, neue Vorgaben mit 80 Schritten und 0,85 Varianz sowie bessere Speicher-/Timeoutmeldungen.
- Optionaler Handy-Zugriff mit Schlüssel auf Port 8767, standardmäßig aus. Die lokale Oberfläche bleibt auf 8766; RVC-/Trainingsverwaltung bleibt lokal.
- Mikrofonideen aus 5–30 Sekunden Summen/Pfeifen/Gesang in Prompt, BPM, Tonart und Takt übertragen; vorhandene Lyrics, Stil und Länge bleiben erhalten. Keine exakte Melodieübernahme.
- Sprachmodell wahlweise automatisch oder nur auf der CPU; die Klangerzeugung bleibt auf der GPU. Auswahl gilt ab dem nächsten Auftrag.
- Eigene trockene Soloaufnahmen importieren, lokal ein RVC-Stimmprofil trainieren und anschließend im Dropdown verwenden. Keine fremden oder persönlichen Stimmen werden mitgeliefert.
- Bereits fertige oder importierte Songs mit einem anderen Stimmprofil als zusätzliche Fassung bearbeiten; Originale bleiben erhalten.
- Gesang entfernen und eine Instrumentalfassung als feste Grundlage für weitere Stimmversuche verwenden.
- Stimmumfang, stabile Oktavlage, eine Oktave höher und tief/mittel/hoch für markierte Strophen und Refrains steuern. Unsichere Zuordnungen und unpassende Wünsche werden sichtbar behandelt.
- Eine zweite Stimme in Refrains mit festem Intervall und eigenem Pegel zuschalten; automatische Zuordnung aus `[chorus]` benötigt den optionalen Abgleich, manuelle Zeiten bleiben möglich.
- Vorschau, zeitgleicher Originalvergleich, Prüfstellen, getrennte Gesangs-/Harmonieexporte und Bearbeitung einzelner Passagen.
- Zuschaltbare unabhängige Pegelstabilisierung für Gesang und Begleitung, Pegelregler sowie erneute lokale Umwandlung bei schweren Gesangsaussetzern im Qualitätsmodus.
- **Simple Mode / Deep Mode:** Originalaufnahme, Lyrics, Akkorde und Nähe zur Vorlage gemeinsam für eine neue Fassung verwenden. Standard oder XL direkt pro Auftrag wählen. Eine fertige Vorschau kann eine Vollfassung mit ihren gespeicherten Einstellungen beauftragen.
- Gemeinsame Warteschlange für Musik, Stimmumwandlung und Training, Abbruch und lokale Wiederaufnahme, geschätzte Verarbeitungszeit, geschützter Updatepfad.

## Transparenz und Datenschutz

`Install.bat` ruft `Install.ps1` auf. Sämtliche Downloadadressen, Größen und SHA-256-Prüfsummen stehen in **downloads-manifest.json**. Exakte Python-Paketversionen und erlaubte Hashes stehen unter **requirements/**. Die eigenen RVC-Anpassungen sind als **scripts/rvc-customizations.patch** sichtbar; der Installer prüft die unveränderte Quellrevision vor der Anwendung.

Das Quellpaket enthält keine `engine/`, `data/`, `.venv/` oder `.git/`-Ordner, keine Nutzeraufnahmen, Songs, trainierten Stimmgewichte, Indizes, Datenbanken, Zugangsdaten oder privaten Entwicklungsberichte. Laufzeitdaten entstehen erst lokal bei der Installation beziehungsweise Benutzung. **PACKAGE-CONTENTS.json** und **SHA256SUMS.txt** ermöglichen die Kontrolle der gelieferten Dateien. Prüfsummen ersetzen keine digitale Herausgebersignatur.

Musik- und Stimmverarbeitung läuft lokal. Die Erstinstallation lädt Komponenten aus dem Internet; die Updateprüfung fragt GitHub ab. Der eigene Fork öffnet seine Dienste nur auf der lokalen Loopback-Adresse. Nur eigene Stimmen oder Stimmen mit ausdrücklicher Erlaubnis verwenden.

## Grenzen

RVC ersetzt die Stimmfarbe eines vorhandenen Gesangs, komponiert keine neue Melodie und korrigiert keinen falsch gesungenen Text. Tonlagen, Refrainzuordnung, Harmonien und Pegelkorrektur sind Hilfen mit hörbaren Grenzen. Mehr Trainingsrunden und mehr Rechenzeit garantieren kein besseres Ergebnis. Eine Deep-Neufassung kann vom Original abweichen; sie ist kein verlustfreier Qualitätsfilter. MIDI-Ausgabe, MIDI-Import und ein synchroner Logic-Mehrspurimport sind nicht enthalten.

Die Originaloberfläche unterstützt zwölf Sprachen; die Fork-Erweiterungen sind deutsch/englisch und verwenden bei anderen Sprachen Englisch. Mac/Linux-Unterstützung des Originalprojekts ist keine Zusage für diesen Windows-/RVC-Fork.

## Lizenz und Herkunft

Der Originalcode steht unter MIT und sein Copyright-Hinweis bleibt in **LICENSE** erhalten. Die Fork-Anpassungen werden ebenfalls unter MIT angeboten. Modelle, FFmpeg, CUDA-Bibliotheken und weitere Laufzeiten haben eigene Bedingungen; insbesondere ist **MMS_FA CC-BY-NC-4.0** und wird nur nach ausdrücklicher Wahl nachgeladen. Keine pauschale MIT- oder kommerzielle Freigabe des gesamten Modellpakets. Siehe [Lizenzübersicht](docs/LIZENZEN.md).

Vielen Dank an ALPHATESTER / rabbitfiremediacreation, ACE-Step, Serveurperso/acestep.cpp, RVC und die Entwickler der verwendeten Werkzeuge.
