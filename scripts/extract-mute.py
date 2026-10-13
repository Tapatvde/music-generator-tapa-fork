import sys,zipfile
from pathlib import Path
archive=Path(sys.argv[1]);destination=Path(sys.argv[2]).resolve();destination.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as source:
    for entry in source.infolist():
        path=(destination/entry.filename).resolve()
        if not path.is_relative_to(destination) or entry.external_attr>>16&0xF000==0xA000:raise ValueError('Unsafe mute archive')
    source.extractall(destination)
assert (destination/'mute/0_gt_wavs/mute40k.wav').is_file(),'Unexpected mute archive structure'
