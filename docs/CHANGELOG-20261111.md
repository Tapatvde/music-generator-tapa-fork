# 2026.11.11-preview.1

Diese Ausgabe integriert 42 Original-Commits seit der Preview vom 21.10.2026. Originalbasis ist 32b049865f0a4677d42e034b56a091c250cc2b56. Die Ausgabe bleibt eine Windows-Preview; frühere Änderungen sind im [Oktober-Changelog](CHANGELOG-20261021.md) dokumentiert.

- WAV-/MP3-Downloadwahl und ZIP-Export, ohne bestehende Bibliotheksdateien zu ersetzen. Native MP3-Umwandlung und FFmpeg-Fallback, getrennte temporäre Ausgaben für parallele Downloads.
- Optionaler Höhenausgleich für neue Musik/Deep; keine doppelte Verarbeitung abgeleiteter RVC-/Instrumentalfassungen.
- Simple-Generierung bis zehn Minuten, Begrenzung der Audio-Codes sowie bessere Timeout-/Speicherhinweise mit den richtigen Fork-Logs.
- Neue Vorgaben mit 80 Iterationen und 0,85 Varianz. Bereits gespeicherte Aufträge bleiben erhalten.
- Ausgeschriebene Sprache für die LM-Planung, Rückkehr zum Sprachcode in Synthese/Bibliothek, begrenzte Wiederholung bei automatisch angefordertem, aber fehlendem Gesang. Vorgegebene Lyrics bleiben bestehen.
- peak_clip=0 bei neuen Musik- und Deep-Anfragen statt Perzentil-Hardclip.
- Beginn der Berechnung separat gespeichert: started_at wird beim Start als nullable Spalte ergänzt; Queue-Wartezeit zählt nicht in die angezeigte Rechenzeit.
- Optionaler Handy-Zugang samt QR-Code auf eigenem Port 8767. Standard aus, Bearer-Schlüssel erforderlich. Lokale Oberfläche weiter auf 8766; Rechnerverwaltung und zusätzliche Fork-Verarbeitungsrouten bleiben remote gesperrt.
- Rückwärtskompatible CPU-Gerätewahl und bis zu zwei Minuten Wartezeit beim ersten Programmstart.
- NumPy 2.4.6 in der App-Umgebung; certifi 2026.10.23 in beiden neuen Paketumgebungen, mit festen Hashes. RVC-Rechenbibliotheken, Quellpatch und neutrale Stimmvorgaben bleiben erhalten.

RVC-Training, Profilbibliothek, Harmonien, Abschnittstonlagen, Pegelsteuerung, Instrumentalgrundlagen, Deep/XL, Vorschau→Vollfassung und Exporte bleiben Bestandteil des Forks. [Prüfstatus](PRUEFSTATUS.md), [Bedienung](BEDIENUNG.md), [Lizenzen](LIZENZEN.md).

Die neue Desktop-App des Originals ist ein separates Projekt. Diese Ausgabe bleibt die transparente Web-/RVC-Anwendung mit Install.bat, ohne persönliche Stimmen, Songs oder private Git-Historie.
