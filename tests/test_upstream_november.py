"""Isolated export, network-boundary, synthesis and EQ regression checks; no user library or LAN listener."""
import asyncio,hashlib,io,json,os,re,subprocess,sys,unittest,uuid,wave,zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,Mock,patch
import httpx
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
os.environ['MUSIC_GENERATOR_DATA']=str(ROOT/'data/validation'/('upstream-20261111-'+uuid.uuid4().hex[:8]))
sys.path.insert(0,str(ROOT))
from app import db,main,engines,klang,managed_engine
from fastapi.testclient import TestClient
db.init();local=TestClient(main.app,base_url='http://localhost:8766',raise_server_exceptions=False)
remote=TestClient(main.app,base_url='http://localhost:8767',raise_server_exceptions=False)

def audio(rate=48000,seconds=2):
    t=np.arange(rate*seconds)/rate
    values=np.stack((.1*np.sin(2*np.pi*500*t)+.05*np.sin(2*np.pi*16000*t),.1*np.sin(2*np.pi*800*t)),axis=1)
    out=io.BytesIO()
    with wave.open(out,'wb') as w:w.setparams((2,2,rate,0,'NONE','not compressed'));w.writeframes((values*32767).astype('<i2').tobytes())
    return out.getvalue()

def song():
    identifier=uuid.uuid4().hex[:12];name=identifier+'.wav'
    (db.songs_dir()/name).write_bytes(audio())
    db.execute('INSERT INTO songs(id,group_id,created_at,status,title,caption,lyrics,seed,params,file) VALUES(?,?,?,?,?,?,?,?,?,?)',
               (identifier,identifier,'2026-11-11T00:00:00','done','Export example','Synthetic export test','[Instrumental]',1,'{}',name))
    return db.one('SELECT * FROM songs WHERE id=?',(identifier,))

class SettingsAndAccess(unittest.TestCase):
    def setUp(self):db.save_settings({'remote':'off','remote_token':'synthetic-test-token','export_format':'wav','highs':'off'})
    def test_local_port_remains_unauthenticated_loopback(self):
        self.assertEqual(main.REMOTE_PORT,8767)
        self.assertEqual(local.get('/api/settings').status_code,200)
        self.assertEqual(local.get('/api/settings',headers={'Host':'evil.example'}).status_code,400)
    def test_remote_requires_correct_bearer(self):
        for headers in ({},{'Authorization':'Bearer wrong'}):self.assertEqual(remote.get('/api/songs',headers=headers).status_code,401)
        self.assertEqual(remote.get('/api/songs',headers={'Authorization':'Bearer synthetic-test-token'}).status_code,200)
    def test_remote_cannot_change_system_or_fork_processing(self):
        headers={'Authorization':'Bearer synthetic-test-token','X-Lang':'en'}
        for method,path in (('GET','/api/remote'),('POST','/api/shutdown'),('GET','/api/update/check'),('PUT','/api/settings'),('GET','/api/voices'),('GET','/api/voice-training'),('POST','/api/deep/generate'),('POST','/api/songs/example/voice'),('GET','/')):
            with self.subTest(path=path):self.assertEqual(remote.request(method,path,headers=headers).status_code,403)
        self.assertEqual(remote.get('/api/settings',headers=headers).status_code,200)
    def test_reserved_settings_cannot_enable_remote(self):
        for values in ({'remote':'on'},{'remote_token':'replacement'}):
            self.assertEqual(local.put('/api/settings',json=values).status_code,422)
        self.assertEqual(db.get_settings()['remote'],'off')
    def test_new_settings_validate_before_side_effects(self):
        for key in ('highs','export_format'):
            for value in ('invalid',True,[],None):
                with self.subTest(key=key,value=value),patch.object(main,'_move_songs') as move:
                    self.assertEqual(local.put('/api/settings',json={key:value,'songs_dir':'unused'}).status_code,422)
                    move.assert_not_called()
    def test_remote_busy_port_does_not_enable_access(self):
        fake=SimpleNamespace(an=False,start=AsyncMock(side_effect=OSError('busy')),stop=AsyncMock())
        with patch.object(main,'_fern',fake):
            self.assertEqual(local.post('/api/remote',json={'enabled':True}).status_code,409)
        self.assertEqual(db.get_settings()['remote'],'off')
    def test_remote_disabled_without_starting_listener(self):
        fake=SimpleNamespace(an=False,start=AsyncMock(),stop=AsyncMock())
        with patch.object(main,'_fern',fake):
            self.assertEqual(local.post('/api/remote',json={'enabled':False}).status_code,200)
        fake.stop.assert_awaited_once();fake.start.assert_not_awaited()
    def test_started_at_migration_is_additive_and_idempotent(self):
        identifier=song()['id']
        db.execute('ALTER TABLE songs DROP COLUMN started_at')
        row=db.one('SELECT * FROM songs WHERE id=?',(identifier,))
        self.assertNotIn('started_at',row)
        db.init();db.init()
        stored=db.one('SELECT * FROM songs WHERE id=?',(row['id'],))
        self.assertIsNone(stored['started_at'])
        for key,value in row.items():self.assertEqual(stored[key],value)

