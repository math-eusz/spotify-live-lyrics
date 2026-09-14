"""Shared validated configuration for file edits, CLI commands and migration."""
import configparser
import datetime
import io
import os
from pathlib import Path
import shutil
import tempfile
from terminal_ui import Settings, DEFAULTS, CONFIG_PATH

THEMES = {
    'warm': dict(text='#DEDAD0',muted='#88867F',accent='#C8BA91',border='#69675E',background='default'),
    'purple': dict(text='#DDD8F0',muted='#938AA8',accent='#BC9CFF',border='#695780',background='default'),
    'mono': dict(text='default',muted='#888888',accent='default',border='#666666',background='default'),
    'ocean': dict(text='#DAE6ED',muted='#819BA6',accent='#7AD9D2',border='#426973',background='default'),
}


def parser_for(path):
    parser=configparser.ConfigParser(interpolation=None)
    parser.read_dict(DEFAULTS)
    if Path(path).exists():
        with Path(path).open(encoding='utf-8') as stream:
            parser.read_file(stream)
    return parser


def write(parser,path,backup=True):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    out=io.StringIO()
    out.write('; sylrics 0.6.3 — salve para aplicar ao vivo. Ajuda: sylrics config list\n')
    parser.write(out)
    fd,name=tempfile.mkstemp(prefix='.ui-',suffix='.ini',dir=path.parent)
    temp=Path(name)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            stream.write(out.getvalue())
        check=Settings(temp)
        check.reload()
        if check.error:
            raise ValueError('Valor inválido; configuração original preservada.')
        if backup and path.exists():
            folder=path.parent/'backup'
            folder.mkdir(exist_ok=True)
            stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            shutil.copy2(path,folder/f'ui-{stamp}.ini')
            for old in sorted(folder.glob('ui-*.ini'))[:-20]:
                old.unlink()
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)


def ensure(path=CONFIG_PATH):
    path=Path(path)
    if not path.exists():
        write(parser_for(path),path,backup=False)
    else:
        existing=configparser.ConfigParser(interpolation=None)
        existing.read(path,encoding='utf-8')
        if not existing.has_section('playback'):
            merged=parser_for(path)
            merged['layout']['show_source']='false'
            write(merged,path)
    return path


def set_value(path,key,value):
    section,separator,name=key.partition('.')
    if not separator or section not in DEFAULTS or name not in DEFAULTS[section]:
        raise ValueError('Opção desconhecida. Use sylrics config list.')
    parser=parser_for(path)
    parser[section][name]=str(value)
    write(parser,path)


def set_theme(path,name):
    if name not in (*THEMES, 'dynamic'):
        raise ValueError('Tema desconhecido: '+name)
    parser=parser_for(path)
    parser['theme']['mode']='dynamic' if name=='dynamic' else 'static'
    if name!='dynamic':
        parser['colors']=THEMES[name]
    write(parser,path)
