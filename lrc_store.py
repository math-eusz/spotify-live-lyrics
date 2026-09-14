"""Bounded plain-LRC storage owned by sylrics, with serialized maintenance."""
from contextlib import contextmanager
import fcntl
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile

LIMIT = 10
MAX_BYTES = 1_000_000

def default_directory():
    return Path.home() / '.local/share/spotify-live-lyrics/lrc'

def synchronized(raw):
    return bool(re.search(r'(?m)^\[\d+:\d+(?:\.\d+)?\]', raw))

class LrcStore:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else default_directory()

    @contextmanager
    def locked(self):
        if self.directory.is_symlink():
            raise OSError('A pasta de letras não pode ser um link simbólico.')
        self.directory.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.directory / '.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def files(self):
        entries = []
        for path in self.directory.glob('*.lrc'):
            try:
                info = path.lstat()
                if stat.S_ISREG(info.st_mode):
                    entries.append((info.st_mtime_ns, path.name, path))
            except FileNotFoundError:
                pass
        return [item[2] for item in sorted(entries)]

    def prune(self):
        removed = 0
        for path in self.files()[:-LIMIT]:
            path.unlink(missing_ok=True)
            removed += 1
        return removed

    def maintain(self, import_from=None):
        with self.locked():
            if import_from is not None:
                source = Path(import_from)
                for path in source.glob('*.lrc'):
                    # Only top-level, regular synchronized lyric files, never symlinks.
                    info = path.lstat()
                    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                        continue
                    try:
                        raw = path.read_text(encoding='utf-8-sig')
                    except (UnicodeError, OSError):
                        continue
                    if not synchronized(raw):
                        continue
                    dest = self.directory / path.name
                    if dest == path:
                        continue
                    if dest.exists() or dest.is_symlink():
                        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
                        dest = self.directory / (path.stem[:100] + '-' + digest + '.lrc')
                        if dest.exists() or dest.is_symlink():
                            # Preserve any unresolved collision in the source folder.
                            continue
                    # Preserve modification time and never overwrite a destination.
                    with dest.open('xb') as output:
                        output.write(raw.encode('utf-8'))
                    os.utime(dest, ns=(info.st_atime_ns, info.st_mtime_ns))
                    path.unlink()
            return self.prune()

    def path(self, key):
        if not re.fullmatch(r'[a-f0-9]{64}', key):
            raise ValueError('Invalid lyric cache key')
        return self.directory / (key + '.lrc')

    def read(self, key):
        with self.locked():
            path = self.path(key)
            try:
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                    return ''
                return path.read_text(encoding='utf-8')
            except (FileNotFoundError, UnicodeError):
                return ''

    def save(self, key, raw):
        if not synchronized(raw) or len(raw.encode('utf-8')) > MAX_BYTES:
            return
        with self.locked():
            path = self.path(key)
            fd, name = tempfile.mkstemp(prefix='.lrc-', dir=self.directory)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                    stream.write(raw)
                os.replace(name, path)
                self.prune()
            finally:
                Path(name).unlink(missing_ok=True)

    def clear(self):
        with self.locked():
            files = self.files()
            for path in files:
                path.unlink(missing_ok=True)
            return len(files)
