import json,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(root))
from app import db
db.init();current={row['key'] for row in db.query('SELECT key FROM settings')}
defaults={'server_url':'http://127.0.0.1:8087','lm_url':'','dit':sys.argv[1]}
db.save_settings({key:value for key,value in defaults.items() if key not in current})
print('Application settings initialized; existing preferences retained')
