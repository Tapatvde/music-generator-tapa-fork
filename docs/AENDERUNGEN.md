# Änderungsnachweis gegenüber dem Original

Original: [rabbitfiremediacreation/music-generator](https://github.com/rabbitfiremediacreation/music-generator), MIT, Copyright ALPHATESTER. Vergleichsbasis dieser Ausgabe: `8c522ee9bb16362a2e12f883b5cec2d45ed1b1e8`. Stand 21.10.2026, Version 2026.10.21-preview.1. Dies bleibt ein dokumentierter Installationskandidat, keine stabile Freigabe.

## Funktionsübersicht

| Bereich | Original / Ausgangspunkt | Erweiterung dieses Forks | Grenzen |
|---|---|---|---|
| Stimmbeispiele | Aufnahme wird für einen Prompt analysiert | Eigene Soloaufnahmen als Trainingsdatensatz importieren, RVC-Modell und Index trainieren | Import allein ist kein trainiertes Profil; trockener Einzelgesang benötigt |
| Stimmenbibliothek | Kein eigener integrierter Trainingsablauf | Benannte Profile, Dropdown, Trainingsstatus, Entfernen und Wiederherstellen | Keine persönlichen Modelle enthalten; laufende/verwendete Profile geschützt |
| Fertige Songs | Generierung aus Prompt und Lyrics | Import fertiger Songs und zusätzliche Stimmversionen mit Originalerhalt | Falscher Ausgangstext wird durch RVC nicht neu gesungen |
| Instrumental | Instrumental generieren | Gesang aus der genau ausgewählten Fassung trennen, Grundlage für weitere Stimmen | Trennung kann Artefakte hinterlassen |
| Hauptgesang | Vom Musikmodell vorgegeben | Umfang, stabile Phrasenlage, +12-Oktavschalter, Oktavkorrektur | Tonhöhenanalyse nicht fehlerfrei; keine Garantie einer gewünschten Lage |
| Strophen/Refrains | Lyrics-Markierungen als Generationseingabe | Tief/mittel/hoch pro Abschnitt, individuelle Überschreibungen und Vorprüfung | Zeitzuordnung unsicher möglich; unpassende Lage wird nicht still ersetzt |
| Zweite Stimme | Keine Fork-Harmonieebene | Manuelle oder aus `[chorus]` zugeordnete Refrainharmonien, feste Oktave/Quinte, Pegel | Keine komponierte Gegenstimme; automatische Zeiten und Quinten prüfen |
| Qualität | Original-ACE-Einstellungen | Standard/Best-Modus für Stimmen, mehr Trennaufwand, erneute kurze Umwandlung schwerer Aussetzer | Zeit zweitrangig ist keine Qualitätsgarantie |
| Mix | Fertiger Gesamtmix | Unabhängige Pegelstabilisierung und Regler für Gesang/Begleitung, gemeinsamer Lead-/Harmonieausgleich | Keine verlorenen Quelldetails rekonstruierbar; zusätzlicher Trennaufwand |
| Vorschau | Songbibliothek und Wiedergabe | Stimm- und Deep-Vorschauen, zeitgleicher Originalvergleich, Prüfstellen | Signalhinweise ersetzen keine Hörprüfung |
| Passagen | Vollständige Generation | RVC-Abschnittsbearbeitung und Einfügen in eine weitere Vollfassung | Benötigt vollständige geeignete Ausgangsfassung und Anhören der Übergänge |
| Exporte | Originalaudio und Lyrics | MP3, VOX, Lead, Harmony je nach Ergebnis, Instrumentalversion | Nicht jede Fassung besitzt jede Ebene |
| Bibliothek | Ordner, Favoriten, Varianten | Endfassung markieren, Ableitungsbeziehungen und Schutz verwendeter Quellen | Endfassung ist eine Nutzerkennzeichnung |
| Deep Mode | Freie Generierung beziehungsweise Audioanalyse | Originalaufnahme, Text, Akkorde, Quellengewichtung, Cover-Modi, optionale Folge-Stimme | Kein taktgenauer Akkord-/MIDI-Import; Neufassung kann abweichen |
| Modellwahl | Standard/XL im Original-Setup | Zusätzlich direkte Auswahl im Deep Mode und gespeicherte Wahl pro Auftrag | XL hat größeren VRAM-Bedarf |
| Deep-Vollfassung | Auswahl über Formular | Button an Vorschau verwendet vollständige Quelle und exakt gespeicherte Einstellungen | Neue Synthese, keine identische Verlängerung |
| Ressourcen | Originalserver-Start | Eigener Server pro Auftrag, anschließende GPU-Freigabe; gemeinsame Queue mit RVC/Training | Andere Prozesse teilen sich weiterhin die GPU |
| Updates | Original kann direkt aktualisieren | Lesende Originalprüfung, gesperrte direkte Übernahme, ZIP-tauglich, keine Annahme `origin=Original` | Eigene neue Releases werden bewusst separat aktualisiert |
| Installation | Install.bat mit Original-Installer | Vollständiger transparenter Downloadweg für RVC und Grundmodelle, Paket-Locks/Hashprüfung, optionale NC-Komponente | Windows/NVIDIA-Kandidat; Treiber vom Nutzer gepflegt |
| Veröffentlichung | Arbeitsinstallation enthält eigene Inhalte | Separater bereinigter Quellordner, neutrale Profilvorgaben, Inhaltsmanifest | Private Git-Historie darf nicht gepusht werden |

Siehe zusätzlich [Änderungen der neuen Preview](CHANGELOG-20261021.md).

## Historische Originalbasis vom 13.10.2026

Die Ausgangsfassung integriert die Originaländerungen bis `3681b03`: zwölf Oberflächensprachen, zentrale Servermeldungen, optionale XL-Installation, Entfernung des Testton-Backends, überarbeitete Installationsanleitungen und verständliche Meldungen für unerwartete Serverfehler. Für die Veröffentlichung werden die Original-Anleitungen durch die konsistenten Fork-Anleitungen dieses Ordners ersetzt. Aufbewahrte Copyright-Hinweise und Links belegen die Herkunft.

## Zuordnung zum Quellcode

| Dateien | Verantwortung |
|---|---|
| app/main.py, app/db.py | API, gemeinsame Queue, Metadaten und neue Auftragsarten |
| app/voices.py, app/voice_training.py | Profile, Stimmumwandlung, eigene Trainingsdaten und Veröffentlichung fertiger Profile innerhalb der lokalen App |
| app/chorus.py, app/register_policy.py | Lyrics-Abschnitte, Zuordnung, neutraler beobachteter Profilmittelpunkt und verbindliche Vorprüfung |
| app/deep.py | Originalaufnahme, Akkordtrennung, Vorschau-/Vollaufträge |
| app/managed_engine.py, app/engines.py | Eigener Musikserver und gespeicherte Standard-/XL-Wahl |
| app/level_dsp.py, app/levels.py, app/mix_settings.py | Opt-in-Pegelsteuerung und Verarbeitung |
| app/review.py, app/updater.py, app/messages.py | Prüfstellen, geschützte Originalprüfung, Meldungen |
| scripts/voice-job.py, voice-separate.py, voice_layers.py, voice_recovery.py | Getrennte Audioverarbeitung, Harmonien, lokaler Aussetzervergleich |
| scripts/train-voice-profile.py, instrumental-job.py, section-pitch-plan.py, level-job.py | Training, Instrumental, Vorprüfung und Pegelaufträge |
| static/voices.js, profile-library.js, mix-levels.js, deep.js | Zusätzliche Oberfläche und Auftragseinstellungen |
| Install.bat, Install.ps1, scripts/installer-common.ps1 | Sichtbarer Installer, Download- und Dateiprüfung |
| scripts/rvc-customizations.patch, apply-rvc-patch.py | Sämtliche Änderungen an der festen RVC-Codebasis |
| downloads-manifest.json, requirements/*.lock | Quellen, Prüfsummen, feste Paketversionen |

## Neutrale Veröffentlichung statt persönlicher Arbeitskopie

Keine persönliche Stimme wird vorgewählt oder vorausgesetzt. Profilnamen stammen aus den jeweiligen Nutzerdateien; der beobachtete Mittelpunkt stammt aus den eigenen Trainingsmetadaten. Ein importiertes Modell ohne Umfangsanalyse erhält nur unbestätigte Eingabewerte und keine aktive pauschale persönliche Begrenzung. Die persönliche Entwicklungsbibliothek, Testberichte, Screenshots, Zugangsdaten und Git-Historie sind nicht Teil dieses Ordners.

Die Veröffentlichung erhält später die öffentliche Originalhistorie als Vorgänger und einen bereinigten zusätzlichen Commit. Die private Entwicklungsinstallation wird nicht bereinigt, umgeschrieben oder als Ganzes hochgeladen.
