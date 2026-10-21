"""Upstream retrieval retries, settings validation and fork ownership in isolated data."""
import asyncio
import json
import os
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx

ROOT = Path(__file__).resolve().parent.parent
os.environ['MUSIC_GENERATOR_DATA'] = str(ROOT/'data/validation'/('upstream-20261020-'+uuid.uuid4().hex[:8]))
sys.path.insert(0, str(ROOT))
from app import db, engines, main
from app.messages import LANGS, tr
from fastapi.testclient import TestClient

db.init()
client = TestClient(main.app, base_url='http://localhost', raise_server_exceptions=False)


class Settings(unittest.TestCase):
    def test_invalid_numbers_rejected_without_saving(self):
        for key in ('timeout_minutes', 'poll_interval'):
            for value in ('text', '', 'nan', 'inf', '-inf', 0, -1, True, False, None, [], {}):
                with self.subTest(key=key, value=value):
                    before = db.get_settings()
                    result = client.put('/api/settings', json={key:value})
                    self.assertEqual(result.status_code, 422, result.text)
                    self.assertEqual(db.get_settings(), before)

    def test_number_errors_are_translated(self):
        for lang in LANGS:
            result = client.put('/api/settings', json={'poll_interval':'invalid'}, headers={'X-Lang':lang})
            self.assertEqual(result.status_code, 422)
            self.assertEqual(result.json()['detail'], tr(lang, 'bad_number', field='poll_interval'))

    def test_numeric_strings_are_saved_as_numbers(self):
        result = client.put('/api/settings', json={'timeout_minutes':'45.0', 'poll_interval':'0.75'})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(db.get_settings()['timeout_minutes'], 45)
        self.assertEqual(db.get_settings()['poll_interval'], .75)

    def test_invalid_sound_model_stays_strict(self):
        before = db.get_settings()
        for value in ('unknown', [], None):
            result = client.put('/api/settings', json={'dit':value})
            self.assertEqual(result.status_code, 422)
        self.assertEqual(db.get_settings(), before)

    def test_windows_shutdown_uses_fork_owned_process_control(self):
        with patch.object(main.subprocess, 'Popen') as popen:
            result = client.post('/api/shutdown', headers={'X-Lang':'de'})
        self.assertEqual(result.status_code, 200)
        command = popen.call_args.args[0]
        self.assertIn('scripts', command[-1])
        self.assertIn('fork-control.ps1', command[-1])
        self.assertIn('-Action Stop', command[-1])


class Retrieval(unittest.IsolatedAsyncioTestCase):
    async def test_complete_song_survives_poll_and_result_disconnects_without_resubmission(self):
        requests, failed = [], set()
        def transport(request):
            requests.append(request)
            if request.method == 'POST':
                return httpx.Response(200, json={'id':request.url.path[1:]})
            job = request.url.params['id']
            key = (job, request.url.params.get('result'))
            if key not in failed:
                failed.add(key)
                raise httpx.ReadError('temporary disconnect', request=request)
            if not key[1]:
                return httpx.Response(200, json={'status':'done'})
            if job == 'lm':
                return httpx.Response(200, json={'audio_codes':'1,2,3'})
            return httpx.Response(200, content=b'finished audio', headers={'Content-Type':'audio/wav'})
        original = httpx.AsyncClient
        async def progress(message): pass
        with patch.object(engines.httpx, 'AsyncClient', side_effect=lambda **kw:original(transport=httpx.MockTransport(transport), **kw)) as factory, patch.object(engines.asyncio, 'sleep', new_callable=AsyncMock):
            audio, extension, metadata = await engines.AceStepCpp('http://localhost', dit='xl').generate({'caption':'Warm'}, progress)
        self.assertEqual(audio, b'finished audio')
        self.assertEqual(extension, 'wav')
        posts = [r for r in requests if r.method == 'POST']
        self.assertEqual([r.url.path for r in posts], ['/lm', '/synth'])
        self.assertTrue(all(json.loads(r.content)['synth_model'] == engines.DIT_MODELS['xl'] for r in posts))
        self.assertEqual(factory.call_count, 5)

    async def test_persistent_disconnect_is_bounded(self):
        c = Mock(get=AsyncMock(side_effect=httpx.ReadError('lost')))
        fresh = Mock(get=AsyncMock(side_effect=httpx.ReadError('lost')))
        manager = Mock(__aenter__=AsyncMock(return_value=fresh), __aexit__=AsyncMock(return_value=False))
        with patch.object(engines.httpx, 'AsyncClient', return_value=manager) as factory, patch.object(engines.asyncio, 'sleep', new_callable=AsyncMock):
            with self.assertRaisesRegex(engines.EngineError, 'ReadError'):
                await engines._get_retry(c, 'http://localhost', {'id':'existing', 'result':1})
        self.assertEqual(c.get.await_count, 1)
        self.assertEqual(fresh.get.await_count, 3)
        self.assertEqual(factory.call_count, 3)

    async def test_http_rejection_is_not_retried(self):
        response = httpx.Response(400, request=httpx.Request('GET', 'http://localhost/job'))
        c = Mock(get=AsyncMock(return_value=response))
        with patch.object(engines.httpx, 'AsyncClient') as factory:
            self.assertIs(await engines._get_retry(c, 'http://localhost', {'id':'existing'}), response)
        factory.assert_not_called()

    async def test_cancellation_is_not_swallowed(self):
        c = Mock(get=AsyncMock(side_effect=asyncio.CancelledError))
        with patch.object(engines.httpx, 'AsyncClient') as factory:
            with self.assertRaises(asyncio.CancelledError):
                await engines._get_retry(c, 'http://localhost', {'id':'existing'})
        factory.assert_not_called()


if __name__ == '__main__': unittest.main(verbosity=2)
