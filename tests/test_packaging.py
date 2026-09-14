import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'releases'))
from artifacts import build


class Packaging(unittest.TestCase):
    def test_reproducible_archives_and_matching_recipe_checksum(self):
        def git(args,cwd):
            if args[1]=='archive':return b'fixture source snapshot'
            return (ROOT/'packaging/aur'/args[-1].split('/')[-1]).read_bytes()
        with patch('artifacts.subprocess.check_output',side_effect=git):
            first=build(ROOT,'a'*40,'0.6.0')
            second=build(ROOT,'a'*40,'0.6.0')
        self.assertEqual(first,second)
        checksum=hashlib.sha256(first['sylrics-0.6.0.tar.gz']).hexdigest()
        with tarfile.open(fileobj=io.BytesIO(first['sylrics-0.6.0-aur.tar.gz'])) as tar:
            for name in ('PKGBUILD','.SRCINFO'):
                content=tar.extractfile(name).read().decode()
                self.assertIn(checksum,content)
                self.assertNotIn('@SOURCE_SHA256@',content)

    def test_pkgbuild_stages_commands_modules_license_and_completions(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'src').mkdir()
            (root/'src/sylrics-0.6.0').symlink_to(ROOT,target_is_directory=True)
            recipe=root/'PKGBUILD'
            recipe.write_text((ROOT/'packaging/aur/PKGBUILD.in').read_text().replace('@SOURCE_SHA256@','0'*64))
            environment=dict(os.environ,srcdir=str(root/'src'),pkgdir=str(root/'pkg'))
            subprocess.run(['bash','-c','source "$1"; package','package-test',str(recipe)],
                           env=environment,check=True,capture_output=True)
            package=root/'pkg'
            self.assertTrue(os.access(package/'usr/bin/sylrics',os.X_OK))
            self.assertEqual((package/'usr/bin/slyrics').readlink(),Path('sylrics'))
            for name in ('cli.py','sources.py','visualizer.py','paging.py','terminal_ui.py'):
                self.assertEqual((package/'usr/lib/sylrics'/name).read_bytes(),(ROOT/name).read_bytes())
            self.assertTrue((package/'usr/share/licenses/sylrics/LICENSE').is_file())
            self.assertTrue((package/'usr/share/fish/vendor_completions.d/sylrics.fish').is_file())
            self.assertTrue((package/'usr/share/bash-completion/completions/sylrics').is_file())
