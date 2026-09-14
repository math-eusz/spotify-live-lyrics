"""Optional loopback bridge lifecycle, separate from native playback."""
import json
import os
from pathlib import Path
import threading
from spicy_bridge import State, PORT, ThreadingHTTPServer, handler_for


def config_path():
    user = Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config'))) / 'spotify-live-lyrics/bridge-config.json'
    old = Path.home()/'.local/share/spotify-live-lyrics/bridge-config.json'
    return user if user.exists() else old


class Bridge:
    def __init__(self):
        self.state = State()
        self.server = None
        self.error = ''
        try:
            token = json.loads(config_path().read_text())['token']
            if not isinstance(token,str) or len(token)<32:
                raise ValueError('token')
            self.server = ThreadingHTTPServer(('127.0.0.1',PORT),handler_for(self.state,token))
            threading.Thread(target=self.server.serve_forever,daemon=True).start()
        except (OSError,ValueError,KeyError,TypeError):
            self.error = 'Ponte indisponível · sylrics bridge install para configurar'

    def snapshot(self):
        data,lines,mode,received = self.state.snapshot()
        if data is None or __import__('time').monotonic()-received>3:
            return None, [], mode
        return dict(data,measured_at=received),lines,mode

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
