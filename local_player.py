"""Optional local audio beta, isolated mpv process with a private JSON IPC socket."""
import json
import math
from pathlib import Path
import queue
import shutil
import socket
import subprocess
import tempfile
import threading
import time

AUDIO = {'.mp3', '.flac', '.ogg', '.opus', '.wav', '.m4a', '.aac', '.wma', '.aiff'}


def collect_files(paths):
    files = []
    for value in paths:
        path = Path(value).expanduser().resolve()
        if path.is_dir():
            files.extend(sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in AUDIO))
        elif path.is_file() and path.suffix.lower() in AUDIO:
            files.append(path)
        else:
            raise ValueError('Arquivo de áudio ou pasta não encontrado: '+str(path))
        if len(files) > 1000:
            raise ValueError('A fila beta aceita até 1000 arquivos por sessão.')
    if not files:
        raise ValueError('Nenhum arquivo de áudio encontrado.')
    return files


class LocalPlayer:
    def __init__(self, files):
        executable = shutil.which('mpv')
        if not executable:
            raise ValueError('O modo local beta requer mpv. No Arch/CachyOS: sudo pacman -S mpv')
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.data = None
        self.entries = []
        self.actions = queue.Queue(maxsize=16)
        self.error = ''
        self.serial = 0
        self.request_id = 0
        self.temp = tempfile.TemporaryDirectory(prefix='sylrics-mpv-')
        self.socket_path = str(Path(self.temp.name)/'ipc')
        try:
            self.proc = subprocess.Popen([executable, '--no-config', '--no-video', '--no-terminal',
                '--idle=yes', '--input-default-bindings=no', '--input-ipc-server='+self.socket_path,
                '--', *(str(p) for p in files)], stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            self.temp.cleanup()
            raise
        self.thread = threading.Thread(target=self.work, daemon=True)
        self.thread.start()

    def request(self, command):
        self.request_id += 1
        self.sock.sendall((json.dumps({'command':command,'request_id':self.request_id})+'\n').encode())
        while not self.stop.is_set():
            raw = self.reader.readline(1024*1024)
            if not raw:
                raise OSError('mpv desconectado')
            reply = json.loads(raw)
            if reply.get('request_id') == self.request_id:
                return reply.get('data') if reply.get('error') == 'success' else None

    def enqueue(self, action):
        try:
            self.actions.put_nowait(action)
            return True
        except queue.Full:
            return False

    def control(self, action):
        commands = {'play-pause':['cycle','pause'], 'next':['playlist-next','weak'],
                    'previous':['playlist-prev','weak']}
        return self.enqueue(('command',commands[action])) if action in commands else False

    def seek(self, position, uri, player=None):
        if not math.isfinite(position) or position < 0:
            return False
        return self.enqueue(('seek',(uri,position)))

    def queue_action(self, entry_id, action):
        return self.enqueue(('queue',(entry_id,action))) if action in ('play','up','down') else False

    def snapshot(self):
        with self.lock:
            return dict(self.data) if self.data else None

    def playlist(self):
        with self.lock:
            return [dict(entry) for entry in self.entries]

    def apply_action(self, kind, value):
        if kind == 'command':
            self.request(value)
        elif kind == 'seek':
            uri,position = value
            path = self.request(['get_property','path'])
            if path and Path(path).as_uri() == uri:
                self.request(['seek',position,'absolute+exact'])
                self.serial += 1
        elif kind == 'queue':
            entry_id,action = value
            entries = self.request(['get_property','playlist']) or []
            index = next((i for i,e in enumerate(entries) if e.get('id') == entry_id),None)
            if index is None:
                return
            if action == 'play':
                self.request(['set_property','playlist-pos',index])
                self.request(['set_property','pause',False])
            elif action == 'up' and index > 0:
                self.request(['playlist-move',index,index-1])
            elif action == 'down' and index+1 < len(entries):
                # mpv inserts before the target entry (not at a final index).
                self.request(['playlist-move',index,index+2])

    def work(self):
        self.sock = None
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.settimeout(.5)
            deadline = time.monotonic()+5
            while not self.stop.is_set():
                try:
                    self.sock.connect(self.socket_path)
                    break
                except (FileNotFoundError, ConnectionRefusedError):
                    if self.proc.poll() is not None or time.monotonic() >= deadline:
                        raise OSError('Não foi possível iniciar o mpv')
                    self.stop.wait(.05)
            self.reader = self.sock.makefile('rb')
            try:
                while not self.stop.is_set():
                    for _ in range(16):
                        try:
                            kind,value = self.actions.get_nowait()
                        except queue.Empty:
                            break
                        self.apply_action(kind,value)
                    entries = self.request(['get_property','playlist']) or []
                    path = self.request(['get_property','path'])
                    metadata = self.request(['get_property','metadata']) or {}
                    position = self.request(['get_property','time-pos'])
                    measured = time.monotonic()
                    duration = self.request(['get_property','duration']) or 0
                    paused = self.request(['get_property','pause'])
                    idle = self.request(['get_property','idle-active'])
                    end_path = self.request(['get_property','path'])
                    data = None
                    if path and path == end_path and position is not None:
                        file = Path(path)
                        meta = {str(k).lower():v for k,v in metadata.items()}
                        art = next((p for name in ('cover.jpg','cover.png','folder.jpg','folder.png')
                                    if (p:=file.parent/name).is_file()),None)
                        data = dict(uri=file.as_uri(),artist=meta.get('artist',''),
                            title=meta.get('title',file.stem),album=meta.get('album',''),
                            art_url=art.as_uri() if art else '',position=float(position),
                            duration=float(duration),playing=not paused and not idle,
                            measured_at=measured,player='local-beta',seek_serial=self.serial,
                            local_path=str(file))
                    with self.lock:
                        if data is None and idle and self.data:
                            data=dict(self.data,playing=False,position=self.data['duration'],measured_at=measured)
                        self.data,self.entries = data,entries
                    self.error = 'Nenhuma faixa disponível · verifique os arquivos de áudio' if idle and data is None else ''
                    self.stop.wait(.1)
            finally:
                self.reader.close()
        except (OSError, ValueError, TypeError) as error:
            if not self.stop.is_set():
                self.error = 'Player local indisponível: '+str(error)
                with self.lock:
                    self.data = None
        finally:
            if self.sock:
                self.sock.close()

    def close(self):
        self.stop.set()
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=2)
        self.thread.join(timeout=2)
        self.temp.cleanup()
