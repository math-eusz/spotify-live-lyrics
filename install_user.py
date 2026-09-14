"""Local installation without root. Called by install.sh, not downloaded alone."""
import datetime
import os
from pathlib import Path
import shutil
import sys

RUNTIME=('lrc_store.py','app.py','cli.py','lyrics.py','spicy_bridge.py','terminal_ui.py','preferences.py',
         'paging.py','sources.py','visualizer.py','bridge_runtime.py','install_bridge.py',
         'slyrics-bridge.js','ui.ini')


def install(root=None):
    root=Path(root) if root else Path(__file__).resolve().parent
    home=Path.home()
    target=home/'.local/share/spotify-live-lyrics'
    timestamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup=target/'backup'/('before-0.6.4-'+timestamp)
    # Validate all files before touching the installed version.
    payload={name:(root/name).read_bytes() for name in RUNTIME}
    for name,content in payload.items():
        if name.endswith('.py'):
            compile(content,name,'exec')
    backup.mkdir(parents=True)
    for name,content in payload.items():
        dest=target/name
        if dest.exists():
            shutil.copy2(dest,backup/name)
        tmp=dest.with_suffix(dest.suffix+'.new')
        tmp.write_bytes(content)
        os.replace(tmp,dest)
    binaries=home/'.local/bin'
    binaries.mkdir(parents=True,exist_ok=True)
    launcher='#!/usr/bin/env python3\nimport sys\nsys.path.insert(0, '+repr(str(target))+')\nfrom cli import main\nraise SystemExit(main())\n'
    for name in ('sylrics','slyrics'):
        dest=binaries/name
        if dest.exists() or dest.is_symlink():
            shutil.copy2(dest,backup/('command-'+name))
            dest.unlink()
        dest.write_text(launcher)
        dest.chmod(0o755)
    sys.path.insert(0,str(target))
    from preferences import ensure
    config=ensure()
    # Fish's conventional user-bin path, without modifying the user's own config.fish.
    fish=home/'.config/fish'
    if fish.is_dir():
        conf=fish/'conf.d/90-sylrics-path.fish'
        conf.parent.mkdir(parents=True,exist_ok=True)
        if conf.exists():
            shutil.copy2(conf,backup/conf.name)
        conf.write_text('if test -d "$HOME/.local/bin"\n    fish_add_path "$HOME/.local/bin"\nend\n')
    completion=home/'.config/fish/completions/sylrics.fish'
    completion.parent.mkdir(parents=True,exist_ok=True)
    if completion.exists():
        shutil.copy2(completion,backup/'sylrics-completion.fish')
    shutil.copy2(root/'completions/sylrics.fish',completion)
    print('sylrics 0.6.4 instalado. Backup: '+str(backup))
    print('Configuração: '+str(config))
    print('Abra um novo terminal e execute: sylrics')
    if str(binaries) not in os.environ.get('PATH','').split(os.pathsep):
        print('Neste terminal, execute: '+str(binaries/'sylrics'))
        print('Em bash/zsh, adicione ~/.local/bin ao PATH se necessário.')


if __name__=='__main__':
    try:
        install()
    except (OSError,ValueError) as error:
        print('Instalação não concluída: '+str(error),file=sys.stderr)
        raise SystemExit(1)
