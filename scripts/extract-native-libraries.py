"""App-local DLLs from verified wheels; does not install a system runtime."""
import hashlib,json,sys,zipfile
from pathlib import Path
archive=Path(sys.argv[1]);destination=Path(sys.argv[2]).resolve();identifier=sys.argv[3]
destination.mkdir(parents=True,exist_ok=True);licenses=destination.parent.parent/'third-party-licenses'/identifier
count=0;hashes={}
with zipfile.ZipFile(archive) as source:
    for member in source.infolist():
        name=Path(member.filename).name
        if not name or member.is_dir():continue
        if name.lower().endswith('.dll'):
            content=source.read(member);target=destination/name;digest=hashlib.sha256(content).hexdigest()
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise ValueError('Existing DLL differs: '+name)
            if not target.exists():target.write_bytes(content)
            hashes[name]=digest;count+=1
        elif 'license' in member.filename.lower() or 'eula' in member.filename.lower():
            licenses.mkdir(parents=True,exist_ok=True);(licenses/name).write_bytes(source.read(member))
if not count:raise ValueError('No native libraries found in verified wheel.')
(destination/('libraries-'+identifier+'.json')).write_text(json.dumps(hashes,indent=2),encoding='utf-8')
print('Verified app-local libraries:',identifier,count)
