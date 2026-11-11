# Bedienung der Original- und Fork-Funktionen

## Neue Songs im Simple Mode

Titel optional, Prompt und Stil beschreiben die gewünschte Musik. Länge, BPM, Lyrics, Sprache, Tonart und Taktmaß können angegeben werden; automatische Angaben bleiben möglich. Mehrere Varianten erhalten eigene Seeds und Versionsbuchstaben. Das Logo importiert eine Aufnahme zur Analyse: Es erzeugt Textvorschläge und ist kein Garant für eine originalgetreue Coverfassung.

Optional ein fertig trainiertes Stimmprofil für die zusätzliche Stimmversion auswählen. Die musikalische Originalfassung wird zuerst erzeugt und erhalten. Die automatische Folgeumwandlung benötigt Gesang, vollständige Fassung und bei automatisch zugeordneten Harmonien passend markierte Lyrics.

## Mikrofonideen und Sprachmodellgerät

Mit dem Mikrofonknopf in der Kopfzeile 5 bis 30 Sekunden summen, pfeifen oder singen. Gedrückthalten nimmt auf, Loslassen beendet die Aufnahme; für assistive Bedienung ist Umschalten vorgesehen, Alt+R ebenfalls. Der Browser kann dafür eine Mikrofonfreigabe verlangen. Die lokale Auswertung ersetzt Prompt, BPM, Tonart und Takt, erhält aber den vorhandenen Titel, Songtext, Gesangssprache, Instrumentalwahl, Stil und Länge. Sie überträgt die konkrete Melodie nicht als Audiovorlage; dafür Deep Mode verwenden. Die Idee wird nicht in der Bibliothek gespeichert.

Unter Zahnrad › Sprachmodell rechnet auf zwischen Automatisch und Nur CPU wählen. Dies ist unabhängig von Standard/XL. Die Klangerzeugung bleibt auf der GPU. Die neue Auswahl gilt ab dem nächsten Auftrag; laufende Aufträge behalten ihre Wahl. Im Normalfall Automatisch verwenden. Nur CPU kann bei Problemen mit der Sprachmodellberechnung helfen, ist aber kein allgemeiner Klangqualitätsregler.

## Eigene Stimmprofile

1. **Stimmprofile verwalten / Manage voice profiles** öffnen.
2. Profil benennen, eine oder mehrere trockene Soloaufnahmen derselben Person auswählen. WAV, MP3, FLAC, M4A und OGG sind möglich. Mindestens 30 Sekunden, besser mehrere Minuten mit unterschiedlichen gut singbaren Lagen; ohne Musik, Hall, Dopplung und möglichst ohne starken Raumklang.
3. Importieren. Dieser Eintrag ist zunächst nur ein Datensatz.
4. Trainingsrunden auswählen und Training starten. Das Training läuft lokal auf der NVIDIA-GPU in der gemeinsamen Warteschlange. Die App erstellt Vorverarbeitung, Tonhöhen, Merkmale, Modell, Index und technische Funktionsprüfung.
5. Erst nach erfolgreichem Training erscheint die Stimme im Dropdown. Die beobachtete Tonlage ist eine vorläufige Schätzung aus den Aufnahmen, keine Messung der physiologischen Stimmgrenzen.
6. Mit einem anderen Song oder einer anderen Passage prüfen. Die eingebaute Trainingsprobe nutzt Trainingsmaterial und ist kein unabhängiger Qualitätsnachweis.

Importierte oder fertige Einträge können aus der Bibliothek entfernt und wiederhergestellt werden; laufende/verwendete Profile sind geschützt. Eine Entfernung ist keine sofortige endgültige Löschung sämtlicher Aufnahmen und Modelldateien. Keine persönlichen Beispielstimmen werden mitgeliefert.

## Fertige Songs und Instrumentalgrundlagen

**Fertigen Song importieren** nimmt eine vollständige Aufnahme in die Bibliothek auf. **Voice / Stimme** erstellt eine zusätzliche RVC-Version. RVC übernimmt die vorhandene gesungene Melodie und Artikulation; ein falscher Text im Ausgangsgesang wird nicht automatisch neu eingesungen.

**Instrumental erstellen** trennt Gesang und Begleitung der genau ausgewählten Version. Die Instrumentalfassung kann mit der verknüpften Gesangsquelle für weitere Stimmen verwendet werden. Änderungen und Oktavkorrekturen einer ausgewählten Gesangsfassung bleiben bei der zugehörigen Grundlage relevant. Die Trennung kann Artefakte und Gesangsreste enthalten.

