# Einen korrekt zugeordneten GitHub-Fork veröffentlichen

## Was ein GitHub-Fork bedeutet

Ein Fork ist ein eigenes Repository unter Deinem Konto, das GitHub dem Originalprojekt zuordnet. Es wird über **Fork → Create fork** am Original angelegt. Ein beliebiges neues Repository und ein ZIP-Upload allein stellen diese Beziehung nicht her. Eine Änderung des Originals ist dafür nicht erforderlich. Ein Pull Request ist nur nötig, wenn der Originalentwickler ausgewählte Änderungen in sein eigenes Projekt übernehmen soll.

Offizielle Anleitung: [GitHub – Fork a repository](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/fork-a-repo).

## Empfohlener Ablauf für dieses Paket

1. Unter Deinem Konto **Tapatvde** auf [die Originalseite](https://github.com/rabbitfiremediacreation/music-generator) gehen und **Fork** anklicken.
2. Als Besitzer **Tapatvde** wählen. Empfohlener Name: **music-generator-tapa-fork**. Beschreibung: „Windows fork with local voice profiles, RVC training, original-song editing and optional XL sound model.“ Nur den Hauptzweig kopieren genügt.
3. **Create fork** ausführen. GitHub zeigt danach die Herkunft „forked from rabbitfiremediacreation/music-generator“ an. Ein Fork eines öffentlichen Projekts ist ebenfalls öffentlich.
4. Den neuen Fork für die verbundene GitHub-App freigeben, falls Deine App-Verbindung nur ausgewählte Repositories sehen darf. Es werden keine Zugangsdaten im Chat oder in Dateien benötigt.
5. Den bereinigten Paketinhalt als zusätzlichen Commit auf Basis der öffentlichen Originalhistorie übertragen. **Nicht den privaten Arbeitszweig oder die gesamte private Installation pushen.** Auch alte gelöschte Inhalte können im privaten Git-Verlauf vorhanden sein.
6. Auf GitHub README, LICENSE, Install.bat, Downloadmanifest und Dateien prüfen. Anschließend gegebenenfalls einen als Vorabversion markierten Release anlegen und Dein selbst erstelltes Quell-ZIP anhängen.
7. Download dieses GitHub-Releases in einen neuen Ordner testen. Die technische Paketprüfung und ein erster eigener Hörtest gehören getrennt dokumentiert.

## Aktuell geprüfte Automatisierung

Der öffentliche Fork **Tapatvde/music-generator-tapa-fork** wurde über die angemeldete Browser-Sitzung erstellt. Die Verbindung zum Original ist erhalten. Nach gesonderter Installation des offiziellen ChatGPT Codex Connector für dieses Repository bestehen die erforderlichen Schreibrechte; Kontoautorisierung allein war dafür nicht ausreichend.

Die vorhandenen GitHub-Werkzeuge übertragen ausschließlich den bereinigten Quellordner als zusätzlichen Commit auf Basis der öffentlichen Originalhistorie. Die private Arbeitsinstallation und ihre Git-Historie bleiben lokal. Es wurde kein Kommentar an den Originalentwickler gesendet. Eine nummerierte stabile Veröffentlichung beziehungsweise ein GitHub-Release ist eine gesonderte spätere Entscheidung.

## Was auf GitHub gehört

Quellcode, lesbare Installationsskripte, Dokumentation, Herkunfts-/Lizenzhinweise und Prüfsummen. Die großen Komponenten werden nachgeladen. Eigene Stimmen, Aufnahmen, trainierte Gewichte, Indizes, Datenbanken, lokale Pfade, Zugangsdaten, Logs und private Historie gehören nicht in das öffentliche Repository.

GitHub warnt ab 50 MiB pro Datei und blockiert reguläre Git-Dateien über 100 MiB; Releases erlauben größere Anlagen innerhalb ihrer eigenen Grenzen. Ein Modell-Upload ist für diesen Fork weder erforderlich noch vorgesehen. [Offizielle Größenregeln](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

## Vor der tatsächlichen Veröffentlichung festlegen

- Endgültiger Repository-Name und Beschreibung; eigene Kontakt-/Supportangaben nur auf ausdrücklichen Wunsch.
- Bezeichnung als Preview/Alpha und eine Versionsnummer, sobald Du sie freigibst.
- Ob automatische NC-Textzuordnung angeboten und in welchem Umfang kommerzielle Nutzung unterstützt werden soll.
- Nachweis eines weiteren Installationsversuchs auf einem anderen passenden Rechner und Hörabnahme mit einem eigenen neuen Profil.
- Langfristig versionierte Bezugsquelle für die geprüften Musikserver-Binärdateien.
- Ob der Originalentwickler zusätzlich informiert oder ein konkreter Pull Request angeboten werden soll; das wird nicht automatisch gesendet.

## Fortschritt am 13.10.2026

Der Fork ist [hier erreichbar](https://github.com/Tapatvde/music-generator-tapa-fork). Vergleichsbasis ist der öffentliche Originalcommit 3681b03fe4a91886413f87577ac94e4c2b583416. Das Quellpaket ist als Installationskandidat/Preview gekennzeichnet.

Der erste Schreibversuch meldete HTTP 403 „Resource not accessible by integration“. Anschließend wurde zwischen Kontoautorisierung und Repository-Installation unterschieden. Nach der Installation des Connectors durch den Kontoinhaber wurde das Repository sichtbar und ein Schreibtest erfolgreich durchgeführt. Zugangsdaten und Bestätigungscodes sind nicht Teil dieses Pakets.
