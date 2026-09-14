"""Opt-in Spicetify integration. Never invoked by normal package installation."""
import datetime
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess


def install():
    executable=shutil.which('spicetify')
    if not executable:
        raise ValueError('Instale Spicetify e Spicy Lyrics antes de configurar a ponte opcional.')
    source=Path(__file__).resolve().parent/'slyrics-bridge.js'
    config=Path(subprocess.check_output([executable,'-c'],text=True).strip()).expanduser()
    if not config.is_file():
        raise ValueError('Configuração do Spicetify não encontrada.')
    user=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'spotify-live-lyrics'
    user.mkdir(parents=True,exist_ok=True)
    backup=user/'backup'/('bridge-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True)
    shutil.copy2(config,backup/'spicetify-config.ini')
    target=config.parent/'Extensions/slyrics-bridge.js'
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        shutil.copy2(target,backup/target.name)
    bridge_config=user/'bridge-config.json'
    token=secrets.token_hex(32)
    if bridge_config.exists():
        shutil.copy2(bridge_config,backup/bridge_config.name)
    descriptor=os.open(bridge_config,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(descriptor,'w') as file:
        json.dump({'token':token},file)
    bridge_config.chmod(0o600)
    target.write_text(source.read_text().replace('"__SLYRICS_LOCAL_TOKEN__"',json.dumps(token)))
    target.chmod(0o600)
    subprocess.run([executable,'config','extensions','slyrics-bridge.js'],check=True)
    subprocess.run([executable,'apply'],check=True)
    print('Ponte instalada. Reinicie sylrics com --source auto ou --source spicy.')
