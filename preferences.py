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
    out.write('; sylrics 0.7.2 — salve para aplicar ao vivo. Ajuda: sylrics config list\n')
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


# Each preset sets the same small set of presentation options. Sources, colors,
# timing, font size, cache and beta preferences are deliberately not part of it.
PRESETS = {
    'minimal': {'layout': {'alignment':'center','vertical':'center','border':'false','line_spacing':'1','history_dim':'true'},
                'visualizer': {'mode':'off','style':'bars','height':'2','width_percent':'70','bar_spacing':'1','bar_width':'1','only_gaps':'false'},
                'pages': {'mode':'rolling','min_lines':'2','max_lines':'3'}},
    'studio': {'layout': {'alignment':'center','vertical':'center','border':'true','line_spacing':'1','history_dim':'true'},
               'visualizer': {'mode':'auto','style':'bars','height':'4','width_percent':'85','bar_spacing':'1','bar_width':'1','only_gaps':'false'},
               'pages': {'mode':'dynamic','min_lines':'2','max_lines':'6'}},
    'cinema': {'layout': {'alignment':'center','vertical':'center','border':'true','line_spacing':'2','history_dim':'true'},
               'visualizer': {'mode':'auto','style':'bars','height':'2','width_percent':'75','bar_spacing':'2','bar_width':'1','only_gaps':'true'},
               'pages': {'mode':'rolling','min_lines':'2','max_lines':'5'}},
}


def set_preset(path, name):
    if name not in PRESETS:
        raise ValueError('Perfil desconhecido: '+name)
    parser = parser_for(path)
    for section, options in PRESETS[name].items():
        parser[section].update(options)
    write(parser, path)


def restore(path):
    path = Path(path)
    backups = sorted((path.parent/'backup').glob('ui-*.ini'))
    if not backups:
        raise ValueError('Nenhum backup de configuração disponível.')
    previous = parser_for(backups[-1])
    write(previous, path)


def reset(path):
    """Restore shipped defaults atomically, preserving the prior INI in backup."""
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_dict(DEFAULTS)
    write(parser, path)