## Stimmumfang, Oktaven und Abschnitte

Tiefsten und höchsten singbaren Ton einstellen, beispielsweise als C3 oder F#4; C4 ist das mittlere C, B entspricht dem deutschen H. Die automatische Begrenzung ist optional. Profilvorgaben lassen sich ausdrücklich speichern. Nicht analysierte importierte Modelle erhalten keine persönliche Tapa-Vorgabe.

**Eine Oktave höher (+12)** beeinflusst die Hauptgesangslage vor der Umwandlung. Die Stimmumfangsbegrenzung kann unpassende hohe Phrasen wieder versetzen. **Stabile Tonlage** versucht grobe Oktavsprünge innerhalb von Phrasen zu vermeiden. **Oktavkorrektur nach Abschnitten** ordnet markierten Strophen und Refrains tief, mittel oder hoch zu. Der Text-Audio-Abgleich liefert die Zeiten; unzuverlässige Zuordnung und ein unpassender Stimmumfang werden sichtbar gemeldet. Drei unterschiedliche singbare Lagen sind nicht bei jeder Melodie möglich.

## Refrainharmonien

**Zweite Stimme in Refrains** aktivieren. Manuelle Zeitbereiche sind ohne zusätzliches Abgleichmodell verfügbar. Automatisch aus `[chorus]` benötigt MMS_FA und passend markierte, möglichst tatsächlich gesungene Lyrics. Zugeordnete Zeiten zuerst anhören und bei Bedarf manuell ändern.

Intervall: Oktave oder Quinte über/unter der Hauptstimme; Pegel getrennt einstellen. Das ist eine parallele Stimme mit festem Abstand, keine musikalisch komponierte Gegenmelodie. Quinten können mit Akkorden kollidieren. Phrasen außerhalb des eingestellten Umfangs können ausgelassen werden. Gesang, Hauptstimme und Harmonie werden je nach Fassung separat angeboten.

## Qualität, Pegel und Vergleich

**Beste Qualität – Zeit zweitrangig** erlaubt mehr Aufwand bei Trennung und Übergängen. Schwere lokale Aussetzer der umgewandelten Stimme werden mit kurzen Durchläufen bei unveränderter Tonhöhenvorgabe erneut versucht. Mehr Rechenzeit garantiert keinen besseren Klang. Die Zeitschätzung beruht auf vorhandenen Laufzeiten; sie berücksichtigt keine fremden GPU-Aufgaben und keine Warteschlangenzeit.

**Pegel und Balance:** Gesang stabil halten und Begleitung stabil halten sind unabhängig schaltbar. Pegelregler verändern Gesang beziehungsweise Begleitung. Haupt- und Harmoniestimme folgen derselben Gesangskorrektur, die Begleitung wird nicht über die Gesangsaktivität geduckt. Pausen, Ausklang und Übersteuerungsschutz bleiben relevant. Ohne Stimmumwandlung kann dafür eine zusätzliche Trennung nötig sein.

Kurze Vorschauen zunächst anhören. **Original** startet den zeitlich passenden Vergleich. Prüfstellen sind Hinweise aus Signal-/Tonhöhenanalysen, keine automatische Garantie eines hörbaren Fehlers. Bei vollständigen RVC-Versionen können einzelne Passagen neu bearbeitet und nach Abnahme in eine weitere vollständige Fassung eingefügt werden. Die Ausgangsversion bleibt erhalten.

## Deep Mode und XL

