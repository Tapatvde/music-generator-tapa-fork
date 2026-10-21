"""Isolated configuration and process-ownership checks for the CPU language-model option."""
import asyncio, json, os, sys, unittest, uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

ROOT=Path(__file__).resolve().parent.parent
os.environ['MUSIC_GENERATOR_DATA']=str(ROOT/'data/validation'/('cpu-settings-'+uuid.uuid4().hex[:8]))
sys.path.insert(0,str(ROOT))
from app import db, main, managed_engine
from app.engines import EngineError
from app.messages import LANGS, tr
from fastapi.testclient import TestClient

db.init();client=TestClient(main.app,base_url='http://localhost',raise_server_exceptions=False)
CONF=db.DATA/'engine.conf'

class Settings(unittest.TestCase):
    def setUp(self):
        self.original=b'\xef\xbb\xbf# untouched\r\nMODE=single\r\nLM_FILE=example.gguf\r\nVAE_CHUNK=256\r\n'
        CONF.write_bytes(self.original)
    def test_cpu_and_auto_preserve_other_config_bytes(self):
        r=client.put('/api/settings',json={'lm_device':'cpu'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(CONF.read_bytes(),self.original+b'LM_DEVICE=cpu\r\n')
        self.assertEqual(client.get('/api/settings').json()['lm_device'],'cpu')
        self.assertIsNone(db.one("SELECT value FROM settings WHERE key='lm_device'"))
        r=client.put('/api/settings',json={'lm_device':'auto'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(CONF.read_bytes(),self.original)
    def test_unchanged_auto_does_not_rewrite_config(self):
        before=CONF.stat().st_mtime_ns
        with patch.object(db.os,'replace') as replace:
            db.set_lm_device('auto')
        replace.assert_not_called();self.assertEqual(CONF.stat().st_mtime_ns,before)
    def test_invalid_device_rejected_before_any_other_changes(self):
        for value in ('GPU',None,True,[],{}):
            with self.subTest(value=value),patch.object(main,'_move_songs') as move:
                r=client.put('/api/settings',json={'lm_device':value,'songs_dir':str(db.DATA/'elsewhere')})
                self.assertEqual(r.status_code,422,r.text)
                move.assert_not_called();self.assertEqual(CONF.read_bytes(),self.original)
    def test_invalid_model_and_numbers_do_not_change_device(self):
        for values in ({'dit':'missing'},{'poll_interval':'invalid'},{'songs_dir':str(ROOT.parent/'outside')}):
            r=client.put('/api/settings',json={**values,'lm_device':'cpu'})
            self.assertIn(r.status_code,(400,422));self.assertEqual(CONF.read_bytes(),self.original)
    def test_device_error_has_language_fallback(self):
        for lang in LANGS:
            r=client.put('/api/settings',json={'lm_device':'unknown'},headers={'X-Lang':lang})
            self.assertEqual(r.json()['detail'],tr(lang,'fork_unknown_lm_device'))
    def test_failed_atomic_replace_retains_original(self):
        with patch.object(db.os,'replace',side_effect=OSError('fixture failure')):
            with self.assertRaises(OSError):db.set_lm_device('cpu')
        self.assertEqual(CONF.read_bytes(),self.original)
        self.assertEqual(list(db.DATA.glob('.engine-conf-*')),[])
    def test_automatic_choice_respects_installer_fallback(self):
        CONF.write_text('MODE=split\n',encoding='utf-8')
        self.assertTrue(managed_engine.ManagedAce(db.get_settings()).lm_on_cpu)
        CONF.write_text('MODE=single\n',encoding='utf-8')
        self.assertFalse(managed_engine.ManagedAce(db.get_settings()).lm_on_cpu)
    def test_default_and_cpu_routes_keep_synth_and_xl_settings(self):
        settings={**db.get_settings(),'dit':'xl'}
        automatic=managed_engine.ManagedAce({**settings,'lm_device':'auto'})
        cpu=managed_engine.ManagedAce({**settings,'lm_device':'cpu'})
        self.assertEqual(automatic.delegate.lm_base,'http://127.0.0.1:8087')
        self.assertEqual(cpu.delegate.lm_base,'http://127.0.0.1:8088')
        self.assertEqual(cpu.delegate.base,'http://127.0.0.1:8087')
        args=cpu.server_arguments();self.assertEqual(args[args.index('--vae-chunk')+1],'256')

class Ownership(unittest.IsolatedAsyncioTestCase):
    def engine(self):
        return managed_engine.ManagedAce({**db.get_settings(),'lm_device':'cpu'})
    async def test_cpu_environment_is_child_local(self):
        engine=self.engine()
        with patch.dict(os.environ,{'GGML_BACKEND':'CUDA0'}),patch.object(managed_engine.asyncio,'create_subprocess_exec',new_callable=AsyncMock) as spawn:
            await engine._start_owned(8088,cpu=True)
            await engine._start_owned(8087)
            self.assertEqual(spawn.call_args_list[0].kwargs['env']['GGML_BACKEND'],'CPU')
            self.assertEqual(spawn.call_args_list[0].args[-2:],('--device','CPU'))
            self.assertNotIn('--device',spawn.call_args_list[1].args)
            self.assertEqual(spawn.call_args_list[1].kwargs['env']['GGML_BACKEND'],'CUDA0')
            self.assertEqual(os.environ['GGML_BACKEND'],'CUDA0')
    async def test_foreign_cpu_port_is_not_touched(self):
        engine=self.engine();writer=Mock(wait_closed=AsyncMock())
        async def connect(host,port):
            if port==8087:raise OSError()
            return Mock(),writer
        with patch.object(managed_engine.asyncio,'open_connection',side_effect=connect),patch.object(engine,'_start_owned',new_callable=AsyncMock) as spawn,patch.object(engine,'cancel',new_callable=AsyncMock) as cancel:
            with self.assertRaisesRegex(EngineError,'8088'):
                await engine._operate(AsyncMock(),AsyncMock())
        spawn.assert_not_called();cancel.assert_not_called();writer.close.assert_called_once()
    async def test_two_owned_servers_are_released_after_success_and_failure(self):
        for failure in (False,True):
            engine=self.engine();cpu=SimpleNamespace(returncode=None);synth=SimpleNamespace(returncode=None)
            operation=AsyncMock(side_effect=EngineError('fixture') if failure else None,return_value='done')
            with patch.object(managed_engine.asyncio,'open_connection',side_effect=OSError()),patch.object(engine,'_start_owned',new_callable=AsyncMock,side_effect=[cpu,synth]),patch.object(engine.delegate,'health',new_callable=AsyncMock),patch.object(engine,'_stop_owned',new_callable=AsyncMock) as stop:
                if failure:
                    with self.assertRaises(EngineError):await engine._operate(operation,AsyncMock())
                else:self.assertEqual(await engine._operate(operation,AsyncMock()),'done')
            self.assertEqual([call.args[0] for call in stop.call_args_list],[cpu,synth])
    async def test_partial_start_failure_releases_cpu_server(self):
        engine=self.engine();cpu=SimpleNamespace(returncode=None)
        with patch.object(managed_engine.asyncio,'open_connection',side_effect=OSError()),patch.object(engine,'_start_owned',new_callable=AsyncMock,side_effect=[cpu,OSError('fixture')]),patch.object(engine,'_stop_owned',new_callable=AsyncMock) as stop:
            with self.assertRaises(OSError):await engine._operate(AsyncMock(),AsyncMock())
        self.assertIs(stop.call_args_list[0].args[0],cpu)
    async def test_shutdown_targets_only_owned_process_handles(self):
        engine=self.engine()
        engine.lm_process=Mock(pid=123,returncode=None,wait=AsyncMock())
        engine.process=Mock(pid=456,returncode=None,wait=AsyncMock())
        killer=Mock(wait=AsyncMock())
        with patch.object(managed_engine.asyncio,'create_subprocess_exec',new_callable=AsyncMock,return_value=killer) as spawn:
            await engine.cancel()
        self.assertEqual([c.args[2] for c in spawn.call_args_list],['123','456'])
        self.assertTrue(all(c.args[0]=='taskkill' for c in spawn.call_args_list))
    async def test_cancelled_operation_still_releases_both_servers(self):
        engine=self.engine();process=SimpleNamespace(returncode=None)
        with patch.object(managed_engine.asyncio,'open_connection',side_effect=OSError()),patch.object(engine,'_start_owned',new_callable=AsyncMock,return_value=process),patch.object(engine.delegate,'health',new_callable=AsyncMock),patch.object(engine,'_stop_owned',new_callable=AsyncMock) as stop:
            with self.assertRaises(asyncio.CancelledError):
                await engine._operate(AsyncMock(side_effect=asyncio.CancelledError),AsyncMock())
        self.assertEqual(stop.await_count,2)

if __name__=='__main__':unittest.main(verbosity=2)
