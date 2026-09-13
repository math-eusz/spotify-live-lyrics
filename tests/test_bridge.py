import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import spicy_bridge as bridge
import install


def syllable(text, start, end, part=False):
    return {'Text': text, 'StartTime': start, 'EndTime': end, 'IsPartOfWord': part}


def vocal(parts):
    return {'Type': 'Vocal', 'Lead': {'Syllables': parts}}


class Timing(unittest.TestCase):
    def test_real_syllable_times_intro_and_gap(self):
        payload = {'Type': 'Syllable', 'Content': [vocal([
            syllable('hel', 30, 30.3, True), syllable('lo', 30.3, 30.5),
            syllable('world', 32, 32.5)])]}
        lines, mode = bridge.timeline(payload)
        self.assertEqual(mode, 'syllable')
        self.assertEqual(lines[0]['text'], 'hello world')
        self.assertEqual(bridge.render(lines, 29.99), '♪ Instrumental...')
        self.assertEqual(bridge.render(lines, 31), 'hello █')
        self.assertEqual(bridge.render(lines, 32.5), 'hello world')

    def test_fourth_holds_until_fifth_not_preview_time(self):
        payload = {'Type': 'Line', 'Content': [
            {'Type': 'Vocal', 'Text': str(i), 'StartTime': 10+i*3, 'EndTime': 11+i*3}
            for i in range(5)]}
        lines, mode = bridge.timeline(payload)
        self.assertIn('3', bridge.render(lines, 21.99))
        self.assertNotIn('4', bridge.render(lines, 21.99))
        self.assertNotIn('3', bridge.render(lines, 22.1))
        self.assertNotIn('3', bridge.render(lines, 13.5))
        self.assertIn('\n\n', bridge.render(lines, 16.5))

    def test_fast_phrase_finishes_on_received_end(self):
        lines, _ = bridge.timeline({'Type': 'Syllable', 'Content': [vocal([
            syllable('rapid', 1, 1.12), syllable('delivery', 1.12, 1.25)])]})
        self.assertEqual(bridge.render(lines, 1.25), 'rapid delivery')

    def test_invalid_and_static(self):
        self.assertEqual(bridge.timeline({'Type': 'Static'})[1], 'static')
        with self.assertRaises(ValueError):
            bridge.timeline({'Type': 'Syllable', 'Content': [vocal([syllable('x', 2, 1)])]})
        self.assertEqual(bridge.clean('\x1bhello\n'), 'hello')

    def test_state_pause_and_song_change(self):
        state = bridge.State()
        data = {'version': 1, 'uri': 'spotify:track:a', 'position': 30, 'playing': False,
                'lyrics': {'Type': 'Line', 'Content': [{'Type': 'Vocal', 'Text': 'A',
                            'StartTime': 30, 'EndTime': 31}]}}
        state.update(data)
        self.assertFalse(state.snapshot()[0]['playing'])
        data.update(uri='spotify:track:b')
        del data['lyrics']
        state.update(data)
        self.assertEqual(state.snapshot()[1], [])
        data['lyrics'] = {'Type': 'Static', 'uri': 'spotify:track:a'}
        with self.assertRaises(ValueError): state.update(data)

    def test_installer_preserves_files_and_adds_extension(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            config = home/'spicetify/config.ini'
            config.parent.mkdir(); config.write_text('existing config')
            target = home/'.local/share/spotify-live-lyrics'
            target.mkdir(parents=True)
            (target/'lyrics.py').write_text('old code')
            with patch.object(Path, 'home', return_value=home), \
                 patch.object(install.shutil, 'which', return_value='/mock/spicetify'), \
                 patch.object(install.subprocess, 'check_output', return_value=str(config)), \
                 patch.object(install.subprocess, 'run') as run:
                install.install(ROOT)
            self.assertEqual(next((target/'backup').glob('*/lyrics.py')).read_text(), 'old code')
            self.assertEqual(config.read_text(), 'existing config')
            ext = (config.parent/'Extensions/slyrics-bridge.js').read_text()
            self.assertNotIn('__SLYRICS_LOCAL_TOKEN__', ext)
            self.assertEqual((target/'bridge-config.json').stat().st_mode & 0o777, 0o600)
            self.assertEqual(run.call_args_list[0].args[0][-2:], ['extensions', 'slyrics-bridge.js'])

    def test_node_to_real_python_server(self):
        state = bridge.State()
        token = 'test-key-not-a-credential'
        server = bridge.ThreadingHTTPServer(('127.0.0.1', 0), bridge.handler_for(state, token))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            code = (ROOT/'slyrics-bridge.js').read_text().replace('__SLYRICS_LOCAL_TOKEN__', token)
            code = code.replace(':43829/state', f':{server.server_port}/state')
            harness = r'''
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(0, 'utf8');
const nativeFetch = global.fetch;
global.location = {origin: 'https://xpui.app.spotify.com'};
global.Spicetify = {Player:{data:{item:{uri:'spotify:track:abc',name:'Test',metadata:{artist_name:'Artist'}}},getProgress:()=>30100,isPlaying:()=>false}};
global.caches = {keys:async()=>['unrelated','SpicyLyrics_LyricsStore_g1'],open:async(name)=>({match:async(url)=>{
 if(name !== 'SpicyLyrics_LyricsStore_g1' || url !== location.origin+'/abc') throw Error('wrong cache');
 return {json:async()=>({ExpiresAt:Date.now()+60000,Content:{Type:'Syllable',uri:'spotify:track:abc',Content:[{Type:'Vocal',Lead:{Syllables:[{Text:'hello',StartTime:30,EndTime:31}]}}]}})};
}})};
global.fetch = async(url, opts) => {
 const body=JSON.parse(opts.body);
 if('token' in body || body.position!==30.1 || body.playing!==false) throw Error('wrong data');
 opts.headers.Origin=location.origin;
 const response = await nativeFetch(url, opts);
 if(response.status !== 204) throw Error('HTTP '+response.status);
 global.__slyricsStop();
 return response;
};
vm.runInThisContext(source);
setTimeout(()=>process.exit(global.__slyricsStop ? 0:1),400);
'''
            subprocess.run(['node','-e',harness],input=code,text=True,check=True,timeout=5)
            self.assertEqual(state.snapshot()[0]['uri'], 'spotify:track:abc')
            self.assertEqual(state.snapshot()[1][0]['text'], 'hello')
            url=f'http://127.0.0.1:{server.server_port}/state'
            req=urllib.request.Request(url,data=b'{}',headers={'Origin':'https://xpui.app.spotify.com','X-Slyrics-Key':'wrong'})
            with self.assertRaises(urllib.error.HTTPError) as error: urllib.request.urlopen(req,timeout=2)
            self.assertEqual(error.exception.code,403)
            req=urllib.request.Request(url,method='OPTIONS',headers={'Origin':'https://xpui.app.spotify.com'})
            with urllib.request.urlopen(req,timeout=2) as response: self.assertEqual(response.status,204)
        finally:
            server.shutdown();server.server_close()


if __name__ == '__main__':
    unittest.main()