class Export(unittest.TestCase):
    def setUp(self):db.save_settings({'export_format':'wav'})
    def test_wav_playback_and_download_preserve_library(self):
        row=song();original=(db.songs_dir()/row['file']).read_bytes()
        self.assertEqual(local.get('/api/songs/'+row['id']+'/audio?download=1').content,original)
    def test_mp3_and_zip_do_not_replace_playback_or_source(self):
        if not main.FFMPEG.is_file():self.skipTest('Local ffmpeg unavailable')
        row=song();source=db.songs_dir()/row['file'];before=source.read_bytes()
        with patch.object(main,'_mp3_tool',return_value=main.FFMPEG):
            self.assertEqual(local.put('/api/settings',json={'export_format':'mp3'}).status_code,200)
            download=local.get('/api/songs/'+row['id']+'/audio?download=1')
            self.assertEqual(download.status_code,200,download.text[:100] if download.status_code!=200 else '')
            self.assertIn('.mp3',download.headers['content-disposition']);self.assertGreater(len(download.content),1000)
            cached=main._export_file(row);mtime=cached.stat().st_mtime_ns
            self.assertEqual(main._export_file(row),cached);self.assertEqual(cached.stat().st_mtime_ns,mtime)
            db.execute('INSERT INTO folders(id,name,created_at) VALUES(?,?,?)',(row['id'],'Export folder','2026-11-11'))
            db.execute('UPDATE songs SET folder_id=? WHERE id=?',(row['id'],row['id']))
            zipped=local.get('/api/download?folder='+row['id']);self.assertEqual(zipped.status_code,200)
            with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:self.assertTrue(all(name.endswith('.mp3') for name in archive.namelist()))
        self.assertEqual(local.get('/api/songs/'+row['id']+'/audio').content,before)
        self.assertEqual(source.read_bytes(),before)
        self.assertEqual(list((db.DATA/'export').glob('*.part.mp3')),[])
        db.save_settings({'export_format':'wav'})
    def test_failed_mp3_conversion_cleans_part_and_keeps_original(self):
        row=song();before=(db.songs_dir()/row['file']).read_bytes();db.save_settings({'export_format':'mp3'})
        with patch.object(main,'_mp3_tool',return_value=Path('mp3-codec.exe')),patch.object(main.subprocess,'run',return_value=SimpleNamespace(returncode=1,stderr=b'failed')):
            with self.assertRaises(main.HTTPException):main._export_file(row)
        self.assertEqual((db.songs_dir()/row['file']).read_bytes(),before)
        self.assertEqual(list((db.DATA/'export').glob('*.part.mp3')),[])
        db.save_settings({'export_format':'wav'})
    def test_missing_converter_rejects_preference(self):
        with patch.object(main,'_mp3_tool',return_value=None):self.assertEqual(local.put('/api/settings',json={'export_format':'mp3'}).status_code,400)
        self.assertEqual(db.get_settings()['export_format'],'wav')

class Highs(unittest.TestCase):
    def test_high_shelf_preserves_format_length_and_low_band(self):
        before=audio();after=klang.hoehen_ausgleichen(before)
        def read(value):
            with wave.open(io.BytesIO(value)) as w:return (w.getframerate(),w.getnchannels(),w.getnframes()),np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2)/32768.
        a,x=read(before);b,y=read(after);self.assertEqual(a,b);self.assertLessEqual(np.max(np.abs(y)),.951)
        t=np.arange(len(x))/a[0]
        def magnitude(z,hz):return abs(np.sum(z[:,0]*np.exp(-2j*np.pi*hz*t)))
        self.assertGreater(20*np.log10(magnitude(y,16000)/magnitude(x,16000)),3)
        self.assertLess(abs(20*np.log10(magnitude(y,500)/magnitude(x,500))),.2)
    def test_low_sample_rate_passes_through(self):
        before=audio(rate=16000);self.assertEqual(klang.hoehen_ausgleichen(before),before)

