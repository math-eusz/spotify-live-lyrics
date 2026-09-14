"""Build a reproducible source archive from an exact Git snapshot."""
import gzip
import re
import subprocess


def build(root,commit,version):
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):
        raise ValueError('Invalid release version')
    source=subprocess.check_output(['git','archive','--format=tar',
                                    f'--prefix=sylrics-{version}/',commit],cwd=root)
    return {f'sylrics-{version}.tar.gz':gzip.compress(source,mtime=0)}
