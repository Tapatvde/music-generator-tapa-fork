"""No personal profiles: isolated database and synthetic audio fixtures."""
import json,os,sys,unittest,uuid,wave
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent.parent
os.environ['MUSIC_GENERATOR_DATA']=str(ROOT/'data/tests'/uuid.uuid4().hex)
sys.path.insert(0,str(ROOT))
from fastapi.testclient import TestClient
from app import db,main,updater,voices,deep
db.init();client=TestClient(main.app,base_url='http://localhost',raise_server_exceptions=False)
def audio():
    output=BytesIO()
    with wave.open(output,'wb') as stream:
        stream.setparams((1,2,8000,0,'NONE','not compressed'));stream.writeframes(b'\0\0'*8000*40)
    return output.getvalue()
def imported():return client.post('/api/library/import',files={'audio':('example.wav',audio(),'audio/wav')}).json()
class PublicAPI(unittest.TestCase):
    def test_no_personal_voice_required(self):self.assertEqual(voices.profile_list(),[])
    def test_import_can_be_removed_and_restored_before_training(self):
        response=client.post('/api/voice-training/import',data={'name':'Synthetic draft'},files=[('files',('draft.wav',audio(),'audio/wav'))])
        self.assertEqual(response.status_code,200,response.text);identifier=response.json()['id']
        self.assertEqual(client.delete('/api/voice-training/'+identifier).status_code,200)
        self.assertTrue(any(r['id']==identifier for r in client.get('/api/voice-training').json()['removed']))
        self.assertEqual(client.post('/api/voice-training/'+identifier+'/restore').status_code,200)
        self.assertTrue(any(r['id']==identifier and r['status']=='draft' for r in client.get('/api/voice-training').json()['items']))
    def test_import_preserves_bytes(self):
        song=imported();self.assertEqual(client.get(song['url']).content,audio())
    def test_default_voice_range_is_not_a_personal_claim(self):
        value=voices.RangeSettings();self.assertFalse(value.enabled);self.assertEqual(value.min_note,'C2')
    def test_deep_full_uses_original_length_and_explicit_model(self):
        song=imported()
        response=client.post('/api/deep/generate',json={'source_song_id':song['id'],'caption':'Warm acoustic arrangement','instrumental':True,'preview':False,'sound_model':'standard'})
        self.assertEqual(response.status_code,200,response.text)
        saved=json.loads(db.one('SELECT params FROM songs WHERE id=?',(response.json()['id'],))['params'])
        self.assertEqual(saved['duration'],40);self.assertEqual(saved['sound_model'],'standard')
    def test_preview_is_not_a_full_source(self):
        song=imported();db.execute('UPDATE songs SET params=? WHERE id=?',(json.dumps({'deep':{'preview':True}}),song['id']))
        response=client.post('/api/deep/generate',json={'source_song_id':song['id'],'caption':'Warm','instrumental':True})
        self.assertEqual(response.status_code,422)
    def test_update_guard_cannot_publish_or_overwrite(self):
        result=client.post('/api/update/apply',headers={'X-Lang':'en'})
        self.assertEqual(result.status_code,400);self.assertIn('reviewed merge',result.json()['detail'])
    def test_zip_update_check_does_not_need_git(self):
        response={'ahead_by':0,'head_commit':{'sha':'3681b03fe4a91886413f87577ac94e4c2b583416'},'commits':[]}
        class Handle:
            def __enter__(self):return BytesIO(json.dumps(response).encode())
            def __exit__(self,*args):pass
        with patch('app.updater.urllib.request.urlopen',return_value=Handle()):result=updater._status()
        self.assertEqual(result['behind'],0);self.assertFalse(result['apply_allowed']);self.assertTrue(result['fork'])
    def test_invalid_model_keeps_validation(self):
        self.assertEqual(client.put('/api/settings',json={'dit':[]}).status_code,422)
    def test_unexpected_error_does_not_expose_internal_text(self):
        with patch.object(db,'query',side_effect=RuntimeError('private sentinel')),self.assertLogs('uvicorn.error'):
            result=client.get('/api/folders',headers={'X-Lang':'en'})
        self.assertEqual(result.status_code,500);self.assertNotIn('private sentinel',result.text)
if __name__=='__main__':unittest.main(verbosity=2)