class Synthesis(unittest.IsolatedAsyncioTestCase):
    async def generate(self,params,responses):
        calls=[];original=httpx.AsyncClient
        def transport(request):
            calls.append(request)
            if request.method=='POST':return httpx.Response(200,json={'id':'lm' if request.url.path=='/lm' else 'synth'})
            if not request.url.params.get('result'):return httpx.Response(200,json={'status':'done'})
            if request.url.params['id']=='lm':return httpx.Response(200,json=responses.pop(0))
            return httpx.Response(200,content=audio(),headers={'Content-Type':'audio/wav'})
        with patch.object(engines.httpx,'AsyncClient',side_effect=lambda **kw:original(transport=httpx.MockTransport(transport),**kw)):
            result=await engines.AceStepCpp('http://localhost',dit='xl').generate(params,AsyncMock())
        return result,[json.loads(call.content) for call in calls if call.method=='POST'],calls
    async def test_missing_lyrics_retry_language_and_temperature(self):
        result,requests,calls=await self.generate({'vocal_language':'de','lyrics':'','duration':10,'lm_temperature':1.4},[{'lyrics':'[Instrumental]','audio_codes':'1,2'},{'lyrics':'Ein neuer Tag','audio_codes':'1,2'}])
        self.assertEqual([r.url.path for r in calls if r.method=='POST'],['/lm','/lm','/synth'])
        self.assertEqual(requests[0]['vocal_language'],'German');self.assertEqual(requests[0]['lm_temperature'],.85)
        self.assertEqual(requests[-1]['vocal_language'],'de');self.assertEqual(result[2]['sound_model'],engines.DIT_MODELS['xl'])
    async def test_supplied_lyrics_are_not_retried_or_rewritten(self):
        _,requests,calls=await self.generate({'vocal_language':'en','lyrics':'Given line','lm_temperature':1.2},[{'lyrics':'Given line','audio_codes':'1,2'}])
        self.assertEqual(len(requests),2);self.assertEqual(requests[0]['lyrics'],'Given line');self.assertEqual(requests[0]['lm_temperature'],1.2)
    async def test_codes_bounded_by_requested_length_and_engine_limit(self):
        for duration,expected in ((10,50),(600,3000),(900,3000)):
            _,requests,_=await self.generate({'duration':duration,'lyrics':'[Instrumental]'},[{'audio_codes':','.join(map(str,range(3100)))}])
            self.assertEqual(len(requests[-1]['audio_codes'].split(',')),expected)
            self.assertEqual(requests[0]['peak_clip'],0);self.assertEqual(requests[-1]['peak_clip'],0)
    async def test_missing_vocal_retry_has_bound(self):
        _,requests,_=await self.generate({'vocal_language':'en'},[{'lyrics':'[Instrumental]','audio_codes':'1'} for _ in range(3)])
        self.assertEqual(len(requests),4)
    async def test_cpu_option_added_only_when_binary_supports_it(self):
        engine=managed_engine.ManagedAce(db.get_settings())
        for available in (True,False):
            with patch.object(engine,'_supports_device_option',return_value=available),patch.object(managed_engine.asyncio,'create_subprocess_exec',new_callable=AsyncMock) as spawn:
                await engine._start_owned(8088,cpu=True)
            self.assertEqual('--device' in spawn.call_args.args,available)
            self.assertEqual(spawn.call_args.kwargs['env']['GGML_BACKEND'],'CPU')
    async def test_memory_hints_only_read_new_fork_log_lines(self):
        path=db.DATA/'ace-fork.log';path.write_text('old out of memory\n',encoding='utf-8');mark=engines._log_sizes()
        self.assertEqual(engines._memory_hint(mark),'')
        with path.open('a') as stream:stream.write('new failed to allocate\n')
        self.assertIn('Grafikspeicher',engines._memory_hint(mark));path.unlink()

class Worker(unittest.IsolatedAsyncioTestCase):
    async def test_highs_apply_once_to_new_music_not_derivatives(self):
        for kind,name,expected in ((None,'acestep_cpp',True),('deep','acestep_cpp',True),('voice','rvc',False),('instrumental','instrumental',False)):
            db.execute('DELETE FROM songs');db.save_settings({'highs':'on'})
            identifier=uuid.uuid4().hex[:12];params={'job_type':kind} if kind else {}
            db.execute('INSERT INTO songs(id,group_id,created_at,status,caption,seed,params) VALUES(?,?,?,?,?,?,?)',(identifier,identifier,'2026-11-11','queued','Synthetic',1,json.dumps(params)))
            engine=SimpleNamespace(name=name,cancel=AsyncMock())
            with patch.object(main,'make_fork_engine',return_value=engine),patch.object(main.deep,'OriginalEdit',return_value=engine),patch.object(main.voices,'VoiceEngine',return_value=engine),patch.object(main.voices,'InstrumentalEngine',return_value=engine),patch.object(main,'wrap_engine',side_effect=lambda value,*args:value),patch.object(main,'run_gpu',new_callable=AsyncMock,return_value=(audio(),'wav',{})),patch.object(main,'hoehen_ausgleichen',return_value=audio()) as eq,patch.object(main.voices,'record_timing'),patch.object(main,'_wach',Mock()):
                task=asyncio.create_task(main.worker())
                try:
                    for _ in range(100):
                        row=db.one('SELECT * FROM songs WHERE id=?',(identifier,))
                        if row['status'] in ('done','error'):break
                        await asyncio.sleep(.01)
                    self.assertEqual(row['status'],'done',row['message']);self.assertEqual(eq.called,expected);self.assertIsNotNone(row['started_at'])
                finally:
                    task.cancel()
                    try:await task
                    except asyncio.CancelledError:pass

if __name__=='__main__':unittest.main(verbosity=2)
