"""Install this project and its Spicetify bridge, preserving previous files."""
import datetime
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys


def install(source):
    executable = shutil.which("spicetify")
    if not executable:
        raise RuntimeError("Spicetify não encontrado no PATH. Abra um terminal onde spicetify funciona.")
    required = ("lyrics.py", "spicy_bridge.py", "slyrics-bridge.js")
    payloads = {name: (source / name).read_text(encoding="utf-8") for name in required}
    for name in ("lyrics.py", "spicy_bridge.py"):
        compile(payloads[name], name, "exec")
    config_path = Path(subprocess.check_output([executable, "-c"], text=True).strip()).expanduser()
    if not config_path.is_file():
        raise RuntimeError("Não consegui localizar o config.ini do Spicetify.")
    target = Path.home() / ".local/share/spotify-live-lyrics"
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = target / "backup" / ("before-spicy-" + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(config_path, backup / "spicetify-config.ini")
    extension = config_path.parent / "Extensions" / "slyrics-bridge.js"
    extension.parent.mkdir(parents=True, exist_ok=True)
    if extension.exists():
        shutil.copy2(extension, backup / "installed-slyrics-bridge.js")
    config = target / "bridge-config.json"
    token = None
    if config.exists():
        shutil.copy2(config, backup / config.name)
        try:
            token = json.loads(config.read_text()).get("token")
        except (ValueError, AttributeError):
            pass
    if not isinstance(token, str) or len(token) < 32:
        token = secrets.token_hex(32)
    for name, text in payloads.items():
        destination = target / name
        if destination.exists():
            shutil.copy2(destination, backup / name)
        destination.write_text(text, encoding="utf-8")
    fd = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as file:
        json.dump({"token": token}, file)
    config.chmod(0o600)
    bridge = payloads["slyrics-bridge.js"].replace('"__SLYRICS_LOCAL_TOKEN__"', json.dumps(token))
    extension.write_text(bridge, encoding="utf-8")
    extension.chmod(0o600)
    print("Arquivos instalados. Backup:", backup)
    subprocess.run([executable, "config", "extensions", "slyrics-bridge.js"], check=True)
    subprocess.run([executable, "apply"], check=True)
    print("Pronto. Abra a letra no Spicy Lyrics e execute slyrics.")


if __name__ == "__main__":
    try:
        install(Path(__file__).resolve().parent)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print("Instalação não concluída:", error)
        sys.exit(1)
