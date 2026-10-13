# Code, Modelle und Werkzeuge haben getrennte Lizenzen

Stand 13.10.2026. Diese Übersicht dokumentiert Herkunft und Bedingungen; sie ist keine pauschale kommerzielle Freigabe sämtlicher Komponenten oder erzeugter Musik. Die maßgeblichen Originaltexte sind verlinkt und werden, soweit in Archiven enthalten, lokal mit heruntergeladen.

| Bestandteil | Quelle | Angegebene Lizenz / Besonderheit |
|---|---|---|
| Music Generator | [Original-LICENSE](https://github.com/rabbitfiremediacreation/music-generator/blob/3681b03fe4a91886413f87577ac94e4c2b583416/LICENSE) | MIT, Copyright ALPHATESTER bleibt enthalten |
| wavesurfer.js | [Projektlizenz](https://github.com/katspaugh/wavesurfer.js/blob/main/LICENSE), mitgelieferte static/vendor/wavesurfer-LICENSE.txt | BSD-3-Clause; separat vom MIT-Forkcode |
| Eigene Fork-Anpassungen | LICENSE dieses Ordners | MIT; keine Umlizenzierung anderer Komponenten |
| RVC-Quellcode | [RVC-LICENSE](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/81eed5e8f68b6bed1789f682fe78cdd324495afc/LICENSE) | MIT; Quelle und Änderungen als Patch nachvollziehbar |
| ACE-Step / GGUF-Gewichte | [ACE-Step](https://github.com/ace-step/ACE-Step-1.5), [GGUF-Repository](https://huggingface.co/Serveurperso/ACE-Step-1.5-GGUF) | MIT laut Quellen; Modellkarten beachten |
| acestep.cpp / GGML | [acestep.cpp-LICENSE](https://github.com/ServeurpersoCom/acestep.cpp/blob/master/LICENSE) | MIT; mitgelieferte Bibliotheken haben zusätzliche Hinweise |
| Python | [PSF-Lizenz](https://docs.python.org/3/license.html) | PSF-2.0 und Lizenztexte eingebundener Komponenten im Laufzeitarchiv |
| uv | [uv-Lizenzen](https://github.com/astral-sh/uv) | MIT oder Apache-2.0 |
| PyTorch / Torchaudio | [PyTorch](https://github.com/pytorch/pytorch), [Torchaudio](https://github.com/pytorch/audio) | jeweilige BSD-Lizenzen; CUDA-Komponenten separat |
| NVIDIA CUDA/cuBLAS | [NVIDIA-EULA](https://docs.nvidia.com/cuda/eula/index.html) | proprietäre NVIDIA-Bedingungen; keine MIT-Gesamtlizenz |
| Microsoft VC++-Laufzeit | [Microsoft-Runtime-Hinweise](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files) | Microsoft-Redistributionsbedingungen; [versionierter Bibliotheks-Wheel](https://pypi.org/project/msvc-runtime/14.44.35112/) |
| HuBERT | [facebook/hubert-base-ls960](https://huggingface.co/facebook/hubert-base-ls960) und RVC-Grundmodellquelle | Apache-2.0 beim Ursprungsmodell; konkrete RVC-Repack-Datei und Herkunft im Downloadmanifest |
| RMVPE | [RMVPE-LICENSE](https://github.com/Dream-High/RMVPE/blob/main/LICENSE) | Apache-2.0 beim Ursprungsprojekt; konkrete Gewichte aus der festen RVC-Grundmodellquelle |
| RVC-40-kHz-Trainingsgrundmodelle | [RVC-Modellquelle](https://huggingface.co/lj1995/VoiceConversionWebUI) | Repository deklariert MIT; diese Grundmodelle sind keine mitgelieferte Sängeridentität |
| Gesangstrennmodell | [baicai1145/pymss](https://huggingface.co/baicai1145/pymss) | Repository deklariert Apache-2.0; [pymss-Code](https://github.com/pymss-project/pymss) und [pymss-core](https://github.com/pymss-project/pymss-core) deklarieren MIT |
| FFmpeg | [FFmpeg-Lizenz](https://ffmpeg.org/legal.html) | konkreter geladener Build verwendet `--enable-version3`, ohne `--enable-gpl`: LGPLv3-Konfiguration; Komponentenbedingungen beachten |
| FFprobe | [FFmpeg-Quellprojekt](https://github.com/FFmpeg/FFmpeg) | konkreter geladener Gyan-Build verwendet `--enable-gpl --enable-version3`: GPLv3-Konfiguration |
| Optional MMS_FA | [Torchaudio MMS_FA](https://docs.pytorch.org/audio/2.7.0/generated/torchaudio.pipelines.MMS_FA.html) | **CC-BY-NC-4.0: nichtkommerzielle Modellnutzung** |
| Weitere Python-Pakete | requirements/*.lock, jeweilige Wheel-Lizenztexte | individuelle Lizenzen; Versions- und Hash-Locks erlauben genaue Zuordnung |

## Warum MMS optional ist

MMS_FA ordnet einen angegebenen Text zeitlich dem Audio zu. Es wird für automatische Refrainzeiten und Abschnittstonlagen verwendet. Der Installer lädt es nur nach ausdrücklicher Wahl beziehungsweise `-Alignment -AcceptNonCommercialLicense`. Ohne dieses Modell bleiben allgemeine Stimmumwandlung, Stimmtraining, Instrumentalversionen und manuell markierte Harmonien verfügbar. Die NC-Lizenz betrifft die Modellnutzung; daraus folgt keine pauschale Aussage über sämtliche Rechte an einer Audiodatei.

## Audio-, Stimmen- und Persönlichkeitsrechte

Nur eigene Aufnahmen oder Aufnahmen mit ausdrücklicher passender Erlaubnis verwenden. Ein frei verfügbares Programm oder Modell macht fremde Gesangsaufnahmen und Sängeridentitäten nicht automatisch zur freien Trainingsgrundlage. Eigene Songs, Texte, Samples, trainierte Profile und Modelle werden nicht automatisch veröffentlicht. Vor jedem öffentlichen Upload getrennt prüfen, was tatsächlich in den Dateien und im Git-Verlauf steckt.

## Weitergabe von Binärdateien

Dieses Quellpaket verteilt keine Modellgewichte oder ausführbaren Laufzeitdateien. Es beschreibt und prüft ihre Downloads. Wer später einen eigenen vollständigen Offline-Download oder native Binär-Releases hostet, muss dafür die jeweiligen Redistributions-, Hinweis- und gegebenenfalls Quellcodepflichten gesondert erfüllen. Der MIT-Hinweis des Forks reicht dafür nicht aus.

Original-Lizenztexte in heruntergeladenen Archiven bleiben erhalten. Die App-lokal extrahierten CUDA-/VC++-Wheel-Lizenztexte liegen unter engine/acestep.cpp/third-party-licenses. Nach einer Installation können weitere Python-Paketlizenzen in den jeweiligen `.dist-info`-Verzeichnissen eingesehen werden.