1. Deep Mode aktivieren oder am vollständigen Bibliothekssong auf Deep Mode klicken. Die Ansicht springt zum Arbeitsbereich.
2. Vollständige Originalaufnahme auswählen oder importieren.
3. **Originalnah neu arrangieren** oder **Freier neu arrangieren** wählen. **Nur Stimme austauschen** öffnet dagegen die RVC-Bearbeitung mit erhaltener Begleitung.
4. Klangmodell wählen: allgemeine Voreinstellung, Standard SFT 2B oder XL SFT 4B. Die Wahl wird im Auftrag gespeichert. 4B bedeutet Modellparameter, nicht vier GB; XL Q8 ist etwa 5,31 GB groß.
5. Instrumentierung, Lyrics mit `[verse]`/`[chorus]` und Akkordvorgaben bearbeiten. **Text und Akkorde trennen** entfernt erkannte Akkordzeilen beziehungsweise eingebettete Akkorde aus dem Gesangstext und übergibt sie separat als Begleitungshinweise.
6. Nähe zur Aufnahme wählen, Tempo/Tonart/Takt prüfen. Nähe ist eine Quellengewichtung und keine gemessene Ähnlichkeit in Prozent.
7. 5–30 Sekunden Vorschau aus einem passenden Bereich erzeugen. Modell und Länge stehen am Startbutton.
8. An der fertigen Deep-Vorschau **Ganzen Song erstellen / Create full song** klicken. Die vollständige ursprüngliche Vorlage und die gespeicherten Vorschau-Einstellungen einschließlich Modell werden verwendet. Änderungen im aktuellen Formular beeinflussen diesen Auftrag nicht.
9. Für geänderte Einstellungen oder eine automatische zusätzliche Stimmprofilfassung die Vorschauoption im Formular ausschalten und eine neue Vollfassung beauftragen.

Eine Vollfassung folgt der Länge der Audio-Vorlage, maximal zehn Minuten. Sie ist eine neue Synthese und keine garantierte identische Verlängerung der Vorschau. Exakte Akkord-, Melodie-, Struktur- oder Klangtreue wird nicht zugesichert. Es gibt keinen MIDI-/Logic-Projektimport.

## Bibliothek und Schutz

Ordner, Suche, Favoriten, Downloads und Endfassungsmarkierung helfen beim Vergleichen. Ein verwendetes Original und verwendete Stimmprofile sind gegen unpassende Entfernung geschützt. Musikgenerierung, Stimme und Training teilen sich eine GPU-Warteschlange. Abbruch wird vor dem nächsten Auftrag verarbeitet. Der Updatebutton zeigt neue Originaländerungen an, übernimmt sie im Fork jedoch nie ungeprüft.

## Export, Höhen und lange Songs

Unter Zahnrad › Export WAV oder MP3 wählen. Die Einstellung gilt für die Downloadknöpfe und den ZIP-Download. Die Bibliotheksdatei und Wiedergabe bleiben erhalten; eine MP3-Kopie mit 192 kbit/s wird bei Bedarf in data/export erzeugt. Das ZIP enthält dieselbe Exportwahl. Vorhandene spezielle VOX-/Lead-/Harmony-Exporte bleiben ihre getrennten Dateien.

Höhen ausgleichen ist standardmäßig aus. Es hebt bei neuen Musik- und Deep-Neufassungen die Höhen ab 12 kHz sanft an und begrenzt anschließend die Spitze. Es ist kein Reparaturfilter für fehlenden Gesang. Der Auftrag übernimmt die Wahl beim Start. Stimm- und Instrumentalableitungen erhalten nicht nochmals denselben Filter.

Im Simple Mode reicht der Längenregler bis zehn Minuten. Über fünf Minuten erscheint ein Hinweis zu Zeit und Speicher. Die Grenze garantiert keinen erfolgreichen langen Render auf jeder GPU. Das Modell kann kürzere Stücke liefern. Neue Formularvorgaben sind 80 Iterationen und 0,85 Varianz; die SFT-Modellvorgabe von 50 Schritten bleibt davon unabhängig. Geladene alte Songparameter werden nicht umgeschrieben.

## Optionaler Handy-Zugriff

Der lokale Einstieg bleibt http://127.0.0.1:8766/. Unter Zahnrad kann ein zusätzlicher Heimnetzzugang auf Port 8767 eingeschaltet werden. Er ist zunächst aus und verlangt einen Zugangsschlüssel. Der QR-Code übergibt Adresse und Schlüssel an die separate iPhone-App des Originalprojekts. Ein physischer iPhone-Praxistest dieser Fork-Ausgabe steht aus.

Update, Serverstopp, Einstellungen-Schreiben und RVC-/Profil-/Trainings-/Deep-Verwaltung sind über diesen Zugang gesperrt. Dafür die lokale Oberfläche am PC verwenden. Der Installer öffnet keine Firewall und installiert keine iPhone- oder Desktop-App. Die neue Desktop-App des Originalentwicklers ist ein eigenes Projekt und ersetzt diesen Web-/RVC-Fork nicht.
