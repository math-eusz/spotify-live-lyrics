"""Build reproducible source and AUR recipe archives from an exact Git snapshot."""
import gzip
import hashlib
import io
import re
import subprocess
import tarfile


def archive_files(files,prefix=''):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w',format=tarfile.USTAR_FORMAT) as tar:
        for name,content in sorted(files.items()):
            info=tarfile.TarInfo(prefix+name)
            info.size=len(content)
            info.mode=0o644
            info.mtime=0
            tar.addfile(info,io.BytesIO(content))
    return gzip.compress(stream.getvalue(),mtime=0)


def build(root,commit,version):
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):
        raise ValueError('Invalid release version')
    source=subprocess.check_output(['git','archive','--format=tar',f'--prefix=sylrics-{version}/',commit],cwd=root)
    source=gzip.compress(source,mtime=0)
    checksum=hashlib.sha256(source).hexdigest()
    files={}
    for src,dest in [('PKGBUILD.in','PKGBUILD'),('SRCINFO.in','.SRCINFO')]:
        content=subprocess.check_output(['git','show',f'{commit}:packaging/aur/{src}'],cwd=root).decode()
        files[dest]=content.replace('@SOURCE_SHA256@',checksum).encode()
    files['README.txt']=(
        'AUR submission bundle for sylrics '+version+'\n\n'
        'Not submitted to the AUR automatically. Publicly accessible release sources\n'
        'and an AUR maintainer account with SSH authentication are required.\n'
        'For a local build, put the matching sylrics-'+version+'.tar.gz beside PKGBUILD,\n'
        'review the recipe, then run makepkg -si as a normal user on Arch/CachyOS.\n'
        'Do not upload this recipe until the source URL works without authentication.\n').encode()
    return {f'sylrics-{version}.tar.gz':source,
            f'sylrics-{version}-aur.tar.gz':archive_files(files)}
