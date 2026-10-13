"""Read-only upstream checks work in a ZIP installation and ignore origin."""
import asyncio,json,urllib.request
from pathlib import Path
from fastapi import APIRouter,Header,HTTPException
from .messages import tr
ROOT=Path(__file__).resolve().parent.parent
REPO_URL='https://github.com/rabbitfiremediacreation/music-generator'
router=APIRouter(prefix='/api/update')

def _status():
    info=json.loads((ROOT/'fork-info.json').read_text(encoding='utf-8'))
    url='https://api.github.com/repos/rabbitfiremediacreation/music-generator/compare/'+info['upstream_commit']+'...main'
    request=urllib.request.Request(url,headers={'User-Agent':'Music-Generator-Tapa-Fork','Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(request,timeout=20) as response:data=json.load(response)
    behind=int(data['ahead_by'])
    return {'current':info['package_date'],'latest':data.get('head_commit',{}).get('sha',info['upstream_commit'])[:7],
        'behind':behind,'ahead':0,'changes':[row['commit']['message'].splitlines()[0] for row in data.get('commits',[])][-15:],
        'fork':True,'apply_allowed':False,'dirty':False,'needs_install':False,'nogit':not (ROOT/'.git').exists()}

@router.get('/check')
async def check(x_lang: str=Header('de')):
    try:return {'ok':True,**await asyncio.to_thread(_status)}
    except Exception:return {'ok':False,'error':tr(x_lang,'gh_unreachable')}

@router.post('/apply')
async def apply(x_lang: str=Header()):
    raise HTTPException(400,tr(x_lang,'fork_update_guard'))
