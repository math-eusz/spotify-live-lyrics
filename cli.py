"""sylrics command library; configuration changes persist and reload live."""
import argparse
import configparser
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from terminal_ui import CONFIG_PATH, Settings
from preferences import ensure, parser_for, set_value, set_theme, THEMES, set_preset, PRESETS, restore, reset, PERFORMANCE, set_performance

VERSION='0.8.6'


def main(argv=None):
    parser=argparse.ArgumentParser(prog='sylrics',description='Letras e visualizador no terminal. Sem Spicy Lyrics obrigatório.')
    parser.add_argument('--version',action='version',version='sylrics '+VERSION)
    parser.add_argument('--config',type=Path,default=CONFIG_PATH,help='arquivo INI alternativo')
    parser.add_argument('--source',choices=('native','auto','spicy'),help='fonte apenas nesta execução')
    sub=parser.add_subparsers(dest='command')
    play=sub.add_parser('play',help='abrir o player (padrão)')
    play.add_argument('--source',choices=('native','auto','spicy'),default=argparse.SUPPRESS)
    performance=sub.add_parser('performance',help='perfil de desempenho, sem alterar o visual')
    performance.add_argument('name',choices=tuple(PERFORMANCE))
    local=sub.add_parser('local-beta',help='reproduzir arquivos locais com mpv, sem Spotify (beta)')
    local.add_argument('files',nargs='+',help='arquivos de áudio ou pastas (sem recursão)')
    controls=sub.add_parser('controls',help='mostrar ou ocultar botões de reprodução')
    controls.add_argument('mode',choices=('on','off'))
    sub.add_parser('demo',help='prévia interativa sem Spotify')
    select=sub.add_parser('source',help='salvar a fonte preferida')
    select.add_argument('mode',choices=('native','auto','spicy'))
    viz=sub.add_parser('visualizer',help='salvar o modo do visualizador')
    viz.add_argument('mode',choices=('auto','spectrum','activity','off'))
    typing=sub.add_parser('typing',help='digitação contínua ou pausas entre palavras (beta)')
    typing.add_argument('mode',choices=('smooth','words-beta'))
    highlight=sub.add_parser('highlight',help='destaque estimado da palavra atual (beta)')
    highlight.add_argument('mode',choices=('off','bold-beta'))
    font=sub.add_parser('font',help='abrir uma janela Kitty com tamanho de fonte próprio')
    font.add_argument('--family', help='família monoespaçada instalada no sistema')
    font.add_argument('size',type=int,nargs='?',help='tamanho de 6 a 48 pontos; reutiliza o tamanho salvo')
    gaps=sub.add_parser('gaps',help='animação de intervalos vocais (beta opcional)')
    gaps.add_argument('mode',choices=('off','dots-beta'))
    seek=sub.add_parser('click-seek',help='buscar trecho clicando em uma palavra (beta)')
    seek.add_argument('mode',choices=('on','off'))
    control=sub.add_parser('control',help='controlar reprodução pelo terminal')
    control.add_argument('action',choices=('play-pause','next','previous'))
    view=sub.add_parser('view',help='interface completa ou somente letras')
    view.add_argument('mode',choices=('full','lyrics'))
    player=sub.add_parser('player',help='player MPRIS: auto, spotify_player ou nome específico')
    player.add_argument('name')
    cover=sub.add_parser('cover',help='mostrar ou ocultar capa do álbum (Kitty)')
    cover.add_argument('mode',choices=('on','off'))
    sub.add_parser('doctor',help='verificar dependências e configuração')
    config=sub.add_parser('config',help='editar configurações persistentes')
    c=config.add_subparsers(dest='config_command')
    for name in ('path','list','edit','restore','reset'):
        c.add_parser(name)
    get=c.add_parser('get');get.add_argument('key')
    put=c.add_parser('set');put.add_argument('key');put.add_argument('value')
    preset=sub.add_parser('preset',help='aplicar um perfil visual com backup')
    preset.add_argument('name',choices=(*PRESETS, 'list'))
    reading=sub.add_parser('reading',help='escolher a organização das frases')
    reading.add_argument('mode',choices=('dynamic','fixed','rolling'))
    theme=sub.add_parser('theme',help='aplicar um tema com backup')
    theme.add_argument('name',choices=(*THEMES, 'dynamic'))
    cache=sub.add_parser('cache',help='gerenciar letras salvas')
    cache.add_argument('action',choices=('clear','info'),default='info',nargs='?')
    bridge=sub.add_parser('bridge',help='ponte opcional do Spicy Lyrics')
    bridge.add_argument('action',choices=('install','status'))
    args=parser.parse_args(argv)
    try:
        if args.command=='doctor':
            config=Settings(args.config);config.reload()
            print('sylrics '+VERSION+'\nConfiguração: '+str(args.config))
            for executable,role in [('playerctl','controle do player nativo'),('cava','espectro de áudio opcional'),('mpv','reprodução local beta opcional'),
                                    ('syncedlyrics','fonte adicional opcional'),('spicetify','ponte opcional')]:
                print(f'{executable}: {shutil.which(executable) or "não instalado"} · {role}')
            from sources import available_players, resolve_player
            from importlib.util import find_spec
            print('Players MPRIS: '+(', '.join(available_players()) or 'nenhum'))
            print('Player selecionado: '+(resolve_player(config.values['playback']['player']) or 'nenhum'))
            print('Capa: '+('Pillow disponível; requer Kitty' if find_spec('PIL') else 'instale python-pillow para habilitar'))
            print('spotify_player: ative enable_media_control = true em app.toml se não for detectado.')
            print('Fonte: '+config.values['playback']['source'])
            print('Configuração: '+(config.error or 'válida'))
            return 1 if config.error else 0
        if args.command=='config' and args.config_command=='path':
            print(args.config)
            return 0
        if args.command=='config' and args.config_command=='edit':
            if not args.config.exists():
                ensure(args.config)
            editor=shlex.split(os.environ.get('EDITOR','nano' if shutil.which('nano') else 'vi'))
            return subprocess.call(editor+[str(args.config)])
        if args.command=='config' and args.config_command=='restore':
            restore(args.config)
            print('Configuração anterior restaurada; estado atual salvo em backup.')
            return 0
        if args.command=='config' and args.config_command=='reset':
            reset(args.config)
            print('Configurações padrão restauradas; configuração anterior salva em backup.')
            return 0
        ensure(args.config)
        if args.command=='config':
            p=parser_for(args.config)
            if args.config_command=='set':
                set_value(args.config,args.key,args.value)
                print(f'{args.key} = {args.value} · salvo, aplica ao vivo')
            elif args.config_command=='get':
                section,_,key=args.key.partition('.')
                if not p.has_option(section,key):
                    raise ValueError('Opção desconhecida')
                print(p[section][key])
            else:
                for section in p.sections():
                    for key,value in p[section].items():
                        print(f'{section}.{key} = {value}')
            return 0
        if args.command=='performance':
            set_performance(args.config,args.name)
            print('Desempenho: '+args.name+' · salvo')
            return 0
        if args.command=='preset':
            if args.name=='list':
                print('minimal · leitura discreta\nstudio · letras e espectro amplo\ncinema · leitura contínua com espaço entre frases')
            else:
                set_preset(args.config,args.name)
                print('Perfil '+args.name+' aplicado. Tema e fonte de letras preservados.')
            return 0
        if args.command=='reading':
            set_value(args.config,'pages.mode',args.mode)
            print('Modo de leitura: '+args.mode+' · salvo')
            return 0
        if args.command=='font':
            executable=shutil.which('kitty')
            if not executable:
                raise ValueError('Este comando requer Kitty. Em outros terminais, use o zoom do próprio terminal.')
            current=Settings(args.config);current.reload()
            size=args.size if args.size is not None else int(current.values['layout']['font_size'])
            if not 6 <= size <= 48:
                raise ValueError('O tamanho da fonte deve estar entre 6 e 48 pontos.')
            family=args.family or current.values['layout']['font_family']
            from terminal_ui import safe
            if not family.strip() or len(family)>120 or safe(family)!=family:
                raise ValueError('Família de fonte inválida.')
            command=[executable,'--override',f'font_size={size}','--override',f'font_family={family}',sys.executable,
                     str(Path(__file__).resolve()),'--config',str(args.config.resolve())]
            if args.source:
                command.extend(['--source',args.source])
            set_value(args.config,'layout.font_family',family)
            set_value(args.config,'layout.font_size',str(size))
            return subprocess.call(command)
        if args.command in ('gaps','click-seek'):
            key='pages.gap_animation' if args.command=='gaps' else 'layout.click_seek'
            set_value(args.config,key,'false' if args.mode=='off' else 'true')
            print(('Intervalos (beta): ' if args.command=='gaps' else 'Clique nas palavras (beta): ')+args.mode+' · salvo')
            return 0
        if args.command=='highlight':
            set_value(args.config,'layout.word_highlight',args.mode)
            print('Destaque da palavra: '+args.mode+' · salvo')
            return 0
        if args.command=='typing':
            set_value(args.config,'playback.typing_mode',args.mode)
            print('Modo de digitação: '+args.mode+' · salvo')
            return 0
        if args.command in ('source','visualizer'):
            key='playback.source' if args.command=='source' else 'visualizer.mode'
            set_value(args.config,key,args.mode)
            print(key+' = '+args.mode+' · salvo')
            return 0
        if args.command in ('view','player','cover','controls'):
            key={'view':'layout.view','player':'playback.player','cover':'layout.cover','controls':'layout.controls'}[args.command]
            value=args.name if args.command=='player' else ('true' if args.mode=='on' else 'false') if args.command in ('cover','controls') else args.mode
            set_value(args.config,key,value)
            print(key+' = '+value+' · salvo')
            return 0
        if args.command=='control':
            settings=Settings(args.config);settings.reload()
            from sources import resolve_player
            selected=resolve_player(settings.values['playback']['player'])
            if not selected:
                raise ValueError('Nenhum player compatível encontrado. Execute sylrics doctor.')
            return subprocess.call(['playerctl','-p',selected,args.action])
        if args.command=='theme':
            set_theme(args.config,args.name)
            print('Tema '+args.name+' aplicado.')
            return 0
        if args.command=='cache':
            from lrc_store import LrcStore
            store=LrcStore()
            store.maintain()
            if args.action=='clear':
                print(f'{store.clear()} letras removidas do cache.')
            else:
                print(f'{len(store.files())}/10 letras · {store.directory}')
            return 0
        if args.command=='bridge':
            if args.action=='install':
                from install_bridge import install
                install()
            else:
                from bridge_runtime import config_path
                print('Configurada: '+str(config_path()) if config_path().is_file() else 'Não configurada (opcional).')
            return 0
        from app import run
        if args.command=='local-beta':
            from local_player import collect_files
            return run(args.config,local_files=collect_files(args.files))
        return run(args.config,args.source,demo=args.command=='demo')
    except (OSError,ValueError,KeyError,configparser.Error,subprocess.SubprocessError) as error:
        print('sylrics: '+str(error),file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())

