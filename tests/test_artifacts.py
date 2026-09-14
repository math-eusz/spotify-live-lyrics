import gzip
import io
from pathlib import Path
import sys
import tarfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'releases'))
from artifacts import build


class SourceArchive(unittest.TestCase):
    def test_archive_is_reproducible_and_preserves_installer_mode(self):
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w') as tar:
            info=tarfile.TarInfo('sylrics-0.6.0/install.sh')
            content=b'#!/bin/sh\n'
            info.size=len(content);info.mode=0o755
            tar.addfile(info,io.BytesIO(content))
        with patch('artifacts.subprocess.check_output',return_value=buffer.getvalue()):
            first=build(Path('.'),'a'*40,'0.6.0')
            second=build(Path('.'),'a'*40,'0.6.0')
        self.assertEqual(first,second)
        self.assertEqual(list(first),['sylrics-0.6.0.tar.gz'])
        with tarfile.open(fileobj=io.BytesIO(first['sylrics-0.6.0.tar.gz'])) as tar:
            self.assertEqual(tar.getmember('sylrics-0.6.0/install.sh').mode,0o755)
