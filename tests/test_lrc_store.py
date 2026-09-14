import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from lrc_store import LrcStore
from lyrics import command

def key(i):
    return hashlib.sha256(str(i).encode()).hexdigest()

class LrcStorage(unittest.TestCase):
    def test_startup_keeps_ten_newest_and_ignores_other_files(self):
        with tempfile.TemporaryDirectory() as td:
            store=LrcStore(Path(td)/'lrc')
            store.directory.mkdir()
            for i in range(15):
                p=store.directory/f'{i:02}.lrc'
                p.write_text('[00:01]Test')
                os.utime(p,ns=(i+1,i+1))
            extra=store.directory/'keep.txt';extra.write_text('keep')
            nested=store.directory/'sub';nested.mkdir()
            (nested/'keep.lrc').write_text('keep')
            self.assertEqual(store.maintain(),5)
            self.assertEqual([p.name for p in store.files()],[f'{i:02}.lrc' for i in range(5,15)])
            self.assertTrue(extra.exists())
            self.assertTrue((nested/'keep.lrc').exists())

    def test_save_always_bounds_count_and_read_does_not_refresh_age(self):
        with tempfile.TemporaryDirectory() as td:
            store=LrcStore(td)
            for i in range(12):
                store.save(key(i),'[00:01]Test '+str(i))
                self.assertLessEqual(len(store.files()),10)
            oldest=store.files()[0]
            before=oldest.stat().st_mtime_ns
            self.assertTrue(store.read(oldest.stem))
            self.assertEqual(oldest.stat().st_mtime_ns,before)
            self.assertEqual(store.clear(),10)
            self.assertEqual(store.files(),[])

    def test_import_moves_valid_home_lyrics_preserving_mtime(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)/'home';home.mkdir()
            store=LrcStore(home/'program/lrc')
            for i in range(12):
                p=home/f'Track {i}.lrc';p.write_text('[00:01]Test')
                os.utime(p,ns=(i+1,i+1))
            untouched=home/'notes.lrc';untouched.write_text('Not synchronized lyrics')
            store.maintain(import_from=home)
            self.assertEqual(len(store.files()),10)
            self.assertEqual([p.name for p in home.glob('*.lrc')],['notes.lrc'])
            self.assertEqual([p.stat().st_mtime_ns for p in store.files()],list(range(3,13)))

    def test_import_collision_and_links_do_not_overwrite_or_follow(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);home=root/'home';home.mkdir()
            store=LrcStore(root/'program');store.directory.mkdir()
            existing=store.directory/'Song.lrc';existing.write_text('[00:01]Existing')
            (home/'Song.lrc').write_text('[00:02]Different')
            external=root/'external.lrc';external.write_text('[00:03]Outside')
            (home/'link.lrc').symlink_to(external)
            (store.directory/'link.lrc').symlink_to(external)
            store.maintain(import_from=home)
            self.assertEqual(existing.read_text(),'[00:01]Existing')
            self.assertEqual(len(store.files()),2)
            self.assertTrue(external.exists())
            self.assertTrue((home/'link.lrc').is_symlink())
            store.clear()
            self.assertTrue(external.exists())

    def test_lookup_files_are_temporary_even_on_failure(self):
        for fail in (False,True):
            folders=[]
            def lookup(args,**kwargs):
                folder=Path(kwargs['cwd']);folders.append(folder)
                (folder/'automatic.lrc').write_text('[00:01]Test')
                if fail:raise subprocess.TimeoutExpired(args,1)
                return '[00:01]Test'
            with patch('lyrics.subprocess.check_output',side_effect=lookup):
                result=command(['syncedlyrics','--synced-only','Artist - Track'])
            self.assertEqual(result,'' if fail else '[00:01]Test')
            self.assertFalse(folders[0].exists())

    def test_malicious_cache_key_cannot_escape(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                LrcStore(td).save('../outside','[00:01]Test')
